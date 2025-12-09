@echo off
REM Script para iniciar agentes automaticamente via Tarefa Agendada
REM Este script é executado pela Tarefa Agendada do Windows

cd /d C:\Projetos\algoritimo_trade_agentes

REM Criar arquivo de log com timestamp
set LOGFILE=logs\agentes_auto_%date:~-4,4%%date:~-7,2%%date:~-10,2%.log
if not exist logs mkdir logs

echo ====================================================================== >> %LOGFILE%
echo Inicio automatico dos agentes - %date% %time% >> %LOGFILE%
echo ====================================================================== >> %LOGFILE%

REM Verificar se Python está disponível
python --version >> %LOGFILE% 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado! >> %LOGFILE%
    exit /b 1
)

REM Iniciar agentes
echo Iniciando agentes... >> %LOGFILE%
python iniciar_agentes.py >> %LOGFILE% 2>&1

