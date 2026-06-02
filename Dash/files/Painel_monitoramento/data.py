"""
data.py — Carregamento de dados do painel
"""

import sys
import pandas as pd
import datetime as dt
import engine as engs
import numpy as np

from sqlalchemy import text
from pathlib import Path

sys.path.insert(0, str(Path("C:/Users/wconceicao/OneDrive - Grupo A Educação SA/Área de Trabalho/Projetos")))



##VARIÁVEIS GLOBAIS

## Horas trabalhadas e totais para projeção, considerando operação das 9h às 21h (12 horas)
## Para proximas versões sera considerado o horario individual de cada equipe.
## --> V1 - HORAS TRABALHADAS PADRÃO <-- ## 
inicio_operacao = 9
fim_operacao = 21
horas_totais = fim_operacao - inicio_operacao

hora_atual = dt.datetime.now().hour + dt.datetime.now().minute / 60
horas_trabalhadas = max(0.1, hora_atual - inicio_operacao)
## --> V1 - HORAS TRABALHADAS PADRÃO <-- ## 

## carrega metas e dados das equipes ## 
metas_dados = pd.read_excel(r'P:\Mais_Campus_CallCenter\Sales Ops - Time Leonardo\Patric_Barbosa\documentação\python\Dash\files\meta_dados_ies.xlsx')
metas_dados = pd.DataFrame(metas_dados)

# ─────────────────────────────────────────────
#  REAL: PostgreSQL via Python_arq
# ─────────────────────────────────────────────
def carregar_dados_db() -> dict[str, pd.DataFrame]:

    eng = engs.get_engine()

    queries = [
        "painel_tickets.sql",
        "painel_vendas_orbita.sql",

    ]

    resultados = {}

    for nome_query in queries:
        chave = nome_query.replace(".sql", "")

        query = text(engs.load_query(nome_query))

        resultados[chave] = pd.read_sql(query, eng)

    return resultados


def tratar_dados(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:

    df_tickets = raw["painel_tickets"]
    df_vendas = raw["painel_vendas_orbita"]

    ordem_ies ={
        'PUCPR DIGITAL':1,
        'Pós PUCCAMPINAS':3,
        'PUCRJ Collab':5,
        'Pós PUCRJ':7,
        'GRADUAÇÃO':9,
        'Pós Artmed':2,
        'SECAD':4,
        'HCOR':6,
        'ESPM':8,
        'DOM CABRAL':10
    }

    print("📊 Colunas de painel_tickets:", df_tickets.columns.tolist())
    print(f"📊 Registros em painel_tickets: {len(df_tickets)}")
    print("📊 Primeiras linhas:\n", df_tickets.head())
    
    print("\n📊 Colunas de painel_vendas:", df_vendas.columns.tolist())
    print(f"📊 Registros em painel_vendas: {len(df_vendas)}")



    # 1️⃣ AGREGAÇÃO: Somar vendas por IES ANTES do merge
    vendas_count = df_vendas[['ies_name', 'vendas']].groupby('ies_name').sum().reset_index()
    print(f"\n📊 IES únicos em painel_vendas: {len(vendas_count)}")
    print("📊 Vendas por IES:\n", vendas_count.head(10))

    # 2️⃣ Renomeia colunas de tickets para lowercase
    df_tickets.columns = df_tickets.columns.str.lower().str.replace(" ", "_")
    
    # 3️⃣ MERGE ÚNICO: tickets com vendas agregadas
    resultado = pd.merge(
        df_tickets,
        vendas_count,
        left_on="ies",
        right_on="ies_name",
        how="left",
    )

    resultado = pd.merge(
        resultado,
        metas_dados,
        left_on='ies',
        right_on='Ies',
        how='left'
    )

    resultado['ordem'] = resultado['ies'].map(ordem_ies)
    resultado = resultado.sort_values('ordem').drop(columns=['ordem','ies_name'])


    print(f"\n📊 Registros após merge: {len(resultado)}")

    # 4️⃣ Preenchimento e cálculos

    resultado['volume_ideal'] = (resultado['meta_atendimento'] / resultado['headcount'].replace(0,np.nan)).round(1) ## META ATENDIMENTO POR OPERADOR
    resultado['volume_vendas_ideal'] = (resultado['meta_vendas'] / resultado['headcount'].replace(0,np.nan)).round(1) ## META VENDAS POR OPERADOR
    resultado['volume_atual'] = (resultado['em_atendimento'] / resultado['headcount'].replace(0,np.nan)).round(1) ## VOLUME ATUAL DE ATENDIMENTO POR OPERADOR
    resultado['volume_vendas_atual'] = (resultado['vendas'] / resultado['headcount'].replace(0, np.nan)).round(1) ## VOLUME ATUAL DE VENDAS POR OPERADOR
    resultado['perc_ideal'] = (
        resultado['volume_atual'] / resultado['volume_ideal'] * 100
    ).fillna(0).round(1)

    resultado['situacao_atendimento'] = np.select(
        [
            resultado['perc_ideal'] >=100,
            resultado['perc_ideal'] >= 80
        ],
        [
            'Verde',
            'Amarelo'
        ],
        default='Vermelho'
    )

    resultado['desvio'] = (
        resultado['perc_ideal'] - 100
    ).round(1)

    resultado["vendas"] = resultado["vendas"].fillna(0).astype(int)
    resultado['perc_meta_vendas'] = (
        resultado['vendas'] / resultado['meta_vendas'] * 100
    ).fillna(0).round(1)
    
    resultado['situacao_vendas'] = np.select(
        [
            resultado['perc_meta_vendas'] >= 100,
            resultado['perc_meta_vendas'] >= 80
        ],
        [
            'Verde',
            'Amarelo'
        ],
        default='Vermelho'
    )


    resultado["encerrado"] = resultado["encerrado"].fillna(1).astype(int)
    
    # Conversão (evita divisão por zero)
    resultado["conversao"] = (
        (resultado["vendas"] / resultado["encerrado"]) * 100
    ).fillna(0).round(1)
    resultado['meta_conversao'] = resultado['meta_conversao'] * 100
    resultado['gap_conversao'] = (
        (resultado['conversao'] / resultado['meta_conversao'] - 1) * 100
    ).fillna(0).round(1)

    resultado['situacao_conversao'] = np.select(
        [
            resultado['gap_conversao'] >= 0,
            resultado['gap_conversao'] >= -20
        ],
        [
            'Verde',
            'Amarelo'
        ],
        default='Vermelho'
    )

    # Calculo de Projeções
    resultado["projecao"] = ((resultado["vendas"] / horas_trabalhadas) * horas_totais).astype(int)

    resultado['projecao_encerrado'] = ((resultado['encerrado'] / horas_trabalhadas) * horas_totais).round(1)
    resultado['perc_meta_encerrado'] = (resultado['projecao_encerrado'] / resultado['meta_atendimento'] * 100)

    resultado['situacao_encerrado'] = np.select(
        [
            resultado['perc_meta_encerrado'] >= 100,
            resultado['perc_meta_encerrado'] >= 80
        ],
        [
            'Verde',
            'Amarelo'
        ],
        default='Vermelho'
    )

    resultado['desvio_encerrado'] = (resultado['perc_meta_encerrado'] - 100).round(0)

    resultado['situacao_fila'] = np.select(
        [
            resultado['fila'] <= 10,
            resultado['fila'] <= 25
        ],
        [
            'Verde',
            'Amarelo'
        ],
        default='Vermelho'
    )

    # 5️⃣ RETORNA APENAS AS COLUNAS NECESSÁRIAS
    resultado = resultado[[
        "ies", 
        "fila", 
        "em_atendimento", 
        "encerrado", 
        "vendas", 
        "situacao_vendas",
        "perc_meta_vendas",
        "conversao",
        "gap_conversao",
        "situacao_conversao",
        "projecao",
        "situacao_fila",
        "situacao_atendimento",
        "desvio",
        "projecao_encerrado",
        "situacao_encerrado",
        "desvio_encerrado"
    ]].reset_index(drop=True)


    print(f"\n✅ Resultado final: {len(resultado)} IES")
    print(resultado)

    return resultado

# ─────────────────────────────────────────────
#  MOCK: fallback para desenvolvimento
# ─────────────────────────────────────────────
def carregar_dados_mock() -> pd.DataFrame:
    equipes = [f"Equipe {i:02d}" for i in range(1, 11)]

    registros = []
    for i, equipe in enumerate(equipes):
        registros.append({
            "ies":             equipe,
            "fila":            0,
            "em_atendimento":  0,
            "encerrado":       0,
            "vendas":          0,
            "conversao":       0,
            "projecao":        0,
            "volume_ideal":    0,
            "volume_atual":    0,
        })

    return pd.DataFrame(registros)


# ─────────────────────────────────────────────
#  ENTRADA PRINCIPAL
#  Tenta o banco — cai no mock se falhar
# ─────────────────────────────────────────────
def carregar_dados() -> pd.DataFrame:

    try:

        print("\n🔄 Tentando carregar dados do banco de dados...")
        raw = carregar_dados_db()

        print("✅ Dados do banco carregados com sucesso!")
        resultado = tratar_dados(raw)
        
        print(f"✅ Dados tratados com sucesso! Total de registros: {len(resultado)}")
        print(f'✅Dados atualizados em: {dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        
        return resultado

    except Exception as e:

        print(f"\n⚠️ ERRO ao carregar do banco: {type(e).__name__}: {e}")
        print("📦 Usando dados de mock (desenvolvimento)...\n")

        return carregar_dados_mock()