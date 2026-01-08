import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import os

# 1. تحميل البيانات بطريقة "القوة الغاشمة" (تتخطى أي أخطاء تنسيق)
def force_load_data():
    file_name = "Aden_METAR_Final_Report.xlsx"
    try:
        # قراءة الملف مع تجاهل أول صفين إذا كان هناك رؤوس جداول معقدة
        df = pd.read_excel(file_name, engine='openpyxl')
        
        # تنظيف تلقائي للبيانات
        df.columns = [str(c).strip() for c in df.columns]
        
        # تحويل التاريخ والوقت مهما كان تنسيقهما
        df['Date'] = df['Date'].astype(str)
        df['UTC'] = df['UTC'].astype(str)
        df['Timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['UTC'], errors='coerce')
        
        # تحويل الأعمدة الرقمية بالقوة
        for col in ['Temp C', 'Humidity %', 'Wind Speed KT']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df.dropna(subset=['Timestamp']).sort_values('Timestamp')
    except Exception as e:
        print(f"Crucial Error: {e}")
        return pd.DataFrame()

df_raw = force_load_data()

# 2. بناء التطبيق
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
server = app.server

app.layout = dbc.Container([
    html.Div(style={'textAlign': 'center', 'padding': '20px'}, children=[
        html.H1("OYAA - ADEN AIRPORT HUB", style={'color': '#00f2ff', 'fontFamily': 'Orbitron'}),
        html.P("System Status: OPERATIONAL", style={'color': '#00ff00'})
    ]),
    
    # قسم المخططات الأساسي
    dbc.Row([
        dbc.Col([
            html.H4("Temperature Analysis", className="text-center"),
            dcc.Graph(id='temp-fig')
        ], width=12)
    ]),

    # جدول البيانات للتأكد من وجودها
    html.Div([
        html.H4("Internal Data Registry", className="mt-5"),
        dash_table.DataTable(
            id='table',
            data=df_raw.tail(15).to_dict('records'),
            columns=[{"name": i, "id": i} for i in df_raw.columns if i != 'Timestamp'],
            style_table={'overflowX': 'auto'},
            style_cell={'backgroundColor': '#000', 'color': '#fff', 'textAlign': 'left', 'border': '1px solid #333'},
            style_header={'backgroundColor': '#111', 'fontWeight': 'bold'}
        )
    ])
], fluid=True, style={'backgroundColor': '#000', 'minHeight': '100vh', 'color': '#fff'})

@app.callback(
    Output('temp-fig', 'figure'),
    Input('temp-fig', 'id')
)
def update_graph(_):
    if df_raw.empty:
        return px.line(title="⚠️ Error: Data stream is empty. Check Excel structure.")
    
    fig = px.line(df_raw, x='Timestamp', y='Temp C', template='plotly_dark')
    fig.update_traces(line_color='#00f2ff', line_width=3)
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    return fig

if __name__ == "__main__":
    app.run(debug=True)
