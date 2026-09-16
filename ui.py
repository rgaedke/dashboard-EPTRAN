# -*- coding: utf-8 -*-
"""Componentes de interface: CSS, barra de navegação/autoplay, filtros da
barra lateral e cards de KPI."""

import datetime as dt

import pandas as pd
import streamlit as st

import config


def aplicar_estilo():
    st.markdown(
        f"""
        <style>
            .stApp {{
                background-color: {config.COR_FUNDO};
                color: {config.COR_TEXTO};
            }}
            section[data-testid="stSidebar"] {{
                background-color: {config.COR_FUNDO_ALT};
                border-right: 1px solid {config.COR_BORDA};
            }}
            div[data-testid="stMetric"] {{
                background-color: {config.COR_FUNDO_ALT};
                border: 1px solid {config.COR_BORDA};
                border-radius: 10px;
                padding: 14px 18px;
            }}
            div[data-testid="stMetricValue"] {{
                color: {config.AZUL_ESCURO};
            }}
            h1, h2, h3 {{
                color: {config.AZUL_PETROLEO};
            }}
            #MainMenu, footer {{visibility: hidden;}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def barra_navegacao():
    """Barra superior com Play/Pause e seleção manual de tela.
    Devolve o índice da tela atual (0, 1 ou 2)."""
    if "tela_atual" not in st.session_state:
        st.session_state.tela_atual = 0
    if "autoplay" not in st.session_state:
        st.session_state.autoplay = True

    col_play, col_nav, col_titulo = st.columns([1.2, 3, 5])

    with col_play:
        rotulo = "⏸ Pausar" if st.session_state.autoplay else "▶ Retomar"
        if st.button(rotulo, use_container_width=True):
            st.session_state.autoplay = not st.session_state.autoplay

    with col_nav:
        indice = st.radio(
            "Tela",
            options=[0, 1, 2],
            index=st.session_state.tela_atual,
            format_func=lambda i: f"Tela {i + 1}",
            horizontal=True,
            label_visibility="collapsed",
            key="seletor_tela_manual",
        )
        if not st.session_state.autoplay:
            st.session_state.tela_atual = indice

    with col_titulo:
        st.markdown(
            f"<div style='text-align:right; padding-top:6px; color:{config.AZUL_PETROLEO}; "
            f"font-weight:600;'>{config.NOMES_TELAS[st.session_state.tela_atual]}</div>",
            unsafe_allow_html=True,
        )

    return st.session_state.tela_atual


def filtros_globais(df: pd.DataFrame, opcoes_bairro: list):
    """Renderiza os filtros na barra lateral e devolve os valores escolhidos."""
    st.sidebar.markdown("## 🚦 Dashboard EPTRAN")
    st.sidebar.markdown("### Filtros")

    metrica = st.sidebar.radio(
        "Métrica",
        options=["Pessoas Impactadas", "Programas"],
        horizontal=True,
    )

    if df.empty or df["data"].dropna().empty:
        hoje = dt.date.today()
        data_min, data_max = hoje, hoje
    else:
        data_min = df["data"].min().date()
        data_max = df["data"].max().date()

    periodo = st.sidebar.date_input(
        "Período",
        value=(data_min, data_max),
        min_value=data_min,
        max_value=data_max,
    )
    if not isinstance(periodo, (list, tuple)) or len(periodo) != 2:
        periodo = (data_min, data_max)

    bairros_sel = st.sidebar.multiselect(
        "Bairro", options=opcoes_bairro, default=opcoes_bairro
    )

    programas_disponiveis = sorted(df["programa"].dropna().unique())
    programas_sel = st.sidebar.multiselect(
        "Programa", options=programas_disponiveis, default=programas_disponiveis
    )

    acoes_disponiveis = sorted(
        df.loc[df["programa"].isin(programas_sel), "acao"].dropna().unique()
    )
    acoes_sel = st.sidebar.multiselect(
        "Ação", options=acoes_disponiveis, default=acoes_disponiveis
    )

    return {
        "metrica": metrica,
        "periodo": periodo,
        "bairros": bairros_sel,
        "programas": programas_sel,
        "acoes": acoes_sel,
    }


def cards_kpi(df_filtrado: pd.DataFrame, df_explodido: pd.DataFrame, metrica: str):
    rotulo_valor = "Pessoas Impactadas" if metrica == "Pessoas Impactadas" else "Programas Realizados"

    total = df_filtrado["peso"].sum()

    if not df_explodido.empty:
        por_bairro = df_explodido.groupby("bairro_oficial")["valor"].sum()
        bairro_top = por_bairro.idxmax() if not por_bairro.empty else "—"
    else:
        bairro_top = "—"

    if not df_filtrado.empty:
        por_programa = df_filtrado.groupby("programa")["peso"].sum()
        programa_top = por_programa.idxmax() if not por_programa.empty else "—"
    else:
        programa_top = "—"

    c1, c2, c3 = st.columns(3)
    c1.metric(f"Total de {rotulo_valor}", f"{total:,.0f}".replace(",", "."))
    c2.metric("Bairro com maior volume", bairro_top)
    c3.metric("Programa com maior ocorrência", programa_top)
