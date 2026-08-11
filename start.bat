@echo off
cd /d "%~dp0"
echo Starting Taobao Store Analytics Workbench...
start "" "http://localhost:8501"
"C:\Users\st150\AppData\Local\Programs\Python\Python312\python.exe" -m streamlit run app.py --server.headless true
pause
