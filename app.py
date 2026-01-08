import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

# 1. تحميل البيانات مع تشخيص الأخطاء
def load_data():
    try:
        df = pd.read_excel("Aden_METAR_Final_Report.xlsx")
        df.columns = [str(c).strip() for c in df.columns] # تنظيف أسماء الأعمدة
        
        # محاولة دمج الوقت والتاريخ
        df["Full_Timestamp"] = pd.to_datetime(df["Date"].astype(str) + " " + df["UTC"].astype(str), errors="coerce")
        df = df.dropna(subset=["Full_Timestamp"])
        
        # تحويل الحرارة لرقم
        if "Temp C" in df.columns:
            df["Temp C"] = pd.to_numeric(df["Temp C"], errors="coerce")
            
        return df.sort_values("Full_Timestamp"), list(df.columns)
    except Exception as e:
        return pd.DataFrame(), str(e)

df_main, columns_found = load_data()

# 2. إعداد التطبيق
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

app.layout = dbc.Container([
    html.H1("OYAA DATA EXPLORER", className="text-center my-4", style={"color": "#00f2ff"}),
    
    html.Div([
        html.H5("Diagnostic Info:", style={"color": "#ffd33d"}),
        html.P(f"Columns detected in your file: {', '.join(columns_found)}"),
        html.P(f"Total rows loaded: {len(df_main)}")
    ], style={"padding": "10px", "border": "1px solid #333", "marginBottom": "20px"}),

    # المخطط البياني
    dcc.Graph(id="main-graph"),
    
    # جدول البيانات للتأكد
    html.H3("Latest 10 Records:", className="mt-4"),
    dash_table.DataTable(
        data=df_main.tail(10).to_dict("records"),
        columns=[{"name": i, "id": i} for i in df_main.columns[:4]], # عرض أول 4 أعمدة
        style_table={'overflowX': 'auto'},
        style_cell={'backgroundColor': '#111', 'color': '#fff', 'textAlign': 'left'}
    )
], fluid=True)

@app.callback(
    Output("main-graph", "figure"),
    Input("main-graph", "id") # يعمل عند التحميل
)
def update_graph(_):
    if df_main.empty:
        return px.line(title="No data to display")
    
    # رسم الحرارة بناءً على الوقت المكتشف
    fig = px.line(df_main, x="Full_Timestamp", y="Temp C", 
                  title="Temperature Monitoring (Aden Airport)",
                  template="plotly_dark")
    fig.update_traces(line_color="#00f2ff")
    return fig

if __name__ == "__main__":
    app.run(debug=True)
