#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simula um dia de mercado real usando dados históricos de um dia específico.
Captura dados conforme o cronograma normal (a cada 5 minutos durante o pregão),
mas usando dados históricos de um dia anterior.

Uso:
    python simular_dia_mercado_real.py --data 2025-11-28
    python simular_dia_mercado_real.py --data ontem
    python simular_dia_mercado_real.py  # Usa ontem por padrão
"""

import json
import sys
import time
import argparse
import logging
from datetime import datetime, timedelta, time as dt_time
from pathlib import Path
import pandas as pd
import pytz

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('simulacao_mercado_real.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from monitoring_service import MonitoringService
    from trading_schedule import TradingSchedule
    from market_data_api import create_market_data_api
except ImportError:
    from src.monitoring_service import MonitoringService
    from src.trading_schedule import TradingSchedule
    from src.market_data_api import create_market_data_api

# Timezone B3
B3_TIMEZONE = pytz.timezone('America/Sao_Paulo')

# Horários B3
B3_PRE_OPEN = dt_time(9, 45)
B3_OPEN = dt_time(10, 0)
B3_CLOSE = dt_time(17, 0)
B3_POST_CLOSE = dt_time(17, 30)


class SimuladorMercadoReal:
    """Simula um dia de mercado real usando dados históricos."""
    
    def __init__(self, config: dict, data_referencia: datetime):
        """
        Inicializa simulador.
        
        Args:
            config: Configuração do sistema
            data_referencia: Data de referência para buscar dados históricos
        """
        self.config = config
        self.data_referencia = data_referencia.date()  # Data histórica (ex: ontem)
        self.trading_schedule = TradingSchedule()
        self.market_api = create_market_data_api('yfinance')
        
        # Criar MonitoringService (mas vamos sobrescrever o scan_market)
        self.monitoring = MonitoringService(config)
        
        # Horários de captura durante o pregão (a cada 5 minutos)
        self.horarios_captura = self._gerar_horarios_captura()
        
        logger.info(f"Simulador inicializado para data: {self.data_referencia}")
        logger.info(f"Horários de captura: {len(self.horarios_captura)} períodos")
    
    def _gerar_horarios_captura(self):
        """Gera lista de horários de captura durante o pregão (a cada 5 minutos)."""
        horarios = []
        
        # Pré-mercado: 09:45 - 10:00 (a cada 5 minutos)
        for hora in range(9, 10):
            for minuto in [45, 50, 55]:
                horarios.append(dt_time(hora, minuto))
        
        # Pregão: 10:00 - 17:00 (a cada 5 minutos)
        for hora in range(10, 17):
            for minuto in range(0, 60, 5):
                horarios.append(dt_time(hora, minuto))
        
        # Pós-mercado: 17:00 - 17:30 (a cada 5 minutos)
        for minuto in [0, 5, 10, 15, 20, 25, 30]:
            horarios.append(dt_time(17, minuto))
        
        return horarios
    
    def _buscar_dados_historicos(self, horario: dt_time):
        """
        Busca dados históricos REAIS de mercado para o horário especificado.
        Usa apenas dados reais do yfinance, sem criar ou simular preços.
        
        Args:
            horario: Horário do dia (ex: 10:30)
        
        Returns:
            Dict com dados de mercado reais no formato esperado
        """
        tickers = self.config.get('monitored_tickers', [])
        market_data = {'spot': {}, 'options': {}}
        
        logger.info(f"Buscando dados REAIS de mercado para {self.data_referencia} às {horario.strftime('%H:%M')}...")
        
        # Criar datetime de referência para o horário específico
        ref_datetime = B3_TIMEZONE.localize(
            datetime.combine(self.data_referencia, horario)
        )
        
        try:
            import yfinance as yf
            
            for ticker in tickers[:30]:  # Limitar a 30 para não demorar muito
                try:
                    stock = yf.Ticker(ticker)
                    
                    # Buscar dados intraday REAIS do dia de referência
                    # Tentar diferentes intervalos para encontrar dados mais próximos
                    hist_data = None
                    intervalo_usado = None
                    
                    # Tentar 5 minutos primeiro (mais preciso)
                    try:
                        hist = stock.history(
                            start=self.data_referencia.strftime('%Y-%m-%d'),
                            end=(self.data_referencia + timedelta(days=1)).strftime('%Y-%m-%d'),
                            interval='5m',
                            timeout=10
                        )
                        if hist is not None and not hist.empty:
                            hist_data = hist
                            intervalo_usado = '5m'
                    except Exception as e:
                        logger.debug(f"Erro ao buscar dados 5m para {ticker}: {e}")
                    
                    # Fallback: tentar 15 minutos
                    if hist_data is None or hist_data.empty:
                        try:
                            hist = stock.history(
                                start=self.data_referencia.strftime('%Y-%m-%d'),
                                end=(self.data_referencia + timedelta(days=1)).strftime('%Y-%m-%d'),
                                interval='15m',
                                timeout=10
                            )
                            if hist is not None and not hist.empty:
                                hist_data = hist
                                intervalo_usado = '15m'
                        except Exception as e:
                            logger.debug(f"Erro ao buscar dados 15m para {ticker}: {e}")
                    
                    # Fallback: tentar 1 hora
                    if hist_data is None or hist_data.empty:
                        try:
                            hist = stock.history(
                                start=self.data_referencia.strftime('%Y-%m-%d'),
                                end=(self.data_referencia + timedelta(days=1)).strftime('%Y-%m-%d'),
                                interval='1h',
                                timeout=10
                            )
                            if hist is not None and not hist.empty:
                                hist_data = hist
                                intervalo_usado = '1h'
                        except Exception as e:
                            logger.debug(f"Erro ao buscar dados 1h para {ticker}: {e}")
                    
                    # Fallback: dados diários (último recurso)
                    if hist_data is None or hist_data.empty:
                        try:
                            hist = stock.history(
                                start=self.data_referencia.strftime('%Y-%m-%d'),
                                end=(self.data_referencia + timedelta(days=1)).strftime('%Y-%m-%d'),
                                interval='1d',
                                timeout=10
                            )
                            if hist is not None and not hist.empty:
                                hist_data = hist
                                intervalo_usado = '1d'
                        except Exception as e:
                            logger.debug(f"Erro ao buscar dados diários para {ticker}: {e}")
                    
                    if hist_data is None or hist_data.empty:
                        logger.debug(f"Nenhum dado REAL encontrado para {ticker} em {self.data_referencia}")
                        continue
                    
                    # IMPORTANTE: Usar apenas dados REAIS, encontrar o mais próximo do horário
                    if isinstance(hist_data.index, pd.DatetimeIndex):
                        # Converter índices para timezone B3 se necessário
                        if hist_data.index.tz is None:
                            # Assumir que está em UTC e converter para B3
                            hist_data.index = hist_data.index.tz_localize('UTC').tz_convert(B3_TIMEZONE)
                        elif hist_data.index.tz != B3_TIMEZONE:
                            hist_data.index = hist_data.index.tz_convert(B3_TIMEZONE)
                        
                        # Filtrar dados até o horário especificado (dados REAIS até esse momento)
                        hist_filtered = hist_data[hist_data.index <= ref_datetime]
                        
                        if hist_filtered.empty:
                            # Se não tiver dados até esse horário, não usar dados desse ticker
                            logger.debug(f"Nenhum dado REAL disponível para {ticker} até {horario.strftime('%H:%M')}")
                            continue
                        
                        # Pegar o último dado REAL disponível até o horário
                        latest = hist_filtered.iloc[-1]
                        timestamp_real = hist_filtered.index[-1]
                        
                        # Calcular dados acumulados do dia até o horário (usando dados REAIS)
                        first_of_day = hist_filtered.iloc[0]
                        open_price = float(first_of_day['Open'])  # Preço de abertura REAL
                        volume_today = int(hist_filtered['Volume'].sum()) if 'Volume' in hist_filtered.columns else 0  # Volume REAL acumulado
                        
                        # Preço atual é o Close do último período REAL disponível
                        current_price = float(latest['Close'])
                        
                        # High e Low do período atual REAL
                        high_price = float(latest['High'])
                        low_price = float(latest['Low'])
                        
                        logger.debug(f"Dados REAIS para {ticker} às {horario.strftime('%H:%M')}: "
                                   f"Preço={current_price:.2f} (intervalo={intervalo_usado}, "
                                   f"timestamp_real={timestamp_real.strftime('%H:%M')})")
                    else:
                        # Se não tiver índice de datetime, usar dados diários
                        latest = hist_data.iloc[-1]
                        open_price = float(latest['Open'])
                        current_price = float(latest['Close'])
                        high_price = float(latest['High'])
                        low_price = float(latest['Low'])
                        volume_today = int(latest['Volume']) if not pd.isna(latest['Volume']) else 0
                        timestamp_real = None
                    
                    # Usar APENAS dados REAIS, sem criar ou simular
                    market_data['spot'][ticker] = {
                        'open': open_price,  # Preço de abertura REAL
                        'close': current_price,  # Preço de fechamento REAL do período
                        'last': current_price,  # Último preço REAL
                        'high': high_price,  # Máxima REAL do período
                        'low': low_price,  # Mínima REAL do período
                        'volume': volume_today,  # Volume REAL acumulado até o horário
                        'adv': 0,  # Será calculado depois se necessário
                        'timestamp_real': timestamp_real.isoformat() if timestamp_real else None,  # Timestamp REAL do dado
                        'intervalo_usado': intervalo_usado  # Intervalo usado para buscar dados
                    }
                    
                except Exception as e:
                    logger.warning(f"Erro ao buscar dados REAIS para {ticker}: {e}")
                    continue
            
            logger.info(f"Dados REAIS coletados: {len(market_data['spot'])} tickers")
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados históricos REAIS: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return market_data
    
    def executar_simulacao(self):
        """Executa simulação completa do dia de mercado."""
        self._stop_simulation = False  # Flag para permitir interrupção
        
        logger.info("=" * 70)
        logger.info("INICIANDO SIMULAÇÃO DE MERCADO REAL")
        logger.info("=" * 70)
        logger.info(f"Data de referência: {self.data_referencia}")
        logger.info(f"Total de horários: {len(self.horarios_captura)}")
        logger.info("")
        
        # Simular cada horário de captura
        for idx, horario in enumerate(self.horarios_captura, 1):
            logger.info(f"[{idx}/{len(self.horarios_captura)}] Processando horário: {horario.strftime('%H:%M')}")
            
            # Buscar dados históricos para este horário
            market_data = self._buscar_dados_historicos(horario)
            
            if not market_data.get('spot'):
                logger.warning(f"Nenhum dado encontrado para {horario.strftime('%H:%M')}")
                continue
            
            # Criar timestamp simulado (hoje, mas com horário histórico)
            timestamp_simulado = datetime.now(B3_TIMEZONE).replace(
                hour=horario.hour,
                minute=horario.minute,
                second=0,
                microsecond=0
            )
            
            # Salvar dados REAIS capturados no banco (marcar como simulação, mas dados são reais)
            if self.monitoring.orders_repo:
                for ticker, spot_info in market_data['spot'].items():
                    try:
                        options_list = market_data.get('options', {}).get(ticker, [])
                        
                        # Preservar informações sobre dados reais
                        raw_data = {
                            'timestamp': timestamp_simulado.isoformat(),
                            'data_referencia': self.data_referencia.isoformat(),
                            'horario_simulado': horario.strftime('%H:%M'),
                            'tipo': 'simulacao_mercado_real',
                            'dados_reais': True,  # Indicar que são dados reais
                            'timestamp_real': spot_info.get('timestamp_real'),
                            'intervalo_usado': spot_info.get('intervalo_usado')
                        }
                        
                        # Remover campos auxiliares antes de salvar
                        spot_info_clean = {k: v for k, v in spot_info.items() 
                                         if k not in ['timestamp_real', 'intervalo_usado']}
                        
                        self.monitoring.orders_repo.save_market_data_capture(
                            ticker=ticker,
                            data_type='spot',
                            spot_data=spot_info_clean,
                            options_data=options_list if options_list else None,
                            raw_data=raw_data,
                            source='simulation'  # Marcado como simulação, mas dados são reais
                        )
                    except Exception as e:
                        logger.error(f"Erro ao salvar dados REAIS para {ticker}: {e}")
            
            # Gerar propostas usando os dados históricos
            # Mas com timestamp simulado de hoje
            if self.monitoring.trading_schedule.is_trading_hours(timestamp_simulado):
                try:
                    # Usar o método scan_market do MonitoringService, mas com dados históricos
                    # Para isso, vamos temporariamente substituir o método de busca de dados
                    proposals = self.monitoring.trader_agent.generate_proposals(
                        pd.to_datetime(timestamp_simulado),
                        market_data
                    )
                    
                    logger.info(f"Propostas geradas: {len(proposals)}")
                    
                    # Avaliar propostas usando o RiskAgent do MonitoringService
                    # Criar RiskAgent se necessário
                    if not hasattr(self.monitoring, 'risk_agent'):
                        from src.agents import RiskAgent, PortfolioManager
                        portfolio = PortfolioManager(initial_nav=self.config.get('initial_nav', 1000000.0))
                        self.monitoring.risk_agent = RiskAgent(
                            portfolio,
                            self.config,
                            self.monitoring.logger,
                            orders_repo=self.monitoring.orders_repo
                        )
                    
                    # Avaliar cada proposta
                    for proposal in proposals:
                        try:
                            decision = self.monitoring.risk_agent.evaluate_proposal(
                                proposal,
                                market_data
                            )
                            logger.info(f"  Proposta {proposal.proposal_id[:20]}...: {decision.decision}")
                        except Exception as e:
                            logger.warning(f"  Erro ao avaliar proposta {proposal.proposal_id}: {e}")
                    
                    logger.info(f"Propostas processadas: {len(proposals)}")
                
                except Exception as e:
                    logger.error(f"Erro ao processar propostas: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            # Aguardar intervalo (simular tempo real, mas acelerado)
            # Em vez de esperar 5 minutos, esperar apenas alguns segundos para acelerar
            if idx < len(self.horarios_captura):
                # Verificar se ainda está rodando (para permitir interrupção)
                if hasattr(self, '_stop_simulation') and self._stop_simulation:
                    logger.info("Simulação interrompida")
                    break
                logger.info(f"Aguardando próximo horário...")
                time.sleep(2)  # 2 segundos entre capturas (acelerado)
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("SIMULAÇÃO CONCLUÍDA")
        logger.info("=" * 70)


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description='Simula dia de mercado real usando dados históricos')
    parser.add_argument(
        '--data',
        type=str,
        default='ontem',
        help='Data de referência (formato: YYYY-MM-DD ou "ontem")'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.json',
        help='Caminho do arquivo de configuração'
    )
    
    args = parser.parse_args()
    
    # Parsear data
    if args.data.lower() == 'ontem':
        data_referencia = datetime.now(B3_TIMEZONE) - timedelta(days=1)
    else:
        try:
            data_referencia = datetime.strptime(args.data, '%Y-%m-%d')
            data_referencia = B3_TIMEZONE.localize(data_referencia)
        except ValueError:
            logger.error(f"Formato de data inválido: {args.data}. Use YYYY-MM-DD")
            sys.exit(1)
    
    # Verificar se é dia útil
    schedule = TradingSchedule()
    if not schedule.is_trading_day(data_referencia):
        logger.warning(f"Data {data_referencia.date()} não é dia útil!")
        resposta = input("Deseja continuar mesmo assim? (s/n): ")
        if resposta.lower() != 's':
            sys.exit(0)
    
    # Carregar configuração
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Arquivo de configuração não encontrado: {config_path}")
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar configuração: {e}")
        sys.exit(1)
    
    # Criar e executar simulador
    simulador = SimuladorMercadoReal(config, data_referencia)
    
    try:
        simulador.executar_simulacao()
    except KeyboardInterrupt:
        logger.info("\n\nSimulação interrompida pelo usuário")
    except Exception as e:
        logger.error(f"\n\nErro durante simulação: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()

