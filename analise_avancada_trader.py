#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Análise Avançada como Trader Experiente
Foco em: Identificação de Oportunidades, Gestão de Risco e Rentabilidade
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
# Visualizações opcionais (comentadas para não exigir instalação)
# import matplotlib.pyplot as plt
# import seaborn as sns

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.orders_repository import OrdersRepository
from src.trading_schedule import TradingSchedule
import yfinance as yf

class AnaliseAvancadaTrader:
    """Análise avançada como trader experiente."""
    
    def __init__(self):
        self.repo = OrdersRepository()
        self.schedule = TradingSchedule()
        
    def analisar_oportunidades(self, data_inicio=None, data_fim=None):
        """Analisa padrões de oportunidades bem-sucedidas."""
        print("=" * 80)
        print("ANÁLISE 1: IDENTIFICAÇÃO DE OPORTUNIDADES")
        print("=" * 80)
        
        if not data_inicio:
            data_inicio = self.schedule.get_current_b3_time().date() - timedelta(days=7)
        if not data_fim:
            data_fim = self.schedule.get_current_b3_time().date()
        
        # Carregar dados do backtest
        backtest_file = f"backtest_propostas_{data_inicio}_{data_fim}.csv"
        if Path(backtest_file).exists():
            df_backtest = pd.read_csv(backtest_file)
        else:
            print("⚠️ Arquivo de backtest não encontrado. Execute backtest_propostas.py primeiro.")
            return
        
        # Filtrar apenas TP (sucessos)
        tp_df = df_backtest[df_backtest['resultado'] == 'TP'].copy()
        
        if tp_df.empty:
            print("⚠️ Nenhuma proposta que atingiu TP encontrada")
            return
        
        print(f"\n📊 ANÁLISE DE {len(tp_df)} OPORTUNIDADES BEM-SUCEDIDAS:")
        print("-" * 80)
        
        # 1. Análise por métricas técnicas
        print("\n1. MÉTRICAS TÉCNICAS DAS OPORTUNIDADES BEM-SUCEDIDAS:")
        print("-" * 80)
        
        metricas_tp = {
            'intraday_return': {
                'media': tp_df['intraday_return'].mean(),
                'mediana': tp_df['intraday_return'].median(),
                'percentil_25': tp_df['intraday_return'].quantile(0.25),
                'percentil_75': tp_df['intraday_return'].quantile(0.75),
                'min': tp_df['intraday_return'].min(),
                'max': tp_df['intraday_return'].max()
            },
            'volume_ratio': {
                'media': tp_df['volume_ratio'].mean(),
                'mediana': tp_df['volume_ratio'].median(),
                'percentil_25': tp_df['volume_ratio'].quantile(0.25),
                'percentil_75': tp_df['volume_ratio'].quantile(0.75)
            },
            'delta': {
                'media': tp_df['delta'].mean(),
                'mediana': tp_df['delta'].median(),
                'percentil_25': tp_df['delta'].quantile(0.25),
                'percentil_75': tp_df['delta'].quantile(0.75)
            }
        }
        
        print(f"\n📈 Intraday Return:")
        print(f"   Média: {metricas_tp['intraday_return']['media']*100:.2f}%")
        print(f"   Mediana: {metricas_tp['intraday_return']['mediana']*100:.2f}%")
        print(f"   Percentil 25: {metricas_tp['intraday_return']['percentil_25']*100:.2f}%")
        print(f"   Percentil 75: {metricas_tp['intraday_return']['percentil_75']*100:.2f}%")
        print(f"   Range: {metricas_tp['intraday_return']['min']*100:.2f}% - {metricas_tp['intraday_return']['max']*100:.2f}%")
        
        print(f"\n📊 Volume Ratio:")
        print(f"   Média: {metricas_tp['volume_ratio']['media']:.2f}x")
        print(f"   Mediana: {metricas_tp['volume_ratio']['mediana']:.2f}x")
        print(f"   Percentil 25: {metricas_tp['volume_ratio']['percentil_25']:.2f}x")
        print(f"   Percentil 75: {metricas_tp['volume_ratio']['percentil_75']:.2f}x")
        
        print(f"\n🎯 Delta:")
        print(f"   Média: {metricas_tp['delta']['media']:.3f}")
        print(f"   Mediana: {metricas_tp['delta']['mediana']:.3f}")
        print(f"   Percentil 25: {metricas_tp['delta']['percentil_25']:.3f}")
        print(f"   Percentil 75: {metricas_tp['delta']['percentil_75']:.3f}")
        
        # 2. Análise por horário
        print("\n2. ANÁLISE POR HORÁRIO DE ENTRADA:")
        print("-" * 80)
        
        # Extrair hora da proposta (se disponível)
        proposals_df = self.repo.get_proposals()
        if not proposals_df.empty:
            proposals_df['created_at'] = pd.to_datetime(proposals_df['created_at'], errors='coerce')
            proposals_df['hora'] = proposals_df['created_at'].dt.hour
            
            # Mesclar com backtest
            tp_with_time = tp_df.merge(
                proposals_df[['proposal_id', 'hora']],
                left_on='proposal_id',
                right_on='proposal_id',
                how='left'
            )
            
            if 'hora' in tp_with_time.columns:
                horario_tp = tp_with_time['hora'].value_counts().sort_index()
                print("\nDistribuição por horário (oportunidades bem-sucedidas):")
                for hora, count in horario_tp.items():
                    pct = count / len(tp_with_time) * 100
                    hora_int = int(hora) if pd.notna(hora) else 0
                    print(f"   {hora_int:02d}:00 - {count:3d} propostas ({pct:.1f}%)")
        
        # 3. Análise por ativo
        print("\n3. ANÁLISE POR ATIVO:")
        print("-" * 80)
        
        ativo_tp = tp_df['underlying'].value_counts().head(10)
        print("\nTop 10 ativos com mais sucessos:")
        for ativo, count in ativo_tp.items():
            pct = count / len(tp_df) * 100
            pnl_medio = tp_df[tp_df['underlying'] == ativo]['pnl_pct'].mean() * 100
            print(f"   {ativo:10s} - {count:3d} sucessos ({pct:5.1f}%) | PnL médio: {pnl_medio:.2f}%")
        
        # 4. Recomendações para identificação
        print("\n💡 RECOMENDAÇÕES PARA IDENTIFICAÇÃO DE OPORTUNIDADES:")
        print("-" * 80)
        
        print(f"\n✅ Thresholds Sugeridos (baseado em percentil 25 das bem-sucedidas):")
        print(f"   min_intraday_return: {metricas_tp['intraday_return']['percentil_25']*100:.2f}%")
        print(f"   min_volume_ratio: {metricas_tp['volume_ratio']['percentil_25']:.2f}x")
        print(f"   delta_min: {metricas_tp['delta']['percentil_25']:.3f}")
        print(f"   delta_max: {metricas_tp['delta']['percentil_75']:.3f}")
        
        print(f"\n✅ Foco em Ativos com Melhor Desempenho:")
        top_ativos = ativo_tp.head(5).index.tolist()
        print(f"   {', '.join(top_ativos)}")
        
        return metricas_tp, tp_df
    
    def analisar_gestao_risco(self, data_inicio=None, data_fim=None):
        """Analisa gestão de risco e sugere melhorias."""
        print("\n" + "=" * 80)
        print("ANÁLISE 2: GESTÃO DE RISCO")
        print("=" * 80)
        
        if not data_inicio:
            data_inicio = self.schedule.get_current_b3_time().date() - timedelta(days=7)
        if not data_fim:
            data_fim = self.schedule.get_current_b3_time().date()
        
        backtest_file = f"backtest_propostas_{data_inicio}_{data_fim}.csv"
        if not Path(backtest_file).exists():
            print("⚠️ Arquivo de backtest não encontrado.")
            return
        
        df_backtest = pd.read_csv(backtest_file)
        
        print(f"\n📊 ANÁLISE DE RISCO:")
        print("-" * 80)
        
        # 1. Análise de Stop Loss vs Take Profit
        tp_count = len(df_backtest[df_backtest['resultado'] == 'TP'])
        sl_count = len(df_backtest[df_backtest['resultado'] == 'SL'])
        aberto_count = len(df_backtest[df_backtest['resultado'] == 'ABERTO'])
        
        print(f"\n1. RESULTADOS:")
        print(f"   Take Profit: {tp_count} ({tp_count/len(df_backtest)*100:.1f}%)")
        print(f"   Stop Loss: {sl_count} ({sl_count/len(df_backtest)*100:.1f}%)")
        print(f"   Abertas: {aberto_count} ({aberto_count/len(df_backtest)*100:.1f}%)")
        
        # 2. Análise de razão ganho/perda
        print(f"\n2. ANÁLISE DE RAZÃO GANHO/PERDA:")
        print("-" * 80)
        
        take_profit_pct = df_backtest['take_profit_pct'].mean()
        stop_loss_pct = df_backtest['stop_loss_pct'].mean()
        gain_loss_ratio = take_profit_pct / stop_loss_pct if stop_loss_pct > 0 else 0
        
        print(f"   Take Profit médio: {take_profit_pct*100:.2f}%")
        print(f"   Stop Loss médio: {stop_loss_pct*100:.2f}%")
        print(f"   Razão G/P atual: {gain_loss_ratio:.2f}")
        
        # 3. Análise de drawdown teórico
        print(f"\n3. ANÁLISE DE DRAWDOWN:")
        print("-" * 80)
        
        # Calcular drawdown máximo teórico
        max_loss = df_backtest['pnl_pct'].min()
        max_gain = df_backtest['pnl_pct'].max()
        
        print(f"   Pior resultado: {max_loss*100:.2f}%")
        print(f"   Melhor resultado: {max_gain*100:.2f}%")
        print(f"   Range: {max_gain*100:.2f}% a {max_loss*100:.2f}%")
        
        # 4. Análise de concentração de risco
        print(f"\n4. CONCENTRAÇÃO DE RISCO:")
        print("-" * 80)
        
        ativo_count = df_backtest['underlying'].value_counts()
        concentracao_top5 = ativo_count.head(5).sum() / len(df_backtest) * 100
        
        print(f"   Top 5 ativos concentram: {concentracao_top5:.1f}% das propostas")
        print(f"   Total de ativos únicos: {len(ativo_count)}")
        
        # 5. Recomendações de gestão de risco
        print(f"\n💡 RECOMENDAÇÕES PARA GESTÃO DE RISCO:")
        print("-" * 80)
        
        print(f"\n✅ Ajuste de Stop Loss:")
        if sl_count == 0:
            print(f"   ⚠️ Nenhum Stop Loss atingido - pode indicar:")
            print(f"      - Stop Loss muito largo ({stop_loss_pct*100:.1f}%)")
            print(f"      - Parâmetros muito conservadores")
            print(f"      - Sugestão: Reduzir para {stop_loss_pct*0.75*100:.1f}% (25% mais apertado)")
        else:
            print(f"   Stop Loss funcionando - {sl_count} propostas atingiram")
        
        print(f"\n✅ Otimização de Take Profit:")
        pnl_medio_tp = df_backtest[df_backtest['resultado'] == 'TP']['pnl_pct'].mean()
        print(f"   PnL médio das TP: {pnl_medio_tp*100:.2f}%")
        print(f"   Take Profit configurado: {take_profit_pct*100:.2f}%")
        
        if pnl_medio_tp < take_profit_pct * 0.8:
            print(f"   ⚠️ PnL médio menor que TP - muitas propostas fechando antes do TP")
            print(f"   Sugestão: Reduzir TP para {pnl_medio_tp*100:.2f}% ou ajustar lógica de fechamento")
        
        print(f"\n✅ Diversificação:")
        if concentracao_top5 > 50:
            print(f"   ⚠️ Alta concentração ({concentracao_top5:.1f}%)")
            print(f"   Sugestão: Limitar exposição por ativo a 20%")
        else:
            print(f"   ✅ Boa diversificação ({concentracao_top5:.1f}%)")
        
        return {
            'tp_count': tp_count,
            'sl_count': sl_count,
            'gain_loss_ratio': gain_loss_ratio,
            'concentracao': concentracao_top5
        }
    
    def analisar_rentabilidade(self, data_inicio=None, data_fim=None):
        """Analisa rentabilidade e sugere melhorias."""
        print("\n" + "=" * 80)
        print("ANÁLISE 3: RENTABILIDADE DA CARTEIRA")
        print("=" * 80)
        
        if not data_inicio:
            data_inicio = self.schedule.get_current_b3_time().date() - timedelta(days=7)
        if not data_fim:
            data_fim = self.schedule.get_current_b3_time().date()
        
        backtest_file = f"backtest_propostas_{data_inicio}_{data_fim}.csv"
        if not Path(backtest_file).exists():
            print("⚠️ Arquivo de backtest não encontrado.")
            return
        
        df_backtest = pd.read_csv(backtest_file)
        
        print(f"\n📊 ANÁLISE DE RENTABILIDADE:")
        print("-" * 80)
        
        # 1. PnL por dia
        print("\n1. RENTABILIDADE POR DIA:")
        print("-" * 80)
        
        df_backtest['date'] = pd.to_datetime(df_backtest['date'])
        pnl_por_dia = df_backtest.groupby('date')['pnl_pct'].sum() * 100
        
        print("\nPnL acumulado por dia:")
        for date, pnl in pnl_por_dia.items():
            print(f"   {date.strftime('%d/%m/%Y')}: {pnl:+.2f}%")
        
        pnl_total = pnl_por_dia.sum()
        pnl_medio_dia = pnl_por_dia.mean()
        dias_positivos = len(pnl_por_dia[pnl_por_dia > 0])
        dias_negativos = len(pnl_por_dia[pnl_por_dia < 0])
        
        print(f"\n   Total acumulado: {pnl_total:+.2f}%")
        print(f"   Média por dia: {pnl_medio_dia:+.2f}%")
        print(f"   Dias positivos: {dias_positivos} ({dias_positivos/(dias_positivos+dias_negativos)*100:.1f}%)")
        print(f"   Dias negativos: {dias_negativos} ({dias_negativos/(dias_positivos+dias_negativos)*100:.1f}%)")
        
        # 2. Sharpe Ratio simplificado
        print("\n2. ANÁLISE DE RISCO-AJUSTADO:")
        print("-" * 80)
        
        if len(pnl_por_dia) > 1:
            retorno_medio = pnl_por_dia.mean()
            desvio_padrao = pnl_por_dia.std()
            sharpe_simples = retorno_medio / desvio_padrao if desvio_padrao > 0 else 0
            
            print(f"   Retorno médio diário: {retorno_medio:.2f}%")
            print(f"   Desvio padrão: {desvio_padrao:.2f}%")
            print(f"   Sharpe Ratio (simplificado): {sharpe_simples:.2f}")
            
            if sharpe_simples > 1:
                print(f"   ✅ Bom Sharpe Ratio (> 1.0)")
            elif sharpe_simples > 0.5:
                print(f"   ⚠️ Sharpe Ratio moderado (0.5 - 1.0)")
            else:
                print(f"   ❌ Sharpe Ratio baixo (< 0.5) - alta volatilidade")
        
        # 3. Análise de eficiência
        print("\n3. EFICIÊNCIA DAS OPERAÇÕES:")
        print("-" * 80)
        
        tp_df = df_backtest[df_backtest['resultado'] == 'TP']
        pnl_medio_tp = tp_df['pnl_pct'].mean() * 100 if not tp_df.empty else 0
        
        # Calcular eficiência (PnL médio vs TP configurado)
        take_profit_pct = df_backtest['take_profit_pct'].mean()
        eficiencia = pnl_medio_tp / (take_profit_pct * 100) if take_profit_pct > 0 else 0
        
        print(f"   PnL médio das TP: {pnl_medio_tp:.2f}%")
        print(f"   Take Profit configurado: {take_profit_pct*100:.2f}%")
        print(f"   Eficiência: {eficiencia*100:.1f}%")
        
        if eficiencia < 0.8:
            print(f"   ⚠️ Baixa eficiência - muitas propostas não atingem TP completo")
        elif eficiencia > 1.0:
            print(f"   ✅ Alta eficiência - propostas superam TP configurado")
        
        # 4. Análise de tamanho de posição
        print("\n4. ANÁLISE DE TAMANHO DE POSIÇÃO:")
        print("-" * 80)
        
        proposals_df = self.repo.get_proposals()
        if not proposals_df.empty:
            # Mesclar com backtest para ter quantidade
            merged = df_backtest.merge(
                proposals_df[['proposal_id', 'quantity', 'price']],
                on='proposal_id',
                how='left'
            )
            
            if 'quantity' in merged.columns:
                # Calcular valor da posição
                merged['position_value'] = merged['quantity'] * merged['price'] * 100  # Opções
                merged['pnl_abs'] = merged['pnl_pct'] * merged['position_value']
                
                pnl_por_tamanho = merged.groupby(pd.cut(merged['position_value'], bins=5))['pnl_pct'].mean() * 100
                
                print("\nPnL médio por tamanho de posição:")
                for intervalo, pnl in pnl_por_tamanho.items():
                    print(f"   {intervalo}: {pnl:+.2f}%")
        
        # 5. Recomendações para rentabilidade
        print("\n💡 RECOMENDAÇÕES PARA MELHORAR RENTABILIDADE:")
        print("-" * 80)
        
        print(f"\n✅ Otimização de Take Profit:")
        if eficiencia < 0.8:
            print(f"   Reduzir TP para {pnl_medio_tp:.2f}% (PnL médio real)")
            print(f"   Benefício: Mais propostas atingindo TP, menos abertas")
        
        print(f"\n✅ Gestão de Posição:")
        print(f"   Focar em posições de tamanho médio (melhor risco/retorno)")
        print(f"   Limitar posições muito grandes (maior risco)")
        
        print(f"\n✅ Seleção de Oportunidades:")
        print(f"   Focar em ativos com melhor histórico")
        print(f"   Evitar operar em dias muito voláteis")
        
        return {
            'pnl_total': pnl_total,
            'pnl_medio_dia': pnl_medio_dia,
            'eficiencia': eficiencia,
            'sharpe': sharpe_simples if len(pnl_por_dia) > 1 else 0
        }
    
    def gerar_relatorio_completo(self, data_inicio=None, data_fim=None):
        """Gera relatório completo de análise."""
        print("\n" + "=" * 80)
        print("RELATÓRIO COMPLETO - ANÁLISE COMO TRADER EXPERIENTE")
        print("=" * 80)
        
        # Executar todas as análises
        metricas_oportunidades, tp_df = self.analisar_oportunidades(data_inicio, data_fim)
        metricas_risco = self.analisar_gestao_risco(data_inicio, data_fim)
        metricas_rentabilidade = self.analisar_rentabilidade(data_inicio, data_fim)
        
        # Resumo executivo
        print("\n" + "=" * 80)
        print("RESUMO EXECUTIVO E RECOMENDAÇÕES FINAIS")
        print("=" * 80)
        
        print("\n🎯 PRIORIDADES PARA MELHORIA:")
        print("-" * 80)
        
        print("\n1. IDENTIFICAÇÃO DE OPORTUNIDADES:")
        print(f"   ✅ Ajustar thresholds baseado em percentil 25 das bem-sucedidas")
        print(f"   ✅ Focar em ativos com melhor desempenho")
        print(f"   ✅ Considerar horário de entrada (se padrão identificado)")
        
        print("\n2. GESTÃO DE RISCO:")
        if metricas_risco['sl_count'] == 0:
            print(f"   ⚠️ Reduzir Stop Loss (nenhum atingido)")
        print(f"   ✅ Manter razão G/P atual: {metricas_risco['gain_loss_ratio']:.2f}")
        if metricas_risco['concentracao'] > 50:
            print(f"   ⚠️ Reduzir concentração de risco")
        
        print("\n3. RENTABILIDADE:")
        print(f"   ✅ PnL total: {metricas_rentabilidade['pnl_total']:+.2f}%")
        print(f"   ✅ PnL médio/dia: {metricas_rentabilidade['pnl_medio_dia']:+.2f}%")
        if metricas_rentabilidade['eficiencia'] < 0.8:
            print(f"   ⚠️ Melhorar eficiência (ajustar TP)")
        
        # Salvar relatório
        relatorio_file = f"relatorio_analise_avancada_{data_inicio}_{data_fim}.txt"
        with open(relatorio_file, 'w', encoding='utf-8') as f:
            f.write("RELATÓRIO DE ANÁLISE AVANÇADA - TRADER EXPERIENTE\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Período: {data_inicio} a {data_fim}\n\n")
            f.write("Análise completa disponível no console.\n")
        
        print(f"\n✅ Relatório salvo em: {relatorio_file}")
        print("\n" + "=" * 80)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--inicio', help='Data de início (YYYY-MM-DD)')
    parser.add_argument('--fim', help='Data de fim (YYYY-MM-DD)')
    args = parser.parse_args()
    
    data_inicio = datetime.strptime(args.inicio, '%Y-%m-%d').date() if args.inicio else None
    data_fim = datetime.strptime(args.fim, '%Y-%m-%d').date() if args.fim else None
    
    analisador = AnaliseAvancadaTrader()
    analisador.gerar_relatorio_completo(data_inicio, data_fim)

