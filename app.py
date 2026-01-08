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
        df["Display_Time"] = df["Full_Timestamp"].dt.strftime('%Y-%m-%d   %H:%M')
        df["Date_Only"] = df["Full_Timestamp"].dt.date
        df["Hour"] = df["Full_Timestamp"].dt.hour
        cols = ["Temp C", "Visibility M", "Humidity %", "Pressure hPa", "Wind Dir", "Lowest Cloud Base FT"]
        for col in cols:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors="coerce")
        if "Wind Spd KT" in df.columns:
            df["Wind Spd KT"] = df["Wind Spd KT"].astype(str).str.extract(r"(\d+)").astype(float)
        df["Sky Conditions"] = df["Sky Conditions"].fillna("SKC")
        df["DewPoint"] = df.apply(lambda x: calculate_dewpoint(x["Temp C"], x["Humidity %"]), axis=1)
        return df.dropna(subset=["Full_Timestamp"])
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()

df_main = load_data()

# ===================== DASH APP =====================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id="sidebar-container"),
    html.Div(id="page-content", style={"marginLeft": "18rem", "minHeight": "100vh"})
])

# ===================== CALLBACKS =====================

@app.callback(
    [Output("page-content", "children"), Output("sidebar-container", "children"), Output("sidebar-container", "style")],
    [Input("url", "pathname")]
)
def render_page(pathname):
    bg_image = "https://raw.githubusercontent.com/salem94980/Aden-Weather-Hub/main/assets/aden_airport.jpg"
    
    if pathname == "/dashboard":
        max_dt = df_main["Date_Only"].max() if not df_main.empty else date.today()
        filters = [
            html.Label("TIME RANGE", style={"fontSize": "11px", "color": "#8b949e", "letterSpacing": "1.5px"}),
            dcc.DatePickerRange(id="d-picker", start_date=max_dt - timedelta(days=7), end_date=max_dt, display_format='YYYY-MM-DD'),
            html.Br(), html.Br(),
            html.Label("HOUR SELECTOR (UTC)", style={"fontSize": "11px", "color": "#8b949e", "letterSpacing": "1.5px"}),
            dcc.Dropdown(id="h-drop", options=[{"label": f"{h:02d}:00", "value": h} for h in range(24)], multi=True, style={"color": "black"})
        ]
        
        sidebar = html.Div(style={"position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "18rem", "padding": "2rem 1rem", "backgroundColor": "#0a0c10", "borderRight": "1px solid #1a1e26"}, children=[
            html.H2("OYAA HUB", style={"fontFamily": "Orbitron", "color": "#00f2ff", "textAlign": "center", "fontSize": "22px"}),
            html.Hr(style={"borderColor": "#00f2ff", "opacity": "0.3"}),
            dbc.Nav([
                dbc.NavLink("🏠 HOME", href="/", active="exact"),
                dbc.NavLink("📊 ANALYTICS", href="/dashboard", active="exact"),
            ], vertical=True, pills=True),
            html.Hr(style={"borderColor": "#00f2ff", "opacity": "0.3"}),
            html.Div(filters)
        ])
        
        layout = html.Div(style={"padding": "2.5rem", "backgroundColor": "#0d1117"}, children=[
            html.H2("OPERATIONAL METAR ANALYTICS", style={"fontFamily": "Orbitron", "color": "#00f2ff"}),
            html.Div(id="stats-row"),
            html.H3("🌡️ TEMPERATURE DYNAMICS", style={"color": "#ff5f5f", "marginTop": "30px"}),
            dcc.Graph(id="t-line-big"),
            html.H3("❄️ DEW POINT MONITOR", style={"color": "#00f2ff", "marginTop": "40px"}),
            dcc.Graph(id="d-line-big"),
            html.H3("💧 HUMIDITY ANALYSIS", style={"color": "#00ff41", "marginTop": "40px"}),
            dcc.Graph(id="h-line"),
            html.H3("⏲️ QNH PRESSURE", style={"color": "#ffa500", "marginTop": "40px"}),
            dcc.Graph(id="p-line"),
            html.H3("☁️ CLOUD BASE & CONDITIONS", style={"color": "#00f2ff", "marginTop": "40px"}),
            dcc.Graph(id="c-scatter-large"),
            html.H3("💨 WIND ROSE ANALYSIS", style={"color": "#00f2ff", "marginTop": "40px"}),
            dcc.Graph(id="w-rose"),
            html.H3("🌩️ WEATHER PHENOMENA", style={"color": "#00f2ff", "marginTop": "40px"}),
            dcc.Graph(id="events-pie"),
            html.Div(id="metar-table-area", style={"marginBottom": "100px"})
        ])
        return layout, sidebar, {"display": "block"}

    # Landing Page
    home_layout = html.Div(style={
        "height": "100vh", "marginLeft": "-18rem",
        "backgroundImage": f'linear-gradient(rgba(10, 12, 16, 0.5), rgba(10, 12, 16, 0.9)), url("{bg_image}")',
        "backgroundSize": "cover", "backgroundPosition": "center", "display": "flex", "flexDirection": "column", "justifyContent": "center", "alignItems": "center"
    }, children=[
        html.H1("OYAA INTELHUB", style={"fontSize": "80px", "color": "#ffffff", "fontFamily": "Orbitron"}),
        html.A(html.Button("INITIATE ANALYTICS", style={"backgroundColor": "transparent", "color": "#00f2ff", "border": "2px solid #00f2ff", "padding": "15px 45px"}), href="/dashboard")
    ])
    return home_layout, None, {"display": "none"}

@app.callback(
    [Output("stats-row", "children"), Output("t-line-big", "figure"), Output("d-line-big", "figure"), 
     Output("h-line", "figure"), Output("p-line", "figure"), Output("events-pie", "figure"), 
     Output("c-scatter-large", "figure"), Output("w-rose", "figure"), Output("metar-table-area", "children")],
    [Input("d-picker", "start_date"), Input("d-picker", "end_date"), Input("h-drop", "value"),
     Input("url", "pathname")] # إضافة الـ URL كـ Trigger لضمان التحديث عند الدخول
)
def update_dash(start, end, hours, pathname):
    if pathname != "/dashboard" or not start or not end: return [dash.no_update]*9
    
    # تحويل آمن للتاريخ
    sd = pd.to_datetime(start).date()
    ed = pd.to_datetime(end).date()
    
    dff = df_main[(df_main["Date_Only"] >= sd) & (df_main["Date_Only"] <= ed)]
    if hours: dff = dff[dff["Hour"].isin(hours)]
    dff = dff.sort_values("Full_Timestamp")
    
    if dff.empty: return [html.Div("No Data Found")] + [go.Figure()]*7 + [html.Div()]

    stats = dbc.Row([
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("AVERAGE TEMPERATURE"), html.H3(f"{dff['Temp C'].mean():.1f}°C", style={"color": "#ff5f5f"})])])),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("AVERAGE HUMIDITY"), html.H3(f"{dff['Humidity %'].mean():.1f}%", style={"color": "#00f2ff"})])])),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("MINIMUM VISIBILITY"), html.H3(f"{dff['Visibility M'].min():.0f} m", style={"color": "#ffd33d"})])])),
    ], className="mb-4 text-center")

    f_t = px.line(dff, x="Full_Timestamp", y="Temp C", template="plotly_dark", height=600).update_traces(line_color="#ff5f5f")
    f_d = px.line(dff, x="Full_Timestamp", y="DewPoint", template="plotly_dark", height=600).update_traces(line_color="#00f2ff")
    f_h = px.line(dff, x="Full_Timestamp", y="Humidity %", template="plotly_dark", height=500).update_traces(line_color="#00ff41")
    f_p = px.line(dff, x="Full_Timestamp", y="Pressure hPa", template="plotly_dark", height=500).update_traces(line_color="#ffa500")
    f_ev = px.pie(dff, names="Present Weather", template="plotly_dark", hole=0.4, height=600)
    f_c = px.scatter(dff, x="Full_Timestamp", y="Lowest Cloud Base FT", color="Sky Conditions", template="plotly_dark", height=600)
    f_w = px.bar_polar(dff, r="Wind Spd KT", theta="Wind Dir", color="Wind Spd KT", template="plotly_dark", height=700)

    for f in [f_t, f_d, f_h, f_p, f_c]:
        f.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")

    table = dash_table.DataTable(
        data=dff[["Display_Time", "METAR"]].to_dict("records"),
        columns=[{"name": "UTC TIMESTAMP", "id": "Display_Time"}, {"name": "RAW METAR", "id": "METAR"}],
        style_table={'height': '400px', 'overflowY': 'auto'},
        style_cell={"backgroundColor": "#0d1117", "color": "#c9d1d9", "textAlign": "left"}
    )

    return stats, f_t, f_d, f_h, f_p, f_ev, f_c, f_w, table

if __name__ == "__main__":
    app.run(debug=True)
