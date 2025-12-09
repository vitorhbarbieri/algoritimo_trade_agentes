#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Análise de Custos B3 e Rentabilidade Mínima
Recalcula análises considerando custos reais de operação
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.b3_costs import B3CostCalculator, default_calculator
from src.orders_repository import OrdersRepository
from src.trading_schedule import TradingSchedule

class AnaliseCustosB3:
    """Análise de custos e rentabilidade mínima B3."""
    
    def __init__(self):
        self.repo = OrdersRepository()
        self.schedule = TradingSchedule()
        self.calculator = default_calculator
    
    def analisar_custos_por_operacao(self, data_inicio=None, data_fim=None):
        """Analisa custos por tipo de operação."""
        print("=" * 80)
        print("ANÁLISE DE CUSTOS OPERACIONAIS B3")
        print("=" * 80)
        
        if not data_inicio:
            data_inicio = self.schedule.get_current_b3_time().date() - timedelta(days=7)
        if not data_fim:
            data_fim = self.schedule.get_current_b3_time().date()
        
        # Carregar dados do backtest
        backtest_file = f"backtest_propostas_{data_inicio}_{data_fim}.csv"
        if not Path(backtest_file).exists():
            print("⚠️ Arquivo de backtest não encontrado.")
            return
        
        df_backtest = pd.read_csv(backtest_file)
        
        # Filtrar apenas operações brasileiras (.SA)
        df_b3 = df_backtest[df_backtest['underlying'].str.contains('.SA', na=False)].copy()
        
        if df_b3.empty:
            print("⚠️ Nenhuma operação brasileira encontrada no período.")
            return
        
        print(f"\n📊 OPERAÇÕES BRASILEIRAS ANALISADAS: {len(df_b3)}")
        print("-" * 80)
        
        # Calcular custos para cada operação
        results = []
        for idx, row in df_b3.iterrows():
            entry_price = row['entry_price']
            exit_price = row.get('close_price', row.get('exit_price_tp', entry_price))
            quantity = 100  # Assumir 1 contrato de opção (100 ações)
            
            entry_value = entry_price * quantity
            exit_value = exit_price * quantity
            
            # Calcular custos
            costs = self.calculator.calculate_total_costs(
                entry_value=entry_value,
                exit_value=exit_value,
                instrument_type='options',
                levar_vencimento=False
            )
            
            results.append({
                'proposal_id': row['proposal_id'],
                'underlying': row['underlying'],
                'entry_value': entry_value,
                'exit_value': exit_value,
                'profit_bruto': costs['profit_bruto'],
                'profit_liquido': costs['profit_liquido'],
                'total_custos': costs['total_costs'],
                'custos_operacionais': costs['total_operational_costs'],
                'impostos': costs['total_taxes'],
                'profit_pct_bruto': costs['profit_pct_bruto'],
                'profit_pct_liquido': costs['profit_pct_liquido']
            })
        
        df_custos = pd.DataFrame(results)
        
        # Estatísticas
        print("\n💰 CUSTOS POR OPERAÇÃO:")
        print("-" * 80)
        print(f"  Custo médio operacional: R$ {df_custos['custos_operacionais'].mean():.2f}")
        print(f"  Impostos médios: R$ {df_custos['impostos'].mean():.2f}")
        print(f"  Custo total médio: R$ {df_custos['total_custos'].mean():.2f}")
        print(f"  Custo total como % do valor: {(df_custos['total_custos'] / df_custos['entry_value']).mean() * 100:.3f}%")
        
        print("\n📊 RENTABILIDADE BRUTA vs LÍQUIDA:")
        print("-" * 80)
        print(f"  Lucro médio bruto: R$ {df_custos['profit_bruto'].mean():.2f}")
        print(f"  Lucro médio líquido: R$ {df_custos['profit_liquido'].mean():.2f}")
        print(f"  Diferença (custos): R$ {(df_custos['profit_bruto'] - df_custos['profit_liquido']).mean():.2f}")
        print(f"  Rentabilidade bruta média: {df_custos['profit_pct_bruto'].mean():.3f}%")
        print(f"  Rentabilidade líquida média: {df_custos['profit_pct_liquido'].mean():.3f}%")
        
        # Operações que não cobrem custos
        operacoes_negativas = df_custos[df_custos['profit_liquido'] < 0]
        print(f"\n⚠️ OPERAÇÕES QUE NÃO COBREM CUSTOS: {len(operacoes_negativas)} ({len(operacoes_negativas)/len(df_custos)*100:.1f}%)")
        
        # Rentabilidade mínima necessária
        print("\n🎯 RENTABILIDADE MÍNIMA NECESSÁRIA:")
        print("-" * 80)
        
        # Calcular para diferentes valores de operação
        valores_teste = [1000, 5000, 10000, 50000, 100000]
        print("\nValor da Operação | Custo Total | Rentabilidade Mínima")
        print("-" * 60)
        for valor in valores_teste:
            min_profit = self.calculator.calculate_minimum_profit(valor, 'options')
            min_profit_pct = self.calculator.calculate_minimum_profit_pct(valor, 'options')
            print(f"R$ {valor:>10,.0f} | R$ {min_profit:>8,.2f} | {min_profit_pct*100:>6.3f}%")
        
        return df_custos
    
    def recalcular_analise_com_custos(self, data_inicio=None, data_fim=None):
        """Recalcula análise considerando custos reais."""
        print("\n" + "=" * 80)
        print("RECÁLCULO DE ANÁLISE CONSIDERANDO CUSTOS REAIS")
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
        
        # Filtrar apenas operações brasileiras
        df_b3 = df_backtest[df_backtest['underlying'].str.contains('.SA', na=False)].copy()
        
        if df_b3.empty:
            print("⚠️ Nenhuma operação brasileira encontrada.")
            return
        
        print(f"\n📊 OPERAÇÕES BRASILEIRAS: {len(df_b3)}")
        
        # Calcular rentabilidade líquida
        results = []
        for idx, row in df_b3.iterrows():
            entry_price = row['entry_price']
            exit_price = row.get('close_price', row.get('exit_price_tp', entry_price))
            quantity = 100
            
            entry_value = entry_price * quantity
            exit_value = exit_price * quantity
            
            costs = self.calculator.calculate_total_costs(
                entry_value=entry_value,
                exit_value=exit_value,
                instrument_type='options'
            )
            
            # Rentabilidade líquida real
            profit_pct_liquido = costs['profit_pct_liquido'] / 100
            
            results.append({
                'proposal_id': row['proposal_id'],
                'underlying': row['underlying'],
                'pnl_pct_bruto': row['pnl_pct'],
                'pnl_pct_liquido': profit_pct_liquido,
                'resultado': row['resultado']
            })
        
        df_resultados = pd.DataFrame(results)
        
        # Análise de resultados líquidos
        print("\n📈 ANÁLISE COM CUSTOS DESCONTADOS:")
        print("-" * 80)
        
        tp_liquido = df_resultados[df_resultados['pnl_pct_liquido'] > 0]
        sl_liquido = df_resultados[df_resultados['pnl_pct_liquido'] < 0]
        
        print(f"\n  Operações com lucro líquido: {len(tp_liquido)} ({len(tp_liquido)/len(df_resultados)*100:.1f}%)")
        print(f"  Operações com prejuízo líquido: {len(sl_liquido)} ({len(sl_liquido)/len(df_resultados)*100:.1f}%)")
        
        if not tp_liquido.empty:
            print(f"\n  Rentabilidade líquida média (lucros): {tp_liquido['pnl_pct_liquido'].mean()*100:.3f}%")
            print(f"  Rentabilidade líquida mediana (lucros): {tp_liquido['pnl_pct_liquido'].median()*100:.3f}%")
        
        if not sl_liquido.empty:
            print(f"\n  Prejuízo líquido médio: {sl_liquido['pnl_pct_liquido'].mean()*100:.3f}%")
        
        # Comparação bruto vs líquido
        print("\n📊 COMPARAÇÃO BRUTO vs LÍQUIDO:")
        print("-" * 80)
        print(f"  Rentabilidade bruta média: {df_resultados['pnl_pct_bruto'].mean()*100:.3f}%")
        print(f"  Rentabilidade líquida média: {df_resultados['pnl_pct_liquido'].mean()*100:.3f}%")
        print(f"  Impacto dos custos: {(df_resultados['pnl_pct_bruto'].mean() - df_resultados['pnl_pct_liquido'].mean())*100:.3f}%")
        
        return df_resultados
    
    def calcular_threshold_minimo(self):
        """Calcula threshold mínimo considerando custos."""
        print("\n" + "=" * 80)
        print("CÁLCULO DE THRESHOLD MÍNIMO CONSIDERANDO CUSTOS")
        print("=" * 80)
        
        # Valores típicos de operação
        valores_teste = [1000, 5000, 10000, 50000]
        
        print("\n💰 RENTABILIDADE MÍNIMA NECESSÁRIA POR VALOR:")
        print("-" * 80)
        
        thresholds = []
        for valor in valores_teste:
            min_pct = self.calculator.calculate_minimum_profit_pct(valor, 'options')
            thresholds.append({
                'valor_operacao': valor,
                'threshold_minimo_pct': min_pct * 100
            })
            print(f"  R$ {valor:>8,.0f}: {min_pct*100:>6.3f}% mínimo")
        
        # Threshold médio recomendado
        threshold_medio = np.mean([t['threshold_minimo_pct'] for t in thresholds])
        threshold_recomendado = threshold_medio * 1.5  # Margem de segurança 50%
        
        print(f"\n💡 THRESHOLD RECOMENDADO:")
        print("-" * 80)
        print(f"  Threshold mínimo médio: {threshold_medio:.3f}%")
        print(f"  Threshold recomendado (com margem 50%): {threshold_recomendado:.3f}%")
        print(f"  Threshold atual configurado: 0.6%")
        
        if threshold_recomendado > 0.6:
            print(f"\n  ⚠️ ATENÇÃO: Threshold atual pode ser insuficiente!")
            print(f"     Recomendação: Ajustar para pelo menos {threshold_recomendado:.3f}%")
        else:
            print(f"\n  ✅ Threshold atual adequado")
        
        return threshold_recomendado

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--inicio', help='Data de início (YYYY-MM-DD)')
    parser.add_argument('--fim', help='Data de fim (YYYY-MM-DD)')
    args = parser.parse_args()
    
    data_inicio = datetime.strptime(args.inicio, '%Y-%m-%d').date() if args.inicio else None
    data_fim = datetime.strptime(args.fim, '%Y-%m-%d').date() if args.fim else None
    
    analisador = AnaliseCustosB3()
    
    # Análise de custos
    df_custos = analisador.analisar_custos_por_operacao(data_inicio, data_fim)
    
    # Recálculo com custos
    df_resultados = analisador.recalcular_analise_com_custos(data_inicio, data_fim)
    
    # Threshold mínimo
    threshold = analisador.calcular_threshold_minimo()
    
    print("\n" + "=" * 80)
    print("ANÁLISE COMPLETA FINALIZADA")
    print("=" * 80)

