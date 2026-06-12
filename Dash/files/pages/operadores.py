"""
pages/operadores.py — Performance Individual de Operadores
"""
import streamlit as st

import sys
import pandas as pd
import datetime as dt
import engine as engs
import numpy as np

from sqlalchemy import text
from pathlib import Path

sys.path.insert(0, str(Path("C:/Users/wconceicao/OneDrive - Grupo A Educação SA/Área de Trabalho/Projetos")))



st.set_page_config(page_title="Performance Operadores", page_icon="👤", layout="wide")

# ─────────────────────────────────────────────
#  ESTILO
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }

    .op-card {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 14px 12px;
        text-align: center;
        border-left: 4px solid #555;
        height: 90px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .op-label { font-size: 14px; color: #aaa; text-transform: uppercase; margin-bottom: 3px; }
    .op-value { font-size: 24px; font-weight: 700; color: #fff; }

    .card-enc   { border-left-color: #3b82f6; }
    .card-venda { border-left-color: #22c55e; }
    .card-conv  { border-left-color: #f43f5e; }
    .card-atend { border-left-color: #f0a500; }

    .op-nome {
        font-size: 17.5px;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 5px;
        padding-left: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  MOCK — substituir por query real quando pronto
# ─────────────────────────────────────────────
def carregar_dados_operadores() -> dict[str, pd.DataFrame]:
    eng = engs.get_engine()

    queries = [
        'painel_tickets_operadores.sql',
        'painel_vendas_operadores.sql'
    ]

    resultado = {}

    try:
        with eng.connect() as conn:
            conexoes = eng.pool.checkedout()
            print(f'conexoes abertas: {conexoes}')
            for nome_query in queries:
                chave = nome_query.replace(".sql","")
                try:
                    query = text(engs.load_query(nome_query))
                    resultado[chave] = pd.read_sql(query,conn)
                except Exception as e:
                    print(f'Erro ao carregar "{nome_query}": {e}')
                    resultado[chave] = pd.DataFrame()
    finally:
        conexoes = eng.pool.checkedout()
        conn.close()
        eng.dispose()
        if conexoes > 0:
            print(f'{conexoes} em aberto... verificar...')
        else:
            print(f'{conexoes} em aberto... conexoes encerradas...')

    return resultado

def tratar_dados(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    df_tickets = raw['painel_tickets_operadores']
    df_vendas = raw['painel_vendas_operadores']

    # Renomear colunas do DF de tickets para padronizar
    df_tickets = df_tickets.rename(columns={
        'Ies': 'ies',
        'atendente': 'operador',
        'Em Atendimento': 'em_atendimento',
        'Encerrado': 'encerrado',
        'Fila': 'fila'
    })

    # Renomear colunas do DF de vendas
    df_vendas = df_vendas.rename(columns={
        'ies_name': 'ies',
        'operator_user': 'operador',
        'vendas': 'vendas'
    })

    # Merge: tickets com vendas (left join em tickets)
    df_merged = df_tickets.merge(
        df_vendas[['ies', 'operador', 'vendas']],
        on=['ies', 'operador'],
        how='left'
    )

    # Preencher vendas NaN com 0
    df_merged['vendas'] = df_merged['vendas'].fillna(0).astype(int)

    # Calcular conversão (vendas / encerrado * 100)
    df_merged['conversao'] = (
        (df_merged['vendas'] / df_merged['encerrado'] * 100)
        .where(df_merged['encerrado'] > 0, 0)
    )

    # Selecionar apenas colunas necessárias
    df_final = df_merged[['ies', 'operador', 'em_atendimento', 'encerrado', 'fila', 'vendas', 'conversao']]

    return df_final

# ─────────────────────────────────────────────
#  CABEÇALHO
# ─────────────────────────────────────────────
col_titulo, col_voltar = st.columns([5, 1])

with col_titulo:
    st.title("👤 Performance Individual")
    st.caption("Acompanhamento por operador — performance em tempo real")

with col_voltar:
    st.write("")
    if st.button("⬅️ Voltar ao Painel", use_container_width=True):
        st.switch_page("painel_monitoramento.py")


# ─────────────────────────────────────────────
#  CARREGAMENTO
# ─────────────────────────────────────────────
dados_brutos = carregar_dados_operadores()
df = tratar_dados(dados_brutos)


# ─────────────────────────────────────────────
#  FILTROS LATERAIS
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("Filtros")

    equipes   = ["Todas"] + sorted(df["ies"].unique().tolist())
    
    # Verificar se veio IES via session_state (do painel)
    index_default = 0
    if "ies_filtro" in st.session_state and st.session_state.ies_filtro in equipes:
        index_default = equipes.index(st.session_state.ies_filtro)
        # Limpar session_state após usar
        del st.session_state.ies_filtro
    
    equipe_sel = st.selectbox("Equipe:", equipes, index=index_default)

    busca = st.text_input("Buscar operador:", placeholder="Digite o nome...")

df_filtrado = df.copy()

if equipe_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["ies"] == equipe_sel]

if busca:
    df_filtrado = df_filtrado[
        df_filtrado["operador"].str.contains(busca, case=False, na=False)
    ]


# ─────────────────────────────────────────────
#  TOTALIZADORES
# ─────────────────────────────────────────────
st.divider()

t1, t2, t3, t4, t5 = st.columns(5)
t1.metric("👥 Operadores",       len(df_filtrado))
t2.metric("💬 Em atendimento",   int(df_filtrado["em_atendimento"].sum()))
t3.metric("✅ Encerrados",       int(df_filtrado["encerrado"].sum()))
t4.metric("💰 Vendas",           int(df_filtrado["vendas"].sum()))


enc_total  = df_filtrado["encerrado"].sum()
conv_geral = (df_filtrado["vendas"].sum() / enc_total * 100) if enc_total > 0 else 0
t5.metric("🎯 Conversão Geral",  f"{conv_geral:.1f}%")

st.divider()


# ─────────────────────────────────────────────
#  RENDERIZAÇÃO: 3 operadores por linha
# ─────────────────────────────────────────────
def render_operador(row: pd.Series) -> None:
    st.markdown(
        f'<div class="op-nome">👤 {row["operador"]} '
        f'<span style="color:#888;font-size:11px;">({row["ies"]})</span></div>',
        unsafe_allow_html=True,
    )

    cards = [
        ("em_atendimento", "💬 Em Atend.",  "card-atend"),
        ("encerrado",      "✅ Encerrado",  "card-enc"),
        ("vendas",         "💰 Vendas",     "card-venda"),
        ("conversao",      "🎯 Conversão",  "card-conv"),
    ]

    cols = st.columns(4, gap="small")
    for col, (chave, label, css) in zip(cols, cards):
        valor = row[chave]
        fmt   = f"{valor:.1f}%" if chave == "conversao" else str(int(valor))
        with col:
            st.markdown(f"""
            <div class="op-card {css}">
                <div class="op-label">{label}</div>
                <div class="op-value">{fmt}</div>
            </div>""", unsafe_allow_html=True)


operadores = [row for _, row in df_filtrado.iterrows()]

if not operadores:
    st.info("Nenhum operador encontrado com os filtros selecionados.")
else:
    for i in range(0, len(operadores), 3):
        cols = st.columns(3, gap="large")
        for j, col in enumerate(cols):
            if i + j < len(operadores):
                with col:
                    render_operador(operadores[i + j])
        st.write("")