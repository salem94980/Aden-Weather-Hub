import dash
from dash import dcc, html, Input, Output, dash_table, State
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
        df = pd.read_excel("Aden_METAR_Final_Report.xlsx")
        df.columns = df.columns.str.strip()
        df["Full_Timestamp"] = pd.to_datetime(df["Date"].astype(str) + " " + df["UTC"].astype(str), errors="coerce")
        df["Date_Only"] = df["Full_Timestamp"].dt.date
        df["Hour"] = df["Full_Timestamp"].dt.hour
        df["Display_Time"] = df["Full_Timestamp"].dt.strftime('%Y-%m-%d   %H:%M')
        
        cols = ["Temp C", "DewPoint", "Humidity %", "Pressure hPa"] # أضف بقية الأعمدة هنا
        df["DewPoint"] = df.apply(lambda x: calculate_dewpoint(x["Temp C"], x["Humidity %"]), axis=1)
        return df.dropna(subset=["Full_Timestamp"])
    except:
        return pd.DataFrame()

df_main = load_data()
max_dt = df_main["Date_Only"].max() if not df_main.empty else date.today()

# ===================== DASH APP =====================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    
    # الـ Sidebar ثابت في الـ Layout لضمان استقرار الفلاتر
    html.Div(id="sidebar-id", style={
        "position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "18rem", 
        "padding": "2rem 1rem", "backgroundColor": "#0a0c10", "borderRight": "1px solid #1a1e26", "zIndex": 100
    }, children=[
        html.H2("OYAA HUB", style={"fontFamily": "Orbitron", "color": "#00f2ff", "textAlign": "center"}),
        html.Hr(style={"borderColor": "#00f2ff", "opacity": "0.3"}),
        dbc.Nav([
            dbc.NavLink("🏠 HOME", href="/", active="exact"),
            dbc.NavLink("📊 ANALYTICS", href="/dashboard", active="exact"),
        ], vertical=True, pills=True),
        html.Hr(style={"borderColor": "#00f2ff", "opacity": "0.3"}),
        
        # الفلتر "موجود" دائماً تقنياً، لكننا نتحكم في ظهوره
        html.Div(id="filter-wrapper", children=[
            html.Label("TIME RANGE", style={"fontSize": "11px", "color": "#8b949e"}),
            dcc.DatePickerRange(
                id="d-picker",
                start_date=max_dt - timedelta(days=7),
                end_date=max_dt,
                display_format='YYYY-MM-DD'
            ),
            html.Br(), html.Br(),
            html.Label("HOUR SELECTOR", style={"fontSize": "11px", "color": "#8b949e"}),
            dcc.Dropdown(id="h-drop", options=[{"label": f"{h:02d}:00", "value": h} for h in range(24)], multi=True, style={"color": "black"})
        ])
    ]),

    html.Div(id="page-content", style={"marginLeft": "18rem", "minHeight": "100vh"})
])

# ===================== CALLBACKS =====================

# 1. المبدل بين الصفحات (يتحكم فقط في إظهار/إخفاء العناصر)
@app.callback(
    [Output("page-content", "children"), Output("sidebar-id", "style"), Output("filter-wrapper", "style")],
    [Input("url", "pathname")]
)
def render_page(pathname):
    bg_image = "https://raw.githubusercontent.com/salem94980/Aden-Weather-Hub/main/assets/aden_airport.jpg"
    
    if pathname == "/dashboard":
        layout = html.Div(style={"padding": "2.5rem", "backgroundColor": "#0d1117"}, children=[
            html.H2("OPERATIONAL METAR ANALYTICS", style={"fontFamily": "Orbitron", "color": "#00f2ff"}),
            html.Div(id="stats-row"),
            dcc.Graph(id="t-line-big"),
            dcc.Graph(id="d-line-big"),
            html.Div(id="metar-table-area")
        ])
        # إظهار الـ Sidebar والفلتر
        return layout, {"display": "block", "position": "fixed", "width": "18rem", "height": "100vh", "backgroundColor": "#0a0c10", "padding": "2rem 1rem"}, {"display": "block"}

    # الصفحة الرئيسية
    home_layout = html.Div(style={
        "height": "100vh", "width": "100vw", "marginLeft": "-18rem",
        "backgroundImage": f'linear-gradient(rgba(10, 12, 16, 0.5), rgba(10, 12, 16, 0.9)), url("{bg_image}")',
        "backgroundSize": "cover", "backgroundPosition": "center", "display": "flex", "flexDirection": "column", "justifyContent": "center", "alignItems": "center"
    }, children=[
        html.H1("OYAA INTELHUB", style={"fontSize": "80px", "color": "#ffffff", "fontFamily": "Orbitron"}),
        html.A(dbc.Button("INITIATE ANALYTICS", color="info", outline=True), href="/dashboard")
    ])
    # إخفاء الـ Sidebar والفلتر
    return home_layout, {"display": "none"}, {"display": "none"}

# 2. المحدث الفعلي للبيانات (يعمل دائماً لأن الفلتر ثابت في الـ Layout)
@app.callback(
    [Output("stats-row", "children"), Output("t-line-big", "figure"), Output("d-line-big", "figure"), Output("metar-table-area", "children")],
    [Input("d-picker", "start_date"), Input("d-picker", "end_date"), Input("h-drop", "value")]
)
def update_dash(start, end, hours):
    if not start or not end: return [dash.no_update]*4
    
    # الفلترة
    sd = pd.to_datetime(start).date()
    ed = pd.to_datetime(end).date()
    dff = df_main[(df_main["Date_Only"] >= sd) & (df_main["Date_Only"] <= ed)]
    
    if hours: dff = dff[dff["Hour"].isin(hours)]
    dff = dff.sort_values("Full_Timestamp")

    if dff.empty: return [html.Div("No Data")] + [go.Figure()]*2 + [html.Div()]

    # الرسوم
    f_t = px.line(dff, x="Full_Timestamp", y="Temp C", template="plotly_dark", title="TEMPERATURE").update_traces(line_color="#ff5f5f")
    f_d = px.line(dff, x="Full_Timestamp", y="DewPoint", template="plotly_dark", title="DEW POINT").update_traces(line_color="#00f2ff")
    
    stats = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("AVG TEMP"), html.H3(f"{dff['Temp C'].mean():.1f}°C")]))),
    ])

    table = dash_table.DataTable(
        data=dff[["Display_Time", "METAR"]].to_dict("records"),
        columns=[{"name": "TIME", "id": "Display_Time"}, {"name": "METAR", "id": "METAR"}],
        style_table={'height': '300px', 'overflowY': 'auto'},
        style_cell={'backgroundColor': '#161b22', 'color': 'white'}
    )

    return stats, f_t, f_d, table

if __name__ == "__main__":
    app.run(debug=True)
