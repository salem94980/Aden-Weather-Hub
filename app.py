import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import timedelta

# ===================== FUNCTIONS =====================
def calculate_dewpoint(T, RH):
    if pd.isna(T) or pd.isna(RH) or RH <= 0:
        return np.nan
    gamma = (17.67 * T / (243.5 + T)) + np.log(RH / 100.0)
    return (243.5 * gamma) / (17.67 - gamma)

# ===================== LOAD DATA =====================
df = pd.read_excel("Aden_METAR_Final_Report.xlsx")
df.columns = df.columns.str.strip()

df["Full_Timestamp"] = pd.to_datetime(
    df["Date"].astype(str) + " " + df["UTC"].astype(str),
    errors="coerce"
)

df["Date_Only"] = df["Full_Timestamp"].dt.date
df["Hour"] = df["Full_Timestamp"].dt.hour
df["Display_Time"] = df["Full_Timestamp"].dt.strftime("%Y-%m-%d %H:%M")

num_cols = [
    "Temp C", "Humidity %", "Pressure hPa",
    "Visibility M", "Wind Dir", "Lowest Cloud Base FT"
]
for c in num_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

df["Wind Spd KT"] = (
    df["Wind Spd KT"].astype(str).str.extract(r"(\d+)").astype(float)
)

df["DewPoint"] = df.apply(
    lambda x: calculate_dewpoint(x["Temp C"], x["Humidity %"]), axis=1
)

df = df.dropna(subset=["Full_Timestamp"])

# ===================== DASH APP =====================
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True
)
server = app.server

# ===================== LAYOUT =====================
app.layout = html.Div([
    dcc.Location(id="url"),

    # SIDEBAR
    html.Div(
        id="sidebar-container",
        style={
            "position": "fixed", "top": 0, "left": 0, "bottom": 0,
            "width": "18rem", "padding": "2rem 1rem",
            "backgroundColor": "#0a0c10", "borderRight": "1px solid #1a1e26"
        },
        children=[
            html.H2("OYAA HUB", style={
                "color": "#00f2ff", "textAlign": "center",
                "fontFamily": "Orbitron"
            }),
            dbc.Nav(
                [
                    dbc.NavLink("🏠 HOME", href="/", active="exact"),
                    dbc.NavLink("📊 ANALYTICS", href="/dashboard", active="exact"),
                ],
                vertical=True, pills=True
            ),
            html.Hr(),
            html.Div(id="filters-container")
        ]
    ),

    html.Div(id="page-content", style={"marginLeft": "18rem"})
])

# ===================== ROUTING =====================
@app.callback(
    [Output("page-content", "children"),
     Output("filters-container", "children")],
    Input("url", "pathname")
)
def render_page(pathname):

    if pathname == "/dashboard":
        max_dt = df["Date_Only"].max()

        filters = [
            html.Label("TIME RANGE"),
            dcc.DatePickerRange(
                id="d-picker",
                start_date=max_dt - timedelta(days=7),
                end_date=max_dt,
                persistence=True
            ),
            html.Br(), html.Br(),
            html.Label("HOUR (UTC)"),
            dcc.Dropdown(
                id="h-drop",
                options=[{"label": f"{h:02d}", "value": h} for h in range(24)],
                multi=True,
                style={"color": "black"}
            )
        ]

        layout = html.Div(style={"padding": "2rem"}, children=[
            html.H2("METAR ANALYTICS", style={"color": "#00f2ff"}),

            html.Div(id="stats-row"),

            dcc.Graph(id="temp-fig"),
            dcc.Graph(id="dew-fig"),
            dcc.Graph(id="pressure-fig"),
            dcc.Graph(id="windspd-fig"),
            dcc.Graph(id="vis-fig"),
            dcc.Graph(id="winddir-fig"),

            html.H3("RAW METAR"),
            html.Div(id="table-area")
        ])

        return layout, filters

    return html.H1("OYAA INTELHUB", style={"color": "white"}), []

# ===================== MAIN CALLBACK =====================
@app.callback(
    [
        Output("stats-row", "children"),
        Output("temp-fig", "figure"),
        Output("dew-fig", "figure"),
        Output("pressure-fig", "figure"),
        Output("windspd-fig", "figure"),
        Output("vis-fig", "figure"),
        Output("winddir-fig", "figure"),
        Output("table-area", "children"),
    ],
    [
        Input("url", "pathname"),
        Input("d-picker", "start_date"),
        Input("d-picker", "end_date"),
        Input("h-drop", "value"),
    ],
    prevent_initial_call=True
)
def update_all(path, start, end, hours):

    if path != "/dashboard":
        return [dash.no_update] * 8

    dff = df.copy()

    if start and end:
        dff = dff[
            (dff["Date_Only"] >= pd.to_datetime(start).date()) &
            (dff["Date_Only"] <= pd.to_datetime(end).date())
        ]

    if hours:
        dff = dff[dff["Hour"].isin(hours)]

    # ===== STATS =====
    stats = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("AVG TEMP"),
            html.H3(f"{dff['Temp C'].mean():.1f} °C")
        ])))
    ])

    # ===== FIGURES =====
    f_temp = px.line(dff, x="Full_Timestamp", y="Temp C", template="plotly_dark")
    f_dew = px.line(dff, x="Full_Timestamp", y="DewPoint", template="plotly_dark")
    f_pres = px.line(dff, x="Full_Timestamp", y="Pressure hPa", template="plotly_dark")
    f_wind = px.line(dff, x="Full_Timestamp", y="Wind Spd KT", template="plotly_dark")
    f_vis = px.line(dff, x="Full_Timestamp", y="Visibility M", template="plotly_dark")

    f_dir = px.scatter_polar(
        dff, r="Wind Spd KT", theta="Wind Dir",
        template="plotly_dark"
    )

    table = dash_table.DataTable(
        data=dff[["Display_Time", "METAR"]].to_dict("records"),
        columns=[
            {"name": "TIME", "id": "Display_Time"},
            {"name": "METAR", "id": "METAR"}
        ],
        style_table={"overflowY": "auto", "height": "300px"},
        style_cell={"backgroundColor": "#0d1117", "color": "white"}
    )

    return stats, f_temp, f_dew, f_pres, f_wind, f_vis, f_dir, table

# ===================== RUN =====================
if __name__ == "__main__":
    app.run_server(debug=True)
