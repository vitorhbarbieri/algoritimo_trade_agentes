@echo off
echo ======================================================================
echo Iniciando API Server do Sistema de Trading
echo ======================================================================
echo.
echo Instalando dependencias (se necessario)...
pip install flask flask-cors -q
echo.
echo Iniciando servidor Flask...
echo.
echo API disponivel em: http://localhost:5000
echo Dashboard disponivel em: http://localhost:8501
echo.
echo Para testar:
echo   curl http://localhost:5000/health
echo.
echo ======================================================================
python run_api.py

