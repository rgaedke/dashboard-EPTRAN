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
# Modo kiosk (autoplay a cada 15s). Isso precisa rodar antes de qualquer
# leitura de st.session_state.tela_atual mais abaixo.
# ---------------------------------------------------------------------------
if "autoplay" not in st.session_state:
    st.session_state.autoplay = False  # começa desligado; liga pelo botão ▶
if "tela_atual" not in st.session_state:
    st.session_state.tela_atual = 0

if st.session_state.autoplay:
    contador = st_autorefresh(interval=config.INTERVALO_AUTOPLAY_MS, key="autorefresh_kiosk")
    st.session_state.tela_atual = contador % 3


# ---------------------------------------------------------------------------
# Barra lateral: filtros + controles de apresentação (Tela / Play-Pause).
# Chamados antes de ler tela_atual abaixo, para o valor já vir atualizado
# nesta mesma execução caso o usuário tenha acabado de trocar de tela.
# ---------------------------------------------------------------------------
filtros = ui.filtros_globais(df, opcoes_bairro)
ui.controle_apresentacao()
tela_atual = st.session_state.tela_atual


# ---------------------------------------------------------------------------
# Área principal: título da tela (alinhado à esquerda)
# ---------------------------------------------------------------------------
ui.titulo_tela()

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
    st.caption("4 opções de gráfico para avaliar — veja o chat para mais sugestões.")
    linha1_col1, linha1_col2 = st.columns(2)
    with linha1_col1:
        fig = charts.grafico_treemap(df_filtrado)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with linha1_col2:
        fig = charts.grafico_sunburst(df_filtrado)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    linha2_col1, linha2_col2 = st.columns(2)
    with linha2_col1:
        fig = charts.grafico_heatmap_programa_acao(df_filtrado)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with linha2_col2:
        fig = charts.grafico_ranking_programas(df_filtrado)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

elif tela_atual == 1:
    fig = charts.grafico_mapa_coropletico(df_explodido_mapa, geojson)
    if fig:
        # height="stretch": o mapa ocupa todo o espaço vertical que sobrar
        # na tela, em vez de uma altura fixa em pixels.
        with st.container(height="stretch"):
            st.plotly_chart(fig, width="stretch", height="stretch")
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
