import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import date, timedelta

# ===================== FUNCTIONS =====================
def calculate_dewpoint(T, RH):
    if pd.isna(T) or pd.isna(RH) or RH <= 0: return np.nan
    gamma = (17.67 * T / (243.5 + T)) + np.log(RH / 100.0)
    return (243.5 * gamma) / (17.67 - gamma)

# ===================== LOAD DATA =====================
def load_data():
    try:
        # قراءة الملف
        df = pd.read_excel("Aden_METAR_Final_Report.xlsx")
        df.columns = df.columns.str.strip()
        df["Full_Timestamp"] = pd.to_datetime(df["Date"].astype(str) + " " + df["UTC"].astype(str), errors="coerce")
        df["Display_Time"] = df["Full_Timestamp"].dt.strftime('%Y-%m-%d %H:%M')
        df["Date_Only"] = df["Full_Timestamp"].dt.date
        df["Hour"] = df["Full_Timestamp"].dt.hour
        
        cols = ["Temp C", "Visibility M", "Humidity %", "Pressure hPa", "Wind Speed KT"]
        for col in cols:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors="coerce")
        
        df["DewPoint"] = df.apply(lambda x: calculate_dewpoint(x["Temp C"], x["Humidity %"]), axis=1)
        return df.dropna(subset=["Full_Timestamp"])
    except Exception as e:
        print(f"Error loading Excel: {e}")
        return pd.DataFrame()

df_main = load_data()

# ===================== DASH APP =====================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)
server = app.server 

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    
    # Sidebar
    html.Div(style={
        "position": "fixed", "top": 0, "left": 0, "bottom": 0, 
        "width": "18rem", "padding": "2rem 1rem", "backgroundColor": "#0a0c10", 
        "borderRight": "1px solid #1a1e26", "zIndex": 100
    }, children=[
        html.H2("OYAA HUB", style={"fontFamily": "Orbitron", "color": "#00f2ff", "textAlign": "center", "fontSize": "22px"}),
        html.Hr(style={"borderColor": "#00f2ff", "opacity": "0.3"}),
        dbc.Nav([
            dbc.NavLink("🏠 HOME", href="/", active="exact", style={"borderRadius": "8px", "marginBottom": "10px"}),
            dbc.NavLink("📊 ANALYTICS", href="/dashboard", active="exact", style={"borderRadius": "8px"}),
        ], vertical=True, pills=True),
        html.Hr(style={"borderColor": "#00f2ff", "opacity": "0.3"}),
        html.Div(id="filters-container")
    ]),

    html.Div(id="page-content", style={"marginLeft": "18rem", "minHeight": "100vh"})
])

# ===================== CALLBACKS =====================

@app.callback(
    [Output("page-content", "children"), Output("filters-container", "children")],
    [Input("url", "pathname")]
)
def render_page(pathname):
    if pathname == "/dashboard":
        if df_main.empty:
            return html.Div("Data file not found or empty. Please check GitHub."), []
            
        # جعل الفلتر يختار آخر تاريخ متاح تلقائياً
        max_dt = df_main["Date_Only"].max()
        min_dt = df_main["Date_Only"].min()
        
        filters = [
            html.Label("TIME RANGE", style={"fontSize": "11px", "color": "#8b949e", "letterSpacing": "1.5px"}),
            dcc.DatePickerRange(
                id="d-picker", 
                start_date=min_dt, 
                end_date=max_dt,
                display_format='Y-MM-DD'
            ),
            html.Br(), html.Br(),
            html.Label("HOUR SELECTOR (UTC)", style={"fontSize": "11px", "color": "#8b949e", "letterSpacing": "1.5px"}),
            dcc.Dropdown(id="h-drop", options=[{"label": f"{h:02d}:00", "value": h} for h in range(24)], multi=True, style={"color": "black"})
        ]
        
        layout = html.Div(style={"padding": "2.5rem", "backgroundColor": "#0d1117"}, children=[
            html.H2("ADEN (OYAA) ANALYTICS", style={"fontFamily": "Orbitron", "color": "#00f2ff", "letterSpacing": "3px", "marginBottom": "40px"}),
            html.Div(id="stats-row"),
            dcc.Graph(id="t-line-big"),
            dcc.Graph(id="d-line-big"),
            html.Div(id="metar-table-area", style={"marginTop": "30px", "marginBottom": "100px"})
        ])
        return layout, filters
    
    # Home Page
    return html.Div(style={
        "height": "100vh", "backgroundColor": "#0a0c10",
        "display": "flex", "flexDirection": "column", "justifyContent": "center", "alignItems": "center", "textAlign": "center"
    }, children=[
        html.H1("OYAA INTELHUB", style={"fontSize": "80px", "color": "#ffffff", "fontFamily": "Orbitron", "letterSpacing": "10px"}),
        html.P("ADEN INTERNATIONAL AIRPORT WEATHER INTELLIGENCE", style={"color": "#00f2ff", "fontSize": "18px"}),
        html.Br(),
        dbc.Button("INITIATE ANALYTICS", href="/dashboard", color="info", outline=True, size="lg")
    ]), []

@app.callback(
    [Output("stats-row", "children"), Output("t-line-big", "figure"), Output("d-line-big", "figure"), 
     Output("metar-table-area", "children")],
    [Input("d-picker", "start_date"), Input("d-picker", "end_date"), Input("h-drop", "value")]
)
def update_dash(start, end, hours):
    if not start or not end: return [dash.no_update]*4
    
    dff = df_main[(df_main["Date_Only"] >= date.fromisoformat(start)) & (df_main["Date_Only"] <= date.fromisoformat(end))]
    if hours: dff = dff[dff["Hour"].isin(hours)]
    dff = dff.sort_values("Full_Timestamp")
    
    if dff.empty: return [html.Div("No Data Found")] + [go.Figure()]*2 + [html.Div()]

    stats = dbc.Row([
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("AVG TEMP"), html.H3(f"{dff['Temp C'].mean():.1f}°C", style={"color": "#ff5f5f"})])], style={"backgroundColor": "#161b22"})),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("AVG HUMIDITY"), html.H3(f"{dff['Humidity %'].mean():.1f}%", style={"color": "#00f2ff"})])], style={"backgroundColor": "#161b22"})),
    ], className="mb-4 text-center")

    f_t = px.line(dff, x="Full_Timestamp", y="Temp C", title="Temperature Trends", template="plotly_dark").update_traces(line_color="#ff5f5f")
    f_d = px.line(dff, x="Full_Timestamp", y="DewPoint", title="Dew Point Trends", template="plotly_dark").update_traces(line_color="#00f2ff")

    table = dash_table.DataTable(
        data=dff.to_dict("records"),
        columns=[{"name": "UTC TIMESTAMP", "id": "Display_Time"}, {"name": "RAW METAR", "id": "METAR"}],
        style_table={'overflowY': 'auto'},
        style_cell={"backgroundColor": "#0d1117", "color": "#c9d1d9", "textAlign": "left"},
        page_size=15
    )
    return stats, f_t, f_d, table

if __name__ == "__main__":
    app.run(debug=True)
