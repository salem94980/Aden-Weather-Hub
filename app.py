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
        # قراءة الملف - تأكد أن الاسم في GitHub هو Aden_METAR_Final_Report.xlsx
        df = pd.read_excel("Aden_METAR_Final_Report.xlsx", engine='openpyxl')
        df.columns = [str(c).strip() for c in df.columns]
        
        # دمج الوقت والتاريخ لضمان رسم المخططات
        df["Full_Timestamp"] = pd.to_datetime(df["Date"].astype(str) + " " + df["UTC"].astype(str), errors="coerce")
        df = df.dropna(subset=["Full_Timestamp"])
        
        # تحويل الأعمدة لأرقام لضمان عمل المخططات
        cols = ["Temp C", "Visibility M", "Humidity %", "Pressure hPa", "Wind Speed KT"]
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        return df.sort_values("Full_Timestamp")
    except Exception as e:
        print(f"Error loading Excel: {e}")
        return pd.DataFrame()

df_main = load_data()

# ===================== DASH APP SETUP =====================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)
server = app.server 

# القائمة الجانبية (Sidebar)
SIDEBAR_STYLE = {
    "position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "18rem",
    "padding": "2rem 1rem", "backgroundColor": "#0a0c10", "borderRight": "2px solid #00f2ff"
}

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    
    html.Div(style=SIDEBAR_STYLE, children=[
        html.H2("OYAA HUB", style={"fontFamily": "Orbitron", "color": "#00f2ff", "textAlign": "center"}),
        html.Hr(style={"borderColor": "#00f2ff"}),
        dbc.Nav([
            dbc.NavLink("🏠 HOME", href="/", active="exact", style={"borderRadius": "8px", "marginBottom": "10px"}),
            dbc.NavLink("📊 ANALYTICS", href="/dashboard", active="exact", style={"borderRadius": "8px"}),
        ], vertical=True, pills=True),
        html.Div(id="sidebar-info", style={"marginTop": "20px", "fontSize": "12px", "color": "#8b949e"})
    ]),

    html.Div(id="page-content", style={"marginLeft": "18rem", "padding": "2rem", "minHeight": "100vh", "backgroundColor": "#0d1117"})
])

# ===================== CALLBACKS =====================

@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page(pathname):
    if pathname == "/dashboard":
        if df_main.empty:
            return html.Div([
                html.H3("⚠️ البيانات غير متوفرة", style={"color": "orange"}),
                html.P("تأكد من وجود ملف الإكسل في المستودع بنفس الاسم المذكور في الكود.")
            ])

        # صفحة التحليلات بالتصميم الناجح
        return html.Div([
            html.H2("ADEN (OYAA) ANALYTICS", style={"fontFamily": "Orbitron", "color": "#00f2ff", "marginBottom": "30px"}),
            
            # كروت الإحصائيات
            dbc.Row([
                dbc.Col(dbc.Card([html.H6("MAX TEMP"), html.H3(f"{df_main['Temp C'].max()}°C", style={"color": "#ff5f5f"})], body=True, style={"backgroundColor": "#161b22", "textAlign": "center"})),
                dbc.Col(dbc.Card([html.H6("AVG HUMIDITY"), html.H3(f"{df_main['Humidity %'].mean():.1f}%", style={"color": "#00f2ff"})], body=True, style={"backgroundColor": "#161b22", "textAlign": "center"})),
                dbc.Col(dbc.Card([html.H6("AVG WIND"), html.H3(f"{df_main['Wind Speed KT'].mean():.1f} KT", style={"color": "#00ffcc"})], body=True, style={"backgroundColor": "#161b22", "textAlign": "center"})),
            ], className="mb-4"),

            # المخططات البيانية
            dbc.Row([
                dbc.Col(dcc.Graph(figure=px.line(df_main, x="Full_Timestamp", y="Temp C", title="Temperature Variation", template="plotly_dark").update_traces(line_color="#ff5f5f")), width=12),
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col(dcc.Graph(figure=px.area(df_main, x="Full_Timestamp", y="Humidity %", title="Humidity Levels", template="plotly_dark").update_traces(line_color="#00f2ff")), width=6),
                dbc.Col(dcc.Graph(figure=px.line(df_main, x="Full_Timestamp", y="Pressure hPa", title="Pressure Tracking", template="plotly_dark").update_traces(line_color="#ffd700")), width=6),
            ]),

            # جدول البيانات
            html.H3("RAW DATA LOGS", style={"color": "#00f2ff", "marginTop": "40px"}),
            dash_table.DataTable(
                data=df_main.tail(20).to_dict("records"),
                columns=[{"name": i, "id": i} for i in ["Full_Timestamp", "Temp C", "Wind Speed KT", "METAR"]],
                style_table={'overflowX': 'auto'},
                style_cell={'backgroundColor': '#0d1117', 'color': '#fff', 'textAlign': 'left', 'fontFamily': 'monospace'},
                style_header={'backgroundColor': '#161b22', 'color': '#00f2ff', 'fontWeight': 'bold'}
            )
        ])

    # الصفحة الرئيسية (Landing Page)
    return html.Div(style={
        "height": "80vh", "display": "flex", "flexDirection": "column", "justifyContent": "center", "alignItems": "center", "textAlign": "center"
    }, children=[
        html.H1("OYAA INTELHUB", style={"fontSize": "70px", "color": "#ffffff", "fontFamily": "Orbitron", "letterSpacing": "10px"}),
        html.Div(style={"width": "100px", "height": "4px", "backgroundColor": "#00f2ff", "margin": "20px 0"}),
        html.P("ADEN INTERNATIONAL AIRPORT WEATHER INTELLIGENCE", style={"color": "#00f2ff", "fontSize": "18px", "letterSpacing": "4px"}),
        html.Br(),
        dbc.Button("INITIATE ANALYTICS", href="/dashboard", color="info", outline=True, size="lg", style={"fontFamily": "Orbitron"})
    ])

if __name__ == "__main__":
    app.run(debug=True)
