@ -1,551 +1,192 @@
import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import time
import unicodedata

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA E CSS
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard EPTRAN",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Estilo Geral da Aplicação */
    .stApp {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
    }
    
    /* Tipografia de Cabeçalho */
    .main-title {
        color: #0F172A !important;
        font-weight: 800;
        font-size: 26px;
        margin-bottom: 2px;
        letter-spacing: -0.5px;
    }
    .sub-title {
        color: #475569 !important;
        font-size: 13px;
        margin-bottom: 20px;
        font-weight: 500;
    }
    
    /* Cartões de KPI */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-left: 4px solid #0F172A !important;
        padding: 14px 18px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 11px !important;
        font-weight: 700 !important;
        color: #64748B !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetricValue"] div {
        font-size: 22px !important;
        font-weight: 800 !important;
        color: #0F172A !important;
    }
</style>
""", unsafe_allow_html=True)
# Estilização
DARK_FONT = dict(color="#212529")

DARK_FONT = dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", color="#0F172A")
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

def normalize_text(text):
    if not isinstance(text, str):
        return ""
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8').lower().strip()
    # 3. Tratamento de Datas
    if 'Data' in df.columns:
        df['Data_Parsed'] = pd.to_datetime(df['Data'], errors='coerce')
    else:
        df['Data_Parsed'] = pd.Timestamp('2022-01-01')

# ------------------------------------------------------------------------------
# 2. CARREGAMENTO E CONSOLIDAÇÃO DOS DADOS (LEITURA ESTÁVEL VIA EXCEL)
# ------------------------------------------------------------------------------
SHEET_ID = "13pLTKJgZRnA6cA4ZaxSZDm7wtvPBbI41Rx-pijOhNK0"
    # Tratar datas nulas
    min_valid_date = df['Data_Parsed'].dropna().min()
    if pd.isna(min_valid_date):
        min_valid_date = pd.Timestamp('2022-01-01')
    df['Data_Parsed'] = df['Data_Parsed'].fillna(min_valid_date)

@st.cache_data(ttl=600)
def load_data():
    target_sheets = [
        "Base de Dados_2026",
        "Base de Dados_2025",
        "Base de Dados_2024",
        "Base de Dados_2023",
        "Base de Dados_2022"
    ]
    dfs = []
    
    # 1. Tentativa de Leitura Completa via XLSX Direct Link (Mais rápido e estável)
    excel_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"
    
    try:
        excel_file = pd.ExcelFile(excel_url)
        available_sheets = excel_file.sheet_names
        
        for s in target_sheets:
            # Procura aba com correspondência sem erros de case
            match_sheet = [sheet for sheet in available_sheets if normalize_text(sheet) == normalize_text(s)]
            if match_sheet:
                t_df = excel_file.parse(match_sheet[0])
                if not t_df.empty:
                    t_df = t_df.dropna(how='all').copy()
                    t_df['Origem_Aba'] = s
                    
                    # Procura pela coluna "Total – Dia"
                    col_found = None
                    for col in t_df.columns:
                        col_str = str(col).strip()
                        if col_str in ["Total – Dia", "Total - Dia", "Total–Dia", "Total-Dia"]:
                            col_found = col
                            break
                        elif "total" in normalize_text(col_str) and "dia" in normalize_text(col_str):
                            col_found = col
                            break

                    if col_found is not None:
                        col_target = t_df[col_found]
                    elif t_df.shape[1] >= 13:
                        col_target = t_df.iloc[:, 12]
                    else:
                        col_target = pd.Series([0] * len(t_df))

                    cleaned_num = (
                        col_target.astype(str)
                        .str.replace('.', '', regex=False)
                        .str.replace(',', '.', regex=False)
                        .str.replace(r'[^\d.]', '', regex=True)
                    )
                    t_df['Total_Num'] = pd.to_numeric(cleaned_num, errors='coerce').fillna(0)
                    dfs.append(t_df)
    except Exception:
        # Fallback para o modo CSV individual se a exportação xlsx for bloqueada
        for s in target_sheets:
            try:
                csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={s}"
                t_df = pd.read_csv(csv_url, header=0)
                if not t_df.empty:
                    t_df = t_df.dropna(how='all').copy()
                    t_df['Origem_Aba'] = s
                    
                    col_found = None
                    for col in t_df.columns:
                        col_str = str(col).strip()
                        if col_str in ["Total – Dia", "Total - Dia", "Total–Dia", "Total-Dia"]:
                            col_found = col
                            break
                        elif "total" in normalize_text(col_str) and "dia" in normalize_text(col_str):
                            col_found = col
                            break

                    if col_found is not None:
                        col_target = t_df[col_found]
                    elif t_df.shape[1] >= 13:
                        col_target = t_df.iloc[:, 12]
                    else:
                        col_target = pd.Series([0] * len(t_df))

                    cleaned_num = (
                        col_target.astype(str)
                        .str.replace('.', '', regex=False)
                        .str.replace(',', '.', regex=False)
                        .str.replace(r'[^\d.]', '', regex=True)
                    )
                    t_df['Total_Num'] = pd.to_numeric(cleaned_num, errors='coerce').fillna(0)
                    dfs.append(t_df)
            except Exception:
                pass

    if dfs:
        df = pd.concat(dfs, ignore_index=True)
    else:
        # Cria estrutura de segurança caso haja falha completa de rede com Google
        df = pd.DataFrame(columns=[
            'Data', 'Programa', 'Ação', 'Bairro', 'Público', 'Total_Num', 
            'Origem_Aba', 'Data_Parsed', 'Ano_Val', 'Bairro_Clean', 
            'Programa_Clean', 'Acao_Clean', 'Publico_Clean'
        ])
        return df

    # Identificação flexível das colunas principais
    col_prog = [c for c in df.columns if 'prog' in normalize_text(str(c))]
    col_prog = col_prog[0] if col_prog else df.columns[0]
    
    col_acao = [c for c in df.columns if any(k in normalize_text(str(c)) for k in ['acao', 'projeto'])]
    col_acao = col_acao[0] if col_acao else (df.columns[1] if len(df.columns) > 1 else df.columns[0])

    col_bairro = [c for c in df.columns if 'bairro' in normalize_text(str(c))]
    col_bairro = col_bairro[0] if col_bairro else (df.columns[2] if len(df.columns) > 2 else df.columns[0])

    col_pub = [c for c in df.columns if any(k in normalize_text(str(c)) for k in ['publico', 'alvo', 'perfil'])]
    col_pub = col_pub[0] if col_pub else (df.columns[3] if len(df.columns) > 3 else df.columns[0])

    col_data = [c for c in df.columns if 'data' in normalize_text(str(c))]
    col_data = col_data[0] if col_data else df.columns[0]

    # Parsing seguro de Datas
    df['Data_Parsed'] = pd.to_datetime(df[col_data].astype(str), errors='coerce', dayfirst=True)
    
    df['Ano_Val'] = df['Data_Parsed'].dt.year
    df['Ano_Val'] = df['Ano_Val'].fillna(
        df['Origem_Aba'].str.extract(r'(\d{4})')[0].astype(float)
    ).fillna(2022).astype(int)

    df['Bairro_Clean'] = df[col_bairro].astype(str).str.strip().str.title()
    df['Bairro_Clean'] = df['Bairro_Clean'].replace({
        'Paraaguamirim': 'Paranaguamirim', 
        'Jardim Paraiso': 'Jardim Paraíso', 
        'Aventreiro': 'Aventureiro', 
        'Nan': 'Não Informado',
        'None': 'Não Informado',
        '': 'Não Informado'
    })
    
    df['Programa_Clean'] = df[col_prog].astype(str).str.strip().replace({'nan': 'Não Informado', '': 'Não Informado'})
    df['Acao_Clean'] = df[col_acao].astype(str).str.strip().replace({'nan': 'Não Informado', '': 'Não Informado'})
    df['Publico_Clean'] = df[col_pub].astype(str).str.strip().replace({'nan': 'Não Informado', '': 'Não Informado'})
    
    df['Total_Num'] = df['Total_Num'].fillna(0).astype(float)
    df['Ano'] = df['Data_Parsed'].dt.year

    return df

df = load_data()

# Garantia de presença das colunas calculadas
for required_col in ['Bairro_Clean', 'Programa_Clean', 'Acao_Clean', 'Publico_Clean', 'Total_Num']:
    if required_col not in df.columns:
        df[required_col] = 'Não Informado' if 'Clean' in required_col else 0.0

if 'Data_Parsed' not in df.columns:
    df['Data_Parsed'] = pd.Series(dtype='datetime64[ns]')

# ------------------------------------------------------------------------------
# 3. SIDEBAR: FILTROS E CONTROLES
# ------------------------------------------------------------------------------
# --------------------------------------------------------------------
# SIDEBAR / LOGO & FILTROS
# --------------------------------------------------------------------
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", width='stretch')
    st.sidebar.image("logo.png", width="stretch")
elif os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", width='stretch')
    st.sidebar.image("logo.jpg", width="stretch")

st.sidebar.subheader("🔍 Filtros de Análise")
st.sidebar.title("Filtros de Análise")

# Métrica Principal
metrica = st.sidebar.radio(
    "Métrica Principal",
    ["👥 Pessoas Impactadas", "📋 Nº de Eventos / Lançamentos"],
    index=0
    ["Pessoas Impactadas", "Nº de Eventos / Lançamentos"]
)
usar_soma = (metrica == "👥 Pessoas Impactadas")

valid_dates = df['Data_Parsed'].dropna() if not df.empty else pd.Series()
min_date = valid_dates.min().date() if not valid_dates.empty else pd.to_datetime('2022-01-01').date()
max_date = valid_dates.max().date() if not valid_dates.empty else pd.to_datetime('2026-12-31').date()
# Filtro por Período
min_date = df['Data_Parsed'].min().date()
max_date = df['Data_Parsed'].max().date()

date_selection = st.sidebar.date_input(
dates_input = st.sidebar.date_input(
    "Período de Execução",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_selection, (list, tuple)) and len(date_selection) == 2:
    start_date, end_date = date_selection
elif isinstance(date_selection, (list, tuple)) and len(date_selection) == 1:
    start_date = end_date = date_selection[0]
if isinstance(dates_input, (list, tuple)) and len(dates_input) == 2:
    start_date, end_date = dates_input
else:
    start_date, end_date = min_date, max_date

bairros_unicos = ["Todos os Bairros"] + sorted([b for b in df['Bairro_Clean'].unique() if b and b not in ['Nan', 'Não Informado']])
# Filtros Dropdown
bairros_unicos = ["Todos os Bairros"] + sorted(list(df['Bairro_Clean'].unique()))
sel_bairro = st.sidebar.selectbox("Bairro", bairros_unicos)

programas_unicos = ["Todos os Programas"] + sorted([p for p in df['Programa_Clean'].unique() if p and p != 'Não Informado'])
sel_prog = st.sidebar.selectbox("Programa", programas_unicos)

if sel_prog != "Todos os Programas":
    df_sub = df[df['Programa_Clean'] == sel_prog]
    acoes_unicas = ["Todas as Ações"] + sorted([a for a in df_sub['Acao_Clean'].unique() if a and a != 'Não Informado'])
else:
    acoes_unicas = ["Todas as Ações"] + sorted([a for a in df['Acao_Clean'].unique() if a and a != 'Não Informado'])
programas_unicos = ["Todos os Programas"] + sorted(list(df['Programa_Clean'].unique()))
sel_programa = st.sidebar.selectbox("Programa", programas_unicos)

acoes_unicas = ["Todas as Ações"] + sorted(list(df['Acao_Clean'].unique()))
sel_acao = st.sidebar.selectbox("Ação / Projeto", acoes_unicas)

st.sidebar.markdown("---")
st.sidebar.subheader("📺 Navegação do Painel")

auto_rotate = st.sidebar.checkbox("🔄 Alternar Páginas Automático (15s)", value=False)

pages = [
    "1. Fluxo de Execução (Sankey)",
    "2. Cobertura Territorial (Mapa)",
    "3. Evolução Histórica e Ranking"
]

if 'page_index' not in st.session_state:
    st.session_state.page_index = 0

selected_page = st.sidebar.radio("Selecione a Visão", pages, index=st.session_state.page_index)
st.session_state.page_index = pages.index(selected_page)

# GeoJSON para a página 2
geojson_data = None
if os.path.exists("bairros.geojson"):
    try:
        with open("bairros.geojson", "r", encoding="utf-8") as f:
            geojson_data = json.load(f)
    except Exception:
        pass

# ------------------------------------------------------------------------------
# 4. FILTRAGEM DOS DADOS
# ------------------------------------------------------------------------------
is_full_range = (start_date <= min_date) and (end_date >= max_date)

if is_full_range or df.empty:
    mask = pd.Series(True, index=df.index)
else:
    mask = df['Data_Parsed'].isna() | ((df['Data_Parsed'].dt.date >= start_date) & (df['Data_Parsed'].dt.date <= end_date))
# --------------------------------------------------------------------
# APLICAÇÃO DOS FILTROS
# --------------------------------------------------------------------
mask = (df['Data_Parsed'].dt.date >= start_date) & (df['Data_Parsed'].dt.date <= end_date)

if sel_bairro != "Todos os Bairros":
    mask &= (df['Bairro_Clean'] == sel_bairro)
if sel_prog != "Todos os Programas":
    mask &= (df['Programa_Clean'] == sel_prog)

if sel_programa != "Todos os Programas":
    mask &= (df['Programa_Clean'] == sel_programa)

if sel_acao != "Todas as Ações":
    mask &= (df['Acao_Clean'] == sel_acao)

df_filtered = df[mask]

# ------------------------------------------------------------------------------
# 5. CABEÇALHO E KPIS
# ------------------------------------------------------------------------------
st.markdown('<p class="main-title">Dashboard EPTRAN — Execuções de Trânsito</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Prefeitura Municipal de Joinville | Série Histórica (2022–2026)</p>', unsafe_allow_html=True)
# --------------------------------------------------------------------
# CABEÇALHO & KPIs
# --------------------------------------------------------------------
st.title("Dashboard EPTRAN — Execuções de Trânsito")
st.caption("Prefeitura Municipal de Joinville | Série Histórica (2022–2026)")

col1, col2, col3, col4 = st.columns(4)

total_pessoas = int(df_filtered['Total_Num'].sum()) if not df_filtered.empty else 0
total_eventos = len(df_filtered)

if usar_soma:
    val_kpi1 = f"{total_pessoas:,}".replace(',', '.')
    label_kpi1 = "Pessoas Impactadas (Total – Dia)"
if metrica == "Pessoas Impactadas":
    val_impacto = int(df_filtered['Pessoas_Impactadas'].sum())
    lbl_impacto = "Pessoas Impactadas (Total)"
else:
    val_kpi1 = f"{total_eventos:,}".replace(',', '.')
    label_kpi1 = "Nº de Eventos"

col1.metric("Impacto Principal", val_kpi1, label_kpi1)
col2.metric("Total de Ações/Eventos", f"{total_eventos:,}".replace(',', '.'))

if not df_filtered.empty:
    grp_b = df_filtered.groupby('Bairro_Clean')['Total_Num'].sum() if usar_soma else df_filtered.groupby('Bairro_Clean').size()
    top_b = grp_b.idxmax() if not grp_b.empty else "-"
    
    grp_p = df_filtered.groupby('Programa_Clean')['Total_Num'].sum() if usar_soma else df_filtered.groupby('Programa_Clean').size()
    top_p = grp_p.idxmax() if not grp_p.empty else "-"
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
    top_b, top_p = "-", "-"

col3.metric("Bairro Destaque", top_b)
col4.metric("Programa Destaque", top_p)

lbl_m = "Soma de Pessoas" if usar_soma else "Nº de Eventos"

# ------------------------------------------------------------------------------
# 6. PÁGINA 1: SANKEY DIAGRAM
# ------------------------------------------------------------------------------
if selected_page.startswith("1"):
    st.subheader(f"📊 Diagrama de Sankey — Fluxo de Atendimento ({lbl_m})")
    if not df_filtered.empty:
        if usar_soma:
            df_p_a = df_filtered.groupby(['Programa_Clean', 'Acao_Clean'])['Total_Num'].sum().reset_index()
            df_a_pub = df_filtered.groupby(['Acao_Clean', 'Publico_Clean'])['Total_Num'].sum().reset_index()
            df_p_a.rename(columns={'Total_Num': 'Val'}, inplace=True)
            df_a_pub.rename(columns={'Total_Num': 'Val'}, inplace=True)
        else:
            df_p_a = df_filtered.groupby(['Programa_Clean', 'Acao_Clean']).size().reset_index(name='Val')
            df_a_pub = df_filtered.groupby(['Acao_Clean', 'Publico_Clean']).size().reset_index(name='Val')

        df_p_a = df_p_a[df_p_a['Val'] > 0]
        df_a_pub = df_a_pub[df_a_pub['Val'] > 0]

        if not df_p_a.empty and not df_a_pub.empty:
            all_nodes = list(pd.unique(pd.concat([
                df_p_a['Programa_Clean'], 
                df_p_a['Acao_Clean'], 
                df_a_pub['Publico_Clean']
            ])))
            node_map = {node: idx for idx, node in enumerate(all_nodes)}

            sources = [node_map[src] for src in df_p_a['Programa_Clean']] + [node_map[src] for src in df_a_pub['Acao_Clean']]
            targets = [node_map[tgt] for tgt in df_p_a['Acao_Clean']] + [node_map[tgt] for tgt in df_a_pub['Publico_Clean']]
            values = list(df_p_a['Val']) + list(df_a_pub['Val'])

            fig_sankey = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=18, thickness=18,
                    line=dict(color="#0F172A", width=0.5),
                    label=all_nodes, color="#1E293B"
                ),
                link=dict(source=sources, target=targets, value=values, color="rgba(15, 23, 42, 0.15)")
            )])
            fig_sankey.update_layout(
                height=580,
                font=DARK_FONT,
                margin=dict(l=10, r=10, t=20, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_sankey, width='stretch')
        else:
            st.warning("Valores zerados para os filtros selecionados.")
    else:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")

# ------------------------------------------------------------------------------
# 7. PÁGINA 2: MAPA DE COBERTURA
# ------------------------------------------------------------------------------
elif selected_page.startswith("2"):
    st.subheader(f"🗺️ Distribuição Geográfica por Bairro ({lbl_m})")
    if not df_filtered.empty:
        if usar_soma:
            df_geo = df_filtered.groupby('Bairro_Clean')['Total_Num'].sum().reset_index()
            val_col = 'Total_Num'
        else:
            df_geo = df_filtered.groupby('Bairro_Clean').size().reset_index(name='Count')
            val_col = 'Count'

        if geojson_data:
            prop_key = "properties.nome_bairr"
            try:
                sample_props = geojson_data['features'][0]['properties']
                for k in ['nome_bairr', 'NM_BAIRRO', 'nome', 'bairro', 'NOME']:
                    if k in sample_props:
                        prop_key = f"properties.{k}"
                        break
            except Exception:
                pass

            df_geo['Bairro_Match'] = df_geo['Bairro_Clean'].str.upper()

            fig_map = px.choropleth_map(
                df_geo,
                geojson=geojson_data,
                locations='Bairro_Match',
                featureidkey=prop_key,
                color=val_col,
                color_continuous_scale="Viridis",
                center={"lat": -26.3000, "lon": -48.8400},
                zoom=10.5,
                opacity=0.75,
                map_style="carto-positron",
                labels={'Bairro_Match': 'Bairro', val_col: lbl_m}
            )
            fig_map.update_layout(
                height=580,
                font=DARK_FONT,
                margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_map, width='stretch')
        else:
            coords = {
                "Centro": [-26.3045, -48.8461], "América": [-26.2890, -48.8475], "Anita Garibaldi": [-26.3190, -48.8520],
                "Aventureiro": [-26.2550, -48.8120], "Boa Vista": [-26.2980, -48.8250], "Boehmerwald": [-26.3510, -48.8480],
                "Bucarein": [-26.3150, -48.8400], "Comasa": [-26.2850, -48.8050], "Costa E Silva": [-26.2680, -48.8650],
                "Fátima": [-26.3320, -48.8250], "Floresta": [-26.3380, -48.8450], "Glória": [-26.2950, -48.8680],
                "Guanabara": [-26.3250, -48.8280], "Iririú": [-26.2720, -48.8200], "Itaum": [-26.3350, -48.8350],
                "Itinga": [-26.3800, -48.8400], "Jardim Iririú": [-26.2650, -48.8080], "Jardim Paraíso": [-26.2300, -48.8150],
                "Paranaguamirim": [-26.3680, -48.8180], "Parque Guarani": [-26.3520, -48.8180], "Pirabeiraba": [-26.1850, -48.8950],
                "Saguaçu": [-26.2780, -48.8380], "Vila Nova": [-26.2880, -48.9100]
            }
            df_geo['Lat'] = df_geo['Bairro_Clean'].map(lambda x: coords.get(x, [np.nan, np.nan])[0])
            df_geo['Lon'] = df_geo['Bairro_Clean'].map(lambda x: coords.get(x, [np.nan, np.nan])[1])
            df_geo = df_geo.dropna(subset=['Lat', 'Lon'])

            fig_map = px.scatter_map(
                df_geo, lat="Lat", lon="Lon", size=val_col, color=val_col,
                hover_name="Bairro_Clean", size_max=35, zoom=10.8,
                center={"lat": -26.3000, "lon": -48.8400},
                map_style="carto-positron", color_continuous_scale="Blues",
                labels={val_col: lbl_m}
            )
            fig_map.update_layout(height=580, font=DARK_FONT, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_map, width='stretch')

# ------------------------------------------------------------------------------
# 8. PÁGINA 3: EVOLUÇÃO E RANKING
# ------------------------------------------------------------------------------
elif selected_page.startswith("3"):
    c1, c2 = st.columns(2)

    with c1:
        st.subheader(f"📈 Evolução Anual por Programa ({lbl_m})")
        if not df_filtered.empty:
            if usar_soma:
                df_temp = df_filtered.groupby(['Ano_Val', 'Programa_Clean'])['Total_Num'].sum().reset_index()
                y_col = 'Total_Num'
            else:
                df_temp = df_filtered.groupby(['Ano_Val', 'Programa_Clean']).size().reset_index(name='Count')
                y_col = 'Count'

            fig_temp = px.bar(
                df_temp, x='Ano_Val', y=y_col, color='Programa_Clean',
                barmode='group',
                labels={'Ano_Val': 'Ano', y_col: lbl_m, 'Programa_Clean': 'Programa'},
                color_discrete_sequence=px.colors.qualitative.Dark24
            )
            fig_temp.update_layout(
                xaxis=dict(type='category', title=dict(text="Ano de Execução", font=DARK_FONT), tickfont=DARK_FONT),
                yaxis=dict(title=dict(text=lbl_m, font=DARK_FONT), tickfont=DARK_FONT),
                legend=dict(font=DARK_FONT, orientation="h", y=-0.25),
                height=520,
                font=DARK_FONT,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_temp, width='stretch')

    with c2:
        st.subheader(f"🏆 Top 15 Bairros Atendidos ({lbl_m})")
        if not df_filtered.empty:
            if usar_soma:
                df_b = df_filtered.groupby('Bairro_Clean')['Total_Num'].sum().reset_index().sort_values(by='Total_Num', ascending=True)
                y_val = 'Total_Num'
            else:
                df_b = df_filtered.groupby('Bairro_Clean').size().reset_index(name='Count').sort_values(by='Count', ascending=True)
                y_val = 'Count'

            fig_b = px.bar(
                df_b.tail(15), x=y_val, y='Bairro_Clean', orientation='h',
                text_auto=True,
                labels={'Bairro_Clean': 'Bairro', y_val: lbl_m},
                color=y_val, color_continuous_scale='Blues'
            )
            fig_b.update_layout(
                xaxis=dict(title=dict(text=lbl_m, font=DARK_FONT), tickfont=DARK_FONT),
                yaxis=dict(title=dict(text="Bairro", font=DARK_FONT), tickfont=DARK_FONT),
                height=520,
                font=DARK_FONT,
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_b, width='stretch')

# Lógica de Rotação Automática
if auto_rotate:
    time.sleep(15)
    st.session_state.page_index = (st.session_state.page_index + 1) % len(pages)
    st.rerun()
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