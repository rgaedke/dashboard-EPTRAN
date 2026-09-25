# -*- coding: utf-8 -*-
"""Componentes de interface: CSS, título da tela, controles de
apresentação (play/pause + seletor de tela), filtros da barra lateral e
cards de KPI."""

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

            /* Remove o fade-in/fade-out padrão do Streamlit a cada rerun
               (fica perceptível no modo kiosk, com autorefresh a cada 15s),
               para a troca de tela ser instantânea. */
            * {{
                animation-duration: 0s !important;
                animation-delay: 0s !important;
                transition-duration: 0s !important;
                transition-delay: 0s !important;
            }}

            /* Cabeçalho do Streamlit: mantido, só bem mais baixo e sem os
               ícones de menu/"Deploy" — mas preserva o botão de
               abrir/fechar a barra lateral, que fica dentro dele. */
            header[data-testid="stHeader"] {{
                height: 2.5rem;
                min-height: 2.5rem;
                background: {config.COR_FUNDO};
            }}
            div[data-testid="stToolbarActions"] {{
                display: none;
            }}
            #MainMenu, footer {{
                visibility: hidden;
            }}

            /* Área principal ocupa exatamente a altura da tela (o respiro
               do topo, dentro do padding, é o que "libera" espaço para o
               cabeçalho acima) e não rola — o que sobrar de espaço fica
               disponível para elementos com height="stretch" (ex.: mapa
               da Tela 2). */
            div[data-testid="stMainBlockContainer"] {{
                height: 100vh;
                max-height: 100vh;
                overflow: hidden;
                display: flex;
                flex-direction: column;
                padding-top: 2.7rem;
                padding-bottom: 0.4rem;
            }}
            section[data-testid="stSidebar"] .block-container {{
                padding-top: 1.2rem;
            }}
            div[data-testid="stVerticalBlock"] {{
                gap: 0.5rem;
            }}
            div[data-testid="stMainBlockContainer"] hr {{
                margin: 0.4rem 0;
            }}

            section[data-testid="stSidebar"] {{
                background-color: {config.COR_FUNDO_ALT};
                border-right: 1px solid {config.COR_BORDA};
            }}
            div[data-testid="stMetric"] {{
                background-color: {config.COR_FUNDO_ALT};
                border: 1px solid {config.COR_BORDA};
                border-radius: 10px;
                padding: 10px 16px;
            }}
            div[data-testid="stMetricValue"] {{
                color: {config.AZUL_ESCURO};
            }}
            h1, h2, h3, h4 {{
                color: {config.AZUL_PETROLEO};
                margin-top: 0rem;
                margin-bottom: 0.3rem;
            }}

            /* Espaço extra acima dos controles de apresentação (Tela +
               Play/Pause), para separar visualmente dos filtros. */
            .bloco-apresentacao {{
                margin-top: 1.6rem;
            }}

            /* Botões (Play/Pause e popovers de filtro) na paleta do projeto */
            .stButton > button, .stPopover > button {{
                border-color: {config.AZUL_PETROLEO};
                color: {config.AZUL_PETROLEO};
            }}
            .stButton > button:hover, .stPopover > button:hover {{
                border-color: {config.AZUL_ESCURO};
                color: {config.AZUL_ESCURO};
                background-color: {config.COR_FUNDO_ALT};
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def titulo_tela():
    """Título da tela atual, alinhado à esquerda, no topo da área
    principal (onde antes ficavam os controles de navegação)."""
    st.markdown(
        f"<div style='text-align:left; padding:2px 0 8px 0; color:{config.AZUL_PETROLEO}; "
        f"font-weight:700; font-size:1.35rem;'>{config.NOMES_TELAS[st.session_state.tela_atual]}</div>",
        unsafe_allow_html=True,
    )


def _cabecalho_sidebar():
    """Mostra o logo (config.LOGO_PATH); se o arquivo não existir, cai de
    volta para um título em texto, sem quebrar o app."""
    try:
        st.sidebar.image(str(config.LOGO_PATH), use_container_width=True)
    except Exception:
        st.sidebar.markdown("## 🚦 Dashboard EPTRAN")


def controle_apresentacao():
    """Controles de apresentação (seletor de tela em dropdown + botão de
    play/pause só com ícone), na barra lateral, abaixo dos filtros."""
    if "tela_atual" not in st.session_state:
        st.session_state.tela_atual = 0
    if "autoplay" not in st.session_state:
        st.session_state.autoplay = False  # começa desligado; liga pelo botão

    st.sidebar.markdown('<div class="bloco-apresentacao"></div>', unsafe_allow_html=True)
    st.sidebar.markdown("##### Apresentação")

    col_tela, col_play = st.sidebar.columns([4, 1])

    with col_tela:
        indice = st.selectbox(
            "Tela",
            options=[0, 1, 2],
            index=st.session_state.tela_atual,
            format_func=lambda i: config.NOMES_TELAS[i],
            label_visibility="collapsed",
            key="seletor_tela_dropdown",
        )
        if not st.session_state.autoplay:
            st.session_state.tela_atual = indice

    with col_play:
        icone = "⏸" if st.session_state.autoplay else "▶"
        if st.button(icone, use_container_width=True, key="botao_play_pause"):
            st.session_state.autoplay = not st.session_state.autoplay


def _multiselect_compacto(rotulo: str, opcoes: list, key: str) -> list:
    """Filtro em formato de dropdown compacto: um botão (popover) com a
    contagem de itens selecionados, que só expande a lista ao ser clicado.
    Seleção vazia é tratada como 'todos' pelo chamador."""
    n_sel = len(st.session_state.get(key, []))
    resumo = "Todos" if n_sel == 0 else f"{n_sel} selecionado(s)"
    with st.sidebar.popover(f"{rotulo} · {resumo}", use_container_width=True):
        selecao = st.multiselect(
            rotulo, options=opcoes, key=key, label_visibility="collapsed"
        )
    return selecao


def _efetivo(selecionado: list, opcoes: list) -> list:
    """Lista vazia (nada marcado no filtro) equivale a 'sem filtro' = todos
    os itens disponíveis."""
    return selecionado if selecionado else opcoes


def filtros_globais(df: pd.DataFrame, opcoes_bairro: list):
    """Renderiza os filtros na barra lateral (em formato compacto) e
    devolve os valores já efetivos (lista vazia = nenhum filtro = todos)."""
    _cabecalho_sidebar()
    st.sidebar.markdown("##### Filtros")

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

    bairros_sel = _multiselect_compacto("Bairro", opcoes_bairro, "filtro_bairro")

    programas_disponiveis = sorted(df["programa"].dropna().unique())
    programas_sel = _multiselect_compacto("Programa", programas_disponiveis, "filtro_programa")
    programas_efetivo = _efetivo(programas_sel, programas_disponiveis)

    acoes_disponiveis = sorted(
        df.loc[df["programa"].isin(programas_efetivo), "acao"].dropna().unique()
    )
    acoes_sel = _multiselect_compacto("Ação", acoes_disponiveis, "filtro_acao")

    return {
        "metrica": metrica,
        "periodo": periodo,
        "bairros": _efetivo(bairros_sel, opcoes_bairro),
        "programas": programas_efetivo,
        "acoes": _efetivo(acoes_sel, acoes_disponiveis),
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
