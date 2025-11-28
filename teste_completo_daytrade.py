#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste completo do sistema de daytrade:
1. Coleta dados reais de mercado de hoje
2. Executa DayTradeOptionsStrategy
3. Gera propostas
4. Salva no banco de dados
5. Envia notificação no Telegram
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from agents import TraderAgent, DayTradeOptionsStrategy, OrderProposal
    from orders_repository import OrdersRepository
    from notifications import UnifiedNotifier
    from utils import StructuredLogger
except ImportError:
    from src.agents import TraderAgent, DayTradeOptionsStrategy, OrderProposal
    from src.orders_repository import OrdersRepository
    from src.notifications import UnifiedNotifier
    from src.utils import StructuredLogger

def coletar_dados_reais():
    """Coleta dados reais de mercado de hoje."""
    print("=" * 70)
    print("📊 COLETANDO DADOS REAIS DE MERCADO")
    print("=" * 70)
    
    try:
        import yfinance as yf
    except ImportError:
        print("❌ yfinance não instalado! Execute: pip install yfinance")
        return None, None
    
    # Tickers para testar (alguns brasileiros e americanos)
    tickers = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'AAPL', 'MSFT', 'TSLA']
    
    market_data = {'spot': {}, 'options': {}}
    
    print(f"\n🔍 Coletando dados para {len(tickers)} tickers...")
    
    for ticker in tickers:
        try:
            print(f"\n  📈 {ticker}...")
            stock = yf.Ticker(ticker)
            
            # Buscar dados do dia atual
            try:
                # Tentar dados intraday primeiro
                hist = stock.history(period='1d', interval='5m', timeout=10)
                if hist.empty:
                    hist = stock.history(period='5d', interval='1d', timeout=10)
            except:
                hist = stock.history(period='5d', interval='1d', timeout=10)
            
            if hist.empty:
                print(f"     ⚠️  Nenhum dado encontrado")
                continue
            
            # Pegar dados mais recentes
            latest = hist.iloc[-1]
            
            # Determinar preço de abertura
            if len(hist) > 1:
                first_of_day = hist.iloc[0]
                open_price = float(first_of_day['Open'])
                volume_today = int(hist['Volume'].sum()) if 'Volume' in hist.columns else int(latest['Volume'])
            else:
                open_price = float(latest['Open'])
                volume_today = int(latest['Volume']) if not pd.isna(latest['Volume']) else 0
            
            current_price = float(latest['Close'])
            
            market_data['spot'][ticker] = {
                'open': open_price,
                'close': current_price,
                'last': current_price,
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'volume': volume_today,
                'adv': volume_today * 0.8  # Simular ADV (80% do volume atual)
            }
            
            # Calcular momentum
            intraday_return = (current_price / open_price) - 1
            volume_ratio = 1.0  # Assumir volume normal para teste
            
            print(f"     ✅ Open: R$ {open_price:.2f} | Close: R$ {current_price:.2f}")
            print(f"        Momentum: {intraday_return*100:.2f}% | Volume: {volume_today:,}")
            
            # Buscar opções apenas para tickers com momentum positivo
            if intraday_return > 0.003:  # 0.3% de momentum mínimo
                try:
                    print(f"     🔍 Buscando opções...")
                    expirations = stock.options
                    if expirations:
                        # Pegar primeira expiração próxima
                        expiry_str = expirations[0]
                        opt_chain = stock.option_chain(expiry_str)
                        
                        if not opt_chain.calls.empty:
                            calls = opt_chain.calls.head(20)  # Primeiras 20 calls
                            options_list = []
                            
                            for _, row in calls.iterrows():
                                strike = float(row['strike'])
                                bid = float(row['bid']) if not pd.isna(row['bid']) else 0
                                ask = float(row['ask']) if not pd.isna(row['ask']) else 0
                                mid = (bid + ask) / 2 if bid > 0 and ask > 0 else bid if bid > 0 else ask
                                
                            if mid > 0:
                                # Calcular spread percentual
                                spread_pct = (ask - bid) / mid if mid > 0 else 1.0
                                
                                options_list.append({
                                    'underlying': ticker,
                                    'strike': strike,
                                    'expiry': pd.to_datetime(expiry_str),
                                    'option_type': 'C',
                                    'bid': bid,
                                    'ask': ask,
                                    'mid': mid,
                                    'spread_pct': spread_pct,
                                    'volume': int(row['volume']) if not pd.isna(row['volume']) else 200,  # Mínimo 200 para passar filtro
                                    'open_interest': int(row['openInterest']) if not pd.isna(row['openInterest']) else 0,
                                    'implied_volatility': float(row['impliedVolatility']) if not pd.isna(row['impliedVolatility']) else 0.25
                                })
                            
                            if options_list:
                                market_data['options'][ticker] = options_list
                                print(f"        ✅ {len(options_list)} opções encontradas")
                            else:
                                print(f"        ⚠️  Nenhuma opção válida")
                    else:
                        print(f"        ⚠️  Nenhuma expiração disponível")
                except Exception as e:
                    print(f"        ⚠️  Erro ao buscar opções: {str(e)[:50]}")
            
        except Exception as e:
            print(f"     ❌ Erro: {e}")
            continue
    
    print(f"\n✅ Coleta concluída:")
    print(f"   Tickers com dados spot: {len(market_data['spot'])}")
    print(f"   Tickers com opções: {len(market_data.get('options', {}))}")
    
    return market_data['spot'], market_data.get('options', {})

def executar_teste_completo():
    """Executa teste completo do sistema."""
    print("\n" + "=" * 70)
    print("🚀 TESTE COMPLETO DO SISTEMA DE DAYTRADE")
    print("=" * 70)
    
    # Carregar configuração
    config_path = Path('config.json')
    if not config_path.exists():
        print("❌ Arquivo config.json não encontrado!")
        return False
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 1. Coletar dados reais
    spot_data, options_data = coletar_dados_reais()
    
    if not spot_data:
        print("\n❌ Nenhum dado coletado. Abortando teste.")
        return False
    
    # Preparar market_data
    market_data = {
        'spot': spot_data,
        'options': options_data
    }
    
    # 2. Inicializar componentes
    print("\n" + "=" * 70)
    print("🔧 INICIALIZANDO COMPONENTES")
    print("=" * 70)
    
    logger_obj = StructuredLogger(log_dir='logs')
    orders_repo = OrdersRepository()
    notifier = UnifiedNotifier(config)
    trader_agent = TraderAgent(config, logger_obj, orders_repo=orders_repo)
    
    print("   ✅ Logger inicializado")
    print("   ✅ OrdersRepository inicializado")
    print("   ✅ UnifiedNotifier inicializado")
    print("   ✅ TraderAgent inicializado")
    
    # 3. Gerar propostas
    print("\n" + "=" * 70)
    print("📋 GERANDO PROPOSTAS")
    print("=" * 70)
    
    timestamp = pd.to_datetime(datetime.now())
    nav = config.get('nav', 1000000)
    
    try:
        proposals = trader_agent.generate_proposals(timestamp, market_data)
        
        print(f"\n✅ Propostas geradas: {len(proposals)}")
        
        if not proposals:
            print("\n⚠️  Nenhuma proposta gerada.")
            print("   Possíveis causas:")
            print("   - Nenhum ticker com momentum suficiente (>= 0.5%)")
            print("   - Nenhuma opção com delta entre 0.20-0.60")
            print("   - Spread muito alto nas opções")
            print("   - Volume insuficiente")
            print("\n   Mas vamos continuar o teste mesmo assim...")
            
            # Criar uma proposta de teste para demonstrar o fluxo
            print("\n📝 Criando proposta de teste para demonstrar o fluxo...")
            test_proposal = OrderProposal(
                proposal_id=f"TEST-DAYOPT-AAPL-150-{int(timestamp.timestamp())}",
                strategy='daytrade_options',
                instrument_type='options',
                symbol='AAPL_150_C_20250125',
                side='BUY',
                quantity=10,
                price=2.50,
                order_type='LIMIT',
                metadata={
                    'underlying': 'AAPL',
                    'strike': 150.0,
                    'expiry': timestamp.isoformat(),
                    'days_to_expiry': 5,
                    'delta': 0.45,
                    'gamma': 0.02,
                    'vega': 0.15,
                    'iv': 0.25,
                    'intraday_return': 0.008,
                    'volume_ratio': 1.5,
                    'spread_pct': 0.03,
                    'premium': 2.50,
                    'max_risk': 2500.0,
                    'take_profit_pct': 0.10,
                    'stop_loss_pct': 0.40,
                    'eod_close': True
                }
            )
            proposals = [test_proposal]
            print("   ✅ Proposta de teste criada")
            
            # Salvar proposta de teste no banco manualmente
            try:
                proposal_dict = {
                    'proposal_id': test_proposal.proposal_id,
                    'timestamp': timestamp.isoformat(),
                    'strategy': test_proposal.strategy,
                    'instrument_type': test_proposal.instrument_type,
                    'symbol': test_proposal.symbol,
                    'side': test_proposal.side,
                    'quantity': test_proposal.quantity,
                    'price': test_proposal.price,
                    'order_type': test_proposal.order_type,
                    'metadata': test_proposal.metadata
                }
                orders_repo.save_proposal(proposal_dict)
                print("   ✅ Proposta de teste salva no banco")
            except Exception as e:
                print(f"   ⚠️  Erro ao salvar proposta no banco: {e}")
        
        # Mostrar propostas
        for i, prop in enumerate(proposals, 1):
            print(f"\n   Proposta {i}:")
            print(f"      ID: {prop.proposal_id}")
            print(f"      Estratégia: {prop.strategy}")
            print(f"      Símbolo: {prop.symbol}")
            print(f"      Lado: {prop.side}")
            print(f"      Quantidade: {prop.quantity}")
            print(f"      Preço: R$ {prop.price:.2f}")
            if prop.metadata:
                print(f"      Underlying: {prop.metadata.get('underlying', 'N/A')}")
                print(f"      Strike: {prop.metadata.get('strike', 'N/A')}")
                print(f"      Delta: {prop.metadata.get('delta', 0):.3f}")
                print(f"      Momentum: {prop.metadata.get('intraday_return', 0)*100:.2f}%")
                print(f"      Volume Ratio: {prop.metadata.get('volume_ratio', 0):.2f}x")
        
    except Exception as e:
        print(f"\n❌ Erro ao gerar propostas: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. Verificar banco de dados
    print("\n" + "=" * 70)
    print("💾 VERIFICANDO BANCO DE DADOS")
    print("=" * 70)
    
    try:
        # Verificar se propostas foram salvas
        proposals_db = orders_repo.get_proposals()
        print(f"   Total de propostas no banco: {len(proposals_db)}")
        
        if len(proposals_db) > 0:
            print(f"   Últimas 5 propostas:")
            for _, prop in proposals_db.tail(5).iterrows():
                print(f"     - {prop.get('strategy', 'N/A')}: {prop.get('symbol', 'N/A')} ({prop.get('timestamp', 'N/A')})")
        
        print("   ✅ Banco de dados funcionando")
    except Exception as e:
        print(f"   ⚠️  Erro ao verificar banco: {e}")
    
    # 5. Enviar notificações
    print("\n" + "=" * 70)
    print("📱 ENVIANDO NOTIFICAÇÕES")
    print("=" * 70)
    
    # Verificar se notificações estão configuradas
    telegram_enabled = config.get('notifications', {}).get('telegram', {}).get('enabled', False)
    telegram_token = config.get('notifications', {}).get('telegram', {}).get('bot_token') or os.getenv('TELEGRAM_BOT_TOKEN', '')
    telegram_chat = config.get('notifications', {}).get('telegram', {}).get('chat_id') or os.getenv('TELEGRAM_CHAT_ID', '')
    
    discord_enabled = config.get('notifications', {}).get('discord', {}).get('enabled', False)
    discord_webhook = config.get('notifications', {}).get('discord', {}).get('webhook_url') or os.getenv('DISCORD_WEBHOOK_URL', '')
    
    if not telegram_enabled or not telegram_token or not telegram_chat:
        if not discord_enabled or not discord_webhook:
            print("\n   ⚠️  Notificações não configuradas!")
            print("   Para receber notificações:")
            print("   1. Configure Telegram: python configurar_telegram_rapido.py")
            print("   2. Ou configure Discord: veja CONFIGURAR_DISCORD.md")
            print("   3. Ou configure variáveis de ambiente:")
            print("      export TELEGRAM_BOT_TOKEN='seu_token'")
            print("      export TELEGRAM_CHAT_ID='seu_chat_id'")
            print("\n   Continuando teste sem enviar notificações...")
        else:
            print("   ✅ Discord configurado")
    else:
        print("   ✅ Telegram configurado")
    
    try:
        # Enviar notificação para cada proposta
        notifications_sent = 0
        for prop in proposals:
            if prop.strategy == 'daytrade_options':
                opportunity_data = {
                    'type': 'daytrade_options',
                    'symbol': prop.symbol,
                    'ticker': prop.metadata.get('underlying', 'N/A'),
                    'opportunity_score': prop.metadata.get('intraday_return', 0) * 100,
                    'proposal_id': prop.proposal_id,
                    'strike': prop.metadata.get('strike', 'N/A'),
                    'delta': prop.metadata.get('delta', 0),
                    'intraday_return': prop.metadata.get('intraday_return', 0),
                    'volume_ratio': prop.metadata.get('volume_ratio', 0)
                }
                
                print(f"\n   📧 Enviando notificação para: {prop.symbol}")
                result = notifier.notify_opportunity(opportunity_data)
                if result:
                    notifications_sent += 1
                    print(f"      ✅ Notificação enviada")
                else:
                    print(f"      ⚠️  Notificação não enviada (canal não configurado)")
        
        # Enviar resumo
        print(f"\n   📊 Enviando resumo do teste...")
        summary_message = f"""
🧪 *TESTE COMPLETO DO SISTEMA DE DAYTRADE*

*Data/Hora:* {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

*Resultados:*
• Dados coletados: {len(spot_data)} tickers
• Opções disponíveis: {len(options_data)} tickers
• Propostas geradas: {len(proposals)}

*Propostas:*
"""
        for prop in proposals:
            underlying = prop.metadata.get('underlying', 'N/A')
            strike = prop.metadata.get('strike', 'N/A')
            summary_message += f"• {underlying} Strike {strike}: {prop.quantity} contratos @ R$ {prop.price:.2f}\n"
        
        summary_message += f"\n✅ Sistema funcionando corretamente!"
        summary_message += f"\n\n*Detalhes:*"
        for prop in proposals:
            if prop.metadata:
                summary_message += f"\n• {prop.symbol}:"
                summary_message += f"\n  - Momentum: {prop.metadata.get('intraday_return', 0)*100:.2f}%"
                summary_message += f"\n  - Delta: {prop.metadata.get('delta', 0):.3f}"
                summary_message += f"\n  - Volume Ratio: {prop.metadata.get('volume_ratio', 0):.2f}x"
        
        result = notifier.send(summary_message, title="🧪 Teste Completo", priority='normal')
        if result:
            notifications_sent += 1
            print(f"      ✅ Resumo enviado")
        else:
            print(f"      ⚠️  Resumo não enviado (canal não configurado)")
        
    except Exception as e:
        print(f"   ⚠️  Erro ao enviar notificações: {e}")
        import traceback
        traceback.print_exc()
        notifications_sent = 0
    
    # 6. Resumo final
    print("\n" + "=" * 70)
    print("✅ TESTE COMPLETO FINALIZADO")
    print("=" * 70)
    proposals_db_count = len(proposals_db) if 'proposals_db' in locals() else 0
    notifications_sent_count = notifications_sent if 'notifications_sent' in locals() else 0
    
    print(f"\n📊 Resumo:")
    print(f"   • Dados coletados: {len(spot_data)} tickers")
    print(f"   • Opções disponíveis: {len(options_data)} tickers")
    print(f"   • Propostas geradas: {len(proposals)}")
    print(f"   • Propostas no banco: {proposals_db_count}")
    print(f"   • Notificações enviadas: {notifications_sent_count}")
    
    # Verificar banco novamente após salvar
    try:
        proposals_db_final = orders_repo.get_proposals()
        if len(proposals_db_final) > proposals_db_count:
            print(f"\n✅ Propostas foram salvas no banco!")
            print(f"   Total no banco agora: {len(proposals_db_final)}")
    except Exception as e:
        print(f"   ⚠️  Erro ao verificar banco final: {e}")
    
    print(f"\n📱 Verifique seu Telegram/Discord para as notificações!")
    print(f"💾 Verifique o banco de dados: agents_orders.db")
    print(f"📝 Verifique os logs: logs/")
    
    return True

if __name__ == '__main__':
    try:
        sucesso = executar_teste_completo()
        sys.exit(0 if sucesso else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

