import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Dashboard EPTRAN",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização
DARK_FONT = dict(color="#212529")

@st.cache_data(ttl=3600)
def load_data():
    # Ajuste o caminho ou método de carregamento conforme o seu projeto
    file_path = "dados_eptran.xlsx" if os.path.exists("dados_eptran.xlsx") else "dados_eptran.csv"
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    # 1. Padronização de Colunas
    df.columns = df.columns.str.strip()

    # Mapeamento de colunas cruciais
    col_map = {
        'Bairro': 'Bairro_Clean',
        'bairro': 'Bairro_Clean',
        'Programa': 'Programa_Clean',
        'programa': 'Programa_Clean',
        'Ação': 'Acao_Clean',
        'acao': 'Acao_Clean',
        'Pessoas Impactadas': 'Pessoas_Impactadas',
        'Impacto': 'Pessoas_Impactadas'
    }
    df.rename(columns=col_map, inplace=True)

    # Garantir existência das colunas limpas
    if 'Bairro_Clean' not in df.columns:
        df['Bairro_Clean'] = 'Não Informado'
    if 'Programa_Clean' not in df.columns:
        df['Programa_Clean'] = 'Não Informado'
    if 'Acao_Clean' not in df.columns:
        df['Acao_Clean'] = 'Geral'

    df['Bairro_Clean'] = df['Bairro_Clean'].fillna('Não Informado').astype(str).str.strip()
    df['Programa_Clean'] = df['Programa_Clean'].fillna('Não Informado').astype(str).str.strip()
    df['Acao_Clean'] = df['Acao_Clean'].fillna('Geral').astype(str).str.strip()

    # 2. Tratamento de Pessoas Impactadas
    if 'Pessoas_Impactadas' in df.columns:
        df['Pessoas_Impactadas'] = pd.to_numeric(df['Pessoas_Impactadas'], errors='coerce').fillna(0)
    else:
        df['Pessoas_Impactadas'] = 1

    # 3. Tratamento de Datas
    if 'Data' in df.columns:
        df['Data_Parsed'] = pd.to_datetime(df['Data'], errors='coerce')
    else:
        df['Data_Parsed'] = pd.Timestamp('2022-01-01')

    # Tratar datas nulas
    min_valid_date = df['Data_Parsed'].dropna().min()
    if pd.isna(min_valid_date):
        min_valid_date = pd.Timestamp('2022-01-01')
    df['Data_Parsed'] = df['Data_Parsed'].fillna(min_valid_date)

    df['Ano'] = df['Data_Parsed'].dt.year

    return df

df = load_data()

# --------------------------------------------------------------------
# SIDEBAR / LOGO & FILTROS
# --------------------------------------------------------------------
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", width="stretch")
elif os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", width="stretch")

st.sidebar.title("Filtros de Análise")

# Métrica Principal
metrica = st.sidebar.radio(
    "Métrica Principal",
    ["Pessoas Impactadas", "Nº de Eventos / Lançamentos"]
)

# Filtro por Período
min_date = df['Data_Parsed'].min().date()
max_date = df['Data_Parsed'].max().date()

dates_input = st.sidebar.date_input(
    "Período de Execução",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

if isinstance(dates_input, (list, tuple)) and len(dates_input) == 2:
    start_date, end_date = dates_input
else:
    start_date, end_date = min_date, max_date

# Filtros Dropdown
bairros_unicos = ["Todos os Bairros"] + sorted(list(df['Bairro_Clean'].unique()))
sel_bairro = st.sidebar.selectbox("Bairro", bairros_unicos)

programas_unicos = ["Todos os Programas"] + sorted(list(df['Programa_Clean'].unique()))
sel_programa = st.sidebar.selectbox("Programa", programas_unicos)

acoes_unicas = ["Todas as Ações"] + sorted(list(df['Acao_Clean'].unique()))
sel_acao = st.sidebar.selectbox("Ação / Projeto", acoes_unicas)

# --------------------------------------------------------------------
# APLICAÇÃO DOS FILTROS
# --------------------------------------------------------------------
mask = (df['Data_Parsed'].dt.date >= start_date) & (df['Data_Parsed'].dt.date <= end_date)

if sel_bairro != "Todos os Bairros":
    mask &= (df['Bairro_Clean'] == sel_bairro)

if sel_programa != "Todos os Programas":
    mask &= (df['Programa_Clean'] == sel_programa)

if sel_acao != "Todas as Ações":
    mask &= (df['Acao_Clean'] == sel_acao)

df_filtered = df[mask]

# --------------------------------------------------------------------
# CABEÇALHO & KPIs
# --------------------------------------------------------------------
st.title("Dashboard EPTRAN — Execuções de Trânsito")
st.caption("Prefeitura Municipal de Joinville | Série Histórica (2022–2026)")

col1, col2, col3, col4 = st.columns(4)

if metrica == "Pessoas Impactadas":
    val_impacto = int(df_filtered['Pessoas_Impactadas'].sum())
    lbl_impacto = "Pessoas Impactadas (Total)"
else:
    val_impacto = len(df_filtered)
    lbl_impacto = "Total de Lançamentos"

tot_eventos = len(df_filtered)

bairro_top = df_filtered['Bairro_Clean'].mode().values[0] if not df_filtered.empty else "-"
prog_top = df_filtered['Programa_Clean'].mode().values[0] if not df_filtered.empty else "-"

with col1:
    st.metric(lbl_impacto, f"{val_impacto:,}".replace(",", "."))
with col2:
    st.metric("Total de Ações/Eventos", f"{tot_eventos:,}".replace(",", "."))
with col3:
    st.metric("Bairro Destaque", bairro_top)
with col4:
    st.metric("Programa Destaque", prog_top)

st.divider()

# --------------------------------------------------------------------
# VISUALIZAÇÃO
# --------------------------------------------------------------------
if df_filtered.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
else:
    st.subheader(f"Diagrama de Sankey — Fluxo de Atendimento ({metrica})")

    # Exemplo simples de Sankey de fluxo (Programa -> Bairro)
    prog_bairro = df_filtered.groupby(['Programa_Clean', 'Bairro_Clean']).agg(
        val=('Pessoas_Impactadas' if metrica == "Pessoas Impactadas" else 'Ano', 'sum' if metrica == "Pessoas Impactadas" else 'count')
    ).reset_index()

    labels = list(pd.concat([prog_bairro['Programa_Clean'], prog_bairro['Bairro_Clean']]).unique())
    label_map = {lbl: i for i, lbl in enumerate(labels)}

    source = prog_bairro['Programa_Clean'].map(label_map).tolist()
    target = prog_bairro['Bairro_Clean'].map(label_map).tolist()
    value = prog_bairro['val'].tolist()

    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5), label=labels),
        link=dict(source=source, target=target, value=value)
    )])

    fig_sankey.update_layout(font=DARK_FONT, height=500)
    st.plotly_chart(fig_sankey, width="stretch")