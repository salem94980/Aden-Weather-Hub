import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import os

# إعداد التطبيق
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)
server = app.server

# دالة لقراءة البيانات بأمان
def get_data():
    file_path = "Aden_METAR_Final_Report.xlsx"
    if not os.path.exists(file_path):
        return pd.DataFrame(), f"Missing File: {file_path}"
    try:
        df = pd.read_excel(file_path)
        df.columns = [str(c).strip() for c in df.columns]
        # دمج التاريخ والوقت
        df['dt'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['UTC'].astype(str), errors='coerce')
        return df.dropna(subset=['dt']), "Success"
    except Exception as e:
        return pd.DataFrame(), f"Error: {str(e)}"

# واجهة المستخدم
app.layout = html.Div([
    dcc.Location(id='url'),
    dbc.NavbarSimple(brand="OYAA AIRPORT HUB", brand_href="/", color="dark", dark=True),
    dbc.Container(id="page-content", className="mt-4")
])

# التنقل بين الصفحات
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page(path):
    df, status = get_data()
    
    # صفحة التحليلات
    if path == "/analytics":
        if df.empty:
            return html.Div([html.H3("Status: " + status), html.P("تأكد من رفع ملف الإكسل بالاسم الصحيح في GitHub")])
        
        fig = px.line(df, x="dt", y="Temp C", title="Temperature Trend")
        return html.Div([
            html.H2("Analytics Dashboard"),
            dcc.Graph(figure=fig),
            dash_table.DataTable(
                data=df.tail(10).to_dict('records'),
                columns=[{"name": i, "id": i} for i in df.columns[:5]],
                style_table={'overflowX': 'auto'},
                style_cell={'backgroundColor': '#222', 'color': 'white'}
            )
        ])
    
    # الصفحة الرئيسية
    return html.Div(style={"textAlign": "center", "marginTop": "100px"}, children=[
        html.H1("ADEN INTERNATIONAL AIRPORT"),
        html.P("Weather Intelligence System"),
        dbc.Button("Go to Analytics", href="/analytics", color="primary", size="lg")
    ])

if __name__ == "__main__":
    app.run(debug=True)
