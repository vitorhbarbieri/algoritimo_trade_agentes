"""
Análise Automática Pós-EOD
Executa backtest, análises de rentabilidade, parâmetros e melhorias após fechamento do mercado.
"""
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import yfinance as yf
from .orders_repository import OrdersRepository
from .trading_schedule import TradingSchedule
from .b3_costs import B3CostCalculator

logger = logging.getLogger(__name__)


class EODAnalyzer:
    """Analisador pós-EOD que executa backtest e análises completas."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.orders_repo = OrdersRepository()
        self.schedule = TradingSchedule()
        self.cost_calculator = B3CostCalculator()
    
    def analyze_daily_proposals(self, date: Optional[str] = None) -> Dict:
        """
        Analisa todas as propostas do dia.
        
        Args:
            date: Data no formato YYYY-MM-DD. Se None, usa hoje.
        
        Returns:
            Dicionário com resultados completos da análise
        """
        if not date:
            date = self.schedule.get_current_b3_time().date().strftime('%Y-%m-%d')
        
        logger.info(f"🔍 Iniciando análise EOD para {date}")
        
        # 1. Buscar propostas do dia
        proposals = self._get_daily_proposals(date)
        if proposals.empty:
            logger.warning(f"Nenhuma proposta encontrada para {date}")
            return self._empty_analysis(date)
        
        logger.info(f"📊 {len(proposals)} propostas encontradas")
        
        # 2. Executar backtest
        backtest_results = self._backtest_proposals(proposals, date)
        
        # 3. Análise de rentabilidade por ação
        profitability_analysis = self._analyze_profitability_by_asset(proposals, backtest_results)
        
        # 4. Análise de parâmetros dos agentes
        agent_params_analysis = self._analyze_agent_parameters(proposals, backtest_results)
        
        # 5. Análise de melhorias operacionais
        operational_improvements = self._analyze_operational_improvements(proposals, backtest_results)
        
        return {
            'date': date,
            'total_proposals': len(proposals),
            'backtest_results': backtest_results,
            'profitability_by_asset': profitability_analysis,
            'agent_parameters': agent_params_analysis,
            'operational_improvements': operational_improvements,
            'summary': self._generate_summary(backtest_results, profitability_analysis)
        }
    
    def _get_daily_proposals(self, date: str) -> pd.DataFrame:
        """Busca propostas do dia."""
        start_time = f"{date} 00:00:00"
        end_time = f"{date} 23:59:59"
        
        proposals = self.orders_repo.get_proposals(start_date=start_time, end_date=end_time)
        
        # Filtrar apenas daytrade
        if not proposals.empty and 'strategy' in proposals.columns:
            proposals = proposals[proposals['strategy'] == 'daytrade_options']
        
        return proposals
    
    def _backtest_proposals(self, proposals: pd.DataFrame, date: str) -> List[Dict]:
        """Executa backtest de todas as propostas."""
        results = []
        
        for idx, row in proposals.iterrows():
            try:
                proposal_id = row['proposal_id']
                symbol = row['symbol']
                side = row['side']
                quantity = row['quantity']
                entry_price = row['price']
                metadata_str = row.get('metadata', '{}')
                
                # Parse metadata
                if isinstance(metadata_str, str):
                    try:
                        metadata = json.loads(metadata_str.replace("'", '"'))
                    except:
                        metadata = {}
                else:
                    metadata = metadata_str if isinstance(metadata_str, dict) else {}
                
                # Buscar preço de fechamento do dia
                close_price = self._get_close_price(symbol, date)
                if close_price is None:
                    continue
                
                # Calcular resultado teórico
                if side == 'BUY':
                    price_change = close_price - entry_price
                    pct_change = (close_price / entry_price) - 1
                else:
                    price_change = entry_price - close_price
                    pct_change = (entry_price / close_price) - 1
                
                # Calcular valores
                entry_value = entry_price * quantity * (100 if metadata.get('comparison_type') == 'options' else 1)
                exit_value = close_price * quantity * (100 if metadata.get('comparison_type') == 'options' else 1)
                
                # Calcular custos B3
                costs = self.cost_calculator.calculate_total_costs(
                    entry_value, exit_value,
                    instrument_type=metadata.get('comparison_type', 'spot'),
                    is_daytrade=True
                )
                
                # Resultado líquido
                net_result = costs['profit_liquido']
                
                # Verificar se atingiu TP ou SL
                take_profit_pct = metadata.get('take_profit_pct', 0.012)
                stop_loss_pct = metadata.get('stop_loss_pct', 0.15)
                exit_price_tp = metadata.get('exit_price_tp', entry_price * (1 + take_profit_pct))
                exit_price_sl = metadata.get('exit_price_sl', entry_price * (1 - stop_loss_pct))
                
                hit_tp = False
                hit_sl = False
                if side == 'BUY':
                    hit_tp = close_price >= exit_price_tp
                    hit_sl = close_price <= exit_price_sl
                else:
                    hit_tp = close_price <= exit_price_tp
                    hit_sl = close_price >= exit_price_sl
                
                results.append({
                    'proposal_id': proposal_id,
                    'symbol': symbol,
                    'underlying': metadata.get('underlying', symbol),
                    'side': side,
                    'entry_price': entry_price,
                    'close_price': close_price,
                    'quantity': quantity,
                    'price_change': price_change,
                    'pct_change': pct_change,
                    'entry_value': entry_value,
                    'exit_value': exit_value,
                    'gross_profit': costs['profit_bruto'],
                    'operational_costs': costs['operational_costs'],
                    'ir_amount': costs['ir_amount'],
                    'net_profit': net_result,
                    'hit_tp': hit_tp,
                    'hit_sl': hit_sl,
                    'take_profit_pct': take_profit_pct,
                    'stop_loss_pct': stop_loss_pct,
                    'comparison_score': metadata.get('comparison_score', 0),
                    'intraday_return': metadata.get('intraday_return', 0),
                    'volume_ratio': metadata.get('volume_ratio', 0),
                    'instrument_type': metadata.get('comparison_type', 'spot'),
                    'delta': metadata.get('delta', 0),
                    'status': row.get('status', 'gerada')
                })
            except Exception as e:
                logger.error(f"Erro ao fazer backtest da proposta {row.get('proposal_id', 'N/A')}: {e}")
                continue
        
        return results
    
    def _get_close_price(self, symbol: str, date: str) -> Optional[float]:
        """Busca preço de fechamento do dia."""
        try:
            # Limpar símbolo para yfinance
            ticker_yf = symbol.split('_')[0] if '_' in symbol else symbol
            
            ticker = yf.Ticker(ticker_yf)
            hist = ticker.history(start=date, end=(datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d'))
            
            if hist.empty:
                return None
            
            return float(hist.iloc[-1]['Close'])
        except Exception as e:
            logger.debug(f"Erro ao buscar preço de fechamento para {symbol}: {e}")
            return None
    
    def _analyze_profitability_by_asset(self, proposals: pd.DataFrame, backtest_results: List[Dict]) -> Dict:
        """Analisa rentabilidade por ação."""
        if not backtest_results:
            return {}
        
        df_results = pd.DataFrame(backtest_results)
        
        # Agrupar por ativo subjacente
        analysis = {}
        
        for underlying in df_results['underlying'].unique():
            asset_results = df_results[df_results['underlying'] == underlying]
            
            total_proposals = len(asset_results)
            profitable = len(asset_results[asset_results['net_profit'] > 0])
            loss_making = len(asset_results[asset_results['net_profit'] < 0])
            
            total_net_profit = asset_results['net_profit'].sum()
            avg_profit = asset_results['net_profit'].mean()
            total_gross_profit = asset_results['gross_profit'].sum()
            total_costs = asset_results['operational_costs'].sum() + asset_results['ir_amount'].sum()
            
            win_rate = (profitable / total_proposals * 100) if total_proposals > 0 else 0
            
            # Análise de TP/SL
            hit_tp_count = asset_results['hit_tp'].sum()
            hit_sl_count = asset_results['hit_sl'].sum()
            
            # Score médio
            avg_score = asset_results['comparison_score'].mean()
            
            analysis[underlying] = {
                'total_proposals': total_proposals,
                'profitable': profitable,
                'loss_making': loss_making,
                'win_rate': win_rate,
                'total_net_profit': total_net_profit,
                'avg_profit': avg_profit,
                'total_gross_profit': total_gross_profit,
                'total_costs': total_costs,
                'hit_tp': hit_tp_count,
                'hit_sl': hit_sl_count,
                'avg_score': avg_score,
                'avg_intraday_return': asset_results['intraday_return'].mean(),
                'avg_volume_ratio': asset_results['volume_ratio'].mean()
            }
        
        return analysis
    
    def _analyze_agent_parameters(self, proposals: pd.DataFrame, backtest_results: List[Dict]) -> Dict:
        """Analisa performance dos parâmetros dos agentes."""
        if not backtest_results:
            return {}
        
        df_results = pd.DataFrame(backtest_results)
        
        # Análise por score
        score_ranges = {
            'high': df_results[df_results['comparison_score'] >= 0.8],
            'medium': df_results[(df_results['comparison_score'] >= 0.6) & (df_results['comparison_score'] < 0.8)],
            'low': df_results[df_results['comparison_score'] < 0.6]
        }
        
        score_analysis = {}
        for range_name, range_df in score_ranges.items():
            if not range_df.empty:
                score_analysis[range_name] = {
                    'count': len(range_df),
                    'win_rate': (len(range_df[range_df['net_profit'] > 0]) / len(range_df) * 100),
                    'avg_profit': range_df['net_profit'].mean(),
                    'total_profit': range_df['net_profit'].sum()
                }
        
        # Análise por tipo de instrumento
        instrument_analysis = {}
        for inst_type in df_results['instrument_type'].unique():
            inst_df = df_results[df_results['instrument_type'] == inst_type]
            instrument_analysis[inst_type] = {
                'count': len(inst_df),
                'win_rate': (len(inst_df[inst_df['net_profit'] > 0]) / len(inst_df) * 100) if len(inst_df) > 0 else 0,
                'avg_profit': inst_df['net_profit'].mean(),
                'total_profit': inst_df['net_profit'].sum()
            }
        
        # Análise de TP/SL
        tp_sl_analysis = {
            'hit_tp_rate': (df_results['hit_tp'].sum() / len(df_results) * 100) if len(df_results) > 0 else 0,
            'hit_sl_rate': (df_results['hit_sl'].sum() / len(df_results) * 100) if len(df_results) > 0 else 0,
            'avg_tp_pct': df_results['take_profit_pct'].mean(),
            'avg_sl_pct': df_results['stop_loss_pct'].mean()
        }
        
        return {
            'score_analysis': score_analysis,
            'instrument_analysis': instrument_analysis,
            'tp_sl_analysis': tp_sl_analysis
        }
    
    def _analyze_operational_improvements(self, proposals: pd.DataFrame, backtest_results: List[Dict]) -> List[str]:
        """Identifica melhorias operacionais."""
        improvements = []
        
        if not backtest_results:
            return improvements
        
        df_results = pd.DataFrame(backtest_results)
        
        # Análise de win rate
        win_rate = (len(df_results[df_results['net_profit'] > 0]) / len(df_results) * 100) if len(df_results) > 0 else 0
        
        if win_rate < 50:
            improvements.append(f"⚠️ Win rate baixo ({win_rate:.1f}%) - Considerar aumentar score mínimo ou ajustar filtros")
        
        # Análise de custos
        total_costs = df_results['operational_costs'].sum() + df_results['ir_amount'].sum()
        total_gross = df_results['gross_profit'].sum()
        cost_ratio = (total_costs / abs(total_gross) * 100) if total_gross != 0 else 0
        
        if cost_ratio > 30:
            improvements.append(f"⚠️ Custos elevados ({cost_ratio:.1f}% do lucro bruto) - Considerar aumentar ticket mínimo")
        
        # Análise de TP/SL
        hit_tp_rate = (df_results['hit_tp'].sum() / len(df_results) * 100) if len(df_results) > 0 else 0
        hit_sl_rate = (df_results['hit_sl'].sum() / len(df_results) * 100) if len(df_results) > 0 else 0
        
        if hit_tp_rate < 20:
            improvements.append(f"⚠️ Taxa de acerto de TP baixa ({hit_tp_rate:.1f}%) - Considerar ajustar take_profit_pct")
        
        if hit_sl_rate > 30:
            improvements.append(f"⚠️ Taxa de acerto de SL alta ({hit_sl_rate:.1f}%) - Considerar ajustar stop_loss_pct ou filtros")
        
        # Análise de score
        avg_score = df_results['comparison_score'].mean()
        if avg_score < 0.6:
            improvements.append(f"⚠️ Score médio baixo ({avg_score:.2f}) - Considerar ajustar parâmetros de comparação")
        
        return improvements
    
    def _generate_summary(self, backtest_results: List[Dict], profitability_analysis: Dict) -> Dict:
        """Gera resumo geral."""
        if not backtest_results:
            return {}
        
        df_results = pd.DataFrame(backtest_results)
        
        total_proposals = len(df_results)
        profitable = len(df_results[df_results['net_profit'] > 0])
        win_rate = (profitable / total_proposals * 100) if total_proposals > 0 else 0
        
        total_net_profit = df_results['net_profit'].sum()
        total_gross_profit = df_results['gross_profit'].sum()
        total_costs = df_results['operational_costs'].sum() + df_results['ir_amount'].sum()
        
        return {
            'total_proposals': total_proposals,
            'profitable': profitable,
            'loss_making': total_proposals - profitable,
            'win_rate': win_rate,
            'total_net_profit': total_net_profit,
            'total_gross_profit': total_gross_profit,
            'total_costs': total_costs,
            'avg_profit_per_trade': df_results['net_profit'].mean(),
            'best_asset': max(profitability_analysis.items(), key=lambda x: x[1]['total_net_profit'])[0] if profitability_analysis else None,
            'worst_asset': min(profitability_analysis.items(), key=lambda x: x[1]['total_net_profit'])[0] if profitability_analysis else None
        }
    
    def _empty_analysis(self, date: str) -> Dict:
        """Retorna análise vazia."""
        return {
            'date': date,
            'total_proposals': 0,
            'backtest_results': [],
            'profitability_by_asset': {},
            'agent_parameters': {},
            'operational_improvements': [],
            'summary': {}
        }
    
    def format_telegram_report(self, analysis: Dict) -> str:
        """Formata relatório para Telegram."""
        if analysis['total_proposals'] == 0:
            return f"""
📊 *ANÁLISE EOD - {analysis['date']}*

Nenhuma proposta encontrada para análise.

_Análise automática executada às {datetime.now().strftime('%H:%M:%S')}_
"""
        
        summary = analysis['summary']
        profitability = analysis['profitability_by_asset']
        improvements = analysis['operational_improvements']
        
        # Cabeçalho
        report = f"""
📊 *ANÁLISE EOD - {analysis['date']}*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*📈 RESUMO GERAL*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Total de Propostas: {summary['total_proposals']}
• Lucrativas: {summary['profitable']} ({summary['win_rate']:.1f}%)
• Prejuízo: {summary['loss_making']}

*💰 RESULTADOS FINANCEIROS:*
• Lucro Líquido Total: R$ {summary['total_net_profit']:,.2f}
• Lucro Bruto Total: R$ {summary['total_gross_profit']:,.2f}
• Custos Totais: R$ {summary['total_costs']:,.2f}
• Lucro Médio por Trade: R$ {summary['avg_profit_per_trade']:,.2f}

"""
        
        # Melhor e Pior Ativo
        if summary.get('best_asset') and summary.get('worst_asset'):
            report += f"""
*🏆 DESTAQUES:*
• Melhor Ativo: {summary['best_asset']}
• Pior Ativo: {summary['worst_asset']}

"""
        
        # Análise por Ativo
        if profitability:
            report += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*📊 ANÁLISE POR ATIVO*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
            # Ordenar por lucro líquido
            sorted_assets = sorted(profitability.items(), key=lambda x: x[1]['total_net_profit'], reverse=True)
            
            for asset, stats in sorted_assets[:10]:  # Top 10
                profit_emoji = "✅" if stats['total_net_profit'] > 0 else "❌"
                report += f"""
{profit_emoji} *{asset}*
• Propostas: {stats['total_proposals']}
• Win Rate: {stats['win_rate']:.1f}%
• Lucro Líquido: R$ {stats['total_net_profit']:,.2f}
• Lucro Médio: R$ {stats['avg_profit']:,.2f}
• Score Médio: {stats['avg_score']:.2f}
• TP Atingido: {stats['hit_tp']} | SL Atingido: {stats['hit_sl']}

"""
        
        # Melhorias Operacionais
        if improvements:
            report += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*🔧 MELHORIAS OPERACIONAIS SUGERIDAS*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
            for improvement in improvements:
                report += f"{improvement}\n"
        
        report += f"\n_Análise automática executada às {datetime.now().strftime('%H:%M:%S')}_"
        
        return report

