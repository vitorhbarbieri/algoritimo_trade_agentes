#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simulador de Market Data para testes dos agentes.
Este script SIMULA dados de mercado como se fosse o mercado real acontecendo,
criando condições favoráveis para os agentes trabalharem.
Os AGENTES processam esses dados normalmente, como se fossem dados reais.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import logging
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('simulador_market_data.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from orders_repository import OrdersRepository
    from market_data_api import create_market_data_api
except ImportError:
    from src.orders_repository import OrdersRepository
    from src.market_data_api import create_market_data_api

def criar_dados_mercado_simulados(tickers_br, orders_repo):
    """
    Cria dados de mercado simulados com condições favoráveis para daytrade.
    Simula como se fosse o mercado real durante o pregão.
    """
    logger.info("=" * 70)
    logger.info("SIMULANDO DADOS DE MERCADO (Como se fosse mercado real)")
    logger.info("=" * 70)
    
    market_data = {'spot': {}, 'options': {}}
    
    logger.info(f"Gerando dados simulados para {len(tickers_br)} tickers...")
    logger.info("Criando condicoes favoraveis para daytrade (momentum positivo, volume alto)...")
    
    # Data de hoje
    today = datetime.now().strftime('%Y-%m-%d')
    
    for i, ticker in enumerate(tickers_br, 1):
        try:
            logger.info(f"\n[{i}/{len(tickers_br)}] Simulando {ticker}...")
            
            # Buscar preço atual real como base
            try:
                stock_api = create_market_data_api('yfinance')
                df_real = stock_api.fetch_spot_data([ticker], 
                                                    (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                                                    today)
                
                if not df_real.empty:
                    latest_real = df_real.iloc[-1]
                    base_price = float(latest_real['close'])
                else:
                    # Preço base simulado se não conseguir dados reais
                    base_price = 20.0 + (i * 2.0)
            except:
                base_price = 20.0 + (i * 2.0)
            
            # SIMULAR condições favoráveis para daytrade:
            # - Momentum positivo entre 0.5% e 3.0%
            # - Volume alto (ratio > 1.0)
            # - Preços intraday variando
            
            import random
            momentum_pct = random.uniform(0.005, 0.030)  # 0.5% a 3.0% de alta
            volume_ratio = random.uniform(1.2, 2.5)  # Volume 1.2x a 2.5x do normal
            
            # Calcular preços simulados
            open_price = base_price * (1 - momentum_pct * 0.3)  # Abriu um pouco abaixo
            current_price = open_price * (1 + momentum_pct)  # Subiu durante o dia
            high_price = current_price * 1.01  # Máxima um pouco acima
            low_price = open_price * 0.995  # Mínima um pouco abaixo
            
            # Volume simulado
            adv = 10000000  # ADV simulado
            volume_today = int(adv * volume_ratio)
            
            spot_data = {
                'open': round(open_price, 2),
                'close': round(current_price, 2),
                'last': round(current_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'volume': volume_today,
                'adv': adv,
                'intraday_return': momentum_pct,
                'volume_ratio': volume_ratio
            }
            
            market_data['spot'][ticker] = spot_data
            
            logger.info(f"  [SIMULADO] Open: R$ {open_price:.2f} | Close: R$ {current_price:.2f}")
            logger.info(f"             Momentum: {momentum_pct*100:.2f}% | Volume: {volume_today:,} | Ratio: {volume_ratio:.2f}x")
            
            # Salvar dados simulados no banco (como se fossem dados reais)
            orders_repo.save_market_data_capture(
                ticker=ticker,
                data_type='spot',
                spot_data=spot_data,
                raw_data={'simulated': True, 'base_price': base_price}
            )
            
            # Criar opções simuladas COM DELTAS ADEQUADOS para passar nos filtros
            logger.info(f"  Criando opcoes simuladas...")
            options_list = []
            expiry_date = pd.to_datetime(datetime.now() + timedelta(days=5))
            
            # Criar 3 opções com deltas diferentes (todas dentro da faixa 0.20-0.60)
            deltas_target = [0.50, 0.40, 0.30]
            
            for target_delta in deltas_target:
                    # Calcular strike baseado no delta
                    if target_delta >= 0.50:
                        strike = current_price * (1.0 - (target_delta - 0.50) * 0.02)
                    else:
                        strike = current_price * (1.0 + (0.50 - target_delta) * 0.03)
                    
                    strike = round(strike, 2)
                    
                    # Preço teórico da opção (ajustado para gerar quantidades menores)
                    time_to_expiry = 5 / 365.0
                    iv = 0.30
                    intrinsic = max(0, current_price - strike)
                    time_value = strike * 0.015 * (time_to_expiry * 365 / 30)  # Reduzido para gerar prêmios menores
                    premium = intrinsic + time_value
                    premium = max(0.10, premium)  # Mínimo de R$ 0.10 para evitar quantidades muito altas
                    
                    delta = target_delta
                    
                    # Spread pequeno (aceitável)
                    bid = premium * 0.98
                    ask = premium * 1.02
                    mid = premium
                    spread_pct = (ask - bid) / mid if mid > 0 else 0.01
                    
                    # Garantir que passa nos filtros
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
                            'volume': 500,  # Volume suficiente
                            'open_interest': 1000,
                            'implied_volatility': iv,
                            'delta': delta,
                            'gamma': 0.02,
                            'vega': 0.15
                        }
                        options_list.append(option_data)
                        logger.info(f"    Opcao: Strike R$ {strike:.2f}, Delta {delta:.2f}, Spread {spread_pct*100:.2f}%")
            
            if options_list:
                market_data['options'][ticker] = options_list
                logger.info(f"  {len(options_list)} opcoes criadas")
                
                # Salvar opções simuladas no banco
                orders_repo.save_market_data_capture(
                    ticker=ticker,
                    data_type='options',
                    spot_data=spot_data,
                    options_data=options_list,
                    raw_data={'simulated': True, 'options_count': len(options_list)}
                )
            else:
                logger.warning(f"  Nenhuma opcao criada")
                
        except Exception as e:
            logger.error(f"  Erro ao simular {ticker}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            continue
    
    logger.info(f"\n[DADOS SIMULADOS] Tickers com spot: {len(market_data['spot'])}")
    logger.info(f"[DADOS SIMULADOS] Tickers com opcoes: {len(market_data.get('options', {}))}")
    
    return market_data['spot'], market_data.get('options', {})

def executar_simulacao_completa():
    """Executa simulação completa: gera dados e deixa os agentes processarem."""
    logger.info("\n" + "=" * 70)
    logger.info("SIMULACAO COMPLETA DE MERCADO")
    logger.info("=" * 70)
    logger.info("Este script simula dados de mercado.")
    logger.info("Os AGENTES processarao esses dados normalmente.")
    logger.info("=" * 70)
    
    # Carregar configuração
    config_path = Path('config.json')
    if not config_path.exists():
        logger.error("Arquivo config.json nao encontrado!")
        return False
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Tickers brasileiros
    tickers_br = [
        'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA',
        'WEGE3.SA', 'MGLU3.SA', 'SUZB3.SA', 'RENT3.SA', 'ELET3.SA',
        'BBAS3.SA', 'SANB11.SA', 'B3SA3.SA', 'RADL3.SA', 'HAPV3.SA'
    ]
    
    # Inicializar repositório
    logger.info("\nInicializando OrdersRepository...")
    orders_repo = OrdersRepository()
    logger.info("OK")
    
    # 1. GERAR DADOS DE MERCADO SIMULADOS
    logger.info("\n" + "=" * 70)
    logger.info("ETAPA 1: GERANDO DADOS DE MERCADO SIMULADOS")
    logger.info("=" * 70)
    
    spot_data, options_data = criar_dados_mercado_simulados(tickers_br, orders_repo)
    
    if not spot_data:
        logger.error("Nenhum dado gerado. Abortando.")
        return False
    
    # 2. PREPARAR MARKET_DATA PARA OS AGENTES
    logger.info("\n" + "=" * 70)
    logger.info("ETAPA 2: PREPARANDO MARKET_DATA PARA OS AGENTES")
    logger.info("=" * 70)
    
    market_data = {
        'spot': spot_data,
        'options': options_data
    }
    
    logger.info(f"Dados preparados:")
    logger.info(f"  - Spot: {len(spot_data)} tickers")
    logger.info(f"  - Opcoes: {len(options_data)} tickers")
    
    # 3. USAR MONITORING SERVICE PARA PROCESSAR (como se fosse mercado real)
    logger.info("\n" + "=" * 70)
    logger.info("ETAPA 3: PROCESSANDO COM MONITORING SERVICE")
    logger.info("=" * 70)
    logger.info("Os agentes processarao os dados simulados normalmente...")
    
    try:
        try:
            from src.monitoring_service import MonitoringService
        except ImportError:
            from monitoring_service import MonitoringService
        
        # Inicializar MonitoringService (ele cria seus próprios componentes internamente)
        monitoring = MonitoringService(config)
        
        # Executar scan de mercado passando market_data diretamente
        # O MonitoringService normalmente busca dados, mas podemos passar dados simulados
        timestamp = pd.to_datetime(datetime.now())
        
        # Usar o método interno do MonitoringService para processar market_data
        # Como scan_market() busca dados internamente, vamos usar o trader_agent diretamente
        # mas através do MonitoringService para manter o fluxo correto
        
        # Processar market_data através do TraderAgent do MonitoringService
        proposals = monitoring.trader_agent.generate_proposals(timestamp, market_data)
        
        logger.info(f"\n[RESULTADO DO PROCESSAMENTO]")
        logger.info(f"  - Propostas geradas: {len(proposals)}")
        
        if proposals:
            logger.info(f"\n  Propostas:")
            for prop in proposals[:5]:
                logger.info(f"    - {prop.strategy}: {prop.symbol} ({prop.side} {prop.quantity} @ R$ {prop.price:.2f})")
            
            # Processar propostas através do RiskAgent
            try:
                from src.agents import RiskAgent, PortfolioManager
            except ImportError:
                from agents import RiskAgent, PortfolioManager
            
            # Criar PortfolioManager necessário para RiskAgent (vazio para não ter delta agregado)
            portfolio_manager = PortfolioManager(config.get('nav', 1000000))
            # Limpar posições para garantir que não há delta agregado pré-existente
            portfolio_manager.positions = {}
            risk_agent = RiskAgent(portfolio_manager, config, monitoring.logger, orders_repo=monitoring.orders_repo)
            
            approved_count = 0
            for proposal in proposals:
                try:
                    # RiskAgent.evaluate_proposal espera (proposal, market_data), não nav
                    evaluation_result = risk_agent.evaluate_proposal(proposal, market_data)
                    decision, modified_proposal, reason = evaluation_result
                    if decision == 'APPROVE':
                        approved_count += 1
                        # Usar proposta modificada se houver
                        proposal_to_execute = modified_proposal if modified_proposal else proposal
                        logger.info(f"    [APPROVE] {proposal.symbol}: APROVADA")
                        
                        # Enviar notificação Telegram no formato melhorado
                        try:
                            # Preparar dados da proposta para Telegram (formato melhorado)
                            proposal_data = {
                                'proposal_id': proposal.proposal_id,
                                'symbol': proposal.symbol,
                                'side': proposal.side,
                                'quantity': proposal.quantity,
                                'price': proposal.price,
                                'metadata': proposal.metadata if proposal.metadata else {}
                            }
                            
                            # Enviar via Telegram com botões de aprovação
                            telegram_channel = None
                            for channel_name, channel in monitoring.notifier.channels:
                                if channel_name == 'telegram' and hasattr(channel, 'send_proposal_with_approval'):
                                    telegram_channel = channel
                                    break
                            
                            if telegram_channel:
                                result = telegram_channel.send_proposal_with_approval(proposal_data)
                                if result:
                                    logger.info(f"      [NOTIFY] Notificacao Telegram enviada (formato melhorado)")
                                else:
                                    logger.warning(f"      [NOTIFY] Falha ao enviar notificacao Telegram")
                            else:
                                logger.warning(f"      [NOTIFY] Canal Telegram nao encontrado ou nao configurado")
                        except Exception as notify_err:
                            logger.error(f"      [ERROR] Erro ao enviar notificacao: {notify_err}")
                            import traceback
                            logger.error(traceback.format_exc())
                        
                        # Executar proposta aprovada
                        try:
                            try:
                                from src.execution import ExecutionSimulator
                            except ImportError:
                                from execution import ExecutionSimulator
                            execution_simulator = ExecutionSimulator(config, monitoring.logger, orders_repo=monitoring.orders_repo)
                            
                            underlying = proposal.metadata.get('underlying', '') if proposal.metadata else ''
                            market_price = market_data['spot'].get(underlying, {}).get('last', proposal.price) if underlying else proposal.price
                            
                            order_dict = {
                                'proposal_id': proposal.proposal_id,
                                'symbol': proposal.symbol,
                                'side': proposal_to_execute.side,
                                'quantity': proposal_to_execute.quantity,
                                'price': proposal_to_execute.price,
                                'order_type': 'MARKET',  # MARKET para garantir execução na simulação
                                'strategy': proposal.strategy
                            }
                            
                            execution_result = execution_simulator.execute_order(order_dict, market_price)
                            
                            logger.info(f"      [EXEC] Resultado: {execution_result}")
                            
                            # ExecutionSimulator retorna dict com fill_id se executado, None se não
                            if execution_result and (execution_result.get('fill_id') or execution_result.get('order_id')):
                                logger.info(f"      [EXEC] Executada: {execution_result.get('quantity', 0)} @ R$ {execution_result.get('price', 0):.2f}")
                                
                                # Criar posição
                                delta_val = proposal.metadata.get('delta', 0) * execution_result.get('quantity', proposal.quantity) * 100 if proposal.metadata else 0
                                gamma_val = proposal.metadata.get('gamma', 0) * execution_result.get('quantity', proposal.quantity) * 100 if proposal.metadata else 0
                                vega_val = proposal.metadata.get('vega', 0) * execution_result.get('quantity', proposal.quantity) * 100 if proposal.metadata else 0
                                
                                monitoring.orders_repo.save_open_position(
                                    symbol=proposal.symbol,
                                    side=proposal.side,
                                    quantity=execution_result.get('quantity', proposal.quantity),
                                    avg_price=execution_result.get('price', proposal.price),
                                    current_price=market_price,
                                    delta=delta_val,
                                    gamma=gamma_val,
                                    vega=vega_val
                                )
                                logger.info(f"      [POS] Posicao criada no banco")
                                
                                # Calcular snapshot de performance
                                open_positions = monitoring.orders_repo.get_open_positions()
                                total_unrealized_pnl = open_positions['unrealized_pnl'].sum() if not open_positions.empty and 'unrealized_pnl' in open_positions.columns else 0
                                
                                # Salvar snapshot de performance (método espera um dict)
                                snapshot_data = {
                                    'timestamp': timestamp.isoformat(),
                                    'nav': config.get('nav', 1000000),
                                    'total_pnl': total_unrealized_pnl,
                                    'daily_pnl': total_unrealized_pnl,
                                    'total_trades': approved_count,
                                    'winning_trades': approved_count if total_unrealized_pnl > 0 else 0,
                                    'losing_trades': 0,
                                    'open_positions': len(open_positions) if not open_positions.empty else 0,
                                    'total_delta': float(open_positions['delta'].sum()) if not open_positions.empty and 'delta' in open_positions.columns else 0.0,
                                    'total_gamma': float(open_positions['gamma'].sum()) if not open_positions.empty and 'gamma' in open_positions.columns else 0.0,
                                    'total_vega': float(open_positions['vega'].sum()) if not open_positions.empty and 'vega' in open_positions.columns else 0.0,
                                    'portfolio_value': config.get('nav', 1000000) + total_unrealized_pnl,
                                    'cash': config.get('nav', 1000000) - (total_unrealized_pnl if total_unrealized_pnl < 0 else 0),
                                    'details': {}
                                }
                                monitoring.orders_repo.save_performance_snapshot(snapshot_data)
                                logger.info(f"      [SNAP] Snapshot de performance salvo")
                        except Exception as exec_err:
                            logger.warning(f"      Erro ao executar: {exec_err}")
                            import traceback
                            logger.error(traceback.format_exc())
                    elif decision == 'MODIFY':
                        approved_count += 1  # Contar modificadas como aprovadas também
                        proposal_to_execute = modified_proposal if modified_proposal else proposal
                        logger.info(f"    [MODIFY] {proposal.symbol}: MODIFICADA - {reason}")
                        # Processar proposta modificada também
                        try:
                            from execution import ExecutionSimulator
                            execution_simulator = ExecutionSimulator(config, monitoring.logger, orders_repo=monitoring.orders_repo)
                            
                            underlying = proposal.metadata.get('underlying', '') if proposal.metadata else ''
                            market_price = market_data['spot'].get(underlying, {}).get('last', proposal.price) if underlying else proposal.price
                            
                            order_dict = {
                                'proposal_id': proposal.proposal_id,
                                'symbol': proposal.symbol,
                                'side': proposal_to_execute.side,
                                'quantity': proposal_to_execute.quantity,
                                'price': proposal_to_execute.price,
                                'order_type': 'MARKET',  # Mudar para MARKET para garantir execução
                                'strategy': proposal.strategy
                            }
                            
                            execution_result = execution_simulator.execute_order(order_dict, market_price)
                            
                            logger.info(f"      [EXEC] Resultado: {execution_result}")
                            
                            if execution_result and (execution_result.get('fill_id') or execution_result.get('order_id')):
                                logger.info(f"      [EXEC] Executada: {execution_result.get('quantity', 0)} @ R$ {execution_result.get('price', 0):.2f}")
                                
                                delta_val = proposal.metadata.get('delta', 0) * execution_result.get('quantity', proposal.quantity) * 100 if proposal.metadata else 0
                                gamma_val = proposal.metadata.get('gamma', 0) * execution_result.get('quantity', proposal.quantity) * 100 if proposal.metadata else 0
                                vega_val = proposal.metadata.get('vega', 0) * execution_result.get('quantity', proposal.quantity) * 100 if proposal.metadata else 0
                                
                                monitoring.orders_repo.save_open_position(
                                    symbol=proposal.symbol,
                                    side=proposal.side,
                                    quantity=execution_result.get('quantity', proposal.quantity),
                                    avg_price=execution_result.get('price', proposal.price),
                                    current_price=market_price,
                                    delta=delta_val,
                                    gamma=gamma_val,
                                    vega=vega_val
                                )
                        except Exception as exec_err:
                            logger.warning(f"      Erro ao executar modificada: {exec_err}")
                    else:
                        logger.info(f"    [REJECT] {proposal.symbol}: REJEITADA - {reason}")
                except Exception as eval_err:
                    logger.warning(f"    Erro ao avaliar {proposal.symbol}: {eval_err}")
            
            logger.info(f"\n  Propostas aprovadas: {approved_count}/{len(proposals)}")
        else:
            logger.warning("  Nenhuma proposta gerada")
        
        result = {
            'opportunities': 0,
            'proposals': len(proposals)
        }
        
        logger.info(f"\n[RESULTADO DO SCAN]")
        logger.info(f"  - Oportunidades encontradas: {result.get('opportunities', 0)}")
        logger.info(f"  - Propostas geradas: {result.get('proposals', 0)}")
        
        if result.get('proposals', 0) > 0:
            logger.info(f"\n  Propostas:")
            for prop in result.get('proposals_list', [])[:5]:
                logger.info(f"    - {prop.get('strategy', 'N/A')}: {prop.get('symbol', 'N/A')}")
        
        logger.info("\n[OK] Processamento concluido pelos agentes!")
        
    except Exception as e:
        logger.error(f"Erro ao processar com MonitoringService: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    # 4. VERIFICAR RESULTADOS
    logger.info("\n" + "=" * 70)
    logger.info("ETAPA 4: VERIFICANDO RESULTADOS")
    logger.info("=" * 70)
    
    try:
        proposals_db = orders_repo.get_proposals(strategy='daytrade_options')
        evaluations_db = orders_repo.get_risk_evaluations()
        executions_db = orders_repo.get_executions()
        positions_db = orders_repo.get_open_positions()
        captures_db = orders_repo.get_market_data_captures()
        
        logger.info(f"Resultados no banco:")
        logger.info(f"  - Propostas de daytrade: {len(proposals_db)}")
        logger.info(f"  - Avaliacoes de risco: {len(evaluations_db)}")
        logger.info(f"  - Execucoes: {len(executions_db)}")
        logger.info(f"  - Posicoes abertas: {len(positions_db)}")
        logger.info(f"  - Capturas de dados: {len(captures_db)}")
        
        if len(proposals_db) > 0:
            logger.info(f"\n  Ultimas propostas:")
            for _, prop in proposals_db.tail(3).iterrows():
                logger.info(f"    - {prop.get('symbol', 'N/A')}: {prop.get('strategy', 'N/A')}")
        
    except Exception as e:
        logger.error(f"Erro ao verificar resultados: {e}")
    
    logger.info("\n" + "=" * 70)
    logger.info("SIMULACAO CONCLUIDA")
    logger.info("=" * 70)
    logger.info("Os agentes processaram os dados simulados normalmente.")
    logger.info("Verifique o dashboard e o banco de dados para ver os resultados.")
    
    return True

if __name__ == '__main__':
    try:
        logger.info("Iniciando simulador de market data...")
        sucesso = executar_simulacao_completa()
        sys.exit(0 if sucesso else 1)
    except KeyboardInterrupt:
        logger.warning("\nSimulacao interrompida pelo usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nErro fatal: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

