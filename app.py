# -*- coding: utf-8 -*-
"""
Dashboard Interativo EPTRAN — ponto de entrada da aplicação Streamlit.

Rode localmente com:
    streamlit run app.py

Veja o README.md para instruções de configuração (credenciais do Google
Sheets) e de deploy no Streamlit Community Cloud.
"""

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

import config
import charts
import ui
from data_loader import carregar_dados_brutos
from data_processing import limpar_dados, aplicar_metrica, explodir_por_bairro
from geo_utils import carregar_geojson, lista_bairros_oficiais


st.set_page_config(
    page_title="Dashboard EPTRAN",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)
ui.aplicar_estilo()


# ---------------------------------------------------------------------------
# Carregamento e limpeza dos dados (cacheados — não roda tudo de novo a
# cada interação do usuário, só quando o cache expira ou é limpo)
# ---------------------------------------------------------------------------
dados_brutos = carregar_dados_brutos()
df = limpar_dados(dados_brutos)
geojson = carregar_geojson()

if df.empty:
    st.error(
        "Não foi possível carregar nenhum dado. Verifique a configuração "
        "da fonte de dados (config.DATA_SOURCE) e as credenciais em "
        "st.secrets — veja o README.md."
    )
    st.stop()

opcoes_bairro = lista_bairros_oficiais()
extras_presentes = sorted(
    set(df["bairro_oficial"].unique()) & {config.BAIRRO_NAO_MAPEADO, config.BAIRRO_NAO_INFORMADO}
)
opcoes_bairro = opcoes_bairro + extras_presentes


# ---------------------------------------------------------------------------
# Barra superior: modo kiosk (autoplay a cada 15s) + navegação manual
# ---------------------------------------------------------------------------
if "autoplay" not in st.session_state:
    st.session_state.autoplay = True
if "tela_atual" not in st.session_state:
    st.session_state.tela_atual = 0

if st.session_state.autoplay:
    contador = st_autorefresh(interval=config.INTERVALO_AUTOPLAY_MS, key="autorefresh_kiosk")
    st.session_state.tela_atual = contador % 3

tela_atual = ui.barra_navegacao()


# ---------------------------------------------------------------------------
# Filtros globais (barra lateral)
# ---------------------------------------------------------------------------
filtros = ui.filtros_globais(df, opcoes_bairro)

data_ini, data_fim = filtros["periodo"]
mascara = (
    df["data"].dt.date.between(data_ini, data_fim)
    & df["programa"].isin(filtros["programas"])
    & df["acao"].isin(filtros["acoes"])
    & df["bairros_filtro"].apply(lambda s: bool(s & set(filtros["bairros"])))
)
df_filtrado = df[mascara].copy()
df_filtrado = aplicar_metrica(df_filtrado, filtros["metrica"])

df_explodido = explodir_por_bairro(df_filtrado)
df_explodido_mapa = df_explodido[
    ~df_explodido["bairro_oficial"].isin([config.BAIRRO_NAO_MAPEADO, config.BAIRRO_NAO_INFORMADO])
]

n_nao_mapeado = df_explodido[
    df_explodido["bairro_oficial"].isin([config.BAIRRO_NAO_MAPEADO, config.BAIRRO_NAO_INFORMADO])
]["valor"].sum()


# ---------------------------------------------------------------------------
# Telas
# ---------------------------------------------------------------------------
if df_filtrado.empty:
    st.warning("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()

if tela_atual == 0:
    ui.cards_kpi(df_filtrado, df_explodido_mapa, filtros["metrica"])
    st.markdown("#### Fluxo: Programa → Ação → Público")
    fig = charts.grafico_sankey(df_filtrado)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

elif tela_atual == 1:
    st.markdown("#### Análise Geográfica")
    fig = charts.grafico_mapa_coropletico(df_explodido_mapa, geojson)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados de bairro para exibir no mapa com os filtros atuais.")
    if n_nao_mapeado > 0:
        st.caption(
            f"⚠️ {n_nao_mapeado:,.0f} (na métrica selecionada) não puderam ser "
            "localizados em um bairro do mapa (nome de bairro fora da malha "
            "geográfica ou não informado) e foram excluídos apenas desta "
            "visualização — continuam nos totais gerais.".replace(",", ".")
        )

else:
    col1, col2 = st.columns(2)
    with col1:
        fig1 = charts.grafico_evolucao_temporal(df_filtrado)
        if fig1:
            st.plotly_chart(fig1, use_container_width=True)
    with col2:
        fig2 = charts.grafico_top15_bairros(df_explodido_mapa)
        if fig2:
            st.plotly_chart(fig2, use_container_width=True)
