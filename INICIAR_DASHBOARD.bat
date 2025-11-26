@echo off
echo ======================================================================
echo Iniciando Dashboard Central
echo ======================================================================
echo.

REM Navegar para o diretorio correto
cd /d "%~dp0"

echo Diretorio atual:
cd
echo.

echo Verificando arquivo...
if exist "dashboard_central.py" (
    echo OK: dashboard_central.py encontrado
) else (
    echo ERRO: dashboard_central.py nao encontrado!
    echo Certifique-se de estar no diretorio correto.
    pause
    exit /b 1
)

echo.
echo Verificando dependencias...
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo Instalando Streamlit...
    pip install streamlit plotly requests -q
)

echo.
echo Verificando se API esta rodando...
python -c "import requests; r = requests.get('http://localhost:5000/health', timeout=2); print('API OK')" 2>nul
if errorlevel 1 (
    echo.
    echo AVISO: API nao esta respondendo!
    echo Certifique-se de que o servidor esta rodando:
    echo   python run_api.py
    echo.
)

echo.
echo ======================================================================
echo Iniciando Dashboard...
echo ======================================================================
echo.
echo O dashboard abrira automaticamente no navegador.
echo URL: http://localhost:8501
echo.
echo Pressione Ctrl+C para parar
echo.

streamlit run dashboard_central.py --server.port 8501

pause

