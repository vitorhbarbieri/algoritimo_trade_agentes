@echo off
echo ======================================================================
echo Iniciando Sistema Completo de Trading
echo ======================================================================
echo.

REM Mudar para diretório do projeto
cd /d C:\Projetos\algoritimo_trade_agentes

echo [1/2] Iniciando Agentes de Trading...
start "Agentes Trading" cmd /k "python iniciar_agentes.py"

echo.
echo Aguardando agentes iniciarem...
timeout /t 5 /nobreak >nul

echo [2/2] Iniciando Dashboard Central...
start "Dashboard Central" cmd /k "streamlit run dashboard_central.py"

echo.
echo ======================================================================
echo Sistema Iniciado!
echo ======================================================================
echo.
echo Agentes: Rodando em janela separada
echo Dashboard: http://localhost:8501 (aguarde alguns segundos)
echo.
echo Para parar:
echo   - Feche as janelas dos agentes e dashboard
echo   - Ou pressione Ctrl+C em cada janela
echo.
echo ======================================================================
pause

