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

df["Display_Time"] = df["Full_Timestamp"].dt.strftime("%Y-%m-%d %H:%M")
df["Date_Only"] = df["Full_Timestamp"].dt.date
df["Hour"] = df["Full_Timestamp"].dt.hour

num_cols = [
    "Temp C", "Humidity %", "Pressure hPa",
    "Visibility M", "Wind Dir", "Lowest Cloud Base FT"
]
for c in num_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

if "Wind Spd KT" in df.columns:
    df["Wind Spd KT"] = (
        df["Wind Spd KT"].astype(str)
        .str.extract(r"(\d+)")
        .astype(float)
    )

df["Sky Conditions"] = df["Sky Conditions"].fillna("SKC")

df["DewPoint"] = df.apply(
    lambda x: calculate_dewpoint(x["Temp C"], x["Humidity %"]),
    axis=1
)

df = df.dropna(subset=["Full_Timestamp"])

# ===================== DASH APP =====================
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True
)
server = app.server

# ===================== MAIN LAYOUT =====================
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),

    # ===== SIDEBAR =====
    html.Div(
        id="sidebar-container",
        style={
            "position": "fixed",
            "top": 0,
            "left": 0,
            "bottom": 0,
            "width": "18rem",
            "padding": "2rem 1rem",
            "backgroundColor": "#0a0c10",
            "borderRight": "1px solid #1a1e26",
            "zIndex": 100
        },
        children=[
            html.H2(
                "OYAA HUB",
                style={
                    "fontFamily": "Orbitron",
                    "color": "#00f2ff",
                    "textAlign": "center",
                    "fontSize": "22px"
                }
            ),
            html.Hr(style={"borderColor": "#00f2ff", "opacity": 0.3}),

            dbc.Nav(
                [
                    dbc.NavLink("🏠 HOME", href="/", active="exact"),
                    dbc.NavLink("📊 ANALYTICS", href="/dashboard", active="exact"),
                ],
                vertical=True,
                pills=True
            ),

            html.Hr(style={"borderColor": "#00f2ff", "opacity": 0.3}),
            html.Div(id="filters-container")
        ]
    ),

    html.Div(
        id="page-content",
        style={"marginLeft": "18rem", "minHeight": "100vh"}
    )
])

# ===================== PAGE ROUTING =====================
@app.callback(
    [
        Output("page-content", "children"),
        Output("filters-container", "children"),
        Output("sidebar-container", "style")
    ],
    Input("url", "pathname")
)
def render_page(pathname):

    sidebar_style = {
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "18rem",
        "padding": "2rem 1rem",
        "backgroundColor": "#0a0c10",
        "borderRight": "1px solid #1a1e26",
        "zIndex": 100
    }

    if pathname == "/dashboard":

        max_dt = df["Date_Only"].max()

        filters = [
            html.Label(
                "TIME RANGE",
                style={"fontSize": "11px", "color": "#8b949e"}
            ),
            dcc.DatePickerRange(
                id="d-picker",
                start_date=max_dt - timedelta(days=7),
                end_date=max_dt,
                display_format="YYYY-MM-DD",
                persistence=True
            ),
            html.Br(), html.Br(),
            html.Label(
                "HOUR SELECTOR (UTC)",
                style={"fontSize": "11px", "color": "#8b949e"}
            ),
            dcc.Dropdown(
                id="h-drop",
                options=[
                    {"label": f"{h:02d}:00", "value": h}
                    for h in range(24)
                ],
                multi=True,
                style={"color": "black"},
                persistence=True
            )
        ]

        layout = html.Div(
            style={"padding": "2.5rem", "backgroundColor": "#0d1117"},
            children=[
                html.H2(
                    "OPERATIONAL METAR ANALYTICS",
                    style={
                        "fontFamily": "Orbitron",
                        "color": "#00f2ff",
                        "letterSpacing": "3px",
                        "marginBottom": "40px"
                    }
                ),

                html.Div(id="stats-row"),

                html.H3("🌡️ TEMPERATURE"),
                dcc.Graph(id="t-line-big"),

                html.H3("❄️ DEW POINT"),
                dcc.Graph(id="d-line-big"),

                html.H3("🌬️ WIND SPEED"),
                dcc.Graph(id="windspd-fig"),

                html.H3("🧭 WIND DIRECTION"),
                dcc.Graph(id="winddir-fig"),

                html.H3("🌫️ VISIBILITY"),
                dcc.Graph(id="vis-fig"),

                html.H3("📉 PRESSURE"),
                dcc.Graph(id="pressure-fig"),

                html.H3("📜 SYSTEM LOGS"),
                html.Div(id="metar-table-area")
            ]
        )

        return layout, filters, sidebar_style

    # ===== HOME PAGE =====
    home = html.Div(
        style={
            "height": "100vh",
            "marginLeft": "-18rem",
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "center",
            "flexDirection": "column",
            "backgroundColor": "#0d1117"
        },
        children=[
            html.H1(
                "OYAA INTELHUB",
                style={
                    "fontSize": "90px",
                    "color": "white",
                    "fontFamily": "Orbitron"
                }
            ),
            html.A(
                html.Button(
                    "INITIATE ANALYTICS",
                    style={
                        "background": "transparent",
                        "color": "#00f2ff",
                        "border": "2px solid #00f2ff",
                        "padding": "15px 40px"
                    }
                ),
                href="/dashboard"
            )
        ]
    )

    return home, [], {"display": "none"}

# ===================== MAIN CALLBACK =====================
@app.callback(
    [
        Output("stats-row", "children"),
        Output("t-line-big", "figure"),
        Output("d-line-big", "figure"),
        Output("windspd-fig", "figure"),
        Output("winddir-fig", "figure"),
        Output("vis-fig", "figure"),
        Output("pressure-fig", "figure"),
        Output("metar-table-area", "children"),
    ],
    [
        Input("url", "pathname"),
        Input("d-picker", "start_date"),
        Input("d-picker", "end_date"),
        Input("h-drop", "value"),
    ],
    prevent_initial_call=True
)
def update_dashboard(pathname, start, end, hours):

    if pathname != "/dashboard":
        return [dash.no_update] * 8

    dff = df.copy()

    if start and end:
        dff = dff[
            (dff["Date_Only"] >= pd.to_datetime(start).date()) &
            (dff["Date_Only"] <= pd.to_datetime(end).date())
        ]

    if hours:
        dff = dff[dff["Hour"].isin(hours)]

    dff = dff.sort_values("Full_Timestamp")

    if dff.empty:
        return (
            html.Div("No Data Found", style={"color": "orange"}),
            go.Figure(), go.Figure(), go.Figure(),
            go.Figure(), go.Figure(), go.Figure(),
            html.Div()
        )

    # ===== STATS =====
    stats = dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H6("AVG TEMP"),
                    html.H3(f"{dff['Temp C'].mean():.1f} °C")
                ])
            )
        )
    ])

    fig_t = px.line(
        dff, x="Full_Timestamp", y="Temp C",
        template="plotly_dark"
    )

    fig_d = px.line(
        dff, x="Full_Timestamp", y="DewPoint",
        template="plotly_dark"
    )

    fig_windspd = px.line(
        dff, x="Full_Timestamp", y="Wind Spd KT",
        template="plotly_dark"
    )

    fig_vis = px.line(
        dff, x="Full_Timestamp", y="Visibility M",
        template="plotly_dark"
    )

    fig_pressure = px.line(
        dff, x="Full_Timestamp", y="Pressure hPa",
        template="plotly_dark"
    )

    fig_winddir = px.scatter_polar(
        dff,
        r="Wind Spd KT",
        theta="Wind Dir",
        template="plotly_dark"
    )

    table = dash_table.DataTable(
        data=dff[["Display_Time", "METAR"]].to_dict("records"),
        columns=[
            {"name": "UTC TIME", "id": "Display_Time"},
            {"name": "RAW METAR", "id": "METAR"}
        ],
        style_table={"height": "300px", "overflowY": "auto"},
        style_cell={
            "backgroundColor": "#0d1117",
            "color": "#c9d1d9"
        }
    )

    return (
        stats,
        fig_t,
        fig_d,
        fig_windspd,
        fig_winddir,
        fig_vis,
        fig_pressure,
        table
    )

# ===================== RUN =====================
if __name__ == "__main__":
    app.run_server(debug=True)
