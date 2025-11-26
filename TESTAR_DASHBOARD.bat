@echo off
echo ======================================================================
echo Testando Dashboard Central
echo ======================================================================
echo.

echo Verificando dependencias...
python -c "import streamlit; print('Streamlit: OK')" 2>nul || echo Streamlit: FALTA INSTALAR
python -c "import plotly; print('Plotly: OK')" 2>nul || echo Plotly: FALTA INSTALAR
python -c "import requests; print('Requests: OK')" 2>nul || echo Requests: FALTA INSTALAR

echo.
echo Verificando sintaxe do dashboard...
python -m py_compile dashboard_central.py 2>nul && echo Sintaxe: OK || echo Sintaxe: ERRO

echo.
echo ======================================================================
echo Para iniciar o dashboard:
echo   python -m streamlit run dashboard_central.py
echo ======================================================================
echo.

pause

