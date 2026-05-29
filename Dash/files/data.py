"""
data.py — Carregamento de dados do painel
"""

import sys
import pandas as pd
from sqlalchemy import text
from pathlib import Path
import datetime as dt

##sys.path.insert(0, str(Path("C:/Users/wconceicao/OneDrive - Grupo A Educação SA/Área de Trabalho/Projetos")))

import engine as engs

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

    print(f"\n📊 Registros após merge: {len(resultado)}")

    # 4️⃣ Preenchimento e cálculos
    resultado["vendas"] = resultado["vendas"].fillna(0).astype(int)
    resultado["encerrado"] = resultado["encerrado"].fillna(1).astype(int)
    
    # Conversão (evita divisão por zero)
    resultado["conversao"] = (
        (resultado["vendas"] / resultado["encerrado"]) * 100
    ).fillna(0).round(1)
    
    # Projeção
    resultado["projecao"] = ((resultado["vendas"] / horas_trabalhadas) * horas_totais).astype(int)

    # 5️⃣ RETORNA APENAS AS 7 COLUNAS NECESSÁRIAS
    resultado = resultado[[
        "ies", 
        "fila", 
        "em_atendimento", 
        "encerrado", 
        "vendas", 
        "conversao",
        "projecao"
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