"""
app.py — Painel de Acompanhamento Operacional
Exibe KPIs de tickets por equipe em cards individuais.
"""

import streamlit as st
import pandas as pd
from data import carregar_dados
from streamlit_autorefresh import st_autorefresh


# ─────────────────────────────────────────────
#  CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Painel Operacional",
    page_icon="📊",
    layout="wide",
)
st_autorefresh(interval=60 * 1000, key='autorefresh')  # Atualiza a cada 60 segundos
# ─────────────────────────────────────────────
#  ESTILO DOS CARDS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }

    .kpi-card {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 16px 12px;
        text-align: center;
        border-left: 4px solid #555;
        height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .kpi-label  { font-size: 12px; color: #aaa; margin-bottom: 4px; text-transform: uppercase; }
    .kpi-value  { font-size: 28px; font-weight: 700; color: #fff; }

    /* Cores por status */
    .card-fila           { border-left-color: #f0a500; }
    .card-em_atendimento { border-left-color: #3b82f6; }
    .card-encerrado      { border-left-color: #6b7280; }
    .card-vendas         { border-left-color: #22c55e; }
    .card-conversao      { border-left-color: #f43f5e; }  /* ← estava faltando */
    .card-projecao       { border-left-color: #a855f7; }

    .equipe-header {
        font-size: 15px;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 6px;
        padding-left: 2px;
    }
</style>
""", unsafe_allow_html=True)




# ─────────────────────────────────────────────
#  FUNÇÃO REUTILIZÁVEL: renderiza 1 equipe
# ─────────────────────────────────────────────
def render_equipe(linha: pd.Series) -> None:
    cards = [
        ("fila",           "🟡 Fila",            "card-fila"),
        ("em_atendimento", "🔵 Em Atendimento",  "card-em_atendimento"),
        ("encerrado",      "⚫ Encerrado",        "card-encerrado"),
        ("vendas",         "🟢 Vendas",           "card-vendas"),
        ("conversao",      "📈 Conversão",        "card-conversao"),  # ← emoji diferenciado
        ("projecao",       "🟣 Projeção Vendas",  "card-projecao"),
    ]

    st.markdown(f'<div class="equipe-header">📋 {linha["ies"]}</div>', unsafe_allow_html=True)

    colunas = st.columns(6, gap="small")

    for col, (chave, label, css_class) in zip(colunas, cards):
        valor = linha[chave]

        # Formatação por tipo de campo          ← estava faltando o elif
        if chave == "projecao":
            valor_fmt = linha['projecao'] if linha['projecao'] > 0 else "0"
        elif chave == "conversao":
            valor_fmt = f"{valor:.1f}%"
        else:
            valor_fmt = str(int(valor))

        with col:
            st.markdown(f"""
            <div class="kpi-card {css_class}">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{valor_fmt}</div>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  CABEÇALHO DO PAINEL
# ─────────────────────────────────────────────
col_titulo, col_atualizar = st.columns([5, 1])

with col_titulo:
    st.title("📊 Painel de Monitoramento Operacional")
    st.caption("Acompanhamento de tickets por equipe")

with col_atualizar:
    st.write("")
    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ─────────────────────────────────────────────
#  CARREGAMENTO DOS DADOS
# ─────────────────────────────────────────────
##@st.cache_data(ttl=60)
def get_dados() -> pd.DataFrame:
    return carregar_dados()

df = get_dados()

# Indicador de fonte de dados
if df.empty:
    st.error("❌ Nenhum dado disponível!")
else:
    n_registros = len(df)
    st.caption(f"📈 {n_registros} equipes carregadas | Última atualização: {pd.Timestamp.now().strftime('%H:%M:%S')}")


# ─────────────────────────────────────────────
#  FILTRO LATERAL
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("Filtros")
    equipes_disponiveis = df["ies"].tolist()
    equipes_selecionadas = st.multiselect(
        label="Exibir equipes:",
        options=equipes_disponiveis,
        default=equipes_disponiveis,
    )


df_filtrado = df[df["ies"].isin(equipes_selecionadas)]


# ─────────────────────────────────────────────
#  RENDERIZAÇÃO: 2 equipes por linha
# ─────────────────────────────────────────────
st.divider()

linhas_df = [row for _, row in df_filtrado.iterrows()]

for i in range(0, len(linhas_df), 2):
    col_esq, col_dir = st.columns(2, gap="large")

    with col_esq:
        render_equipe(linhas_df[i])

    with col_dir:
        if i + 1 < len(linhas_df):
            render_equipe(linhas_df[i + 1])

    st.write("")