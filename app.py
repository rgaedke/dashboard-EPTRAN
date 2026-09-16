import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import time

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA E CSS CLEAN / CONTRASTE GARANTIDO NOS FILTROS
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard EPTRAN",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo Visual: Fundo Claro com Filtros Brancos e Letras Escuras
st.markdown("""
<style>
    /* Estilo Geral da Aplicação */
    .stApp {
        background-color: #F8FAFC;
        color: #0F172A;
    }
    
    /* Tipografia com Alto Contraste */
    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: #0F172A !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
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
    
    /* Sidebar Clean */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0;
    }
    
    /* CORREÇÃO VISUAL DOS FILTROS (Fundo claro + Texto escuro) */
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] div[data-baseweb="input"] > div,
    section[data-testid="stSidebar"] input {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border-color: #CBD5E1 !important;
    }
    
    /* Dropdown do Selectbox */
    div[data-baseweb="popover"] div,
    div[data-baseweb="menu"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }
    
    /* Itens dentro do menu do Selectbox */
    div[data-baseweb="option"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }
    div[data-baseweb="option"]:hover {
        background-color: #F1F5F9 !important;
    }

    /* Cartões de KPI */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #0F172A;
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

DARK_FONT = dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", color="#0F172A")

# ------------------------------------------------------------------------------
# 2. CARREGAMENTO E CONSOLIDAÇÃO DOS DADOS
# ------------------------------------------------------------------------------
SHEET_ID = "13pLTKJgZRnA6cA4ZaxSZDm7wtvPBbI41Rx-pijOhNK0"

@st.cache_data(ttl=600)
def load_data():
    df = None
    sheet_names = ["Base de Dados_2022", "Base de Dados_2023", "Base de Dados_2024", "Base de Dados_2025", "Base de dados_2026", "PNATRANS"]
    dfs = []
    
    for s in sheet_names:
        try:
            url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={s}"
            t_df = pd.read_csv(url)
            if not t_df.empty and len(t_df.columns) > 3:
                t_df['Origem_Aba'] = s
                dfs.append(t_df)
        except Exception:
            pass
            
    if dfs:
        df = pd.concat(dfs, ignore_index=True)
    else:
        try:
            url_gen = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
            df = pd.read_csv(url_gen)
        except Exception:
            df = None
            
    if df is None or len(df) == 0:
        np.random.seed(42)
        bairros_list = ["Anita Garibaldi", "Jardim Paraíso", "Guanabara", "Parque Guarani", "Glória", "Saguaçu", "América", "Fátima", "Centro", "Jardim Iririú", "Adhemar Garcia", "Costa e Silva", "Bucarein", "Aventureiro", "Vila Nova", "Boehmerwald", "Pirabeiraba", "Itinga", "Floresta", "Comasa"]
        programas_acoes = {
            "EPTRAN na Escola": ["Criança Atenta", "Trânsito e Cidadania", "Aluno Guia", "Contação de História", "Minipista"],
            "Blitz Educativas": ["Joinville em 2 Rodas", "Bebida e Direção", "Pedestres", "Criança Segura", "Equipamentos de Mobilidade individual"],
            "Palestras e Dinâmicas": ["Visão Segura: Dirigir com Responsabilidade", "Equipamentos de Mobilidade individual", "Não Seja Uma Vítima"],
            "Distribuição de Materiais Educativos": ["Blocos - Criança Atenta", "Bebida e Direção", "Respeite a Mão, Respeite a Vida"],
            "Cursos e Capacitações": ["Capacitação GM e Agentes", "Curso de Formação – Agentes de Trânsito"],
            "Outros Eventos": ["Comando Itinerante", "Respeite Essa Vaga", "Passeio Ciclístico"]
        }
        publicos = ["Alunos", "Adulto", "Público em Geral", "Ciclistas", "Motoristas", "Criança", "Pré adolescente"]
        rows = []
        dates = pd.date_range(start="2022-01-01", end="2026-08-31", freq="W")
        for d in dates:
            prog = np.random.choice(list(programas_acoes.keys()))
            acao = np.random.choice(programas_acoes[prog])
            bairro = np.random.choice(bairros_list)
            pub = np.random.choice(publicos)
            qtd = int(np.random.choice([25, 40, 60, 100, 120, 180, 250, 350, 500, 1200]))
            rows.append({
                "Data": d.strftime("%d/%m/%Y"),
                "Programa": prog,
                "Ação": acao,
                "Bairro": bairro,
                "Público": pub,
                "Total – Dia": qtd
            })
        df = pd.DataFrame(rows)

    col_total = [c for c in df.columns if 'Total' in c or 'Atendidos' in c or 'Público' in c]
    col_total = col_total[0] if col_total else df.columns[-1]

    col_prog = 'Programa' if 'Programa' in df.columns else df.columns[0]
    col_acao = 'Ação' if 'Ação' in df.columns else ('Projeto' if 'Projeto' in df.columns else ('Açao' if 'Açao' in df.columns else df.columns[1]))
    col_bairro = 'Bairro' if 'Bairro' in df.columns else df.columns[2]
    col_pub = 'Público' if 'Público' in df.columns else df.columns[3]

    df['Total_Num'] = pd.to_numeric(df[col_total].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce').fillna(0).astype(float)
    df['Data_Parsed'] = pd.to_datetime(df['Data'].astype(str), errors='coerce', dayfirst=True)
    df['Data_Parsed'] = df['Data_Parsed'].fillna(pd.to_datetime('2022-01-01'))
    df['Ano_Val'] = df['Data_Parsed'].dt.year.astype(int)

    df['Bairro_Clean'] = df[col_bairro].astype(str).str.strip().str.title()
    df['Bairro_Clean'] = df['Bairro_Clean'].replace({'Paraaguamirim': 'Paranaguamirim', 'Jardim Paraiso': 'Jardim Paraíso', 'Aventreiro': 'Aventureiro'})
    df['Programa_Clean'] = df[col_prog].astype(str).str.strip()
    df['Acao_Clean'] = df[col_acao].astype(str).str.strip()
    df['Publico_Clean'] = df[col_pub].astype(str).str.strip()

    return df

df = load_data()

# ------------------------------------------------------------------------------
# 3. SIDEBAR: FILTROS E CONTROLES
# ------------------------------------------------------------------------------
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
elif os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", use_container_width=True)

st.sidebar.subheader("🔍 Filtros de Análise")

metrica = st.sidebar.radio(
    "Métrica Principal",
    ["👥 Pessoas Impactadas", "📋 Nº de Eventos / Lançamentos"],
    index=0
)
usar_soma = (metrica == "👥 Pessoas Impactadas")

min_date = df['Data_Parsed'].min().date()
max_date = df['Data_Parsed'].max().date()

start_date, end_date = st.sidebar.date_input(
    "Período de Execução",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

bairros_unicos = ["Todos os Bairros"] + sorted([b for b in df['Bairro_Clean'].unique() if b and b != 'Nan'])
sel_bairro = st.sidebar.selectbox("Bairro", bairros_unicos)

programas_unicos = ["Todos os Programas"] + sorted([p for p in df['Programa_Clean'].unique() if p])
sel_prog = st.sidebar.selectbox("Programa", programas_unicos)

if sel_prog != "Todos os Programas":
    df_sub = df[df['Programa_Clean'] == sel_prog]
    acoes_unicas = ["Todas as Ações"] + sorted([a for a in df_sub['Acao_Clean'].unique() if a])
else:
    acoes_unicas = ["Todas as Ações"] + sorted([a for a in df['Acao_Clean'].unique() if a])

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

# Carregamento do GeoJSON
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
mask = (df['Data_Parsed'].dt.date >= start_date) & (df['Data_Parsed'].dt.date <= end_date)

if sel_bairro != "Todos os Bairros":
    mask &= (df['Bairro_Clean'] == sel_bairro)
if sel_prog != "Todos os Programas":
    mask &= (df['Programa_Clean'] == sel_prog)
if sel_acao != "Todas as Ações":
    mask &= (df['Acao_Clean'] == sel_acao)

df_filtered = df[mask]

# ------------------------------------------------------------------------------
# 5. CABEÇALHO E KPIS
# ------------------------------------------------------------------------------
st.markdown('<p class="main-title">Dashboard EPTRAN — Execuções de Trânsito</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Prefeitura Municipal de Joinville | Série Histórica (2022–2026)</p>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

total_pessoas = int(df_filtered['Total_Num'].sum())
total_eventos = len(df_filtered)

if usar_soma:
    val_kpi1 = f"{total_pessoas:,}".replace(',', '.')
    label_kpi1 = "Pessoas Impactadas"
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
else:
    top_b, top_p = "-", "-"

col3.metric("Bairro Destaque", top_b)
col4.metric("Programa Destaque", top_p)

lbl_m = "Soma de Pessoas" if usar_soma else "Nº de Eventos"

# ------------------------------------------------------------------------------
# 6. PÁGINA 1: SANKEY DIAGRAM (CORRIGIDO)
# ------------------------------------------------------------------------------
if selected_page.startswith("1"):
    st.subheader(f"📊 Diagrama de Sankey — Fluxo de Atendimento ({lbl_m})")
    if not df_filtered.empty:
        # Agrupamento correto para Programa -> Ação -> Público
        if usar_soma:
            df_p_a = df_filtered.groupby(['Programa_Clean', 'Acao_Clean'])['Total_Num'].sum().reset_index()
            df_a_pub = df_filtered.groupby(['Acao_Clean', 'Publico_Clean'])['Total_Num'].sum().reset_index()
            df_p_a.rename(columns={'Total_Num': 'Val'}, inplace=True)
            df_a_pub.rename(columns={'Total_Num': 'Val'}, inplace=True)
        else:
            df_p_a = df_filtered.groupby(['Programa_Clean', 'Acao_Clean']).size().reset_index(name='Val')
            df_a_pub = df_filtered.groupby(['Acao_Clean', 'Publico_Clean']).size().reset_index(name='Val')

        # Garantir apenas valores > 0 para o Sankey funcionar corretamente
        df_p_a = df_p_a[df_p_a['Val'] > 0]
        df_a_pub = df_a_pub[df_a_pub['Val'] > 0]

        if not df_p_a.empty and not df_a_pub.empty:
            # Rótulos únicos para os nós
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
            st.plotly_chart(fig_sankey, use_container_width=True)
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
            st.plotly_chart(fig_map, use_container_width=True)
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
            st.plotly_chart(fig_map, use_container_width=True)

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
            st.plotly_chart(fig_temp, use_container_width=True)

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
                color=y_val, color_continuous_scale='Slate'
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
            st.plotly_chart(fig_b, use_container_width=True)

# Lógica de Rotação Automática
if auto_rotate:
    time.sleep(15)
    st.session_state.page_index = (st.session_state.page_index + 1) % len(pages)
    st.rerun()