@echo off
echo ======================================================================
echo Iniciando Sistema de Trading - API + Dashboard
echo ======================================================================
echo.
echo Passo 1: Verificando dependencias...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Instalando Flask...
    pip install flask flask-cors -q
)

python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo Instalando Streamlit...
    pip install streamlit -q
)

echo.
echo Passo 2: Iniciando API Server em background...
start "API Server" cmd /c "python run_api.py"

echo Aguardando servidor iniciar...
timeout /t 5 /nobreak >nul

echo.
echo Passo 3: Testando conexao...
python -c "import requests; r = requests.get('http://localhost:5000/health', timeout=2); print('API OK:', r.json())" 2>nul
if errorlevel 1 (
    echo AVISO: API pode nao estar respondendo ainda. Aguarde alguns segundos.
)

echo.
echo Passo 4: Iniciando Dashboard...
echo.
echo ======================================================================
echo Sistema iniciado!
echo ======================================================================
echo API Server: http://localhost:5000
echo Dashboard:  http://localhost:8501
echo.
echo Para testar a API:
echo   python test_api.py
echo.
echo Para parar os servidores, feche as janelas ou pressione Ctrl+C
echo ======================================================================
echo.

start "Dashboard" cmd /c "streamlit run dashboard.py"

pause

