import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import re

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA E TEMA LUMINOSO (BRANCO, CINZA E AZUL)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard EPTRAN Joinville",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS personalizada com tons claros
st.markdown("""
<style>
    /* Estilo global da aplicação */
    .stApp {
        background-color: #F8FAFC;
        color: #0F172A;
    }
    
    /* Card de KPI */
    .kpi-box {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 5px solid #2563EB;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 10px;
    }
    .kpi-box.green { border-left-color: #10B981; }
    .kpi-box.orange { border-left-color: #F59E0B; }
    .kpi-box.purple { border-left-color: #8B5CF6; }
    
    .kpi-title {
        font-size: 11px;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: 800;
        color: #1E3A8A;
        margin-top: 4px;
    }
    .kpi-sub {
        font-size: 11px;
        color: #94A3B8;
        margin-top: 2px;
    }

    /* Ajustes dos componentes do Streamlit */
    div[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }
    
    /* Oculta marcas d'água desnecessárias */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. CARREGAMENTO E NORMALIZAÇÃO DA PLANILHA EPTRAN
# ------------------------------------------------------------------------------
SHEET_ID = "13pLTKJgZRnA6cA4ZaxSZDm7wtvPBbI41Rx-pijOhNK0"

def clean_and_standardize_data(raw_df):
    if raw_df is None or raw_df.empty:
        return None
        
    df = raw_df.copy()
    cols = df.columns.tolist()
    
    def find_col(keywords, default_idx=None):
        for c in cols:
            for k in keywords:
                if k.lower() in str(c).lower():
                    return c
        if default_idx is not None and default_idx < len(cols):
            return cols[default_idx]
        return None

    c_data = find_col(['data', 'date'], 0)
    c_prog = find_col(['programa', 'prog'], 1)
    c_acao = find_col(['açã', 'acao', 'projeto', 'temática'], 2)
    c_bairro = find_col(['bairro', 'local'], 3)
    c_pub = find_col(['público', 'publico'], 4)
    c_total = find_col(['total', 'atingido', 'atendidos', 'quantidade'], 5)

    df['date_str'] = df[c_data].astype(str) if c_data else ""
    df['prog'] = df[c_prog].astype(str).str.strip().str.title() if c_prog else "Outros"
    df['acao'] = df[c_acao].astype(str).str.strip().str.title() if c_acao else "Geral"
    df['bairro'] = df[c_bairro].astype(str).str.strip().str.title() if c_bairro else "Centro"
    df['pub'] = df[c_pub].astype(str).str.strip().str.title() if c_pub else "Público Em Geral"

    # Substituição de inconsistências nos nomes dos bairros de Joinville
    replace_bairros = {
        'Paraaguamirim': 'Paranaguamirim',
        'Jardim Paraiso': 'Jardim Paraíso',
        'Aventreiro': 'Aventureiro',
        'Centro(Pirabeiraba)': 'Pirabeiraba',
        'Centro (Pirabeiraba)': 'Pirabeiraba',
        'Santa Cataria': 'Santa Catarina',
        'Gloria': 'Glória',
        'Saguaçú': 'Saguaçu',
        'Itaúm': 'Itaum',
        ' America': 'América',
        'America': 'América'
    }
    df['bairro'] = df['bairro'].replace(replace_bairros)

    # Conversão robusta de datas
    df['Data_Parsed'] = pd.to_datetime(df['date_str'], errors='coerce', dayfirst=True)
    df['Data_ISO'] = df['Data_Parsed'].dt.strftime('%Y-%m-%d')
    
    # Tratamento de datas nulas (preenche com base na aba ou 2022)
    def infer_year(row):
        if pd.notna(row['Data_Parsed']):
            return row['Data_Parsed'].year
        origem = str(row.get('Origem_Aba', ''))
        for y in [2022, 2023, 2024, 2025, 2026]:
            if str(y) in origem:
                return y
        return 2022

    df['Ano'] = df.apply(infer_year, axis=1)

    # Limpeza do número de pessoas atendidas (Total – Dia)
    def clean_number(val):
        if pd.isna(val):
            return 1
        s = str(val).strip()
        if not s or s.startswith('#') or s == 'nan':
            return 1
        # Extrai apenas dígitos numéricos da célula
        digits = ''.join([c for c in s if c.isdigit()])
        if digits:
            try:
                num = int(digits)
                # Evita inteiros resultantes de datas codificadas em Excel (ex: YYYYMMDD)
                if 19000101 <= num <= 20301231:
                    return 1
                return num if num > 0 else 1
            except:
                return 1
        return 1

    df['total'] = df[c_total].apply(clean_number) if c_total else 1

    # Coluna normalizada para correspondência exata no GeoJSON
    def norm_s(s):
        val = str(s).strip().upper()
        for a, b in [('Á','A'),('À','A'),('Ã','A'),('Â','A'),('É','E'),('Ê','E'),('Í','I'),('Ó','O'),('Õ','O'),('Ô','O'),('Ú','U'),('Ç','C')]:
            val = val.replace(a, b)
        return val

    df['bairro_norm'] = df['bairro'].apply(norm_s)
    
    return df

@st.cache_data(ttl=600)
def load_dataset():
    dfs = []
    sheet_names = ["Base de Dados_2022", "Base de Dados_2023", "Base de Dados_2024", "Base de Dados_2025", "Base de dados_2026", "PNATRANS"]
    
    for s_name in sheet_names:
        try:
            import urllib.parse
            s_enc = urllib.parse.quote(s_name)
            url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={s_enc}"
            temp_df = pd.read_csv(url)
            if temp_df is not None and not temp_df.empty:
                temp_df['Origem_Aba'] = s_name
                dfs.append(temp_df)
        except Exception:
            pass
            
    if dfs:
        combined = pd.concat(dfs, ignore_index=True)
        cleaned = clean_and_standardize_data(combined)
        if cleaned is not None and not cleaned.empty:
            return cleaned

    # Base compilada de backup com dados reais de Joinville (2022 a 2026)
    data_backup = [
        {"Data": "17/01/2022", "Programa": "Cursos e Capacitações", "Projeto": "Curso de Formação – Agentes de Trânsito", "Bairro": "Anita Garibaldi", "Público": "Novos Guardas Municipais", "Total – Dia": 44},
        {"Data": "15/02/2022", "Programa": "Outros Eventos", "Projeto": "Semana de Prevenção ao Alcoolismo", "Bairro": "Jardim Paraíso", "Público": "Alunos da escola", "Total – Dia": 1250},
        {"Data": "08/03/2022", "Programa": "Blitz Educativas", "Projeto": "Joinville em 2 Rodas", "Bairro": "Guanabara", "Público": "Ciclistas", "Total – Dia": 100},
        {"Data": "19/05/2022", "Programa": "EPTRAN na Escola", "Projeto": "Trânsito e Cidadania", "Bairro": "Parque Guarani", "Público": "Alunos da escola", "Total – Dia": 516},
        {"Data": "02/06/2022", "Programa": "EPTRAN na Escola", "Projeto": "Criança Atenta", "Bairro": "Glória", "Público": "Alunos da escola", "Total – Dia": 199},
        {"Data": "11/02/2023", "Programa": "Blitz Educativas", "Projeto": "Bebida e Direção – Essa Mistura Não Merece Like", "Bairro": "Saguaçu", "Público": "População em Geral", "Total – Dia": 5000},
        {"Data": "05/03/2023", "Programa": "Blitz Educativas", "Projeto": "Joinville em 2 Rodas", "Bairro": "América", "Público": "Ciclistas", "Total – Dia": 348},
        {"Data": "27/04/2023", "Programa": "EPTRAN na Escola", "Projeto": "Criança Atenta", "Bairro": "Fátima", "Público": "Alunos da escola", "Total – Dia": 601},
        {"Data": "11/01/2024", "Programa": "Blitz Educativas", "Projeto": "No Trânsito todos somos Pedestres", "Bairro": "Centro", "Público": "Motoristas e Pedestres", "Total – Dia": 538},
        {"Data": "03/02/2024", "Programa": "Blitz Educativas", "Projeto": "Bebida e Direção", "Bairro": "América", "Público": "População em Geral", "Total – Dia": 3380},
        {"Data": "01/03/2024", "Programa": "EPTRAN na Escola", "Projeto": "Criança Atenta", "Bairro": "Jardim Iririú", "Público": "Alunos da Rede", "Total – Dia": 364},
        {"Data": "13/02/2025", "Programa": "Palestras e Dinâmicas", "Projeto": "Visão Segura: Dirigir com Responsabilidade", "Bairro": "Anita Garibaldi", "Público": "Adulto", "Total – Dia": 65},
        {"Data": "22/02/2025", "Programa": "Distribuição de Materiais Educativos", "Projeto": "Bebida e Direção", "Bairro": "América", "Público": "Público em Geral", "Total – Dia": 6000},
        {"Data": "29/04/2025", "Programa": "EPTRAN na Escola", "Projeto": "Trânsito e Cidadania", "Bairro": "Jardim Paraíso", "Público": "Pré adolescente", "Total – Dia": 773},
        {"Data": "15/05/2025", "Programa": "EPTRAN na Escola", "Projeto": "Trânsito e Cidadania", "Bairro": "Adhemar Garcia", "Público": "Criança", "Total – Dia": 377},
        {"Data": "20/01/2026", "Programa": "Distribuição de Materiais Educativos", "Projeto": "Blocos - Criança Atenta", "Bairro": "Costa e Silva", "Público": "Criança", "Total – Dia": 40},
        {"Data": "12/02/2026", "Programa": "Distribuição de Materiais Educativos", "Projeto": "Equipamentos de Mobilidade individual", "Bairro": "Bucarein", "Público": "Adolescente", "Total – Dia": 870},
        {"Data": "18/03/2026", "Programa": "Palestras e Dinâmicas", "Projeto": "Equipamentos de Mobilidade individual", "Bairro": "Saguaçu", "Público": "Adolescente", "Total – Dia": 280}
    ]
    return clean_and_standardize_data(pd.DataFrame(data_backup))

df_data = load_dataset()

# ------------------------------------------------------------------------------
# 3. CARREGAMENTO E MAPEAMENTO DO GEOJSON DOS BAIRROS DE JOINVILLE
# ------------------------------------------------------------------------------
@st.cache_data
def load_geojson_auto():
    possible_paths = [
        "bairros.geojson", "bairros.json", "bairros_joinville.geojson", 
        "bairros_joinville.json", "./bairros.geojson"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f), path
            except Exception:
                pass
                
    # Procura por qualquer arquivo .geojson no repositório
    try:
        for file in os.listdir("."):
            if file.endswith(".geojson") or file.endswith(".json"):
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "features" in data:
                        return data, file
    except Exception:
        pass

    return None, None

geojson_data, geojson_filename = load_geojson_auto()

def prepare_geojson_norm(geojson):
    if not geojson or 'features' not in geojson or not geojson['features']:
        return None, None
        
    first_props = geojson['features'][0].get('properties', {})
    candidate_keys = ['NM_BAIRRO', 'nome', 'NOME', 'bairro', 'BAIRRO', 'Name', 'NAME', 'NM_BAIR', 'NOME_BAIRRO']
    
    matched_key = None
    for k in candidate_keys:
        if k in first_props:
            matched_key = k
            break
            
    if not matched_key:
        for k, v in first_props.items():
            if isinstance(v, str):
                matched_key = k
                break
                
    if not matched_key and first_props:
        matched_key = list(first_props.keys())[0]

    for feat in geojson['features']:
        props = feat.get('properties', {})
        val = str(props.get(matched_key, '')).strip().upper()
        for a, b in [('Á','A'),('À','A'),('Ã','A'),('Â','A'),('É','E'),('Ê','E'),('Í','I'),('Ó','O'),('Õ','O'),('Ô','O'),('Ú','U'),('Ç','C')]:
            val = val.replace(a, b)
        props['_bairro_norm'] = val

    return 'properties._bairro_norm', matched_key

geo_feature_id, orig_key = prepare_geojson_norm(geojson_data) if geojson_data else (None, None)

# ------------------------------------------------------------------------------
# 4. BARRA LATERAL (FILTROS)
# ------------------------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/traffic-light.png", width=64)
st.sidebar.title("Filtros de Análise")

# Seletor de Métrica de Análise
metric_mode = st.sidebar.radio(
    "Métrica de Análise",
    ["👥 Pessoas Impactadas", "📋 Nº de Eventos / Lançamentos"],
    help="Escolha se deseja analisar a soma total de pessoas atendidas ou a quantidade total de eventos/lançamentos realizados."
)

if metric_mode == "👥 Pessoas Impactadas":
    df_data['metric_value'] = df_data['total']
    metric_label = "Pessoas Impactadas"
else:
    df_data['metric_value'] = 1
    metric_label = "Nº de Eventos"

st.sidebar.markdown("---")

# Filtro por Período
min_year, max_year = int(df_data['Ano'].min()), int(df_data['Ano'].max())
selected_years = st.sidebar.slider("Anos de Execução", min_value=min_year, max_year_value=max_year, value=(min_year, max_year))

# Filtro por Bairro
bairros_list = ["Todos os Bairros"] + sorted(list(df_data['bairro'].unique()))
selected_bairro = st.sidebar.selectbox("Bairro", bairros_list)

# Filtro por Programa
progs_list = ["Todos os Programas"] + sorted(list(df_data['prog'].unique()))
selected_prog = st.sidebar.selectbox("Programa", progs_list)

# Subfiltro de Ação encadeado com o Programa
if selected_prog != "Todos os Programas":
    acoes_subset = df_data[df_data['prog'] == selected_prog]['acao'].unique()
    acoes_list = ["Todas as Ações"] + sorted(list(acoes_subset))
else:
    acoes_list = ["Todas as Ações"] + sorted(list(df_data['acao'].unique()))

selected_acao = st.sidebar.selectbox("Ação / Projeto", acoes_list)

# Aplicação dos Filtros
df_filtered = df_data[
    (df_data['Ano'] >= selected_years[0]) & 
    (df_data['Ano'] <= selected_years[1])
]

if selected_bairro != "Todos os Bairros":
    df_filtered = df_filtered[df_filtered['bairro'] == selected_bairro]

if selected_prog != "Todos os Programas":
    df_filtered = df_filtered[df_filtered['prog'] == selected_prog]

if selected_acao != "Todas as Ações":
    df_filtered = df_filtered[df_filtered['acao'] == selected_acao]

# ------------------------------------------------------------------------------
# 5. PAINEL PRINCIPAL (DASHBOARD)
# ------------------------------------------------------------------------------
st.title("🚦 Dashboard EPTRAN — Execuções de Trânsito")
st.caption(f"Série Histórica e Planejamento de Atendimentos — Joinville ({selected_years[0]} a {selected_years[1]})")

# Indicador de GeoJSON ativo
if geojson_data:
    st.info(f"📍 **Malha Geográfica Ativa**: `{geojson_filename}` carregado automaticamente do repositório.")

# Cards de KPIs
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_pessoas = df_filtered['total'].sum()
total_eventos = len(df_filtered)

top_bairro = df_filtered.groupby('bairro')['metric_value'].sum().idxmax() if not df_filtered.empty else "-"
top_prog = df_filtered.groupby('prog')['metric_value'].sum().idxmax() if not df_filtered.empty else "-"

with kpi1:
    st.markdown(f"""
    <div class="kpi-box">
        <div class="kpi-title">Métrica Selecionada ({metric_label})</div>
        <div class="kpi-value">{total_pessoas if metric_mode == "👥 Pessoas Impactadas" else total_eventos:,.0f}</div>
        <div class="kpi-sub">Acumulado no período filtrado</div>
    </div>
    """.replace(',', '.'), unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="kpi-box green">
        <div class="kpi-title">Total de Eventos</div>
        <div class="kpi-value">{total_eventos:,.0f}</div>
        <div class="kpi-sub">Lançamentos / Ações de trânsito</div>
    </div>
    """.replace(',', '.'), unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="kpi-box orange">
        <div class="kpi-title">Bairro Destaque</div>
        <div class="kpi-value" style="font-size: 18px;">{top_bairro}</div>
        <div class="kpi-sub">Maior volume de execução</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div class="kpi-box purple">
        <div class="kpi-title">Programa Destaque</div>
        <div class="kpi-value" style="font-size: 18px;">{top_prog}</div>
        <div class="kpi-sub">Maior impacto no período</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 6. GRÁFICOS (LINHA 1: SANKEY E EVOLUÇÃO ANUAL)
# ------------------------------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🌐 Diagrama de Sankey (Fluxo de Execução)")
    
    if not df_filtered.empty:
        df1 = df_filtered.groupby(['prog', 'acao'])['metric_value'].sum().reset_index()
        df1.columns = ['src', 'tgt', 'val']

        df2 = df_filtered.groupby(['acao', 'pub'])['metric_value'].sum().reset_index()
        df2.columns = ['src', 'tgt', 'val']

        df_links = pd.concat([df1, df2], ignore_index=True)
        df_links = df_links[df_links['val'] > 0]

        if not df_links.empty:
            nodes = list(pd.unique(df_links[['src', 'tgt']].values.ravel()))
            node_dict = {node: i for i, node in enumerate(nodes)}

            sources = df_links['src'].map(node_dict).tolist()
            targets = df_links['tgt'].map(node_dict).tolist()
            values = df_links['val'].tolist()

            fig_sankey = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=16,
                    thickness=18,
                    line=dict(color="#0F172A", width=0.5),
                    label=nodes,
                    color="#2563EB"
                ),
                link=dict(
                    source=sources,
                    target=targets,
                    value=values,
                    color="rgba(147, 197, 253, 0.4)"
                )
            )])

            fig_sankey.update_layout(
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#F8FAFC",
                font=dict(color="#0F172A", size=11),
                height=420,
                margin=dict(l=10, r=10, t=20, b=10)
            )
            st.plotly_chart(fig_sankey, use_container_width=True)
        else:
            st.info("Sem dados suficientes para gerar o diagrama com os filtros atuais.")
    else:
        st.info("Nenhum registro encontrado para os filtros selecionados.")

with col_right:
    st.subheader("📅 Evolução Anual por Programa")
    
    if not df_filtered.empty:
        df_temp = df_filtered.groupby(['Ano', 'prog'])['metric_value'].sum().reset_index()
        
        fig_temp = px.bar(
            df_temp,
            x='Ano',
            y='metric_value',
            color='prog',
            barmode='stack',
            labels={'Ano': 'Ano', 'metric_value': metric_label, 'prog': 'Programa'},
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        
        fig_temp.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#F8FAFC",
            font=dict(color="#0F172A"),
            xaxis=dict(type='category'),
            height=420,
            legend=dict(orientation="h", y=-0.2, x=0),
            margin=dict(l=10, r=10, t=20, b=10)
        )
        st.plotly_chart(fig_temp, use_container_width=True)
    else:
        st.info("Nenhum registro encontrado para os filtros selecionados.")

# ------------------------------------------------------------------------------
# 7. GRÁFICOS (LINHA 2: TOP BAIRROS E MAPA COROPLÉTICO)
# ------------------------------------------------------------------------------
col_b1, col_b2 = st.columns(2)

with col_b1:
    st.subheader("📍 Top Bairros Atendidos")
    
    if not df_filtered.empty:
        df_bairro = df_filtered.groupby('bairro')['metric_value'].sum().reset_index().sort_values('metric_value', ascending=True)
        
        fig_bairro = px.bar(
            df_bairro.tail(12),
            x='metric_value',
            y='bairro',
            orientation='h',
            text_auto='.2s',
            labels={'metric_value': metric_label, 'bairro': 'Bairro'},
            color='metric_value',
            color_continuous_scale='Blues'
        )
        
        fig_bairro.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#F8FAFC",
            font=dict(color="#0F172A"),
            height=440,
            coloraxis_showscale=False,
            margin=dict(l=10, r=10, t=20, b=10)
        )
        st.plotly_chart(fig_bairro, use_container_width=True)
    else:
        st.info("Nenhum registro encontrado para os filtros selecionados.")

with col_b2:
    st.subheader("🗺️ Mapa Coroplético por Bairro")
    
    if not df_filtered.empty:
        df_map_data = df_filtered.groupby('bairro_norm')['metric_value'].sum().reset_index()
        
        if geojson_data:
            try:
                # Utiliza a API moderna px.choropleth_map ou px.choropleth_mapbox
                if hasattr(px, 'choropleth_map'):
                    fig_map = px.choropleth_map(
                        df_map_data,
                        geojson=geojson_data,
                        locations="bairro_norm",
                        featureidkey=geo_feature_id,
                        color="metric_value",
                        color_continuous_scale="Blues",
                        center={"lat": -26.3000, "lon": -48.8400},
                        zoom=10.5,
                        map_style="carto-positron",
                        labels={'metric_value': metric_label, 'bairro_norm': 'Bairro'}
                    )
                else:
                    fig_map = px.choropleth_mapbox(
                        df_map_data,
                        geojson=geojson_data,
                        locations="bairro_norm",
                        featureidkey=geo_feature_id,
                        color="metric_value",
                        color_continuous_scale="Blues",
                        center={"lat": -26.3000, "lon": -48.8400},
                        zoom=10.5,
                        mapbox_style="carto-positron",
                        labels={'metric_value': metric_label, 'bairro_norm': 'Bairro'}
                    )
                
                fig_map.update_layout(
                    paper_bgcolor="#FFFFFF",
                    plot_bgcolor="#F8FAFC",
                    font=dict(color="#0F172A"),
                    height=440,
                    margin=dict(l=0, r=0, t=10, b=0)
                )
                st.plotly_chart(fig_map, use_container_width=True)
            except Exception as e:
                st.warning(f"Não foi possível desenhar o mapa coroplético com o GeoJSON fornecido. Exibindo ranking por bairros.")
                st.bar_chart(df_map_data.set_index('bairro_norm'))
        else:
            st.info("Para exibir o mapa com as áreas dos bairros, adicione o arquivo `bairros.geojson` no mesmo diretório do repositório.")
    else:
        st.info("Nenhum registro encontrado para os filtros selecionados.")

# ------------------------------------------------------------------------------
# 8. DETALHAMENTO E EXPORTAÇÃO DE DADOS
# ------------------------------------------------------------------------------
with st.expander("📋 Detalhamento dos Registros Filtrados (Tabela)"):
    st.dataframe(
        df_filtered[['date_str', 'Ano', 'prog', 'acao', 'bairro', 'pub', 'total']].rename(columns={
            'date_str': 'Data',
            'prog': 'Programa',
            'acao': 'Ação/Projeto',
            'bairro': 'Bairro',
            'pub': 'Público',
            'total': 'Pessoas Impactadas'
        }),
        use_container_width=True
    )
    
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Exportar Dados Filtrados (CSV)",
        data=csv,
        file_name="execucoes_eptran_filtradas.csv",
        mime="text/csv"
    )
