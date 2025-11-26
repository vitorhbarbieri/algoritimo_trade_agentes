@echo off
echo ======================================================================
echo Iniciando Dashboard Central - Trading Agents
echo ======================================================================
echo.
echo Verificando se Streamlit esta instalado...
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo Instalando Streamlit e dependencias...
    pip install streamlit plotly requests -q
)

echo.
echo Verificando se a API esta rodando...
python -c "import requests; r = requests.get('http://localhost:5000/health', timeout=2); print('API OK')" 2>nul
if errorlevel 1 (
    echo.
    echo AVISO: API nao esta respondendo!
    echo Certifique-se de que o servidor esta rodando:
    echo   python run_api.py
    echo.
    pause
)

echo.
echo ======================================================================
echo Dashboard iniciando em http://localhost:8501
echo ======================================================================
echo.
echo Pressione Ctrl+C para parar
echo.

python -m streamlit run dashboard_central.py --server.port 8501

pause

