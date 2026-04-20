# =============================================================
# LIB'S NECESSARIAS
# =============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
import engine as engs  

from sqlalchemy import text
from streamlit_autorefresh import st_autorefresh

# =============================================================
# LIB'S NECESSARIAS
# =============================================================

# =============================================================
# CONEXÃO COM O BANCO DE DADOS
# =============================================================

try:
    qry_operacional = text(engs.load_qry('qry_olos.sql'))
    qry_vendas = text(engs.load_qry('qry_sispag.sql'))
    eng = engs.get_engine()
    df_operacional = pd.read_sql(qry_operacional, eng)
    df_vendas = pd.read_sql(qry_vendas, eng)
except Exception as e:
    print(f'Erro: {e}...')
    print(f'acionando engine secundaria...')
    eng = engs.get_engine_heavy()
    df_operacional = pd.read_sql(qry_operacional, eng)
    df_vendas = pd.read_sql(qry_vendas, eng)



df_vendas['data'] = pd.to_datetime(df_vendas['data'], errors='coerce')
df_operacional['data'] = pd.to_datetime(df_operacional['data'], errors='coerce')

# =============================================================
# CONEXÃO COM O BANCO DE DADOS
# =============================================================

# ── ATUALIZAÇÃO AUTOMÁTICA A CADA 5 MINUTOS ──
st_autorefresh(interval=5 * 60 * 1000, key="datarefresh")

st.set_page_config(page_title="SECAD | Resultado Geral", layout="wide")

# =============================================================
# ESTILOS VISUAIS (CSS) — não precisa mexer aqui
# =============================================================
st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background-color: #080b12 !important;
    font-family: 'DM Sans', sans-serif !important;
}

[data-testid="stMainBlockContainer"] { padding-top: 1rem; }

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #1e2540; border-radius: 4px; }

h1, h2, h3 {
    font-family: 'DM Sans', sans-serif !important;
    color: #f0f2f8 !important;
    font-weight: 700 !important;
    letter-spacing: -0.3px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #0e1221;
    border: 1px solid #1a2035 !important;
    border-radius: 12px !important;
    padding: 10px 16px !important;
}

[data-testid="stMetricLabel"] > div {
    font-size: 11px !important;
    font-weight: 500 !important;
    color: #9699a3 !important;
    letter-spacing: 0.6px !important;
    text-transform: uppercase;
}

[data-testid="stMetricValue"] > div {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 30px !important;
    font-weight: 700 !important;
    color: #6898f1 !important;
    letter-spacing: -0.5px;
}

[data-testid="stMetricDelta"] { display: none; }

[data-testid="column"] { padding: 0px 6px !important; }

[data-testid="column"] > div { height: fit-content !important; }

[data-testid="stVerticalBlock"] > div { align-items: flex-start !important; }

.js-plotly-plot .plotly .modebar { display: none !important; }

.ultima-atualizacao {
    font-size: 11px;
    color: #3d4560;
    margin-top: -0.3rem;
    margin-bottom: 1.4rem;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.3px;
}

.section-header {
    font-size: 14px;
    font-weight: 600;
    color: #e2e4eb;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    margin: 18px 0 10px 2px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.section-header::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #1a2035;
}

.kpi-card {
    background: transparent;
    border: none;
    padding: 4px 0px;
    position: relative;
    height: fit-content;
    align-self: flex-start;
}

.kpi-card-label {
    font-size: 14px;
    font-weight: 600;
    color: #9699a3;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    margin-bottom: 6px;
}

.kpi-card-value {
    font-family: 'DM Sans', sans-serif;
    font-size: 28px;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 6px;
    letter-spacing: -0.5px;
}

.kpi-card-value.red   { color: #f87171; }
.kpi-card-value.green { color: #4ade80; }
.kpi-card-value.blue  { color: #6898f1; }

.kpi-card-delta {
    font-size: 10px;
    font-family: 'JetBrains Mono', monospace;
    display: flex;
    align-items: center;
    gap: 3px;
}

.kpi-card-delta.neg { color: #f87171; }
.kpi-card-delta.pos { color: #4ade80; }

</style>
""", unsafe_allow_html=True)

# =============================================================
# FUNÇÕES AUXILIARES — não precisa mexer aqui
# =============================================================

def kpi_taxa(label: str, valor: float, delta: float) -> str:
    """Gera um card estilizado para métricas de taxa (%)."""
    cor      = "green" if delta >= 0 else "red"
    sinal    = "▲" if delta >= 0 else "▼"
    classe_d = "pos" if delta >= 0 else "neg"
    return f"""
    <div class="kpi-card {cor}">
        <div class="kpi-card-label">{label}</div>
        <div class="kpi-card-value {cor}">{valor:.2f}%</div>
        <div class="kpi-card-delta {classe_d}">{sinal} {abs(delta):.2f} pp vs média (5m)</div>
    </div>
    """

def section_header(titulo: str) -> str:
    """Gera um separador de seção com linha."""
    return f'<div class="section-header">{titulo}</div>'

def ultima_atualizacao(hora: str) -> str:
    """Gera o texto de última atualização."""
    return f'<div class="ultima-atualizacao">◎ última atualização &nbsp;{hora}</div>'

# =============================================================
# CONFIGURAÇÕES DOS GRÁFICOS — não precisa mexer aqui
# =============================================================

PLOTLY_LAYOUT_VENDAS = dict(
    showlegend=False,
    barmode='overlay',
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    height=360,
    margin=dict(t=60, b=10, l=0, r=0),
    font=dict(family='DM Sans, sans-serif', color="#f1f5ff"),
    yaxis=dict(visible=False, gridcolor='#ffffff'),
    xaxis=dict(
        title=None,
        tickfont=dict(size=16, color="#ffffff", family='Arial Black'),
        ticklen=0, showline=False, zeroline=False,
    ),
    uniformtext=dict(mode='hide', minsize=8),
    hoverlabel=dict(
        bgcolor='#ffffff', bordercolor='#1a2035',
        font=dict(color='#ffffff', size=15, family='Arial'),
    ),
)

PLOTLY_LAYOUT_ATENDIMENTO = dict(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    height=360,
    margin=dict(t=40, b=10, l=0, r=0),
    font=dict(family='DM Sans, sans-serif', color='#8892b0'),
    barmode='overlay',
    yaxis=dict(
        visible=False, gridcolor='#1a2035',
        showline=False, zeroline=False,
        tickfont=dict(size=11, color="#98a3ca"),
    ),
    xaxis=dict(
        title=None,
        tickfont=dict(size=15, color='#ffffff', family='Arial Black'),
        ticklen=0, showline=False, zeroline=False,
    ),
    legend=dict(
        orientation='h', yanchor='bottom', y=1.05,
        xanchor='center', x=0.5,
        font=dict(size=14, color="#878fac"),
        bgcolor='rgba(0,0,0,0)', borderwidth=0,
    ),
    hoverlabel=dict(
        bgcolor='#141b2d', bordercolor='#1a2035',
        font=dict(color='#c9d1e8', size=13, family='Arial'),
    ),
    hovermode='x unified',
)

# Cores das barras
BAR_COLOR_PRINCIPAL    = "#6898f1"       # azul principal
BAR_COLOR_OVERLAY      = "rgba(0,0,0,0)" # transparente (camada de qtd)
ATEND_COLOR_TENTATIVAS = "#4b7cf3"       # azul escuro
ATEND_COLOR_ATENDIDAS  = "#7b9ee8"       # azul claro


# =============================================================
# FILTROS (mantém todas as áreas disponíveis)
# =============================================================

areas_fin  = df_vendas['area'].unique().tolist()      if not df_vendas.empty     else []
areas_ops  = df_operacional['area'].unique().tolist() if not df_operacional.empty else []

df_filtrado             = df_vendas[df_vendas['area'].isin(areas_fin)]             if not df_vendas.empty     else pd.DataFrame()
df_operacional_filtrado = df_operacional[df_operacional['area'].isin(areas_ops)]   if not df_operacional.empty else pd.DataFrame()


# =============================================================
# CABEÇALHO
# =============================================================

st.markdown(
    '<h1 style="font-size:22px;font-weight:700;margin-bottom:4px;">📊 SECAD | Monitor Operacional</h1>',
    unsafe_allow_html=True
)
st.markdown(
    ultima_atualizacao(datetime.datetime.now().strftime('%H:%M:%S')),
    unsafe_allow_html=True
)


# =============================================================
# DATAS BASE
# =============================================================

hoje = pd.to_datetime(datetime.datetime.now().date())

df_financeiro_hoje  = df_filtrado[df_filtrado['data'].dt.normalize() == hoje]
df_operacional_hoje = df_operacional_filtrado.loc[
    df_operacional_filtrado['data'].dt.normalize() == hoje
].copy()


# =============================================================
# MÉDIAS HISTÓRICAS (últimos 5 meses, excluindo hoje)
# =============================================================

# Taxa de Localização histórica
df_hist = df_operacional_filtrado.loc[
    (df_operacional_filtrado['data'] >= hoje - pd.DateOffset(months=5)) &
    (df_operacional_filtrado['data'] < hoje)
].copy()
df_hist['mes'] = df_hist['data'].dt.to_period('M')
df_hist_mensal = df_hist.groupby('mes', as_index=False).agg(
    tentativas=('tentativas', 'sum'),
    atendidas=('atendidas', 'sum')
)
df_hist_mensal['tx_loc'] = df_hist_mensal['atendidas'] / df_hist_mensal['tentativas'] * 100
taxa_hist = df_hist_mensal['tx_loc'].mean()

# Taxa de Conversão histórica
df_fin_hist = df_filtrado.loc[
    (df_filtrado['data'] >= hoje - pd.DateOffset(months=5)) &
    (df_filtrado['data'] < hoje)
].copy()
df_fin_hist['mes'] = df_fin_hist['data'].dt.to_period('M')
df_fin_hist_mensal = df_fin_hist.groupby('mes', as_index=False).agg(qtd_vendas=('qtd_vendas', 'sum'))
df_fin_hist_mensal = df_fin_hist_mensal.merge(df_hist_mensal[['mes', 'atendidas']], how='left', on='mes')
df_fin_hist_mensal['tx_conv'] = df_fin_hist_mensal['qtd_vendas'] / df_fin_hist_mensal['atendidas'] * 100
conv_hist = df_fin_hist_mensal['tx_conv'].mean()


# =============================================================
# DASHBOARD PRINCIPAL
# =============================================================

if not df_filtrado.empty:

    inicio_mes = hoje.replace(day=1).normalize()
    fim_mes    = hoje.normalize()

    # ── Dados do mês atual ──
    df_financeiro_mes = df_filtrado[
        (df_filtrado['data'].dt.normalize() >= inicio_mes) &
        (df_filtrado['data'].dt.normalize() <= fim_mes)
    ]
    hist_mes = df_operacional_filtrado[
        (df_operacional_filtrado['data'].dt.normalize() >= inicio_mes) &
        (df_operacional_filtrado['data'].dt.normalize() <= fim_mes)
    ]

    ven_mes          = int(df_financeiro_mes['qtd_vendas'].sum())
    tent_mes         = int(hist_mes['tentativas'].sum())
    atend_mes        = int(hist_mes['atendidas'].sum())
    vendas_mes_total = df_financeiro_mes['qtd_vendas'].sum()
    valor_mes_total  = df_financeiro_mes['total_valor'].sum()
    ticket_mes       = (valor_mes_total / vendas_mes_total) if vendas_mes_total > 0 else 0
    tx_loc_mes       = (atend_mes / tent_mes * 100)         if tent_mes          > 0 else 0
    tx_conv_mes      = (ven_mes   / atend_mes * 100)        if atend_mes         > 0 else 0
    dif_loc_mes      = tx_loc_mes  - taxa_hist
    dif_conv_mes     = tx_conv_mes - conv_hist

    # ── Dados de hoje ──
    financeiro_hoje_agg = df_financeiro_hoje.groupby('area').agg(
        receita=('total_valor', 'sum'),
        vendas=('qtd_vendas', 'sum')
    ).reset_index()

    vendas_total      = financeiro_hoje_agg['vendas'].sum()
    receita_total     = financeiro_hoje_agg['receita'].sum()
    ticket_medio_hoje = (receita_total / vendas_total) if vendas_total > 0 else 0

    tentativas = int(df_operacional_hoje['tentativas'].sum())
    atendidas  = int(df_operacional_hoje['atendidas'].sum())
    drop       = int(df_operacional_hoje['drop'].sum())
    hangup     = int(df_operacional_hoje['hangup'].sum())
    taxa       = (atendidas  / tentativas   * 100) if tentativas > 0 else 0
    tx_conv    = (vendas_total / atendidas  * 100) if atendidas  > 0 else 0
    dif_loc    = taxa    - taxa_hist
    dif_conv   = tx_conv - conv_hist


    # ── SEÇÃO: PERFORMANCE MENSAL ──────────────────────────────

    with st.container(border=False):
        st.markdown(section_header("📈 Performance Mensal"), unsafe_allow_html=True)

        m1, m2, m3, m4, m5 = st.columns([1.5, 2, 2, 2, 5], gap='small')

        with m1:
            st.metric('Vendas', int(vendas_mes_total))
        with m2:
            st.metric('Receita', f"R${valor_mes_total:,.2f}")
        with m3:
            st.metric('Ticket Médio', f"R$ {ticket_mes:,.2f}")
        with m4:
            st.markdown(kpi_taxa("Taxa de Localização", tx_loc_mes, dif_loc_mes), unsafe_allow_html=True)
        with m5:
            st.markdown(kpi_taxa("Taxa de Conversão", tx_conv_mes, dif_conv_mes), unsafe_allow_html=True)


    # ── SEÇÃO: RESULTADO DE HOJE ───────────────────────────────

    st.markdown(
        section_header(f'Resultado Operacional — {hoje.strftime("%d/%m/%Y")}'),
        unsafe_allow_html=True
    )

    with st.container(border=False):

        # Linha 1: Vendas / Receita / Ticket / Taxa de Conversão
        col_v, col_r, col_t, col_conv,spacer = st.columns([1.5, 2, 2, 2, 6], gap='xsmall')

        with col_v:
            st.metric('Vendas', int(vendas_total))
        with col_r:
            st.metric('Receita', f"R$ {receita_total:,.2f}")
        with col_t:
            st.metric('Ticket Médio', f"R$ {ticket_medio_hoje:,.2f}")
        with col_conv:
            st.markdown(kpi_taxa("Taxa de Conversão", tx_conv, dif_conv), unsafe_allow_html=True)

        # Linha 2: Tentativas / Atendidas / Taxa de Localização / Overflow / Drop
        col_tent, col_aten, col_taxa, col_hu, col_drop = st.columns(
            [1.5, 2, 2, 2, 6], gap='xsmall'
        )

        with col_tent:
            st.metric('Tentativas', tentativas)
        with col_aten:
            st.metric('Atendidas', atendidas)
        with col_taxa:
            st.markdown(kpi_taxa("Taxa de Localização", taxa, dif_loc), unsafe_allow_html=True)
        with col_hu:
            st.metric("Overflow Calls", hangup)
        with col_drop:
            st.metric("Drop Calls", drop)


    # ── GRÁFICOS ───────────────────────────────────────────────

    col_graf_vendas, col_graf_atend = st.columns([1, 1], gap='medium', border=True)

    # Gráfico de Vendas por Área
    with col_graf_vendas:
        st.subheader("💰 Venda por Área")

        fig = go.Figure()

        # Barra principal: receita (colorida)
        fig.add_trace(go.Bar(
            x=financeiro_hoje_agg['area'],
            y=financeiro_hoje_agg['receita'],
            text=financeiro_hoje_agg['receita'],
            texttemplate='<b>R$ %{text:,.2f}</b>',
            textposition='outside',
            textfont=dict(size=13, color="#ffffff", family='Arial Black'),
            marker_color=BAR_COLOR_PRINCIPAL,
            marker_line=dict(color="#3d6fd4", width=1),
            name='Receita',
        ))

        # Barra invisível: apenas mostra a quantidade de vendas dentro da barra
        fig.add_trace(go.Bar(
            x=financeiro_hoje_agg['area'],
            y=financeiro_hoje_agg['receita'],  # mesma altura da barra principal
            text=financeiro_hoje_agg['vendas'],
            texttemplate='%{text}',
            textposition='inside',
            insidetextanchor='start',
            textfont=dict(size=14, color="#ffffff", family='Arial Black'),
            marker_color=BAR_COLOR_OVERLAY,
            showlegend=False,
            hoverinfo='skip',
        ))

        fig.update_layout(**PLOTLY_LAYOUT_VENDAS)

        # Garante que o texto acima das barras não seja cortado
        if not financeiro_hoje_agg.empty:
            max_val = financeiro_hoje_agg['receita'].max()
            fig.update_yaxes(range=[0, max_val * 1.30])

        st.plotly_chart(fig, use_container_width=True)

    # Gráfico de Atendimentos por Área
    with col_graf_atend:
        df_operacional_hoje['tx_loc'] = (
            df_operacional_hoje['atendidas'] /
            df_operacional_hoje['tentativas'] * 100
        ).round(2)

        st.subheader("📞 Atendimentos por Área")

        fig2 = go.Figure()

        # Barra de tentativas (azul escuro)
        fig2.add_trace(go.Bar(
            x=df_operacional_hoje['area'],
            y=df_operacional_hoje['tentativas'],
            text=df_operacional_hoje['tentativas'],
            texttemplate='<b>%{text}</b>',
            textposition='outside',
            textfont=dict(size=13, color='#c9d1e8', family='DM Sans'),
            marker_color=ATEND_COLOR_TENTATIVAS,
            name='Tentativas',
            customdata=df_operacional_hoje['tx_loc'],
            hovertemplate=(
                '<b>Área:</b> %{x}<br>'
                '<b>Tentativas:</b> %{y}<br>'
                '<b>Tx Localização:</b> %{customdata}%<extra></extra>'
            ),
        ))

        # Barra de atendidas (azul claro, sobreposta)
        fig2.add_trace(go.Bar(
            x=df_operacional_hoje['area'],
            y=df_operacional_hoje['atendidas'],
            text=df_operacional_hoje['atendidas'],
            texttemplate='%{text}',
            textposition='outside',
            textfont=dict(size=13, color="#ffffff", family='DM Sans'),
            marker_color=ATEND_COLOR_ATENDIDAS,
            opacity=0.85,
            name='Atendidas',
            customdata=df_operacional_hoje[['tx_loc']],
            hovertemplate=(
                '<b>Área:</b> %{x}<br>'
                '<b>Atendidas:</b> %{y}<br>'
                '<b>Tx Localização:</b> %{customdata[0]}%<extra></extra>'
            ),
        ))

        fig2.update_layout(**PLOTLY_LAYOUT_ATENDIMENTO)
        st.plotly_chart(fig2, use_container_width=True)

else:
    st.warning("Aguardando dados de vendas para o dia de hoje...")