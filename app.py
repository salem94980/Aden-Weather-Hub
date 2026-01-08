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
        # تأكد أن اسم الملف هنا يطابق ملفك بالضبط
        df = pd.read_excel("Aden_METAR_Final_Report.xlsx")
        df.columns = df.columns.str.strip()
        df["Full_Timestamp"] = pd.to_datetime(df["Date"].astype(str) + " " + df["UTC"].astype(str), errors="coerce")
        df["Display_Time"] = df["Full_Timestamp"].dt.strftime('%Y-%m-%d   %H:%M')
        df["Date_Only"] = df["Full_Timestamp"].dt.date
        df["Hour"] = df["Full_Timestamp"].dt.hour
        
        # تحويل الأعمدة لأرقام لضمان عمل الرسوم
        cols = ["Temp C", "Visibility M", "Humidity %", "Pressure hPa", "Wind Dir", "Lowest Cloud Base FT"]
        for col in cols:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors="coerce")
        
        df["DewPoint"] = df.apply(lambda x: calculate_dewpoint(x["Temp C"], x["Humidity %"]), axis=1)
        return df.dropna(subset=["Full_Timestamp"])
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()

df_main = load_data()

# ===================== DASH APP =====================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)
server = app.server  # السطر المطلوب للرابط القديم

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    
    # Sidebar الاحترافي باللون الداكن
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
        max_dt = df_main["Date_Only"].max() if not df_main.empty else date.today()
        filters = [
            html.Label("TIME RANGE", style={"fontSize": "11px", "color": "#8b949e", "letterSpacing": "1.5px"}),
            dcc.DatePickerRange(id="d-picker", start_date=max_dt - timedelta(days=7), end_date=max_dt),
            html.Br(), html.Br(),
            html.Label("HOUR SELECTOR (UTC)", style={"fontSize": "11px", "color": "#8b949e", "letterSpacing": "1.5px"}),
            dcc.Dropdown(id="h-drop", options=[{"label": f"{h:02d}:00", "value": h} for h in range(24)], multi=True, style={"color": "black"})
        ]
        
        layout = html.Div(style={"padding": "2.5rem", "backgroundColor": "#0d1117"}, children=[
            html.H2("ADEN (OYAA) ANALYTICS", style={"fontFamily": "Orbitron", "color": "#00f2ff", "letterSpacing": "3px", "marginBottom": "40px"}),
            html.Div(id="stats-row"),
            
            html.H3("🌡️ TEMPERATURE DYNAMICS", style={"color": "#ff5f5f", "marginTop": "30px", "fontWeight": "bold"}),
            dcc.Graph(id="t-line-big"),

            html.H3("❄️ DEW POINT MONITOR", style={"color": "#00f2ff", "marginTop": "40px", "fontWeight": "bold"}),
            dcc.Graph(id="d-line-big"),

            html.H3("📜 SYSTEM LOGS", style={"color": "#8b949e", "marginTop": "60px", "fontWeight": "bold"}),
            html.Div(id="metar-table-area", style={"marginBottom": "100px"})
        ])
        return layout, filters
    
    # Landing Page - مطار عدن فقط
    return html.Div(style={
        "height": "100vh",
        "backgroundImage": f'linear-gradient(rgba(10, 12, 16, 0.4), rgba(10, 12, 16, 0.9)), url("{app.get_asset_url("aden_airport.jpg")}")',
        "backgroundSize": "cover", "backgroundPosition": "center",
        "display": "flex", "flexDirection": "column", "justifyContent": "center", "alignItems": "center", "textAlign": "center"
    }, children=[
        html.H1("OYAA INTELHUB", style={"fontSize": "80px", "color": "#ffffff", "fontFamily": "Orbitron", "letterSpacing": "10px", "fontWeight": "900"}),
        html.Div(style={"width": "150px", "height": "4px", "backgroundColor": "#00f2ff", "margin": "20px 0"}),
        html.P("ADEN INTERNATIONAL AIRPORT WEATHER INTELLIGENCE", style={"color": "#00f2ff", "fontSize": "18px", "letterSpacing": "5px"}),
        html.Br(),
        html.A(html.Button("INITIATE ANALYTICS", style={
            "backgroundColor": "transparent", "color": "#00f2ff", "border": "2px solid #00f2ff",
            "padding": "15px 45px", "fontSize": "18px", "fontFamily": "Orbitron", "cursor": "pointer"
        }), href="/dashboard")
    ])

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
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("AVERAGE TEMPERATURE"), html.H3(f"{dff['Temp C'].mean():.1f}°C", style={"color": "#ff5f5f"})])], style={"backgroundColor": "#161b22", "border": "1px solid #30363d"})),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("AVERAGE HUMIDITY"), html.H3(f"{dff['Humidity %'].mean():.1f}%", style={"color": "#00f2ff"})])], style={"backgroundColor": "#161b22", "border": "1px solid #30363d"})),
        # الرؤية بوحدة m صغيرة
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("MINIMUM VISIBILITY"), html.H3(f"{dff['Visibility M'].min():.0f} m", style={"color": "#ffd33d"})])], style={"backgroundColor": "#161b22", "border": "1px solid #30363d"})),
    ], className="mb-4 text-center")

    f_t = px.line(dff, x="Full_Timestamp", y="Temp C", template="plotly_dark", height=600).update_traces(line_color="#ff5f5f", line_width=4)
    f_d = px.line(dff, x="Full_Timestamp", y="DewPoint", template="plotly_dark", height=600).update_traces(line_color="#00f2ff", line_width=4)

    table = dash_table.DataTable(
        data=dff[["Display_Time", "METAR"]].to_dict("records"),
        columns=[{"name": "UTC TIMESTAMP", "id": "Display_Time"}, {"name": "RAW METAR DATA", "id": "METAR"}],
        fixed_rows={'headers': True},
        style_table={'height': '400px', 'overflowY': 'auto'},
        style_cell={"backgroundColor": "#0d1117", "color": "#c9d1d9", "textAlign": "left", "fontFamily": "monospace", "padding": "12px"},
        style_header={"backgroundColor": "#161b22", "color": "#00f2ff", "fontWeight": "bold"}
    )
    return stats, f_t, f_d, table

if __name__ == "__main__":
    app.run(debug=True)