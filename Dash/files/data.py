"""
data.py — Carregamento de dados do painel
"""

import sys
import pandas as pd
import datetime as dt
import engine as engs
import numpy as np

import sqlalchemy as sql
from pathlib import Path

sys.path.insert(0, str(Path("C:/Users/wconceicao/OneDrive - Grupo A Educação SA/Área de Trabalho/Projetos")))



##VARIÁVEIS GLOBAIS



## carrega metas e dados das equipes ## 
meta_dados = pd.read_excel(
    r'P:\Mais_Campus_CallCenter\Sales Ops - Time Leonardo\Patric_Barbosa\documentação\python\Dash\meta_dados_ies.xlsx',
    sheet_name='meta_dia'
)
meta_dados = pd.DataFrame(meta_dados)
meta_dados = meta_dados[meta_dados['Data'] == str(dt.date.today())]
print('Log arquivo de metas')
print(meta_dados)
print('------------------------------------------------')

# ─────────────────────────────────────────────
#  REAL: PostgreSQL via Python_arq
# ─────────────────────────────────────────────
def carregar_dados_db() -> dict[str, pd.DataFrame]:

    eng = engs.get_engine()

    queries = [
        "painel_tickets.sql",
        "painel_vendas.sql",
    ]

    resultados = {}

    try:
        with eng.connect() as conn:
            conexoes = eng.pool.checkedout()
            print(f'conexoes a encerrar: {conexoes}')
            for nome_query in queries:
                chave = nome_query.replace('.sql','')
                try:
                    query = sql.text(engs.load_query(nome_query))
                    resultados[chave] = pd.read_sql(query, conn)
                except Exception as e:
                    print(f'Erro ao carregar "{nome_query}":{e}')
                    resultados[chave] = pd.DataFrame()              
    finally:
            conexoes = eng.pool.checkedout()
            conn.close()
            eng.dispose()
            if conexoes > 0:
                print(f'Possui conexoes abertas... Verificar...')
            else:
                print(f'{conexoes} abertas...Conexões encerradas...\n\n')
    
    return resultados


def tratar_dados(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:

    ## Horas trabalhadas e totais para projeção, considerando operação das 9h às 21h (12 horas)
    ## Para proximas versões sera considerado o horario individual de cada equipe.
    ## --> V1 - HORAS TRABALHADAS PADRÃO <-- ## 
    inicio_operacao = 9
    fim_operacao = 21
    horas_totais = fim_operacao - inicio_operacao

    hora_atual = dt.datetime.now().hour + dt.datetime.now().minute / 60
    horas_trabalhadas = max(0.1, hora_atual - inicio_operacao)
    ## --> V1 - HORAS TRABALHADAS PADRÃO <-- ## 

    df_tickets = raw["painel_tickets"]
    df_vendas = raw["painel_vendas"]

    
    ordem_ies ={
        'PUCPR DIGITAL':1,
        'Pós PUCCAMPINAS':2,
        'PUCRJ Collab':3,
        'Pós PUCRJ':4,
        'GRADUAÇÃO':5,
        'Pós Artmed':6,
        'SECAD':7,
        'HCOR':8,
        'ESPM':9,
        'DOM CABRAL':10
    }

    print("📊 Colunas de painel_tickets:", df_tickets.columns.tolist())
    print(f"📊 Registros em painel_tickets: {len(df_tickets)}")
    print("📊 Primeiras linhas:\n", df_tickets.head())
    
    print("\n📊 Colunas de painel_vendas:", df_vendas.columns.tolist())
    print(f"📊 Registros em painel_vendas: {len(df_vendas)}")



    # 1️⃣ AGREGAÇÃO: Somar vendas por IES ANTES do merge
    vendas_count = df_vendas[['ies_name', 'vendas','vendas_historico']].groupby('ies_name').sum().reset_index()
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

    resultado['vendas'] = (
        pd.to_numeric(resultado['vendas'],errors='coerce')
        .fillna(0)
        .astype(int)
    )

    resultado['vendas_historico'] = (
        pd.to_numeric(resultado['vendas_historico'],errors='coerce')
        .fillna(0)
        .astype(int)
    )

    resultado = pd.merge(
        resultado,
        meta_dados,
        left_on='ies',
        right_on='IES',
        how='left'
    )

    resultado['ordem'] = resultado['ies'].map(ordem_ies)
    resultado = resultado.sort_values('ordem').drop(columns=['ordem','ies_name'])


    print(f"\n📊 Registros após merge: {len(resultado)}")

    # 4️⃣ Preenchimento e cálculos

    resultado['volume_ideal'] = (resultado['meta_ticket'] / resultado['hc_ativo'].replace(0,np.nan)).round(1) ## META ATENDIMENTO POR OPERADOR
    resultado['volume_vendas_ideal'] = (resultado['meta_ies'] / resultado['hc_ativo'].replace(0,np.nan)).round(1) ## META VENDAS POR OPERADOR
    resultado['volume_atual'] = (resultado['em_atendimento'] / resultado['hc_ativo'].replace(0,np.nan)).round(1) ## VOLUME ATUAL DE ATENDIMENTO POR OPERADOR
    resultado['volume_vendas_atual'] = (resultado['vendas'] / resultado['hc_ativo'].replace(0, np.nan)).round(1) ## VOLUME ATUAL DE VENDAS POR OPERADOR
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
        resultado['vendas'] / resultado['meta_ies'] * 100
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

    resultado['conversao_historico'] = (
        resultado['vendas_historico'] / resultado['encerrado_historico']
    ).fillna(0)

    resultado["projecao_vendas"] = ((resultado["vendas"] / horas_trabalhadas) * horas_totais).astype(int)
    
    resultado['projecao_encerrado'] = ((resultado['encerrado'] / horas_trabalhadas) * horas_totais).round(1)

    resultado["projecao_vendas2"] = ((resultado['conversao_historico'] * resultado['projecao_encerrado'])).round(0)

    

    resultado['perc_meta_encerrado'] = (resultado['projecao_encerrado'] / resultado['meta_ticket'] * 100)

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
        "meta_conversao",
        "conversao",
        "gap_conversao",
        "situacao_conversao",
        "situacao_fila",
        "situacao_atendimento",
        "desvio",
        "situacao_encerrado",
        "desvio_encerrado",
        "projecao_encerrado",
        "projecao_vendas",
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
            "projecao_vendas": 0,
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