# Script PowerShell para configurar Tarefa Agendada (versão simples - sem admin)
# Executa os agentes automaticamente todos os dias às 09:30

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Configurando Tarefa Agendada para Agentes de Trading" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Caminhos
$taskName = "TradingAgents_AutoStart"
$scriptPath = "C:\Projetos\algoritimo_trade_agentes\iniciar_agentes_auto.bat"
$workingDir = "C:\Projetos\algoritimo_trade_agentes"

Write-Host "Configurando tarefa:" -ForegroundColor Green
Write-Host "  Nome: $taskName" -ForegroundColor White
Write-Host "  Script: $scriptPath" -ForegroundColor White
Write-Host "  Horario: 09:30 todos os dias" -ForegroundColor White
Write-Host ""

# Verificar se o script existe
if (-not (Test-Path $scriptPath)) {
    Write-Host "ERRO: Script nao encontrado: $scriptPath" -ForegroundColor Red
    exit 1
}

# Verificar se a tarefa já existe
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Tarefa ja existe. Removendo..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
}

# Criar ação (executar o script)
$action = New-ScheduledTaskAction -Execute $scriptPath -WorkingDirectory $workingDir

# Criar gatilho (diariamente às 09:30)
$trigger = New-ScheduledTaskTrigger -Daily -At "09:30"

# Criar configurações
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Criar principal (executar como usuário atual)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive

# Registrar a tarefa
try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Inicia agentes de trading automaticamente todos os dias às 09:30" `
        -Force | Out-Null
    
    Write-Host "======================================================================" -ForegroundColor Green
    Write-Host "TAREFA AGENDADA CRIADA COM SUCESSO!" -ForegroundColor Green
    Write-Host "======================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Detalhes:" -ForegroundColor Cyan
    Write-Host "  Nome: $taskName" -ForegroundColor White
    Write-Host "  Horario: 09:30 todos os dias" -ForegroundColor White
    Write-Host "  Script: $scriptPath" -ForegroundColor White
    Write-Host ""
    Write-Host "A tarefa iniciara automaticamente amanha as 09:30!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Para verificar:" -ForegroundColor Yellow
    Write-Host "  Get-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Para testar agora:" -ForegroundColor Yellow
    Write-Host "  Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "ERRO ao criar tarefa: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Tente executar manualmente:" -ForegroundColor Yellow
    Write-Host "  1. Abra o Agendador de Tarefas (Win+R, digite: taskschd.msc)" -ForegroundColor Yellow
    Write-Host "  2. Clique em 'Criar Tarefa Básica'" -ForegroundColor Yellow
    Write-Host "  3. Nome: TradingAgents_AutoStart" -ForegroundColor Yellow
    Write-Host "  4. Gatilho: Diariamente às 09:30" -ForegroundColor Yellow
    Write-Host "  5. Ação: Iniciar programa: $scriptPath" -ForegroundColor Yellow
    exit 1
}

# Perguntar se quer testar agora
Write-Host "Deseja testar a tarefa agora? (S/N)" -ForegroundColor Cyan
$test = Read-Host
if ($test -eq "S" -or $test -eq "s") {
    Write-Host "Executando tarefa..." -ForegroundColor Yellow
    Start-ScheduledTask -TaskName $taskName
    Write-Host "Tarefa iniciada! Verifique os logs em: logs\agentes_auto_*.log" -ForegroundColor Green
    Write-Host "Ou verifique se o processo Python esta rodando:" -ForegroundColor Green
    Write-Host "  Get-Process python" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Configuracao concluida!" -ForegroundColor Green

