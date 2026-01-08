import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta

# ===================== LOAD DATA =====================
def load_data():
    try:
        df = pd.read_excel("Aden_METAR_Final_Report.xlsx")
        df.columns = df.columns.str.strip()
        df["Full_Timestamp"] = pd.to_datetime(df["Date"].astype(str) + " " + df["UTC"].astype(str), errors="coerce")
        df["Display_Time"] = df["Full_Timestamp"].dt.strftime('%Y-%m-%d %H:%M')
        df["Date_Only"] = df["Full_Timestamp"].dt.date
        
        # تحويل الأعمدة إلى أرقام لضمان ظهور المخططات
        numeric_cols = ["Temp C", "Visibility M", "Humidity %", "Pressure hPa", "Wind Speed KT"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        return df.dropna(subset=["Full_Timestamp"])
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()

df_main = load_data()

# ===================== APP SETUP =====================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG], suppress_callback_exceptions=True)
server = app.server

# ===================== LAYOUT =====================
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    
    # Sidebar
    html.Div(style={
        "position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "18rem",
        "padding": "2rem 1rem", "backgroundColor": "#050505", "borderRight": "2px solid #00f2ff"
    }, children=[
        html.H2("OYAA HUB", style={"color": "#00f2ff", "fontFamily": "Orbitron", "textAlign": "center"}),
        html.Hr(style={"borderColor": "#00f2ff"}),
        dbc.Nav([
            dbc.NavLink("🏠 HOME", href="/", active="exact"),
            dbc.NavLink("📊 ANALYTICS", href="/dashboard", active="exact"),
        ], vertical=True, pills=True),
        html.Div(id="sidebar-filters", style={"marginTop": "20px"})
    ]),

    # Main Content
    html.Div(id="page-content", style={"marginLeft": "18rem", "padding": "2rem"})
])

# ===================== CALLBACKS =====================
@app.callback(
    [Output("page-content", "children"), Output("sidebar-filters", "children")],
    [Input("url", "pathname")]
)
def render_page(pathname):
    if pathname == "/dashboard":
        if df_main.empty:
            return html.Div("تحذير: ملف البيانات غير موجود أو فارغ في GitHub!"), []
            
        min_date = df_main["Date_Only"].min()
        max_date = df_main["Date_Only"].max()
        
        filters = [
            html.Label("SELECT DATE RANGE:", style={"color": "#00f2ff", "fontSize": "12px"}),
            dcc.DatePickerRange(
                id="date-picker",
                min_date_allowed=min_date,
                max_date_allowed=max_date,
                start_date=min_date,
                end_date=max_date,
                style={"fontSize": "10px"}
            )
        ]
        
        content = html.Div([
            html.H1("ADEN AIRPORT REAL-TIME ANALYTICS", style={"color": "#00f2ff", "textAlign": "center", "fontFamily": "Orbitron"}),
            html.Div(id="stats-cards", style={"marginTop": "20px"}),
            
            # قسم المخططات
            dbc.Row([
                dbc.Col(dcc.Graph(id="temp-graph"), width=6),
                dbc.Col(dcc.Graph(id="wind-graph"), width=6),
            ], style={"marginTop": "20px"}),
            
            dbc.Row([
                dbc.Col(dcc.Graph(id="humidity-graph"), width=6),
                dbc.Col(dcc.Graph(id="pressure-graph"), width=6),
            ], style={"marginTop": "20px"}),
            
            html.H3("VISIBILITY MONITOR (M)", style={"color": "#00f2ff", "marginTop": "40px"}),
            dcc.Graph(id="visibility-graph"),
            
            html.H3("RAW DATA LOGS", style={"color": "#00f2ff", "marginTop": "40px"}),
            html.Div(id="data-table")
        ])
        return content, filters

    # Home Page
    return html.Div(style={
        "height": "80vh", "display": "flex", "flexDirection": "column", "justifyContent": "center", "alignItems": "center"
    }, children=[
        html.H1("WELCOME TO OYAA HUB", style={"fontSize": "60px", "color": "#fff", "fontFamily": "Orbitron"}),
        html.P("ADEN INTERNATIONAL AIRPORT WEATHER SYSTEM", style={"color": "#00f2ff", "fontSize": "20px"}),
        dbc.Button("ENTER ANALYTICS", href="/dashboard", color="info", size="lg", style={"marginTop": "20px"})
    ]), []

@app.callback(
    [Output("stats-cards", "children"), Output("temp-graph", "figure"), 
     Output("wind-graph", "figure"), Output("humidity-graph", "figure"),
     Output("pressure-graph", "figure"), Output("visibility-graph", "figure"),
     Output("data-table", "children")],
    [Input("date-picker", "start_date"), Input("date-picker", "end_date")]
)
def update_graphs(start, end):
    dff = df_main[(df_main["Date_Only"] >= date.fromisoformat(start)) & (df_main["Date_Only"] <= date.fromisoformat(end))]
    dff = dff.sort_values("Full_Timestamp")

    # 1. Stats
    stats = dbc.Row([
        dbc.Col(dbc.Card([html.H5("MAX TEMP"), html.H2(f"{dff['Temp C'].max()}°C")], body=True, color="danger", inverse=True)),
        dbc.Col(dbc.Card([html.H5("AVG HUMIDITY"), html.H2(f"{dff['Humidity %'].mean():.1f}%")], body=True, color="info", inverse=True)),
        dbc.Col(dbc.Card([html.H5("AVG WIND"), html.H2(f"{dff['Wind Speed KT'].mean():.1f} KT")], body=True, color="success", inverse=True)),
    ])

    # 2. Graphs
    f_temp = px.line(dff, x="Full_Timestamp", y="Temp C", title="Temperature Variation", template="plotly_dark").update_traces(line_color="#ff4b4b")
    f_wind = px.area(dff, x="Full_Timestamp", y="Wind Speed KT", title="Wind Speed Trends", template="plotly_dark").update_traces(line_color="#00ffcc")
    f_hum = px.line(dff, x="Full_Timestamp", y="Humidity %", title="Humidity Levels", template="plotly_dark").update_traces(line_color="#00f2ff")
    f_press = px.line(dff, x="Full_Timestamp", y="Pressure hPa", title="Barometric Pressure", template="plotly_dark").update_traces(line_color="#ffd700")
    f_vis = px.bar(dff, x="Full_Timestamp", y="Visibility M", title="Visibility Range", template="plotly_dark").update_traces(marker_color="#ffffff")

    # 3. Table
    table = dash_table.DataTable(
        data=dff.to_dict("records"),
        columns=[{"name": i, "id": i} for i in ["Display_Time", "Temp C", "Wind Speed KT", "METAR"]],
        style_table={'overflowX': 'auto'},
        style_cell={'backgroundColor': '#111', 'color': '#fff', 'textAlign': 'left'},
        page_size=10
    )

    return stats, f_temp, f_wind, f_hum, f_press, f_vis, table

if __name__ == "__main__":
    app.run(debug=True)
