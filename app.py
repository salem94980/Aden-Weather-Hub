import dash
from dash import html
import os

app = dash.Dash(__name__)
server = app.server

# فحص وجود الملفات قبل تشغيل الموقع
files_in_github = os.listdir('.')
target_file = "Aden_METAR_Final_Report.xlsx"

if target_file in files_in_github:
    status_msg = f"✅ الملف {target_file} موجود بنجاح. المخططات يجب أن تعمل."
    color = "green"
else:
    status_msg = f"❌ خطأ: ملف {target_file} غير موجود في GitHub. الموجود حالياً هو: {files_in_github}"
    color = "red"

app.layout = html.Div([
    html.H1("OYAA Debugger", style={"color": color}),
    html.P(status_msg, style={"fontSize": "20px"}),
    html.P("تأكد من رفع ملف الإكسل بنفس الاسم المذكور أعلاه تماماً.")
])

if __name__ == "__main__":
    app.run(debug=True)
