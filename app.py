import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import date, timedelta

# ===================== LOAD DATA =====================
def load_data():
    try:
        # قراءة الملف من المجلد الرئيسي
        df = pd.read_excel("Aden_METAR_Final_Report.xlsx", engine='openpyxl')
        df.columns = df.columns.str.strip()
        
        # تحويل الوقت والتاريخ
        df["Full_Timestamp"] = pd.to_datetime(df["Date"].astype(str) + " " + df["UTC"].astype(str), errors="coerce")
        df["Display_Time"] = df["Full_Timestamp"].dt.strftime('%Y-%m-%d %H:%M')
        df["Date_Only"] = df["Full_Timestamp"].dt.date
        df["Hour"] = df["Full_Timestamp"].dt.hour
        
        # تحويل الأرقام
        numeric_cols = ["Temp C", "DewPt C", "Humidity %", "Pressure hPa", "Wind Spd KT", "Visibility M", "Lowest Cloud Base FT"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        return df.dropna(subset=["Full_Timestamp"]).sort_values("Full_Timestamp")
    except Exception as e:
        print(f"Data Loading Error: {e}")
        return pd.DataFrame()

df_main = load_data()

# ===================== APP SETUP =====================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)
server = app.server

SIDEBAR_STYLE = {
    "position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "18rem",
    "padding": "2rem 1rem", "backgroundColor": "#0a0c10", "borderRight": "1px solid #00f2ff", "zIndex": 100
}

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    # القائمة الجانبية ستظهر فقط في صفحة التحليلات عبر الكولباك
    html.Div(id="sidebar-container"),
    html.Div(id="page-content")
])

# ===================== CALLBACKS =====================

@app.callback(
    [Output("page-content", "children"), Output("sidebar-container", "children")],
    [Input("url", "pathname")]
)
def render_page(pathname):
    # رابط الصورة المباشر من مستودعك
    img_url = "https://raw.githubusercontent.com/salem94980/Aden-Weather-Hub/main/assets/aden_airport.jpg"

    if pathname == "/dashboard":
        if df_main.empty:
            return html.Div([html.H3("⚠️ عذراً، لم يتم العثور على بيانات في ملف الإكسل", style={"color":"orange", "textAlign":"center", "marginTop":"50px"})]), None
        
        # محتوى القائمة الجانبية
        max_dt = df_main["Date_Only"].max()
        sidebar = html.Div(style=SIDEBAR_STYLE, children=[
            html.H2("OYAA HUB", style={"fontFamily": "Orbitron", "color": "#00f2ff", "textAlign": "center", "fontSize": "22px"}),
            html.Hr(style={"borderColor": "#00f2ff"}),
            dbc.Nav([
                dbc.NavLink("🏠 HOME", href="/", active="exact"),
                dbc.NavLink("📊 ANALYTICS", href="/dashboard", active="exact"),
            ], vertical=True, pills=True),
            html.Hr(),
            html.Label("TIME RANGE", style={"fontSize": "11px", "color": "#8b949e"}),
            dcc.DatePickerRange(id="d-picker", start_date=max_dt - timedelta(days=7), end_date=max_dt, style={"width":"100%"}),
            html.Br(), html.Br(),
            dcc.Dropdown(id="h-drop", placeholder="Select Hour", options=[{"label": f"{h:02d}:00", "value": h} for h in range(24)], multi=True, style={"color": "black"})
        ])

        # محتوى صفحة التحليلات
        content = html.Div(style={"marginLeft": "18rem", "padding": "2rem", "backgroundColor": "#0d1117"}, children=[
            html.H2("ADEN OPERATIONAL ANALYTICS", style={"fontFamily": "Orbitron", "color": "#00f2ff"}),
            html.Div(id="stats-cards"),
            dcc.Graph(id="main-temp-graph"),
            html.H4("METAR LOGS", className="mt-4", style={"color":"#00f2ff"}),
            html.Div(id="table-container")
        ])
        return content, sidebar

    # الصفحة الرئيسية (Landing Page) مع الصورة
    home = html.Div(style={
        "height": "100vh", "width": "100vw",
        "backgroundImage": f'linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.8)), url("{img_url}")',
        "backgroundSize": "cover", "backgroundPosition": "center",
        "display": "flex", "flexDirection": "column", "justifyContent": "center", "alignItems": "center", "textAlign": "center"
    }, children=[
        html.H1("OYAA INTELHUB", style={"fontSize": "80px", "color": "#fff", "fontFamily": "Orbitron", "fontWeight": "900"}),
        html.P("ADEN INTERNATIONAL AIRPORT WEATHER INTELLIGENCE", style={"color": "#00f2ff", "fontSize": "20px", "letterSpacing": "5px"}),
        html.Br(),
        dbc.Button("INITIATE ANALYTICS", href="/dashboard", color="info", outline=True, size="lg", style={"fontFamily": "Orbitron", "borderWidth":"2px"})
    ])
    return home, None

@app.callback(
    [Output("stats-cards", "children"), Output("main-temp-graph", "figure"), Output("table-container", "children")],
    [Input("d-picker", "start_date"), Input("d-picker", "end_date"), Input("h-drop", "value")]
)
def update_dashboard(start, end, hours):
    if df_main.empty: return None, go.Figure(), None
    
    dff = df_main[(df_main["Date_Only"] >= date.fromisoformat(start)) & (df_main["Date_Only"] <= date.fromisoformat(end))]
    if hours: dff = dff[dff["Hour"].isin(hours)]
    
    # الكروت
    cards = dbc.Row([
        dbc.Col(dbc.Card([html.H6("AVG TEMP"), html.H2(f"{dff['Temp C'].mean():.1f}°C")], body=True, color="dark", style={"border":"1px solid #ff5f5f", "textAlign":"center"})),
        dbc.Col(dbc.Card([html.H6("AVG HUMIDITY"), html.H2(f"{dff['Humidity %'].mean():.1f}%")], body=True, color="dark", style={"border":"1px solid #00f2ff", "textAlign":"center"})),
    ], className="mb-4")

    # المخطط
    fig = px.line(dff, x="Full_Timestamp", y="Temp C", title="Temperature Trend", template="plotly_dark")
    fig.update_traces(line_color="#ff5f5f")
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # الجدول
    table = dash_table.DataTable(
        data=dff.tail(15).to_dict("records"),
        columns=[{"name": "TIME", "id": "Display_Time"}, {"name": "METAR", "id": "METAR"}],
        style_table={'overflowX': 'auto'},
        style_cell={'backgroundColor': '#111', 'color': '#fff', 'textAlign': 'left', 'fontFamily': 'monospace'},
        style_header={'backgroundColor': '#161b22', 'color': '#00f2ff'}
    )
    
    return cards, fig, table

if __name__ == "__main__":
    app.run(debug=True)
