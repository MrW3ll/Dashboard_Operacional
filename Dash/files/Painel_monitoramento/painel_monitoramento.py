"""
app.py — Painel de Acompanhamento Operacional
Exibe KPIs de tickets por equipe em cards individuais.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
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
st_autorefresh(interval= 60 * 60 * 1000, key='autorefresh' )  # Atualiza a cada 60 minutos
# ─────────────────────────────────────────────
#  ESTILO DOS CARDS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    
    /* ── Fundo global fixo dark ── */
    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > .main,
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    section.main > div {
        background-color: #0e1117 !important;
        color: #fafafa !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161b27 !important;
    }

    /* Header/toolbar do Streamlit */
    [data-testid="stHeader"] {
        background-color: #0e1117 !important;
    }

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
    .kpi-label  { 
            font-size: 13.5px; 
            color: #e6e6e6; 
            margin-bottom: 4px; 
            text-transform: uppercase; 
            font-weight: 500;
        }
    .kpi-value  { 
            font-size: 28px; 
            font-weight: 700; 
            color: #fff; 
        }
    .kpi-subtitle { 
            font-size: 12.5px;
            color: #e6e6e6; 
            margin-top: 4px;
            font-weight: 700;
        }

    /* Cores por status */
    .card-fila-verde {
            background: #14532d;
            border: 2px solid #22c55e;
    }
    .card-fila-amarelo{
            background: #78350f;
            border: 2px solid #facc15;
    }
    .card-fila-vermelho{
            background: #7f1d1d;
            border: 2px solid #DC143C;
    }
            

    .card-encerrado {
            border-left: 5px solid #3b82f6; /* azul */
    }
    .card-encerrado-verde {
        border-left: 5px solid #3b82f6; /* azul */;
    }
    .card-encerrado-amarelo{
        border-left: 5px solid #78350f;
    }
    .card-encerrado-vermelho{
        border-left: 5px solid #7f1d1d;
    }




    .card-em_atendimento-verde {
        background: #14532d;
        border: 2px solid #22c55e;
    }
    .card-em_atendimento-amarelo{
        background: #78350f;
        border: 2px solid #facc15;
    }
    .card-em_atendimento-vermelho{
        background: #7f1d1d;
        border: 2px solid #ef4444;
    }
    
    .card-vendas-verde {
        background: #14532d;
        border: 2px solid #22c55e;
    }
    .card-vendas-amarelo{
        background: #78350f;
        border: 2px solid #facc15;
    }
    .card-vendas-vermelho{
        background: #7f1d1d;
        border: 2px solid #ef4444;
    }


    .card-conversao-verde {
        background: #14532d;
        border: 2px solid #22c55e;
    }
    .card-conversao-amarelo{
        background: #78350f;
        border: 2px solid #facc15;
    }
    .card-conversao-vermelho{
        background: #7f1d1d;
        border: 2px solid #ef4444;
    }
            
    .card-projecao  {
             border-left: 5px solid #7c3aed; /* roxo */ 
        }  

    .equipe-header {
        font-size: 20px;
        text-transform: uppercase;
        font-weight: 800;
        color: #fafafa;
        margin-bottom: 6px;
        padding-left: 2px;
    }
</style>
""", unsafe_allow_html=True)




# ─────────────────────────────────────────────
#  FUNÇÃO REUTILIZÁVEL: renderiza 1 equipe
# ─────────────────────────────────────────────
def render_header_equipe(ies: str) -> None:
    """Renderiza apenas o header (nome da IES + botão operadores)"""
    col_header, col_btn = st.columns([5, 1])
    with col_header:
        st.markdown(f'<div class="equipe-header">📋 {ies}</div>', unsafe_allow_html=True)
    with col_btn:
        st.write("")
        if st.button("👤", use_container_width=True, key=f"btn_operadores_{ies}", help=f"Ver operadores de {ies}"):
            # Armazenar IES no session_state e navegar
            st.session_state.ies_filtro = ies
            st.switch_page("pages/operadores.py")

def render_header_cards() -> None:
    """Renderiza apenas os títulos dos cards na parte superior"""
    cards_labels = [
        "📥 Fila",
        "💬 Em Atendimento",
        "✅ Encerrado",
        "💰 Vendas",
        "🎯 Conversão",
        "📈 Projeção",
    ]
    
    colunas = st.columns(6, gap="small")
    for col, label in zip(colunas, cards_labels):
        with col:
            st.markdown(f"""
            <div style="text-align: center; font-size: 16px; font-weight: 600; color: #aaa; text-transform: uppercase; margin-bottom: 8px;">
                {label}
            </div>""", unsafe_allow_html=True)

def render_cards_equipe(linha: pd.Series) -> None:
    """Renderiza apenas os cards de métricas da equipe (sem labels)"""
    cards = [
        ("fila",                  "📥 Fila",             "card-fila"),
        ("em_atendimento",        "💬 Em Atendimento",   "card-em_atendimento"),
        ("encerrado",             "✅ Encerrado",        "card-encerrado"),
        ("vendas",                "💰 Vendas",           "card-vendas"),
        ("conversao",             "🎯 Conversão",        "card-conversao"),  
        ("projecao_vendas",       "📈 Projeção",         "card-projecao"),
    ]

    colunas = st.columns(6, gap="small")

    for col, (chave, label, css_class) in zip(colunas, cards):
        valor = linha[chave]

        legenda = ""

        if chave == 'vendas':
            situacao_vendas = linha['situacao_vendas']
            if situacao_vendas == 'Verde':
                css_class = 'card-vendas-verde'
            elif situacao_vendas == 'Amarelo':
                css_class = 'card-vendas-amarelo'
            else:
                css_class = 'card-vendas-vermelho'

            perc_meta_vendas = linha['perc_meta_vendas']
            if perc_meta_vendas > 100:
                legenda = f'+{perc_meta_vendas:.1f}% acima da meta'
            elif perc_meta_vendas < 100:
                legenda = f'{perc_meta_vendas:.1f}% abaixo da meta'
            else:
                legenda = 'No ideal'

        if chave == 'fila':
            fila = linha['fila']
            if fila <= 10:
                css_class = 'card-fila-verde'
            elif fila <= 25:
                css_class = 'card-fila-amarelo'
            else:
                css_class = 'card-fila-vermelho'

        if chave == 'encerrado':
            projecao_encerrado = linha['projecao_encerrado']
            situacao_encerrado = linha['situacao_encerrado']

            if projecao_encerrado > 100:
                legenda = f"+{projecao_encerrado:.0f}% acima da meta"
            elif projecao_encerrado < 100:
                legenda = f"-{projecao_encerrado:.0f}% abaixo da meta"
            else:
                legenda = "No ideal"   
            
            if situacao_encerrado == 'Verde':
                css_class = 'card-encerrado-verde'
            elif situacao_encerrado == 'Amarelo':
                css_class = 'card-encerrado-amarelo'
            else:
                css_class = 'card-encerrado-vermelho'

        if chave == 'em_atendimento':

            desvio = linha['desvio']

            if desvio > 0:
                legenda = f"+{desvio:.1f}% acima do ideal"
            elif desvio < 0:
                legenda = f"{desvio:.1f}% abaixo do ideal"
            else:
                legenda = "No ideal"    

            
            situacao = linha['situacao_atendimento']

            if situacao == 'Verde':
                css_class = 'card-em_atendimento-verde'
            elif situacao == 'Amarelo':
                css_class = 'card-em_atendimento-amarelo'
            else:
                css_class = 'card-em_atendimento-vermelho'


        # Formatação por tipo de campo          ← estava faltando o elif
        if chave == "projecao_vendas":

            

            valor_fmt = linha['projecao_vendas'] if linha['projecao_vendas'] > 0 else "0"
            
            


        elif chave == "conversao":
            valor_fmt = f"{valor:.1f}%"
            gap_conversao = linha['gap_conversao']

            if gap_conversao > 0:
                legenda = f"+{gap_conversao:.1f}% acima da meta"
            elif gap_conversao < 0:
                legenda = f"{gap_conversao:.1f}% abaixo da meta"
            else:
                legenda = "No ideal"
            
            situacao_conversao = linha['situacao_conversao']
            if situacao_conversao == 'Verde':
                css_class = 'card-conversao-verde'
            elif situacao_conversao == 'Amarelo':
                css_class = 'card-conversao-amarelo'
            else:
                css_class = 'card-conversao-vermelho'


        else:
            valor_fmt = str(int(valor))

        with col:
            st.markdown(f"""
            <div class="kpi-card {css_class}">
                <div class="kpi-value">{valor_fmt}</div>
                <div class="kpi-subtitle">{legenda}</div>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  CABEÇALHO DO PAINEL
# ─────────────────────────────────────────────
col_titulo, col_operadores, col_atualizar = st.columns([4, 1, 1])

with col_titulo:
    st.title("📊 Painel de Monitoramento Operacional")
    st.caption("Acompanhamento de tickets por equipe")

with col_operadores:
    st.write("")
    if st.button("👤 Operadores", use_container_width=True):
        st.switch_page(Path("pages")/"operadores.py")

with col_atualizar:
    st.write("")
    if st.button("🔄 Atualizar", use_container_width=True):
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
#  RENDERIZAÇÃO: 2 blocos (esquerda e direita)
# ─────────────────────────────────────────────
st.divider()

linhas_df = [row for _, row in df_filtrado.iterrows()]

# Dividir equipes em dois blocos: esquerda e direita
meio = len(linhas_df) // 2
equipes_esq = linhas_df[:meio]
equipes_dir = linhas_df[meio:]

col_esq, col_dir = st.columns(2, gap="large")

# ─── BLOCO ESQUERDO ───
with col_esq:
    render_header_cards()
    st.write("")
    for equipe in equipes_esq:
        render_header_equipe(equipe["ies"])
        render_cards_equipe(equipe)
        st.write("")

# ─── BLOCO DIREITO ───
with col_dir:
    render_header_cards()
    st.write("")
    for equipe in equipes_dir:
        render_header_equipe(equipe["ies"])
        render_cards_equipe(equipe)
        st.write("")