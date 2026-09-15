import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import time

# Configuração da página
st.set_page_config(
    page_title="Dashboard EPTRAN",
    page_icon="🚦",
    layout="wide"
)

# Estilo CSS customizado - Tema Claro com Fontes Escuras
st.markdown("""
<style>
    /* Estilo Geral de Fontes Escuras */
    body, .stApp {
        background-color: #f8fafc;
        color: #0f172a;
    }
    .main-title {
        color: #1e3a8a;
        font-weight: 800;
        font-size: 26px;
        margin-bottom: 2px;
        padding-top: 0px;
    }
    .sub-title {
        color: #475569;
        font-size: 13px;
        font-weight: 500;
        margin-bottom: 15px;
    }
    
    /* Customização dos Cards de Métricas (KPIs) */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #2563eb;
        border-radius: 8px;
        padding: 10px 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricLabel"] > label {
        color: #475569 !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-size: 22px !important;
        font-weight: 800 !important;
    }
    
    /* Ajustes na Barra Lateral */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    section[data-testid="stSidebar"] label {
        color: #1e293b !important;
        font-weight: 600 !important;
    }
    .css-1d31200, .stSelectbox, .stDateInput, .stRadio {
        color: #0f172a !important;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# CONSTANTES DE ESTILO PLOTLY (FONTES ESCURAS)
# ------------------------------------------------------------------------------
DARK_FONT = dict(family="Arial, sans-serif", size=12, color="#0f172a")
DARK_TITLE_FONT = dict(family="Arial, sans-serif", size=14, color="#0f172a", weight="bold")

# ------------------------------------------------------------------------------
# CARREGAMENTO E CONSOLIDAÇÃO DOS DADOS
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

    df['Total_Num'] = pd.to_numeric(df[col_total], errors='coerce').fillna(0).astype(int)
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
# SIDEBAR / LOGO & FILTROS
# ------------------------------------------------------------------------------
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_column_width=True)
elif os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", use_column_width=True)

st.sidebar.title("🚦 EPTRAN Joinville")

# Navegação e Rotação Automática
st.sidebar.markdown("### 📄 Páginas do Dashboard")
page_options = [
    "1. Fluxo de Execução (Sankey)",
    "2. Mapa de Cobertura (Bairros)",
    "3. Evolução e Rankings"
]

if "page_idx" not in st.session_state:
    st.session_state.page_idx = 0

auto_rotate = st.sidebar.checkbox("🔄 Alternar Páginas Automático (15s)", value=False)

selected_page_str = st.sidebar.radio(
    "Selecione a Página",
    page_options,
    index=st.session_state.page_idx
)
st.session_state.page_idx = page_options.index(selected_page_str)

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filtros de Dados")

# Seletor de Métrica
metrica = st.sidebar.radio(
    "Métrica de Análise",
    ["👥 Pessoas Impactadas", "📋 Nº de Eventos / Lançamentos"],
    index=0
)
usar_soma = (metrica == "👥 Pessoas Impactadas")

# Filtro de Data
min_date = df['Data_Parsed'].min().date()
max_date = df['Data_Parsed'].max().date()

start_date, end_date = st.sidebar.date_input(
    "Período de Execução",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Filtro de Bairro
bairros_unicos = ["Todos os Bairros"] + sorted([b for b in df['Bairro_Clean'].unique() if b and b != 'Nan'])
sel_bairro = st.sidebar.selectbox("Bairro", bairros_unicos)

# Filtro de Programa e Ação Encadeada
programas_unicos = ["Todos os Programas"] + sorted([p for p in df['Programa_Clean'].unique() if p])
sel_prog = st.sidebar.selectbox("Programa", programas_unicos)

if sel_prog != "Todos os Programas":
    df_sub = df[df['Programa_Clean'] == sel_prog]
    acoes_unicas = ["Todas as Ações"] + sorted([a for a in df_sub['Acao_Clean'].unique() if a])
else:
    acoes_unicas = ["Todas as Ações"] + sorted([a for a in df['Acao_Clean'].unique() if a])

sel_acao = st.sidebar.selectbox("Ação / Projeto", acoes_unicas)

# Carregamento do GeoJSON
geojson_data = None
if os.path.exists("bairros.geojson"):
    try:
        with open("bairros.geojson", "r", encoding="utf-8") as f:
            geojson_data = json.load(f)
    except Exception:
        pass

# ------------------------------------------------------------------------------
# FILTRAGEM DOS DADOS
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
# HEADER COMPACTO E CARDS DE KPIS
# ------------------------------------------------------------------------------
st.markdown('<p class="main-title">Dashboard EPTRAN — Execuções de Trânsito</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Prefeitura Municipal de Joinville | Série Histórica (2022–2026)</p>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

total_pessoas = df_filtered['Total_Num'].sum()
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

st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# RENDERIZAÇÃO DAS PÁGINAS INDIVIDUAIS
# ------------------------------------------------------------------------------
lbl_m = "Pessoas Impactadas" if usar_soma else "Nº de Eventos"

if st.session_state.page_idx == 0:
    # --------------------------------------------------------------------------
    # PÁGINA 1: DIAGRAMA DE SANKEY (LARGURA TOTAL E GRANDE DESTAQUE)
    # --------------------------------------------------------------------------
    st.subheader(f"📊 Fluxo Integrado de Execução — EPTRAN ({lbl_m})")
    if not df_filtered.empty:
        links_map = {}
        for _, r in df_filtered.iterrows():
            val = r['Total_Num'] if usar_soma else 1
            k1 = f"{r['Programa_Clean']}|||{r['Acao_Clean']}"
            k2 = f"{r['Acao_Clean']}|||{r['Publico_Clean']}"
            links_map[k1] = links_map.get(k1, 0) + val
            links_map[k2] = links_map.get(k2, 0) + val

        nodes = list(set([k.split("|||")[0] for k in links_map.keys()] + [k.split("|||")[1] for k in links_map.keys()]))
        node_dict = {n: i for i, n in enumerate(nodes)}

        sources = [node_dict[k.split("|||")[0]] for k in links_map.keys()]
        targets = [node_dict[k.split("|||")[1]] for k in links_map.keys()]
        values = list(links_map.values())

        fig_sankey = go.Figure(data=[go.Sankey(
            node=dict(
                pad=18, thickness=20,
                line=dict(color="#0f172a", width=0.5),
                label=nodes,
                color="#2563eb",
                font=DARK_FONT
            ),
            link=dict(
                source=sources, target=targets, value=values,
                color="rgba(148, 163, 184, 0.35)"
            )
        )])
        fig_sankey.update_layout(
            height=560,
            font=DARK_FONT,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_sankey, width='stretch')
    else:
        st.warning("Nenhum registro encontrado para os filtros selecionados.")

elif st.session_state.page_idx == 1:
    # --------------------------------------------------------------------------
    # PÁGINA 2: MAPA COROPLÉTICO DE JOINVILLE (TELA CHEIA)
    # --------------------------------------------------------------------------
    st.subheader(f"🗺️ Cobertura Geográfica por Bairro de Joinville ({lbl_m})")
    if not df_filtered.empty:
        if usar_soma:
            df_geo = df_filtered.groupby('Bairro_Clean')['Total_Num'].sum().reset_index()
            val_col = 'Total_Num'
        else:
            df_geo = df_filtered.groupby('Bairro_Clean').size().reset_index(name='Count')
            val_col = 'Count'

        if geojson_data:
            prop_key = "properties.NM_BAIRRO"
            try:
                sample_props = geojson_data['features'][0]['properties']
                for k in ['NM_BAIRRO', 'nome', 'bairro', 'NOME', 'NM_BAIRR']:
                    if k in sample_props:
                        prop_key = f"properties.{k}"
                        break
            except Exception:
                pass

            map_kwargs = dict(
                data_frame=df_geo,
                geojson=geojson_data,
                locations='Bairro_Clean',
                featureidkey=prop_key,
                color=val_col,
                color_continuous_scale="OrRd",
                center={"lat": -26.3000, "lon": -48.8400},
                zoom=10.4,
                opacity=0.65,
                labels={'Bairro_Clean': 'Bairro', val_col: lbl_m}
            )

            if hasattr(px, 'choropleth_map'):
                try:
                    fig_map = px.choropleth_map(**map_kwargs, map_style="carto-positron")
                except Exception:
                    fig_map = px.choropleth_map(**map_kwargs)
            elif hasattr(px, 'choropleth_mapbox'):
                try:
                    fig_map = px.choropleth_mapbox(**map_kwargs, mapbox_style="carto-positron")
                except Exception:
                    fig_map = px.choropleth_mapbox(**map_kwargs)
            else:
                fig_map = go.Figure()

            fig_map.update_layout(
                height=580,
                font=DARK_FONT,
                margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
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

            fig_map = px.scatter_mapbox(
                df_geo, lat="Lat", lon="Lon", size=val_col, color=val_col,
                hover_name="Bairro_Clean", size_max=35, zoom=10.5,
                center={"lat": -26.3000, "lon": -48.8400},
                mapbox_style="carto-positron",
                color_continuous_scale="OrRd",
                labels={val_col: lbl_m}
            )
            fig_map.update_layout(
                height=580,
                font=DARK_FONT,
                margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_map, width='stretch')
    else:
        st.warning("Nenhum registro encontrado para os filtros selecionados.")

elif st.session_state.page_idx == 2:
    # --------------------------------------------------------------------------
    # PÁGINA 3: EVOLUÇÃO TEMPORAL E RANKING DOS BAIRROS
    # --------------------------------------------------------------------------
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
                labels={'Ano_Val': 'Ano de Execução', y_col: lbl_m, 'Programa_Clean': 'Programa'},
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_temp.update_layout(
                xaxis=dict(type='category', title="Ano de Execução", tickfont=DARK_FONT),
                yaxis=dict(title=lbl_m, tickfont=DARK_FONT),
                legend=dict(font=DARK_FONT, orientation="h", y=-0.2),
                font=DARK_FONT,
                height=500,
                margin=dict(l=10, r=10, t=20, b=10),
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
                xaxis=dict(title=lbl_m, tickfont=DARK_FONT),
                yaxis=dict(title="Bairro", tickfont=DARK_FONT),
                font=DARK_FONT,
                height=500,
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=20, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_b, width='stretch')

# Lógica de Rotação Automática de Páginas (15s)
if auto_rotate:
    time.sleep(15)
    st.session_state.page_idx = (st.session_state.page_idx + 1) % 3
    st.rerun()
