#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Análise Detalhada por Ativo - Mercado Brasileiro (B3)
Analisa desempenho, oportunidades perdidas e melhorias específicas por ativo
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

class AnaliseDetalhadaPorAtivo:
    """Análise detalhada por ativo do mercado brasileiro."""
    
    def __init__(self):
        self.repo = OrdersRepository()
        self.schedule = TradingSchedule()
        self.calculator = default_calculator
    
    def carregar_dados(self, data_inicio=None, data_fim=None):
        """Carrega e prepara dados para análise."""
        if not data_inicio:
            data_inicio = self.schedule.get_current_b3_time().date() - timedelta(days=7)
        if not data_fim:
            data_fim = self.schedule.get_current_b3_time().date()
        
        # Carregar backtest
        backtest_file = f"backtest_propostas_{data_inicio}_{data_fim}.csv"
        if not Path(backtest_file).exists():
            print(f"⚠️ Arquivo de backtest não encontrado: {backtest_file}")
            return None, None
        
        df_backtest = pd.read_csv(backtest_file)
        
        # Filtrar apenas brasileiros OU usar todos se não houver brasileiros
        df_b3 = df_backtest[df_backtest['underlying'].str.contains('.SA', na=False)].copy()
        
        # Se não houver brasileiros, usar todos os dados mas marcar como análise geral
        if df_b3.empty:
            print("⚠️ Nenhum dado brasileiro encontrado no backtest.")
            print("   Analisando todos os dados disponíveis para demonstração...")
            df_b3 = df_backtest.copy()  # Usar todos para demonstração
        
        # Carregar propostas do banco
        proposals_df = self.repo.get_proposals()
        
        # Carregar avaliações de risco
        risk_eval_df = self.repo.get_risk_evaluations()
        
        return df_b3, proposals_df, risk_eval_df
    
    def calcular_custos_e_lucro_liquido(self, row):
        """Calcula custos e lucro líquido para uma operação."""
        entry_price = row['entry_price']
        exit_price = row.get('close_price', row.get('exit_price_tp', entry_price))
        quantity = 100  # 1 contrato de opção
        
        entry_value = entry_price * quantity
        exit_value = exit_price * quantity
        
        costs = self.calculator.calculate_total_costs(
            entry_value=entry_value,
            exit_value=exit_value,
            instrument_type='options'
        )
        
        return {
            'profit_bruto': costs['profit_bruto'],
            'profit_liquido': costs['profit_liquido'],
            'custos_operacionais': costs['total_operational_costs'],
            'impostos': costs['total_taxes'],
            'profit_pct_bruto': costs['profit_pct_bruto'],
            'profit_pct_liquido': costs['profit_pct_liquido']
        }
    
    def analisar_ativo(self, ativo, df_backtest, proposals_df, risk_eval_df):
        """Analisa um ativo específico em detalhes."""
        print("\n" + "=" * 100)
        print(f"📊 ANÁLISE DETALHADA: {ativo}")
        print("=" * 100)
        
        # Filtrar dados do ativo
        df_ativo = df_backtest[df_backtest['underlying'] == ativo].copy()
        
        if df_ativo.empty:
            print(f"⚠️ Nenhum dado encontrado para {ativo}")
            return None
        
        print(f"\n📈 ESTATÍSTICAS GERAIS:")
        print("-" * 100)
        print(f"  Total de propostas: {len(df_ativo)}")
        
        # Resultados
        tp_count = len(df_ativo[df_ativo['resultado'] == 'TP'])
        sl_count = len(df_ativo[df_ativo['resultado'] == 'SL'])
        aberto_count = len(df_ativo[df_ativo['resultado'] == 'ABERTO'])
        
        print(f"  Take Profit: {tp_count} ({tp_count/len(df_ativo)*100:.1f}%)")
        print(f"  Stop Loss: {sl_count} ({sl_count/len(df_ativo)*100:.1f}%)")
        print(f"  Abertas: {aberto_count} ({aberto_count/len(df_ativo)*100:.1f}%)")
        
        # Calcular custos e lucro líquido
        resultados_custos = []
        for idx, row in df_ativo.iterrows():
            custos = self.calcular_custos_e_lucro_liquido(row)
            resultados_custos.append(custos)
        
        df_custos = pd.DataFrame(resultados_custos)
        df_ativo_com_custos = pd.concat([df_ativo.reset_index(drop=True), df_custos], axis=1)
        
        # Rentabilidade
        print(f"\n💰 RENTABILIDADE:")
        print("-" * 100)
        
        if not df_custos.empty:
            lucro_total_bruto = df_custos['profit_bruto'].sum()
            lucro_total_liquido = df_custos['profit_liquido'].sum()
            custos_totais = df_custos['custos_operacionais'].sum() + df_custos['impostos'].sum()
            
            print(f"  Lucro total bruto: R$ {lucro_total_bruto:,.2f}")
            print(f"  Custos totais: R$ {custos_totais:,.2f}")
            print(f"  Lucro total líquido: R$ {lucro_total_liquido:,.2f}")
            print(f"  Rentabilidade média bruta: {df_custos['profit_pct_bruto'].mean():.3f}%")
            print(f"  Rentabilidade média líquida: {df_custos['profit_pct_liquido'].mean():.3f}%")
            
            # Operações lucrativas vs prejuízos
            lucrativas = df_custos[df_custos['profit_liquido'] > 0]
            prejuizos = df_custos[df_custos['profit_liquido'] < 0]
            
            print(f"\n  Operações lucrativas: {len(lucrativas)} ({len(lucrativas)/len(df_custos)*100:.1f}%)")
            print(f"  Operações com prejuízo: {len(prejuizos)} ({len(prejuizos)/len(df_custos)*100:.1f}%)")
            
            if not lucrativas.empty:
                print(f"  Lucro médio (lucrativas): R$ {lucrativas['profit_liquido'].mean():,.2f}")
            if not prejuizos.empty:
                print(f"  Prejuízo médio: R$ {prejuizos['profit_liquido'].mean():,.2f}")
        
        # Métricas técnicas
        print(f"\n📊 MÉTRICAS TÉCNICAS:")
        print("-" * 100)
        
        print(f"  Intraday Return médio: {df_ativo['intraday_return'].mean()*100:.3f}%")
        print(f"  Intraday Return mediano: {df_ativo['intraday_return'].median()*100:.3f}%")
        print(f"  Volume Ratio médio: {df_ativo['volume_ratio'].mean():.2f}x")
        print(f"  Delta médio: {df_ativo['delta'].mean():.3f}")
        
        # Análise de TP
        tp_df = df_ativo[df_ativo['resultado'] == 'TP']
        if not tp_df.empty:
            print(f"\n  📈 OPORTUNIDADES BEM-SUCEDIDAS ({len(tp_df)}):")
            print(f"     Intraday Return médio: {tp_df['intraday_return'].mean()*100:.3f}%")
            print(f"     Volume Ratio médio: {tp_df['volume_ratio'].mean():.2f}x")
            print(f"     Delta médio: {tp_df['delta'].mean():.3f}")
            print(f"     PnL médio: {tp_df['pnl_pct'].mean()*100:.3f}%")
        
        # Análise por horário
        if not proposals_df.empty:
            proposals_ativo = proposals_df[proposals_df['symbol'].str.contains(ativo.replace('.SA', ''), na=False)]
            if not proposals_ativo.empty:
                proposals_ativo['created_at'] = pd.to_datetime(proposals_ativo['created_at'], errors='coerce')
                proposals_ativo['hora'] = proposals_ativo['created_at'].dt.hour
                
                horario_dist = proposals_ativo['hora'].value_counts().sort_index()
                print(f"\n⏰ DISTRIBUIÇÃO POR HORÁRIO:")
                print("-" * 100)
                for hora, count in horario_dist.items():
                    pct = count / len(proposals_ativo) * 100
                    print(f"  {int(hora):02d}:00 - {count:3d} propostas ({pct:5.1f}%)")
        
        # Oportunidades perdidas (rejeitadas pelo RiskAgent)
        print(f"\n🚫 OPORTUNIDADES PERDIDAS:")
        print("-" * 100)
        
        if not risk_eval_df.empty:
            risk_ativo = risk_eval_df[risk_eval_df['proposal_id'].isin(df_ativo['proposal_id'])]
            rejeitadas = risk_ativo[risk_ativo['approved'] == False]
            
            if not rejeitadas.empty:
                print(f"  Total rejeitadas pelo RiskAgent: {len(rejeitadas)}")
                
                # Razões de rejeição
                if 'rejection_reason' in rejeitadas.columns:
                    razoes = rejeitadas['rejection_reason'].value_counts()
                    print(f"\n  Razões de rejeição:")
                    for razao, count in razoes.items():
                        print(f"    • {razao}: {count}")
            else:
                print(f"  Nenhuma proposta rejeitada encontrada")
        
        # Análise de propostas não geradas (oportunidades perdidas)
        # Comparar com mercado para identificar oportunidades não capturadas
        print(f"\n🔍 ANÁLISE DE OPORTUNIDADES NÃO CAPTURADAS:")
        print("-" * 100)
        
        # Verificar se há dias sem propostas
        df_ativo['date'] = pd.to_datetime(df_ativo['date'])
        dias_com_propostas = df_ativo['date'].dt.date.nunique()
        dias_totais = (df_ativo['date'].max() - df_ativo['date'].min()).days + 1
        
        print(f"  Dias com propostas: {dias_com_propostas} de {dias_totais} dias")
        print(f"  Taxa de cobertura: {dias_com_propostas/dias_totais*100:.1f}%")
        
        # Recomendações específicas
        print(f"\n💡 RECOMENDAÇÕES ESPECÍFICAS PARA {ativo}:")
        print("-" * 100)
        
        recomendacoes = []
        
        # 1. Threshold de intraday return
        if not tp_df.empty:
            p25_intraday = tp_df['intraday_return'].quantile(0.25)
            atual_threshold = 0.006  # 0.6%
            
            if p25_intraday < atual_threshold:
                recomendacoes.append(
                    f"  ✅ Threshold atual (0.6%) adequado - percentil 25 das bem-sucedidas: {p25_intraday*100:.2f}%"
                )
            else:
                recomendacoes.append(
                    f"  ⚠️ Considerar aumentar threshold para {p25_intraday*100:.2f}% (baseado em P25)"
                )
        
        # 2. Delta
        if not tp_df.empty:
            delta_medio = tp_df['delta'].mean()
            delta_p25 = tp_df['delta'].quantile(0.25)
            delta_p75 = tp_df['delta'].quantile(0.75)
            
            recomendacoes.append(
                f"  🎯 Delta ideal: {delta_p25:.3f} - {delta_p75:.3f} (média: {delta_medio:.3f})"
            )
        
        # 3. Horário ideal
        if not proposals_ativo.empty and 'hora' in proposals_ativo.columns:
            horario_ideal = proposals_ativo['hora'].mode()[0] if len(proposals_ativo['hora'].mode()) > 0 else None
            if horario_ideal:
                recomendacoes.append(
                    f"  ⏰ Horário mais frequente: {int(horario_ideal):02d}:00"
                )
        
        # 4. Volume
        volume_medio = df_ativo['volume_ratio'].mean()
        if volume_medio < 0.5:
            recomendacoes.append(
                f"  ⚠️ Volume ratio baixo ({volume_medio:.2f}x) - considerar aumentar threshold mínimo"
            )
        
        # 5. Rentabilidade líquida
        if not df_custos.empty:
            rent_liquida_media = df_custos['profit_pct_liquido'].mean()
            if rent_liquida_media < 0.001:  # Menos que 0.1%
                recomendacoes.append(
                    f"  ⚠️ Rentabilidade líquida baixa ({rent_liquida_media*100:.3f}%) - considerar aumentar TP"
                )
            elif rent_liquida_media > 0.01:  # Mais que 1%
                recomendacoes.append(
                    f"  ✅ Rentabilidade líquida excelente ({rent_liquida_media*100:.3f}%)"
                )
        
        for rec in recomendacoes:
            print(rec)
        
        # Retornar resumo
        return {
            'ativo': ativo,
            'total_propostas': len(df_ativo),
            'tp_count': tp_count,
            'sl_count': sl_count,
            'taxa_acerto': tp_count / len(df_ativo) if len(df_ativo) > 0 else 0,
            'lucro_total_liquido': lucro_total_liquido if not df_custos.empty else 0,
            'rentabilidade_media_liquida': df_custos['profit_pct_liquido'].mean() if not df_custos.empty else 0,
            'recomendacoes': recomendacoes
        }
    
    def gerar_relatorio_completo(self, data_inicio=None, data_fim=None):
        """Gera relatório completo por ativo."""
        print("=" * 100)
        print("ANÁLISE DETALHADA POR ATIVO - MERCADO BRASILEIRO (B3)")
        print("=" * 100)
        
        # Carregar dados
        df_backtest, proposals_df, risk_eval_df = self.carregar_dados(data_inicio, data_fim)
        
        if df_backtest is None or df_backtest.empty:
            print("⚠️ Nenhum dado brasileiro encontrado para análise")
            return
        
        # Listar ativos únicos
        ativos = sorted(df_backtest['underlying'].unique())
        
        print(f"\n📋 ATIVOS ENCONTRADOS: {len(ativos)}")
        print("-" * 100)
        for i, ativo in enumerate(ativos, 1):
            count = len(df_backtest[df_backtest['underlying'] == ativo])
            print(f"  {i:2d}. {ativo:15s} - {count:3d} propostas")
        
        # Analisar cada ativo
        resultados = []
        for ativo in ativos:
            resultado = self.analisar_ativo(ativo, df_backtest, proposals_df, risk_eval_df)
            if resultado:
                resultados.append(resultado)
        
        # Resumo executivo
        print("\n" + "=" * 100)
        print("📊 RESUMO EXECUTIVO - TODOS OS ATIVOS")
        print("=" * 100)
        
        df_resumo = pd.DataFrame(resultados)
        
        print("\n🏆 RANKING POR RENTABILIDADE LÍQUIDA:")
        print("-" * 100)
        df_resumo_sorted = df_resumo.sort_values('rentabilidade_media_liquida', ascending=False)
        for idx, row in df_resumo_sorted.iterrows():
            print(f"  {row['ativo']:15s} - {row['rentabilidade_media_liquida']*100:>6.3f}% | "
                  f"{row['total_propostas']:3d} propostas | Taxa acerto: {row['taxa_acerto']*100:>5.1f}%")
        
        print("\n💰 RANKING POR LUCRO TOTAL LÍQUIDO:")
        print("-" * 100)
        df_resumo_sorted = df_resumo.sort_values('lucro_total_liquido', ascending=False)
        for idx, row in df_resumo_sorted.iterrows():
            print(f"  {row['ativo']:15s} - R$ {row['lucro_total_liquido']:>10,.2f} | "
                  f"{row['total_propostas']:3d} propostas")
        
        print("\n🎯 RANKING POR TAXA DE ACERTO:")
        print("-" * 100)
        df_resumo_sorted = df_resumo.sort_values('taxa_acerto', ascending=False)
        for idx, row in df_resumo_sorted.iterrows():
            print(f"  {row['ativo']:15s} - {row['taxa_acerto']*100:>5.1f}% | "
                  f"{row['total_propostas']:3d} propostas")
        
        # Salvar relatório
        relatorio_file = f"relatorio_analise_por_ativo_{data_inicio}_{data_fim}.txt"
        with open(relatorio_file, 'w', encoding='utf-8') as f:
            f.write("RELATÓRIO DE ANÁLISE POR ATIVO - MERCADO BRASILEIRO\n")
            f.write("=" * 100 + "\n\n")
            f.write(f"Período: {data_inicio} a {data_fim}\n\n")
            f.write("Análise completa disponível no console.\n")
        
        print(f"\n✅ Relatório salvo em: {relatorio_file}")
        print("\n" + "=" * 100)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--inicio', help='Data de início (YYYY-MM-DD)')
    parser.add_argument('--fim', help='Data de fim (YYYY-MM-DD)')
    args = parser.parse_args()
    
    data_inicio = datetime.strptime(args.inicio, '%Y-%m-%d').date() if args.inicio else None
    data_fim = datetime.strptime(args.fim, '%Y-%m-%d').date() if args.fim else None
    
    analisador = AnaliseDetalhadaPorAtivo()
    analisador.gerar_relatorio_completo(data_inicio, data_fim)

