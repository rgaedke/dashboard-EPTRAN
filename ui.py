# -*- coding: utf-8 -*-
"""Componentes de interface: CSS, barra superior (título da tela +
play/pause + pontos de navegação), filtros da barra lateral e cards de
KPI."""

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

            /* Cabeçalho do Streamlit: mantido, mas transparente e baixo, e
               sem capturar cliques (só o botão de abrir/fechar a barra
               lateral, dentro dele, continua clicável). Assim o conteúdo
               pode começar bem perto do topo da tela. */
            header[data-testid="stHeader"] {{
                height: 2rem;
                min-height: 2rem;
                background: transparent;
                pointer-events: none;
            }}
            header[data-testid="stHeader"] button,
            header[data-testid="stHeader"] a {{
                pointer-events: auto;
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
                padding-top: 1.1rem;
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

            /* Elemento invisível (o próprio <style>) não deve gastar espaço */
            div[data-testid="stElementContainer"]:has(style) {{
                display: none;
            }}

            /* Barra superior: título à esquerda, controles centralizados */
            .titulo-slide {{
                text-align: left;
                color: {config.AZUL_PETROLEO};
                font-weight: 700;
                font-size: 1.35rem;
                line-height: 1.2;
            }}
            /* Com a barra lateral recolhida, o botão de reabrir fica no
               canto superior esquerdo: afasta o título dele. */
            .stApp:has(section[data-testid="stSidebar"][aria-expanded="false"]) .titulo-slide {{
                padding-left: 2.4rem;
            }}
            .st-key-controles_slide div[role="radiogroup"] {{
                justify-content: center;
                gap: 0.15rem;
            }}
            .st-key-controles_slide .stButton {{
                display: flex;
                justify-content: flex-end;
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


def _cabecalho_sidebar():
    """Mostra o logo (config.LOGO_PATH); se o arquivo não existir, cai de
    volta para um título em texto, sem quebrar o app."""
    try:
        st.sidebar.image(str(config.LOGO_PATH), use_container_width=True)
    except Exception:
        st.sidebar.markdown("## 🚦 Dashboard EPTRAN")


def _alternar_autoplay():
    st.session_state.autoplay = not st.session_state.autoplay


def _ir_para_tela():
    """Clicar em um ponto = navegação manual: vai para a tela escolhida e
    pausa a rotação automática."""
    st.session_state.tela_atual = st.session_state["seletor_tela_pontos"]
    st.session_state.autoplay = False


def barra_superior() -> int:
    """Linha no topo da área principal: título da tela à esquerda e, no
    centro, botão play/pause (só ícone) + 3 pontos para trocar de tela.
    Devolve o índice da tela atual."""
    if "tela_atual" not in st.session_state:
        st.session_state.tela_atual = 0
    if "autoplay" not in st.session_state:
        st.session_state.autoplay = False  # começa desligado; liga pelo botão

    # Mantém os pontos sincronizados com a tela atual (inclusive quando o
    # autoplay troca de tela sozinho). Precisa ser feito antes de criar o
    # widget.
    st.session_state["seletor_tela_pontos"] = st.session_state.tela_atual

    col_titulo, col_ctrl, _ = st.columns([3, 2, 3], vertical_alignment="center")

    with col_titulo:
        st.markdown(
            f"<div class='titulo-slide'>{config.NOMES_TELAS[st.session_state.tela_atual]}</div>",
            unsafe_allow_html=True,
        )

    with col_ctrl:
        with st.container(key="controles_slide"):
            col_play, col_pontos = st.columns([1, 1.6], vertical_alignment="center", gap="small")
            with col_play:
                icone = ":material/pause:" if st.session_state.autoplay else ":material/play_arrow:"
                st.button(
                    " ",
                    icon=icone,
                    type="tertiary",
                    key="botao_play_pause",
                    help="Pausar rotação automática" if st.session_state.autoplay else "Iniciar rotação automática",
                    on_click=_alternar_autoplay,
                )
            with col_pontos:
                st.radio(
                    "Tela",
                    options=[0, 1, 2],
                    format_func=lambda i: "",
                    horizontal=True,
                    label_visibility="collapsed",
                    key="seletor_tela_pontos",
                    on_change=_ir_para_tela,
                )

    return st.session_state.tela_atual


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
