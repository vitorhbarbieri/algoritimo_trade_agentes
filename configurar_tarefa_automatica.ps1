# Script PowerShell para configurar Tarefa Agendada do Windows
# Executa os agentes automaticamente todos os dias às 09:30

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Configurando Tarefa Agendada para Agentes de Trading" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se está executando como Administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "AVISO: Execute como Administrador para criar a tarefa agendada" -ForegroundColor Yellow
    Write-Host "Clique com botao direito no PowerShell e escolha 'Executar como Administrador'" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Deseja continuar mesmo assim? (S/N)"
    if ($continue -ne "S" -and $continue -ne "s") {
        exit
    }
}

# Caminhos
$taskName = "TradingAgents_AutoStart"
$scriptPath = "C:\Projetos\algoritimo_trade_agentes\iniciar_agentes_auto.bat"
$workingDir = "C:\Projetos\algoritimo_trade_agentes"
$pythonPath = (Get-Command python).Source

Write-Host "Configurando tarefa:" -ForegroundColor Green
Write-Host "  Nome: $taskName" -ForegroundColor White
Write-Host "  Script: $scriptPath" -ForegroundColor White
Write-Host "  Horario: 09:30 todos os dias" -ForegroundColor White
Write-Host ""

# Verificar se o script existe
if (-not (Test-Path $scriptPath)) {
    Write-Host "ERRO: Script nao encontrado: $scriptPath" -ForegroundColor Red
    Write-Host "Criando script..." -ForegroundColor Yellow
    # O script já foi criado acima, mas vamos garantir
}

# Verificar se a tarefa já existe
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Tarefa ja existe. Deseja atualizar? (S/N)" -ForegroundColor Yellow
    $update = Read-Host
    if ($update -eq "S" -or $update -eq "s") {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "Tarefa removida. Criando nova..." -ForegroundColor Green
    } else {
        Write-Host "Cancelado." -ForegroundColor Yellow
        exit
    }
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
    -RunOnlyIfNetworkAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

# Criar principal (executar mesmo se usuário não estiver logado)
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Highest

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
    Write-Host "Para verificar:" -ForegroundColor Yellow
    Write-Host "  Get-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Para testar agora:" -ForegroundColor Yellow
    Write-Host "  Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Para remover:" -ForegroundColor Yellow
    Write-Host "  Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "ERRO ao criar tarefa: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Tente executar este script como Administrador:" -ForegroundColor Yellow
    Write-Host "  1. Clique com botao direito no PowerShell" -ForegroundColor Yellow
    Write-Host "  2. Escolha 'Executar como Administrador'" -ForegroundColor Yellow
    Write-Host "  3. Execute este script novamente" -ForegroundColor Yellow
    exit 1
}

# Perguntar se quer testar agora
Write-Host "Deseja testar a tarefa agora? (S/N)" -ForegroundColor Cyan
$test = Read-Host
if ($test -eq "S" -or $test -eq "s") {
    Write-Host "Executando tarefa..." -ForegroundColor Yellow
    Start-ScheduledTask -TaskName $taskName
    Write-Host "Tarefa iniciada! Verifique os logs em: logs\agentes_auto_*.log" -ForegroundColor Green
}

Write-Host ""
Write-Host "Configuracao concluida!" -ForegroundColor Green

