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

# ===================== LOAD & FIX DATA =====================
def load_data():
    try:
        df = pd.read_excel("Aden_METAR_Final_Report.xlsx")
        df.columns = df.columns.str.strip()
        
        # تحويل عمود التاريخ إلى صيغة datetime حقيقية وتنظيفه
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        
        # دمج التاريخ والوقت
        df["Full_Timestamp"] = pd.to_datetime(df["Date"].dt.strftime('%Y-%m-%d') + " " + df["UTC"].astype(str), errors="coerce")
        
        # استخراج التاريخ فقط للمقارنة (تأكد من أنه نوع date)
        df["Date_Only"] = df["Full_Timestamp"].dt.date
        df["Hour"] = df["Full_Timestamp"].dt.hour
        df["Display_Time"] = df["Full_Timestamp"].dt.strftime('%Y-%m-%d %H:%M')
        
        # تنظيف الأرقام
        cols = ["Temp C", "Visibility M", "Humidity %", "Pressure hPa", "Wind Dir", "Lowest Cloud Base FT"]
        for col in cols:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors="coerce")
        
        if "Wind Spd KT" in df.columns:
            df["Wind Spd KT"] = df["Wind Spd KT"].astype(str).str.extract(r"(\d+)").astype(float)
        
        df["Sky Conditions"] = df["Sky Conditions"].fillna("SKC")
        df["Present Weather"] = df["Present Weather"].fillna("NIL")
        df["DewPoint"] = df.apply(lambda x: calculate_dewpoint(x["Temp C"], x["Humidity %"]), axis=1)
        
        return df.dropna(subset=["Full_Timestamp"])
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return pd.DataFrame()

df_main = load_data()

# ===================== DASH APP =====================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

SIDEBAR_STYLE = {
    "position": "fixed", "top": 0, "left": 0, "bottom": 0, 
    "width": "18rem", "padding": "2rem 1rem", "backgroundColor": "#0a0c10", 
    "borderRight": "1px solid #1a1e26", "zIndex": 100
}

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id="sidebar-container"),
    html.Div(id="page-content", style={"marginLeft": "18rem", "minHeight": "100vh"})
])

@app.callback(
    [Output("page-content", "children"), Output("sidebar-container", "children"), Output("sidebar-container", "style")],
    [Input("url", "pathname")]
)
def render_page(pathname):
    bg_image = "https://raw.githubusercontent.com/salem94980/Aden-Weather-Hub/main/assets/aden_airport.jpg"
    if pathname == "/dashboard":
        # تحديد أصغر وأكبر تاريخ موجود في البيانات فعلياً
        min_date = df_main["Date_Only"].min() if not df_main.empty else date(2020,1,1)
        max_date = df_main["Date_Only"].max() if not df_main.empty else date.today()
        
        filters = [
            html.Label("TIME RANGE", style={"fontSize": "11px", "color": "#8b949e", "letterSpacing": "1.5px"}),
            dcc.DatePickerRange(
                id="d-picker",
                min_date_allowed=min_date,
                max_date_allowed=max_date,
                start_date=min_date,
                end_date=max_date,
                display_format='YYYY-MM-DD',
                style={"backgroundColor": "#161b22"}
            ),
            html.Br(), html.Br(),
            html.Label("HOUR SELECTOR (UTC)", style={"fontSize": "11px", "color": "#8b949e", "letterSpacing": "1.5px"}),
            dcc.Dropdown(id="h-drop", options=[{"label": f"{h:02d}:00", "value": h} for h in range(24)], multi=True, style={"color": "black"})
        ]
        
        sidebar = html.Div(style=SIDEBAR_STYLE, children=[
            html.H2("OYAA HUB", style={"fontFamily": "Orbitron", "color": "#00f2ff", "textAlign": "center"}),
            html.Hr(style={"borderColor": "#00f2ff", "opacity": "0.3"}),
            dbc.Nav([
                dbc.NavLink("🏠 HOME", href="/", active="exact"),
                dbc.NavLink("📊 ANALYTICS", href="/dashboard", active="exact"),
            ], vertical=True, pills=True),
            html.Div(filters, style={"marginTop": "20px"})
        ])
        
        layout = html.Div(style={"padding": "2.5rem", "backgroundColor": "#0d1117"}, children=[
            html.H2("OPERATIONAL METAR ANALYTICS", style={"fontFamily": "Orbitron", "color": "#00f2ff"}),
            html.Div(id="stats-row"),
            dcc.Graph(id="t-line-big"),
            dcc.Graph(id="d-line-big"),
            dcc.Graph(id="h-line"),
            dcc.Graph(id="p-line"),
            dcc.Graph(id="c-scatter-large"),
            dcc.Graph(id="w-rose"),
            dcc.Graph(id="events-pie"),
            html.Div(id="metar-table-area", style={"marginTop": "60px", "marginBottom": "100px"})
        ])
        return layout, sidebar, SIDEBAR_STYLE

    home_layout = html.Div(style={"height": "100vh", "marginLeft": "-18rem", "backgroundImage": f'url("{bg_image}")', "backgroundSize": "cover", "display": "flex", "justifyContent": "center", "alignItems": "center"}, children=[
        html.A(html.Button("INITIATE ANALYTICS"), href="/dashboard")
    ])
    return home_layout, None, {"display": "none"}

@app.callback(
    [Output("stats-row", "children"), Output("t-line-big", "figure"), Output("d-line-big", "figure"), 
     Output("h-line", "figure"), Output("p-line", "figure"), Output("events-pie", "figure"), 
     Output("c-scatter-large", "figure"), Output("w-rose", "figure"), Output("metar-table-area", "children")],
    [Input("d-picker", "start_date"), Input("d-picker", "end_date"), Input("h-drop", "value")]
)
def update_dash(start, end, hours):
    if not start or not end: return [dash.no_update]*9
    
    # تحويل الاختيار إلى كائن date للمقارنة الصحيحة
    sel_start = pd.to_datetime(start).date()
    sel_end = pd.to_datetime(end).date()
    
    # التصفية الصارمة
    mask = (df_main["Date_Only"] >= sel_start) & (df_main["Date_Only"] <= sel_end)
    dff = df_main.loc[mask]
    
    if hours:
        dff = dff[dff["Hour"].isin(hours)]
    
    if dff.empty:
        return [html.Div("No Data Found", style={"color": "orange"})] + [go.Figure()]*7 + [html.Div()]

    # الإحصائيات الكاملة
    stats = dbc.Row([
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("AVERAGE TEMPERATURE"), html.H3(f"{dff['Temp C'].mean():.1f}°C")])])),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("AVERAGE HUMIDITY"), html.H3(f"{dff['Humidity %'].mean():.1f}%")])])),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("MINIMUM VISIBILITY"), html.H3(f"{dff['Visibility M'].min():.0f} m")])])),
    ])

    # الرسوم البيانية
    f_t = px.line(dff, x="Full_Timestamp", y="Temp C", template="plotly_dark")
    f_d = px.line(dff, x="Full_Timestamp", y="DewPoint", template="plotly_dark")
    f_h = px.line(dff, x="Full_Timestamp", y="Humidity %", template="plotly_dark")
    f_p = px.line(dff, x="Full_Timestamp", y="Pressure hPa", template="plotly_dark")
    f_ev = px.pie(dff, names="Present Weather", template="plotly_dark")
    f_c = px.scatter(dff, x="Full_Timestamp", y="Lowest Cloud Base FT", color="Sky Conditions", template="plotly_dark")
    f_w = px.bar_polar(dff, r="Wind Spd KT", theta="Wind Dir", color="Wind Spd KT", template="plotly_dark")

    table = dash_table.DataTable(
        data=dff[["Display_Time", "METAR"]].to_dict("records"),
        columns=[{"name": "UTC TIMESTAMP", "id": "Display_Time"}, {"name": "RAW METAR", "id": "METAR"}],
        style_table={'height': '300px', 'overflowY': 'auto'},
        style_cell={'textAlign': 'left', 'backgroundColor': '#161b22', 'color': 'white'}
    )

    return stats, f_t, f_d, f_h, f_p, f_ev, f_c, f_w, table

if __name__ == "__main__":
    app.run(debug=True)
