"""
Script para executar fechamento EOD manual e análise
"""
import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent))

from src.orders_repository import OrdersRepository
from src.eod_analysis import EODAnalyzer
from src.notifications import UnifiedNotifier

print("=" * 70)
print("FECHAMENTO EOD MANUAL E ANÁLISE")
print("=" * 70)
print()

# Carregar config
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

repo = OrdersRepository()
notifier = UnifiedNotifier(config)
hoje = datetime.now().strftime('%Y-%m-%d')

print(f"📅 Data: {hoje}")
print()

# Verificar posições abertas
print("1. VERIFICANDO POSIÇÕES ABERTAS:")
print("-" * 70)
posicoes = repo.get_open_positions()
print(f"   Total de posições abertas: {len(posicoes)}")

if not posicoes.empty:
    print("   Posições:")
    for idx, row in posicoes.iterrows():
        print(f"     - {row.get('symbol', 'N/A')}: {row.get('quantity', 0)} @ R$ {row.get('avg_price', 0):.2f}")
    
    print()
    print("2. FECHANDO POSIÇÕES:")
    print("-" * 70)
    closed_count = repo.close_all_daytrade_positions()
    print(f"   ✅ {closed_count} posições fechadas")
else:
    print("   ✅ Nenhuma posição aberta")
    closed_count = 0

print()

# Executar análise
print("3. EXECUTANDO ANÁLISE EOD:")
print("-" * 70)
analyzer = EODAnalyzer(config)
analysis = analyzer.analyze_daily_proposals(hoje)

print(f"   Total de propostas: {analysis['total_proposals']}")
print(f"   Análise concluída")

# Formatar e enviar relatório
print()
print("4. ENVIANDO RELATÓRIO VIA TELEGRAM:")
print("-" * 70)
report = analyzer.format_telegram_report(analysis)

# Enviar notificação de fechamento
b3_time = datetime.now()
message_eod = f"""
🏁 *FECHAMENTO EOD MANUAL - {b3_time.strftime('%d/%m/%Y')}*

*Horário:* {b3_time.strftime('%H:%M:%S')} (B3)

*Posições Fechadas:*
• Total: {closed_count} posições

🔄 Executando análise automática pós-EOD...
"""

notifier.send(message_eod, title="Fechamento EOD", priority='normal')

# Enviar relatório completo
if analysis['total_proposals'] > 0:
    notifier.send(report, title="📊 Análise EOD Completa", priority='normal')
    print("   ✅ Relatório enviado")
else:
    print("   ℹ️  Nenhuma proposta para analisar")

print()
print("=" * 70)
print("✅ PROCESSO CONCLUÍDO")
print("=" * 70)

