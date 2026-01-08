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
        df = pd.read_excel("Aden_METAR_Final_Report.xlsx", engine='openpyxl')
        df.columns = df.columns.str.strip()
        df["Full_Timestamp"] = pd.to_datetime(df["Date"].astype(str) + " " + df["UTC"].astype(str), errors="coerce")
        df["Display_Time"] = df["Full_Timestamp"].dt.strftime('%Y-%m-%d %H:%M')
        df["Date_Only"] = df["Full_Timestamp"].dt.date
        df["Hour"] = df["Full_Timestamp"].dt.hour
        
        numeric_cols = ["Temp C", "DewPt C", "Humidity %", "Pressure hPa", "Wind Spd KT", "Visibility M", "Lowest Cloud Base FT"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        if "Wind Dir" in df.columns:
            df["Wind Dir"] = pd.to_numeric(df["Wind Dir"], errors="coerce")
            
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
    html.Div(id="sidebar-container"),
    html.Div(id="page-content")
])

# ===================== CALLBACKS =====================

@app.callback(
    [Output("page-content", "children"), Output("sidebar-container", "children")],
    [Input("url", "pathname")]
)
def render_page(pathname):
    img_url = "https://raw.githubusercontent.com/salem94980/Aden-Weather-Hub/main/assets/aden_airport.jpg"

    if pathname == "/dashboard":
        if df_main.empty:
            return html.Div([html.H3("⚠️ عذراً، لم يتم العثور على بيانات", style={"color":"orange", "textAlign":"center", "marginTop":"50px"})]), None
        
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

        content = html.Div(style={"marginLeft": "18rem", "padding": "2.5rem", "backgroundColor": "#0d1117"}, children=[
            html.H2("ADEN OPERATIONAL ANALYTICS", style={"fontFamily": "Orbitron", "color": "#00f2ff", "letterSpacing": "2px"}),
            html.Div(id="stats-cards", className="mt-4"),
            
            html.H3("🌡️ TEMPERATURE & DEW POINT", style={"color": "#ff5f5f", "marginTop": "40px"}),
            dcc.Graph(id="temp-dew-graph"),
            
            html.H3("🌧️ WEATHER PHENOMENA", style={"color": "#00f2ff", "marginTop": "40px"}),
            dcc.Graph(id="phenomena-pie"),

            html.H3("💨 WIND ROSE ANALYSIS", style={"color": "#00ff41", "marginTop": "40px"}),
            dcc.Graph(id="wind-rose"),

            html.H4("📜 METAR SYSTEM LOGS", className="mt-5", style={"color":"#8b949e"}),
            html.Div(id="table-container", style={"marginBottom": "50px"})
        ])
        return content, sidebar

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
    [Output("stats-cards", "children"), Output("temp-dew-graph", "figure"), 
     Output("phenomena-pie", "figure"), Output("wind-rose", "figure"), Output("table-container", "children")],
    [Input("d-picker", "start_date"), Input("d-picker", "end_date"), Input("h-drop", "value")]
)
def update_dashboard(start, end, hours):
    if df_main.empty: return [dash.no_update]*5
    
    dff = df_main[(df_main["Date_Only"] >= date.fromisoformat(start)) & (df_main["Date_Only"] <= date.fromisoformat(end))]
    if hours: dff = dff[dff["Hour"].isin(hours)]
    
    # 1. كروت الإحصائيات
    cards = dbc.Row([
        dbc.Col(dbc.Card([html.H6("AVG TEMP"), html.H2(f"{dff['Temp C'].mean():.1f}°C")], body=True, color="dark", style={"border":"1px solid #ff5f5f", "textAlign":"center"})),
        dbc.Col(dbc.Card([html.H6("AVG HUMIDITY"), html.H2(f"{dff['Humidity %'].mean():.1f}%")], body=True, color="dark", style={"border":"1px solid #00f2ff", "textAlign":"center"})),
        dbc.Col(dbc.Card([html.H6("MIN VISIBILITY"), html.H2(f"{dff['Visibility M'].min():.0f}m")], body=True, color="dark", style={"border":"1px solid #ffd33d", "textAlign":"center"})),
    ])

    # 2. مخطط الحرارة ونقطة الندى
    fig_temp = go.Figure()
    fig_temp.add_trace(go.Scatter(x=dff["Full_Timestamp"], y=dff["Temp C"], name="Temp C", line=dict(color='#ff5f5f', width=3)))
    fig_temp.add_trace(go.Scatter(x=dff["Full_Timestamp"], y=dff["DewPt C"], name="Dew Point", line=dict(color='#00f2ff', width=3, dash='dot')))
    fig_temp.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=450)

    # 3. WEATHER PHENOMENA (المخطط الدائري)
    fig_pie = px.pie(dff, names="Present Weather", hole=0.4, template="plotly_dark")
    fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # 4. WIND ROSE
    fig_rose = px.bar_polar(dff, r="Wind Spd KT", theta="Wind Dir", color="Wind Spd KT", template="plotly_dark")
    fig_rose.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # 5. الجدول
    table = dash_table.DataTable(
        data=dff.tail(20).to_dict("records"),
        columns=[{"name": "TIMESTAMP", "id": "Display_Time"}, {"name": "METAR DATA", "id": "METAR"}],
        style_table={'overflowX': 'auto'},
        style_cell={'backgroundColor': '#111', 'color': '#fff', 'textAlign': 'left', 'fontFamily': 'monospace', 'padding': '10px'},
        style_header={'backgroundColor': '#161b22', 'color': '#00f2ff', 'fontWeight': 'bold'}
    )
    
    return cards, fig_temp, fig_pie, fig_rose, table

if __name__ == "__main__":
    app.run(debug=True)
