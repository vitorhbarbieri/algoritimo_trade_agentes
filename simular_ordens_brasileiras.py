#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para simular ordens de daytrade para ações brasileiras.
Usa a API do projeto para capturar dados e salva tudo no banco de dados.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import logging
import time

# Configurar logging detalhado com encoding UTF-8
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('simulador_ordens.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def log_step(step_name, start_time=None):
    """Log de etapa com timing."""
    if start_time:
        elapsed = time.time() - start_time
        logger.info(f"[TIMING] [{step_name}] Concluido em {elapsed:.2f}s")
    else:
        logger.info(f"[INICIO] [{step_name}] Iniciando...")
        return time.time()

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

logger.info("=" * 70)
logger.info("INICIANDO SIMULADOR DE ORDENS BRASILEIRAS")
logger.info("=" * 70)

# Importar módulos com logs
import_start = time.time()
logger.info("[IMPORT] Importando modulos...")

try:
    logger.info("[IMPORT]   -> Importando agents...")
    from agents import TraderAgent, OrderProposal, RiskAgent
    logger.info("[IMPORT]   [OK] agents importado")
except ImportError:
    logger.info("[IMPORT]   -> Tentando importar de src.agents...")
    from src.agents import TraderAgent, OrderProposal, RiskAgent
    logger.info("[IMPORT]   [OK] src.agents importado")

try:
    logger.info("[IMPORT]   -> Importando orders_repository...")
    from orders_repository import OrdersRepository
    logger.info("[IMPORT]   [OK] orders_repository importado")
except ImportError:
    logger.info("[IMPORT]   -> Tentando importar de src.orders_repository...")
    from src.orders_repository import OrdersRepository
    logger.info("[IMPORT]   [OK] src.orders_repository importado")

try:
    logger.info("[IMPORT]   -> Importando notifications...")
    from notifications import UnifiedNotifier
    logger.info("[IMPORT]   [OK] notifications importado")
except ImportError:
    logger.info("[IMPORT]   -> Tentando importar de src.notifications...")
    from src.notifications import UnifiedNotifier
    logger.info("[IMPORT]   [OK] src.notifications importado")

try:
    logger.info("[IMPORT]   -> Importando utils...")
    from utils import StructuredLogger
    logger.info("[IMPORT]   [OK] utils importado")
except ImportError:
    logger.info("[IMPORT]   -> Tentando importar de src.utils...")
    from src.utils import StructuredLogger
    logger.info("[IMPORT]   [OK] src.utils importado")

try:
    logger.info("[IMPORT]   -> Importando market_data_api...")
    from market_data_api import create_market_data_api
    logger.info("[IMPORT]   [OK] market_data_api importado")
except ImportError:
    logger.info("[IMPORT]   -> Tentando importar de src.market_data_api...")
    from src.market_data_api import create_market_data_api
    logger.info("[IMPORT]   [OK] src.market_data_api importado")

import_time = time.time() - import_start
logger.info(f"[IMPORT] [OK] Todos os modulos importados em {import_time:.2f}s")

def coletar_dados_via_api(tickers_br, orders_repo):
    """Coleta dados reais usando a API do projeto e salva no banco."""
    step_time = log_step("COLETANDO DADOS VIA API")
    
    logger.info("=" * 70)
    logger.info("📊 COLETANDO DADOS VIA API DO PROJETO")
    logger.info("=" * 70)
    
    # Criar API
    logger.info("🔧 Criando instância da API...")
    api_start = time.time()
    stock_api = create_market_data_api('yfinance')
    logger.info(f"✅ API criada em {time.time() - api_start:.2f}s")
    
    market_data = {'spot': {}, 'options': {}}
    
    logger.info(f"🔍 Coletando dados para {len(tickers_br)} ações brasileiras...")
    
    # Data de hoje
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    logger.info(f"📅 Período: {yesterday} até {today}")
    
    ticker_count = 0
    for ticker in tickers_br:
        ticker_count += 1
        ticker_start = time.time()
        try:
            logger.info(f"\n  📈 [{ticker_count}/{len(tickers_br)}] Processando {ticker}...")
            
            # Buscar dados spot via API
            try:
                logger.info(f"     🔄 Buscando dados spot via API...")
                api_call_start = time.time()
                df_spot = stock_api.fetch_spot_data([ticker], yesterday, today)
                logger.info(f"     ✅ Dados recebidos em {time.time() - api_call_start:.2f}s")
                
                if df_spot.empty:
                    logger.warning(f"     ⚠️  Nenhum dado encontrado para {ticker}")
                    continue
                
                logger.info(f"     📊 DataFrame recebido: {len(df_spot)} registros")
                
                # Pegar último registro
                latest = df_spot.iloc[-1]
                logger.info(f"     📈 Último preço: R$ {latest.get('close', 'N/A')}")
                
                # Buscar dados intraday para calcular abertura do dia
                try:
                    logger.info(f"     🔄 Buscando dados intraday...")
                    intraday_start = time.time()
                    # Tentar buscar dados intraday
                    import yfinance as yf
                    stock = yf.Ticker(ticker)
                    hist_intraday = stock.history(period='1d', interval='5m', timeout=10)
                    logger.info(f"     ✅ Dados intraday recebidos em {time.time() - intraday_start:.2f}s")
                    
                    if not hist_intraday.empty:
                        first_of_day = hist_intraday.iloc[0]
                        open_price = float(first_of_day['Open'])
                        volume_today = int(hist_intraday['Volume'].sum()) if 'Volume' in hist_intraday.columns else int(latest['volume'])
                    else:
                        open_price = float(latest['open'])
                        volume_today = int(latest['volume']) if not pd.isna(latest['volume']) else 0
                except:
                    open_price = float(latest['open'])
                    volume_today = int(latest['volume']) if not pd.isna(latest['volume']) else 0
                
                current_price = float(latest['close'])
                high_price = float(latest['high'])
                low_price = float(latest['low'])
                
                # Calcular momentum
                intraday_return = (current_price / open_price) - 1 if open_price > 0 else 0
                
                # Calcular ADV (média dos últimos 20 dias)
                try:
                    hist_20d = stock_api.fetch_spot_data([ticker], 
                                                         (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d'),
                                                         today)
                    if not hist_20d.empty and 'volume' in hist_20d.columns:
                        adv = float(hist_20d['volume'].mean())
                    else:
                        adv = volume_today * 0.8
                except:
                    adv = volume_today * 0.8
                
                volume_ratio = volume_today / max(adv, 1)
                
                spot_data = {
                    'open': open_price,
                    'close': current_price,
                    'last': current_price,
                    'high': high_price,
                    'low': low_price,
                    'volume': volume_today,
                    'adv': adv,
                    'intraday_return': intraday_return,
                    'volume_ratio': volume_ratio
                }
                
                market_data['spot'][ticker] = spot_data
                
                logger.info(f"     ✅ Open: R$ {open_price:.2f} | Close: R$ {current_price:.2f}")
                logger.info(f"        Momentum: {intraday_return*100:.2f}% | Volume: {volume_today:,} | Ratio: {volume_ratio:.2f}x")
                
                # Salvar dados capturados no banco
                logger.info(f"     💾 Salvando dados no banco...")
                save_start = time.time()
                orders_repo.save_market_data_capture(
                    ticker=ticker,
                    data_type='spot',
                    spot_data=spot_data,
                    raw_data=latest.to_dict() if hasattr(latest, 'to_dict') else {}
                )
                logger.info(f"     ✅ Dados salvos em {time.time() - save_start:.2f}s")
                
                # Criar opções simuladas para ações brasileiras (já que yfinance não tem opções BR)
                # Criar opções mesmo com momentum baixo para garantir que algumas propostas sejam geradas
                # Na simulação, vamos criar opções para tickers com qualquer momentum (positivo ou negativo)
                # para testar o sistema completo
                logger.info(f"     🔍 Criando opções simuladas (momentum: {intraday_return*100:.2f}%)...")
                options_start = time.time()
                options_list = []
                
                # Criar opções com delta variado para garantir que algumas passem
                deltas_target = [0.50, 0.40, 0.30]
                expiry_date = pd.to_datetime(datetime.now() + timedelta(days=5))
                
                for target_delta in deltas_target:
                        # Calcular strike baseado no delta desejado
                        if target_delta >= 0.50:
                            strike = current_price * (1.0 - (target_delta - 0.50) * 0.02)
                        else:
                            strike = current_price * (1.0 + (0.50 - target_delta) * 0.03)
                        
                        strike = round(strike, 2)
                        
                        # Calcular preço teórico da opção
                        time_to_expiry = 5 / 365.0
                        iv = 0.30
                        intrinsic = max(0, current_price - strike)
                        time_value = strike * 0.02 * (time_to_expiry * 365 / 30)
                        premium = intrinsic + time_value
                        premium = max(0.01, premium)
                        
                        delta = target_delta
                        
                        # Calcular spread
                        bid = premium * 0.97
                        ask = premium * 1.03
                        mid = premium
                        spread_pct = (ask - bid) / mid if mid > 0 else 0.01
                        
                        if 0.20 <= delta <= 0.60 and spread_pct <= 0.05:
                            option_data = {
                                'underlying': ticker,
                                'strike': strike,
                                'expiry': expiry_date.isoformat(),
                                'option_type': 'C',
                                'bid': round(bid, 2),
                                'ask': round(ask, 2),
                                'mid': round(mid, 2),
                                'spread_pct': spread_pct,
                                'volume': 500,
                                'open_interest': 1000,
                                'implied_volatility': iv,
                                'delta': delta,
                                'gamma': 0.02,
                                'vega': 0.15
                            }
                        options_list.append(option_data)
                        logger.info(f"          ✅ Opção: Strike R$ {strike:.2f}, Delta {delta:.2f}, Spread {spread_pct*100:.2f}%")
                
                if options_list:
                    market_data['options'][ticker] = options_list
                    logger.info(f"        ✅ {len(options_list)} opções simuladas criadas em {time.time() - options_start:.2f}s")
                    
                    # Salvar dados de opções no banco
                    logger.info(f"        💾 Salvando opções no banco...")
                    save_options_start = time.time()
                    orders_repo.save_market_data_capture(
                        ticker=ticker,
                        data_type='options',
                        spot_data=spot_data,
                        options_data=options_list,
                        raw_data={'options_count': len(options_list)}
                    )
                    logger.info(f"        ✅ Opções salvas em {time.time() - save_options_start:.2f}s")
                else:
                    logger.warning(f"        ⚠️  Nenhuma opção criada")
            except Exception as api_err:
                logger.error(f"     ⚠️  Erro ao buscar dados via API: {api_err}")
                import traceback
                logger.error(traceback.format_exc())
                continue
            
            ticker_elapsed = time.time() - ticker_start
            logger.info(f"  ✅ {ticker} processado em {ticker_elapsed:.2f}s")
            
        except Exception as e:
            logger.error(f"     ❌ Erro ao processar {ticker}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            continue
    
    log_step("COLETANDO DADOS VIA API", step_time)
    logger.info(f"\n✅ Coleta concluída:")
    logger.info(f"   Tickers com dados spot: {len(market_data['spot'])}")
    logger.info(f"   Tickers com opções simuladas: {len(market_data.get('options', {}))}")
    
    return market_data['spot'], market_data.get('options', {})

def simular_ordens_completas():
    """Simula ordens completas para ações brasileiras."""
    script_start = time.time()
    logger.info("\n" + "=" * 70)
    logger.info("🚀 SIMULAÇÃO DE ORDENS PARA AÇÕES BRASILEIRAS")
    logger.info("=" * 70)
    
    # Carregar configuração
    logger.info("📄 Carregando configuração...")
    config_start = time.time()
    config_path = Path('config.json')
    if not config_path.exists():
        logger.error("❌ Arquivo config.json não encontrado!")
        return False
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    logger.info(f"✅ Configuração carregada em {time.time() - config_start:.2f}s")
    
    # Ações brasileiras do radar
    tickers_br = [
        'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA',
        'WEGE3.SA', 'MGLU3.SA', 'SUZB3.SA', 'RENT3.SA', 'ELET3.SA',
        'BBAS3.SA', 'SANB11.SA', 'B3SA3.SA', 'RADL3.SA', 'HAPV3.SA'
    ]
    
    # Inicializar componentes
    logger.info("\n" + "=" * 70)
    logger.info("🔧 INICIALIZANDO COMPONENTES")
    logger.info("=" * 70)
    
    init_start = time.time()
    
    logger.info("   🔄 Inicializando StructuredLogger...")
    logger_start = time.time()
    logger_obj = StructuredLogger(log_dir='logs')
    logger.info(f"   ✅ Logger inicializado em {time.time() - logger_start:.2f}s")
    
    logger.info("   🔄 Inicializando OrdersRepository...")
    repo_start = time.time()
    orders_repo = OrdersRepository()
    logger.info(f"   ✅ OrdersRepository inicializado em {time.time() - repo_start:.2f}s")
    
    logger.info("   🔄 Inicializando UnifiedNotifier...")
    notifier_start = time.time()
    notifier = UnifiedNotifier(config)
    logger.info(f"   ✅ UnifiedNotifier inicializado em {time.time() - notifier_start:.2f}s")
    
    logger.info("   🔄 Inicializando TraderAgent...")
    trader_start = time.time()
    trader_agent = TraderAgent(config, logger_obj, orders_repo=orders_repo)
    logger.info(f"   ✅ TraderAgent inicializado em {time.time() - trader_start:.2f}s")
    
    logger.info("   🔄 Inicializando RiskAgent...")
    risk_start = time.time()
    risk_agent = RiskAgent(config, logger_obj, orders_repo=orders_repo)
    logger.info(f"   ✅ RiskAgent inicializado em {time.time() - risk_start:.2f}s")
    
    logger.info("   🔄 Inicializando ExecutionSimulator...")
    exec_start = time.time()
    try:
        from src.execution import ExecutionSimulator
    except ImportError:
        from execution import ExecutionSimulator
    execution_simulator = ExecutionSimulator(config, logger_obj, orders_repo=orders_repo)
    logger.info(f"   ✅ ExecutionSimulator inicializado em {time.time() - exec_start:.2f}s")
    
    logger.info(f"✅ Todos os componentes inicializados em {time.time() - init_start:.2f}s")
    
    # 1. Coletar dados via API e salvar no banco
    spot_data, options_data = coletar_dados_via_api(tickers_br, orders_repo)
    
    if not spot_data:
        print("\n❌ Nenhum dado coletado. Abortando simulação.")
        return False
    
    # Preparar market_data
    market_data = {
        'spot': spot_data,
        'options': options_data
    }
    
    # 2. Gerar propostas
    logger.info("\n" + "=" * 70)
    logger.info("📋 GERANDO PROPOSTAS DE DAYTRADE")
    logger.info("=" * 70)
    
    timestamp = pd.to_datetime(datetime.now())
    nav = config.get('nav', 1000000)
    logger.info(f"📊 NAV: R$ {nav:,.2f}")
    logger.info(f"📅 Timestamp: {timestamp}")
    
    try:
        logger.info("🔄 Gerando propostas...")
        proposals_start = time.time()
        proposals = trader_agent.generate_proposals(timestamp, market_data)
        proposals_time = time.time() - proposals_start
        logger.info(f"✅ Propostas geradas: {len(proposals)} em {proposals_time:.2f}s")
        
        if not proposals:
            print("\n⚠️  Nenhuma proposta gerada.")
            print("   Isso pode acontecer se:")
            print("   - Nenhum ticker com momentum suficiente (>= 0.5%)")
            print("   - Nenhuma opção com delta entre 0.20-0.60")
            print("   - Spread muito alto nas opções")
            print("   - Volume insuficiente")
            return False
        
        # Mostrar propostas
        daytrade_count = 0
        for i, prop in enumerate(proposals, 1):
            if prop.strategy == 'daytrade_options':
                daytrade_count += 1
                print(f"\n   📊 Proposta Daytrade {daytrade_count}:")
                print(f"      ID: {prop.proposal_id}")
                print(f"      Ativo: {prop.metadata.get('underlying', 'N/A')}")
                print(f"      Símbolo: {prop.symbol}")
                print(f"      Strike: R$ {prop.metadata.get('strike', 0):.2f}")
                print(f"      Lado: {prop.side}")
                print(f"      Quantidade: {prop.quantity}")
                print(f"      Preço: R$ {prop.price:.2f}")
                print(f"      Delta: {prop.metadata.get('delta', 0):.3f}")
                print(f"      Momentum: {prop.metadata.get('intraday_return', 0)*100:.2f}%")
                print(f"      Volume Ratio: {prop.metadata.get('volume_ratio', 0):.2f}x")
        
        print(f"\n   📈 Total de propostas de daytrade: {daytrade_count}")
        
    except Exception as e:
        print(f"\n❌ Erro ao gerar propostas: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. Avaliar propostas com RiskAgent
    logger.info("\n" + "=" * 70)
    logger.info("🔍 AVALIANDO PROPOSTAS COM RISK AGENT")
    logger.info("=" * 70)
    
    evaluation_start = time.time()
    evaluated_count = 0
    approved_count = 0
    approved_proposals = []
    
    logger.info(f"🔄 Avaliando {len(proposals)} propostas...")
    for i, proposal in enumerate(proposals, 1):
        try:
            logger.info(f"   [{i}/{len(proposals)}] Avaliando {proposal.symbol}...")
            eval_proposal_start = time.time()
            evaluation = risk_agent.evaluate_proposal(proposal, nav)
            evaluated_count += 1
            eval_time = time.time() - eval_proposal_start
            
            if evaluation.decision == 'APPROVE':
                approved_count += 1
                approved_proposals.append((proposal, evaluation))
                logger.info(f"   ✅ {proposal.symbol}: APROVADA ({eval_time:.2f}s)")
                
                # Enviar notificação no Telegram
                try:
                    opportunity_data = {
                        'type': 'daytrade_options',
                        'symbol': proposal.symbol,
                        'ticker': proposal.metadata.get('underlying', 'N/A'),
                        'opportunity_score': proposal.metadata.get('intraday_return', 0) * 100,
                        'proposal_id': proposal.proposal_id,
                        'strike': proposal.metadata.get('strike', 'N/A'),
                        'delta': proposal.metadata.get('delta', 0),
                        'intraday_return': proposal.metadata.get('intraday_return', 0),
                        'volume_ratio': proposal.metadata.get('volume_ratio', 0)
                    }
                    notifier.notify_opportunity(opportunity_data)
                    logger.info(f"      📱 Notificação enviada para Telegram")
                except Exception as notify_err:
                    logger.warning(f"      ⚠️  Erro ao enviar notificação: {notify_err}")
                    
            elif evaluation.decision == 'MODIFY':
                # Usar valores modificados se houver
                if evaluation.modified_quantity:
                    proposal.quantity = evaluation.modified_quantity
                if evaluation.modified_price:
                    proposal.price = evaluation.modified_price
                approved_proposals.append((proposal, evaluation))
                approved_count += 1
                logger.warning(f"   ⚠️  {proposal.symbol}: MODIFICADA - {evaluation.reason} ({eval_time:.2f}s)")
            else:
                logger.warning(f"   ❌ {proposal.symbol}: REJEITADA - {evaluation.reason} ({eval_time:.2f}s)")
        except Exception as e:
            logger.error(f"   ⚠️  Erro ao avaliar {proposal.symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    evaluation_time = time.time() - evaluation_start
    logger.info(f"\n   📊 Avaliações: {evaluated_count} | Aprovadas: {approved_count} | Tempo: {evaluation_time:.2f}s")
    
    # 4. Executar propostas aprovadas
    logger.info("\n" + "=" * 70)
    logger.info("⚡ EXECUTANDO PROPOSTAS APROVADAS")
    logger.info("=" * 70)
    
    execution_start = time.time()
    executed_count = 0
    positions_created = 0
    
    if approved_proposals:
        logger.info(f"🔄 Executando {len(approved_proposals)} propostas aprovadas...")
        
        for i, (proposal, evaluation) in enumerate(approved_proposals, 1):
            try:
                logger.info(f"   [{i}/{len(approved_proposals)}] Executando {proposal.symbol}...")
                exec_order_start = time.time()
                
                # Preparar ordem para execução
                order_dict = {
                    'proposal_id': proposal.proposal_id,
                    'symbol': proposal.symbol,
                    'side': proposal.side,
                    'quantity': proposal.quantity,
                    'price': proposal.price,
                    'order_type': proposal.order_type,
                    'strategy': proposal.strategy
                }
                
                # Obter preço de mercado atual
                underlying = proposal.metadata.get('underlying', '')
                if underlying in spot_data:
                    market_price = spot_data[underlying]['last']
                else:
                    market_price = proposal.price
                
                # Executar ordem
                execution_result = execution_simulator.execute_order(order_dict, market_price)
                
                if execution_result and execution_result.get('status') == 'FILLED':
                    executed_count += 1
                    logger.info(f"      ✅ Executada: {execution_result.get('quantity', 0)} @ R$ {execution_result.get('price', 0):.2f} ({time.time() - exec_order_start:.2f}s)")
                    
                    # Criar posição aberta
                    try:
                        orders_repo.save_open_position(
                            symbol=proposal.symbol,
                            side=proposal.side,
                            quantity=execution_result.get('quantity', proposal.quantity),
                            avg_price=execution_result.get('price', proposal.price),
                            current_price=market_price,
                            delta=proposal.metadata.get('delta', 0) * execution_result.get('quantity', proposal.quantity) * 100,
                            gamma=proposal.metadata.get('gamma', 0) * execution_result.get('quantity', proposal.quantity) * 100,
                            vega=proposal.metadata.get('vega', 0) * execution_result.get('quantity', proposal.quantity) * 100
                        )
                        positions_created += 1
                        logger.info(f"      📊 Posição criada no banco")
                    except Exception as pos_err:
                        logger.warning(f"      ⚠️  Erro ao criar posição: {pos_err}")
                else:
                    logger.warning(f"      ⚠️  Execução não completada: {execution_result}")
                    
            except Exception as exec_err:
                logger.error(f"      ❌ Erro ao executar {proposal.symbol}: {exec_err}")
                import traceback
                logger.error(traceback.format_exc())
    else:
        logger.warning("   ⚠️  Nenhuma proposta aprovada para executar")
    
    execution_time = time.time() - execution_start
    logger.info(f"\n   📊 Execuções: {executed_count} | Posições criadas: {positions_created} | Tempo: {execution_time:.2f}s")
    
    # 5. Calcular snapshot de performance
    logger.info("\n" + "=" * 70)
    logger.info("📈 CALCULANDO SNAPSHOT DE PERFORMANCE")
    logger.info("=" * 70)
    
    try:
        # Obter posições abertas
        open_positions = orders_repo.get_open_positions()
        total_positions = len(open_positions) if not open_positions.empty else 0
        
        # Calcular métricas
        total_delta = 0
        total_gamma = 0
        total_vega = 0
        total_unrealized_pnl = 0
        
        if not open_positions.empty:
            total_delta = open_positions['delta'].sum() if 'delta' in open_positions.columns else 0
            total_gamma = open_positions['gamma'].sum() if 'gamma' in open_positions.columns else 0
            total_vega = open_positions['vega'].sum() if 'vega' in open_positions.columns else 0
            total_unrealized_pnl = open_positions['unrealized_pnl'].sum() if 'unrealized_pnl' in open_positions.columns else 0
        
        # Salvar snapshot
        orders_repo.save_performance_snapshot(
            timestamp=timestamp.isoformat(),
            nav=nav,
            total_pnl=total_unrealized_pnl,
            daily_pnl=total_unrealized_pnl,
            total_trades=executed_count,
            winning_trades=executed_count if total_unrealized_pnl > 0 else 0,
            losing_trades=0,
            open_positions=total_positions,
            total_delta=total_delta,
            total_gamma=total_gamma,
            total_vega=total_vega,
            portfolio_value=nav + total_unrealized_pnl,
            cash=nav - (total_unrealized_pnl if total_unrealized_pnl < 0 else 0)
        )
        
        logger.info(f"   ✅ Snapshot salvo:")
        logger.info(f"      • Posições abertas: {total_positions}")
        logger.info(f"      • PnL não realizado: R$ {total_unrealized_pnl:,.2f}")
        logger.info(f"      • Delta total: {total_delta:.2f}")
        logger.info(f"      • Gamma total: {total_gamma:.2f}")
        logger.info(f"      • Vega total: {total_vega:.2f}")
        
    except Exception as snap_err:
        logger.error(f"   ⚠️  Erro ao calcular snapshot: {snap_err}")
        import traceback
        logger.error(traceback.format_exc())
    
    # 6. Verificar banco de dados
    print("\n" + "=" * 70)
    print("💾 VERIFICANDO BANCO DE DADOS")
    print("=" * 70)
    
    try:
        # Verificar propostas
        proposals_db = orders_repo.get_proposals(strategy='daytrade_options')
        print(f"   Total de propostas de daytrade no banco: {len(proposals_db)}")
        
        # Verificar avaliações
        evaluations_db = orders_repo.get_risk_evaluations()
        print(f"   Total de avaliações no banco: {len(evaluations_db)}")
        
        # Verificar capturas de dados
        captures_db = orders_repo.get_market_data_captures()
        print(f"   Total de capturas de dados no banco: {len(captures_db)}")
        
        if len(proposals_db) > 0:
            print(f"\n   Últimas 5 propostas de daytrade:")
            for _, prop in proposals_db.tail(5).iterrows():
                symbol = prop.get('symbol', 'N/A')
                timestamp_str = prop.get('timestamp', 'N/A')
                if isinstance(timestamp_str, str):
                    timestamp_str = timestamp_str[:19]
                print(f"     • {symbol} - {timestamp_str}")
        
        print("   ✅ Banco de dados funcionando")
    except Exception as e:
        print(f"   ⚠️  Erro ao verificar banco: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. Resumo final
    total_time = time.time() - script_start
    logger.info("\n" + "=" * 70)
    logger.info("✅ SIMULAÇÃO CONCLUÍDA")
    logger.info("=" * 70)
    logger.info(f"\n📊 Resumo:")
    logger.info(f"   • Dados coletados: {len(spot_data)} tickers brasileiros")
    logger.info(f"   • Opções simuladas: {len(options_data)} tickers")
    logger.info(f"   • Propostas geradas: {len(proposals)}")
    logger.info(f"   • Propostas de daytrade: {daytrade_count}")
    logger.info(f"   • Propostas avaliadas: {evaluated_count}")
    logger.info(f"   • Propostas aprovadas: {approved_count}")
    logger.info(f"   • Propostas executadas: {executed_count if 'executed_count' in locals() else 0}")
    logger.info(f"   • Posições criadas: {positions_created if 'positions_created' in locals() else 0}")
    logger.info(f"   • Capturas de dados salvas: {len(captures_db) if 'captures_db' in locals() else 0}")
    logger.info(f"   • Tempo total: {total_time:.2f}s")
    
    logger.info(f"\n📱 Próximos passos:")
    logger.info(f"   1. Verifique o dashboard: streamlit run dashboard_central.py")
    logger.info(f"   2. Verifique o banco: agents_orders.db")
    logger.info(f"   3. Verifique os logs: logs/ e simulador_ordens.log")
    
    return True

if __name__ == '__main__':
    try:
        logger.info("🎬 Iniciando execução do script...")
        sucesso = simular_ordens_completas()
        if sucesso:
            logger.info("✅ Script executado com sucesso!")
        else:
            logger.warning("⚠️  Script executado com avisos")
        sys.exit(0 if sucesso else 1)
    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Simulação interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ Erro fatal: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
