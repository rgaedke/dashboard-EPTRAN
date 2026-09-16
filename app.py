import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO (UI/UX)
# ==========================================
st.set_page_config(
    page_title="Dashboard Socioeducativo",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta Azul Petróleo
PALETTE = ["#004C6D", "#257D9D", "#4A90E2", "#002B49", "#6AABD2", "#90C2E7"]
COLOR_PRIMARY = "#004C6D"
COLOR_BG = "#F8F9FA"

st.markdown(f"""
    <style>
        .stApp {{
            background-color: {COLOR_BG};
        }}
        .metric-card {{
            background-color: #FFFFFF;
            border-left: 5px solid {COLOR_PRIMARY};
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .metric-title {{
            font-size: 0.9rem;
            color: #6c757d;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 1.6rem;
            font-weight: bold;
            color: {COLOR_PRIMARY};
        }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CARREGAMENTO E TRATAMENTO DE DADOS
# ==========================================
SHEET_ID = "13pLTKJgZRnA6cA4ZaxSZDm7wtvPBbI41Rx-pijOhNK0"
YEARS = ["2022", "2023", "2024", "2025", "2026"]

@st.cache_data(ttl=600)
def load_data():
    dfs = []
    for year in YEARS:
        # URL de exportação direta do Google Sheets em formato CSV por nome de aba
        sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Base%20de%20Dados_{year}"
        try:
            df = pd.read_csv(sheet_url)
            # Garantir colunas essenciais
            # Esperado: Coluna D (Programa), E (Ação), I (Bairro), J (Público), M (Total Dia), Data
            df['Ano'] = year
            dfs.append(df)
        except Exception as e:
            st.warning(f"Não foi possível carregar a aba Base de Dados_{year}: {e}")
    
    if not dfs:
        # Retorna DataFrame vazio estruturado caso haja falha
        return pd.DataFrame(columns=["Data", "Programa", "Ação", "Bairro", "Público", "Total Dia"])
    
    full_df = pd.concat(dfs, ignore_index=True)
    
    # Tratamento de datas e valores numéricos
    if "Data" in full_df.columns:
        full_df["Data"] = pd.to_datetime(full_df["Data"], errors="coerce")
    else:
        full_df["Data"] = pd.to_datetime("2022-01-01")

    # Mapeamento / Ajuste de Nomes das Colunas (caso haja variações)
    col_mapping = {
        full_df.columns[3] if len(full_df.columns) > 3 else "Programa": "Programa",
        full_df.columns[4] if len(full_df.columns) > 4 else "Ação": "Ação",
        full_df.columns[8] if len(full_df.columns) > 8 else "Bairro": "Bairro",
        full_df.columns[9] if len(full_df.columns) > 9 else "Público": "Público",
        full_df.columns[12] if len(full_df.columns) > 12 else "Total Dia": "Total Dia",
    }
    full_df = full_df.rename(columns=col_mapping)
    
    full_df["Total Dia"] = pd.to_numeric(full_df["Total Dia"], errors="coerce").fillna(0)
    full_df["Bairro"] = full_df["Bairro"].astype(str).str.strip()
    full_df["Programa"] = full_df["Programa"].astype(str).str.strip()
    full_df["Ação"] = full_df["Ação"].astype(str).str.strip()
    full_df["Público"] = full_df["Público"].astype(str).str.strip()

    return full_df

@st.cache_data
def load_geojson():
    geojson_path = "bairros.geojson"
    if os.path.exists(geojson_path):
        with open(geojson_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

df_raw = load_data()
geojson_data = load_geojson()

# ==========================================
# 3. BARRA LATERAL - CONTROLES & FILTROS
# ==========================================
st.sidebar.title("📌 Painel de Controle")

# Controles de Exibição / Kiosk Mode
st.sidebar.subheader("🎥 Modo de Apresentação")
autoplay = st.sidebar.checkbox("Ativar Autoplay (Giro a cada 15s)", value=False)

if "screen_index" not in st.session_state:
    st.session_state.screen_index = 0

if autoplay:
    st_autorefresh(interval=15000, key="kiosk_refresh")
    st.session_state.screen_index = (st.session_state.screen_index + 1) % 3

screen_option = st.sidebar.radio(
    "Navegação entre Telas:",
    ["Tela 1: Visão Geral & Sankey", "Tela 2: Mapa Geográfico", "Tela 3: Evolução & Comparativos"],
    index=st.session_state.screen_index
)

# Atualizar o índice manual
screens_map = {
    "Tela 1: Visão Geral & Sankey": 0,
    "Tela 2: Mapa Geográfico": 1,
    "Tela 3: Evolução & Comparativos": 2
}
st.session_state.screen_index = screens_map[screen_option]

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Filtros Globais")

# Switch Métrica Global
metric_mode = st.sidebar.radio(
    "Métrica Principal:",
    ["Pessoas Impactadas", "Programas"],
    help="Altera a contagem entre o somatório do Total Dia e o número de registros/ações."
)

# Filtro de Período
min_date = df_raw["Data"].min().date() if not df_raw.empty else pd.to_datetime("2022-01-01").date()
max_date = df_raw["Data"].max().date() if not df_raw.empty else pd.to_datetime("2025-12-31").date()

date_range = st.sidebar.date_input(
    "Período:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Filtro de Bairro
all_bairros = sorted(df_raw["Bairro"].dropna().unique().tolist())
selected_bairros = st.sidebar.multiselect("Bairro:", options=all_bairros, default=[])

# Filtro de Programa
all_programas = sorted(df_raw["Programa"].dropna().unique().tolist())
selected_programas = st.sidebar.multiselect("Programa:", options=all_programas, default=[])

# Sub-filtro de Ação (Dependente)
if selected_programas:
    available_acoes = sorted(df_raw[df_raw["Programa"].isin(selected_programas)]["Ação"].dropna().unique().tolist())
else:
    available_acoes = sorted(df_raw["Ação"].dropna().unique().tolist())

selected_acoes = st.sidebar.multiselect("Ação (Dependente do Programa):", options=available_acoes, default=[])

# ==========================================
# 4. APLICAÇÃO DOS FILTROS
# ==========================================
df_filtered = df_raw.copy()

if len(date_range) == 2:
    df_filtered = df_filtered[(df_filtered["Data"].dt.date >= date_range[0]) & (df_filtered["Data"].dt.date <= date_range[1])]

if selected_bairros:
    df_filtered = df_filtered[df_filtered["Bairro"].isin(selected_bairros)]

if selected_programas:
    df_filtered = df_filtered[df_filtered["Programa"].isin(selected_programas)]

if selected_acoes:
    df_filtered = df_filtered[df_filtered["Ação"].isin(selected_acoes)]

# Cálculo da métrica selecionada
def calc_metric(df):
    if metric_mode == "Pessoas Impactadas":
        return df["Total Dia"].sum()
    else:
        return len(df)

# ==========================================
# 5. RENDERIZAÇÃO DAS TELAS
# ==========================================

# HEADER
st.title("📊 Monitoramento de Programas Socioeducativos")
st.markdown(f"**Modo Ativo:** `{metric_mode}` | Registros Filtrados: `{len(df_filtered)}`")

# ------------------------------------------
# TELA 1: VISÃO GERAL & SANKEY
# ------------------------------------------
if st.session_state.screen_index == 0:
    st.subheader("Tela 1: Visão Geral de Fluxo e Métricas Principais")
    
    # Cards KPI
    col1, col2, col3 = st.columns(3)
    
    val_total = calc_metric(df_filtered)
    
    # Bairro com maior volume
    bairro_grouped = df_filtered.groupby("Bairro").apply(calc_metric)
    top_bairro = bairro_grouped.idxmax() if not bairro_grouped.empty else "N/A"
    top_bairro_val = bairro_grouped.max() if not bairro_grouped.empty else 0

    # Programa com maior ocorrência
    prog_grouped = df_filtered.groupby("Programa").apply(calc_metric)
    top_prog = prog_grouped.idxmax() if not prog_grouped.empty else "N/A"
    top_prog_val = prog_grouped.max() if not prog_grouped.empty else 0

    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total ({metric_mode})</div>
                <div class="metric-value">{val_total:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Bairro com Maior Volume</div>
                <div class="metric-value">{top_bairro} ({top_bairro_val:,.0f})</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Programa com Maior Ocorrência</div>
                <div class="metric-value">{top_prog} ({top_prog_val:,.0f})</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.write("### Fluxo de Atendimentos (Programa ➔ Ação ➔ Público)")

    if not df_filtered.empty:
        # Prepara dados para o Diagrama de Sankey
        # Nós: Programa -> Ação -> Público
        df_sankey1 = df_filtered.groupby(["Programa", "Ação"]).apply(calc_metric).reset_index(name="value")
        df_sankey1.columns = ["source", "target", "value"]

        df_sankey2 = df_filtered.groupby(["Ação", "Público"]).apply(calc_metric).reset_index(name="value")
        df_sankey2.columns = ["source", "target", "value"]

        df_links = pd.concat([df_sankey1, df_sankey2], ignore_index=True)
        
        labels = list(pd.unique(df_links[["source", "target"]].values.ravel()))
        mapping = {label: idx for idx, label in enumerate(labels)}

        df_links["source_idx"] = df_links["source"].map(mapping)
        df_links["target_idx"] = df_links["target"].map(mapping)

        fig_sankey = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels,
                color="#004C6D"
            ),
            link=dict(
                source=df_links["source_idx"],
                target=df_links["target_idx"],
                value=df_links["value"],
                color="rgba(37, 125, 157, 0.4)"
            )
        )])
        fig_sankey.update_layout(height=500, margin=dict(l=10, r=10, t=20, b=20))
        st.plotly_chart(fig_sankey, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para os filtros selecionados.")

# ------------------------------------------
# TELA 2: ANÁLISE GEOGRÁFICA (MAPA)
# ------------------------------------------
elif st.session_state.screen_index == 1:
    st.subheader("Tela 2: Análise Geográfica (Mapa Coroplético)")

    geo_df = df_filtered.groupby("Bairro").apply(calc_metric).reset_index(name="Métrica")
    
    # Principal programa de cada bairro
    main_prog = df_filtered.groupby(["Bairro", "Programa"]).size().reset_index(name="count")
    main_prog = main_prog.sort_values(["Bairro", "count"], ascending=[True, False]).drop_duplicates("Bairro")
    geo_df = geo_df.merge(main_prog[["Bairro", "Programa"]], on="Bairro", how="left").fillna({"Programa": "N/A"})

    if geojson_data:
        fig_map = px.choropleth_mapbox(
            geo_df,
            geojson=geojson_data,
            locations="Bairro",
            featureidkey="properties.name",  # Ajustar conforme o atributo do seu GeoJSON
            color="Métrica",
            color_continuous_scale=["#E9ECEF", "#4A90E2", "#257D9D", "#004C6D", "#002B49"],
            hover_name="Bairro",
            hover_data={"Métrica": True, "Programa": True, "Bairro": False},
            mapbox_style="carto-positron",
            zoom=11,
            center={"lat": -26.3045, "lon": -48.8487},  # Coordenadas ajustáveis
            opacity=0.75
        )
        fig_map.update_layout(
            height=600,
            margin=dict(l=0, r=0, t=10, b=0),
            coloraxis_colorbar=dict(title=metric_mode)
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("Arquivo `bairros.geojson` não encontrado no diretório do projeto. Renderizando visão em tabela/barras:")
        fig_geo_fallback = px.bar(
            geo_df.sort_values("Métrica", ascending=False),
            x="Bairro",
            y="Métrica",
            hover_data=["Programa"],
            color="Métrica",
            color_continuous_scale=["#257D9D", "#004C6D"]
        )
        st.plotly_chart(fig_geo_fallback, use_container_width=True)

# ------------------------------------------
# TELA 3: COMPARATIVOS E EVOLUÇÃO TEMPORAL
# ------------------------------------------
elif st.session_state.screen_index == 2:
    st.subheader("Tela 3: Comparativos e Evolução Temporal")

    col_left, col_right = st.columns(2)

    # Gráfico 1: Evolução Temporal
    with col_left:
        st.write("### Evolução Temporal")
        df_temp = df_filtered.set_index("Data").resample("MS").apply(calc_metric).reset_index(name="Métrica")
        
        fig_temp = px.line(
            df_temp,
            x="Data",
            y="Métrica",
            markers=True,
            line_shape="spline",
            color_discrete_sequence=["#004C6D"]
        )
        fig_temp.update_layout(
            xaxis_title="Período (Mês/Ano)",
            yaxis_title=metric_mode,
            height=450
        )
        st.plotly_chart(fig_temp, use_container_width=True)

    # Gráfico 2: Top 15 Bairros
    with col_right:
        st.write("### Top 15 Bairros Atendidos")
        top15_df = df_filtered.groupby("Bairro").apply(calc_metric).reset_index(name="Métrica")
        top15_df = top15_df.sort_values("Métrica", ascending=True).tail(15)

        fig_top15 = px.bar(
            top15_df,
            x="Métrica",
            y="Bairro",
            orientation="h",
            color="Métrica",
            color_continuous_scale=["#4A90E2", "#004C6D"]
        )
        fig_top15.update_layout(
            xaxis_title=metric_mode,
            yaxis_title="Bairro",
            height=450,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_top15, use_container_width=True)