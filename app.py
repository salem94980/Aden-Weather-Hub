import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# ===================== LOAD DATA WITH FALLBACK =====================
def load_data():
    file_name = "Aden_METAR_Final_Report.xlsx"
    try:
        df = pd.read_excel(file_name, engine='openpyxl')
        df.columns = [str(c).strip() for c in df.columns]
        df["Full_Timestamp"] = pd.to_datetime(df["Date"].astype(str) + " " + df["UTC"].astype(str), errors="coerce")
        df = df.dropna(subset=["Full_Timestamp"])
        for col in ["Temp C", "Humidity %", "Wind Speed KT"]:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.sort_values("Full_Timestamp")
    except:
        # إذا فشل الإكسل، نصنع بيانات وهمية لكي لا يتعطل الموقع
        dates = [datetime.now() - timedelta(hours=i) for i in range(24)]
        return pd.DataFrame({
            "Full_Timestamp": dates,
            "Temp C": np.random.randint(25, 35, 24),
            "Humidity %": np.random.randint(50, 80, 24),
            "Wind Speed KT": np.random.randint(5, 20, 24),
            "METAR": ["DATA PREVIEW MODE"] * 24
        })

df_main = load_data()

# ===================== APP SETUP =====================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)
server = app.server 

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    # Sidebar
    html.Div(style={"position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "18rem", "padding": "2rem 1rem", "backgroundColor": "#0a0c10", "borderRight": "2px solid #00f2ff"}, children=[
        html.H2("OYAA HUB", style={"fontFamily": "Orbitron", "color": "#00f2ff", "textAlign": "center"}),
        html.Hr(style={"borderColor": "#00f2ff"}),
        dbc.Nav([
            dbc.NavLink("🏠 HOME", href="/", active="exact"),
            dbc.NavLink("📊 ANALYTICS", href="/dashboard", active="exact"),
        ], vertical=True, pills=True),
    ]),
    html.Div(id="page-content", style={"marginLeft": "18rem", "padding": "2rem", "minHeight": "100vh", "backgroundColor": "#0d1117"})
])

@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page(pathname):
    if pathname == "/dashboard":
        fig = px.line(df_main, x="Full_Timestamp", y="Temp C", title="Temperature Variation", template="plotly_dark")
        fig.update_traces(line_color="#00f2ff")
        return html.Div([
            html.H2("ADEN (OYAA) ANALYTICS", style={"fontFamily": "Orbitron", "color": "#00f2ff"}),
            dbc.Row([
                dbc.Col(dbc.Card([html.H6("LATEST TEMP"), html.H2(f"{df_main['Temp C'].iloc[0]}°C")], body=True, color="info", inverse=True)),
                dbc.Col(dbc.Card([html.H6("HUMIDITY"), html.H2(f"{df_main['Humidity %'].iloc[0]}%")], body=True, color="primary", inverse=True)),
            ], className="mb-4"),
            dcc.Graph(figure=fig),
            html.H4("DATA LOGS", className="mt-4"),
            dash_table.DataTable(
                data=df_main.tail(10).to_dict("records"),
                columns=[{"name": i, "id": i} for i in ["Full_Timestamp", "Temp C", "METAR"]],
                style_table={'overflowX': 'auto'},
                style_cell={'backgroundColor': '#111', 'color': '#fff'}
            )
        ])
    return html.Div(style={"height": "80vh", "display": "flex", "flexDirection": "column", "justifyContent": "center", "alignItems": "center"}, children=[
        html.H1("OYAA INTELHUB", style={"fontSize": "60px", "fontFamily": "Orbitron", "color": "#fff"}),
        html.P("ADEN AIRPORT INTELLIGENCE SYSTEM", style={"color": "#00f2ff"}),
        dbc.Button("ENTER SYSTEM", href="/dashboard", color="info", outline=True, size="lg")
    ])

if __name__ == "__main__":
    app.run(debug=True)
