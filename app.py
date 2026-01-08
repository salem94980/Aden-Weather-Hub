import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import date, timedelta

# ===================== وظيفة حساب نقطة الندى =====================
def calculate_dewpoint(T, RH):
    if pd.isna(T) or pd.isna(RH) or RH <= 0: return np.nan
    gamma = (17.67 * T / (243.5 + T)) + np.log(RH / 100.0)
    return (243.5 * gamma) / (17.67 - gamma)

# ===================== تحميل وتنظيف البيانات =====================
def load_data():
    try:
        df = pd.read_excel("Aden_METAR_Final_Report.xlsx")
        df.columns = df.columns.str.strip()
        
        # تحويل التاريخ لضمان أنه بصيغة تاريخ حقيقية
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        
        # دمج الوقت والتاريخ
        df["Full_Timestamp"] = pd.to_datetime(df["Date"].dt.strftime('%Y-%m-%d') + " " + df["UTC"].astype(str), errors="coerce")
        
        # استخراج التاريخ فقط للمقارنة مع الفلتر
        df["Date_Only"] = df["Full_Timestamp"].dt.date
        df["Hour"] = df["Full_Timestamp"].dt.hour
        df["Display_Time"] = df["Full_Timestamp"].dt.strftime('%Y-%m-%d %H:%M')
        
        # تنظيف القيم الرقمية
        cols = ["Temp C", "Visibility M", "Humidity %", "Pressure hPa", "Wind Dir", "Lowest Cloud Base FT"]
        for col in cols:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors="coerce")
        
        if "Wind Spd KT" in df.columns:
            df["Wind Spd KT"] = df["Wind Spd KT"].astype(str).str.extract(r"(\d+)").astype(float)
        
        df["Present Weather"] = df["Present Weather"].fillna("NIL")
        df["DewPoint"] = df.apply(lambda x: calculate_dewpoint(x["Temp C"], x["Humidity %"]), axis=1)
        
        return df.dropna(subset=["Full_Timestamp"])
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()

df_main = load_data()

# ===================== تصميم التطبيق =====================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

SIDEBAR_STYLE = {
    "position": "fixed", "top": 0, "left": 0, "bottom": 0, 
    "width": "18rem", "padding": "2rem 1rem", "backgroundColor": "#0a0c10", 
    "borderRight": "1px solid #1a1e26"
}

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id="sidebar-container"),
    html.Div(id="page-content", style={"marginLeft": "18rem", "padding": "2rem"})
])

@app.callback(
    [Output("page-content", "children"), Output("sidebar-container", "children")],
    [Input("url", "pathname")]
)
def render_page(pathname):
    # تحديد أصغر وأكبر تاريخ في البيانات لضبط الفلتر تلقائياً
    if not df_main.empty:
        abs_min = df_main["Date_Only"].min()
        abs_max = df_main["Date_Only"].max()
    else:
        abs_min = date(2025, 1, 1)
        abs_max = date.today()

    filters = [
        html.Label("TIME RANGE", style={"color": "#8b949e", "fontSize": "12px"}),
        dcc.DatePickerRange(
            id="d-picker",
            min_date_allowed=abs_min,
            max_date_allowed=abs_max,
            start_date=abs_min, # سيبدأ من أول تاريخ متاح في ملفك
            end_date=abs_max,   # سينتهي عند آخر تاريخ متاح في ملفك
            display_format='YYYY-MM-DD',
            style={"marginBottom": "20px"}
        ),
        html.Br(),
        html.Label("HOUR SELECTOR (UTC)", style={"color": "#8b949e", "fontSize": "12px"}),
        dcc.Dropdown(id="h-drop", options=[{"label": f"{h:02d}:00", "value": h} for h in range(24)], multi=True, style={"color": "black"})
    ]
    
    sidebar = html.Div(style=SIDEBAR_STYLE, children=[
        html.H2("OYAA HUB", style={"color": "#00f2ff", "textAlign": "center", "fontFamily": "Orbitron"}),
        html.Hr(),
        dbc.Nav([
            dbc.NavLink("🏠 HOME", href="/", active="exact"),
            dbc.NavLink("📊 ANALYTICS", href="/dashboard", active="exact"),
        ], vertical=True, pills=True),
        html.Div(filters, style={"marginTop": "30px"})
    ])

    if pathname == "/dashboard":
        layout = html.Div([
            html.H2("OPERATIONAL METAR ANALYTICS", style={"color": "#00f2ff", "fontFamily": "Orbitron"}),
            html.Div(id="stats-row"),
            dcc.Graph(id="t-line-big"),
            dcc.Graph(id="events-pie"),
            html.Div(id="metar-table-area")
        ])
        return layout, sidebar
    
    return html.Div([html.H1("WELCOME TO OYAA HUB"), html.A("GO TO DASHBOARD", href="/dashboard")]), sidebar

# ===================== تحديث البيانات عند تغيير الفلتر =====================
@app.callback(
    [Output("stats-row", "children"), Output("t-line-big", "figure"), Output("events-pie", "figure"), Output("metar-table-area", "children")],
    [Input("d-picker", "start_date"), Input("d-picker", "end_date"), Input("h-drop", "value")]
)
def update_dashboard(start, end, hours):
    if not start or not end: return [dash.no_update]*4
    
    # تحويل الاختيار إلى صيغة مقارنة صحيحة
    sd = pd.to_datetime(start).date()
    ed = pd.to_datetime(end).date()
    
    # تصفية البيانات
    mask = (df_main["Date_Only"] >= sd) & (df_main["Date_Only"] <= ed)
    dff = df_main.loc[mask]
    
    if hours:
        dff = dff[dff["Hour"].isin(hours)]
    
    if dff.empty:
        return [html.Div("No Data Found", style={"color": "orange"})] + [go.Figure()]*2 + [html.Div()]

    # الإحصائيات
    stats = dbc.Row([
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("AVERAGE TEMPERATURE"), html.H3(f"{dff['Temp C'].mean():.1f}°C")])])),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("MINIMUM VISIBILITY"), html.H3(f"{dff['Visibility M'].min():.0f} m")])])),
    ])

    f_t = px.line(dff, x="Full_Timestamp", y="Temp C", title="Temperature Trend", template="plotly_dark")
    f_ev = px.pie(dff, names="Present Weather", title="Weather Phenomena", template="plotly_dark")
    
    table = dash_table.DataTable(
        data=dff[["Display_Time", "METAR"]].to_dict("records"),
        columns=[{"name": "TIME", "id": "Display_Time"}, {"name": "METAR", "id": "METAR"}],
        style_table={'height': '300px', 'overflowY': 'auto'},
        style_cell={'backgroundColor': '#161b22', 'color': 'white', 'textAlign': 'left'}
    )

    return stats, f_t, f_ev, table

if __name__ == "__main__":
    app.run(debug=True)
