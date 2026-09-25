# -*- coding: utf-8 -*-
"""Funções que montam cada gráfico do dashboard (todas em Plotly)."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import config


def _layout_padrao(fig, titulo=None, altura=None):
    fig.update_layout(
        title=titulo,
        paper_bgcolor=config.COR_FUNDO,
        plot_bgcolor=config.COR_FUNDO,
        font=dict(color=config.COR_TEXTO, family="Segoe UI, Arial, sans-serif"),
        margin=dict(l=10, r=10, t=44 if titulo else 16, b=10),
        height=altura,
    )
    return fig


def grafico_sankey(df: pd.DataFrame):
    """Programa -> Ação -> Público, ponderado pela coluna 'peso'.
    As cores seguem a escala azul petróleo por nível (Programa mais escuro
    -> Ação -> Público mais claro), e os links herdam a cor do nó de
    origem para facilitar visualmente o acompanhamento de cada fluxo."""
    if df.empty:
        return None

    nivel1 = df.groupby(["programa", "acao"], as_index=False)["peso"].sum()
    nivel2 = df.groupby(["acao", "publico"], as_index=False)["peso"].sum()

    programas = sorted(nivel1["programa"].unique())
    acoes = sorted(set(nivel1["acao"]) | set(nivel2["acao"]))
    publicos = sorted(nivel2["publico"].unique())

    idx_programa = {v: i for i, v in enumerate(programas)}
    off_acao = len(programas)
    idx_acao = {v: i + off_acao for i, v in enumerate(acoes)}
    off_publico = off_acao + len(acoes)
    idx_publico = {v: i + off_publico for i, v in enumerate(publicos)}

    labels = programas + acoes + publicos

    # Gradiente por nível: cada bloco de nós (Programa / Ação / Público)
    # recebe uma cor um pouco diferente dentro da paleta azul petróleo,
    # em vez de tudo na mesma cor.
    def _gradiente(n, cor_ini, cor_fim):
        def _hex_to_rgb(h):
            h = h.lstrip("#")
            return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))

        def _rgb_to_hex(rgb):
            return "#" + "".join(f"{max(0, min(255, int(c))):02X}" for c in rgb)

        ini, fim = _hex_to_rgb(cor_ini), _hex_to_rgb(cor_fim)
        if n <= 1:
            return [cor_ini]
        return [
            _rgb_to_hex(tuple(ini[k] + (fim[k] - ini[k]) * i / (n - 1) for k in range(3)))
            for i in range(n)
        ]

    cores_programa = _gradiente(len(programas), config.AZUL_ESCURO, config.AZUL_PETROLEO)
    cores_acao = _gradiente(len(acoes), config.AZUL_PETROLEO, config.AZUL_MEDIO)
    cores_publico = _gradiente(len(publicos), config.AZUL_MEDIO, config.AZUL_CLARO)
    cores_nos = cores_programa + cores_acao + cores_publico

    source, target, value, cor_link = [], [], [], []
    for r in nivel1.itertuples(index=False):
        i_prog = idx_programa[r.programa]
        source.append(i_prog)
        target.append(idx_acao[r.acao])
        value.append(r.peso)
        cor_link.append(cores_nos[i_prog] + "80")  # com transparência
    for r in nivel2.itertuples(index=False):
        i_acao = idx_acao[r.acao]
        source.append(i_acao)
        target.append(idx_publico[r.publico])
        value.append(r.peso)
        cor_link.append(cores_nos[i_acao] + "80")

    fig = go.Figure(
        go.Sankey(
            arrangement="snap",
            node=dict(
                label=labels,
                color=cores_nos,
                pad=14,
                thickness=16,
                line=dict(color=config.COR_BORDA, width=0.5),
            ),
            link=dict(source=source, target=target, value=value, color=cor_link),
        )
    )
    return _layout_padrao(fig, altura=config.ALTURA_SANKEY)


def grafico_mapa_coropletico(df_explodido: pd.DataFrame, geojson: dict):
    """Mapa coroplético por bairro. Recebe o dataframe já 'explodido'
    (uma linha por bairro citado) e já sem os registros Não mapeado /
    Não informado."""
    if df_explodido.empty:
        return None

    agrupado = (
        df_explodido.groupby("bairro_oficial", as_index=False)
        .agg(valor=("valor", "sum"), principal_programa=("programa", lambda s: s.value_counts().idxmax()))
    )

    fig = px.choropleth_map(
        agrupado,
        geojson=geojson,
        locations="bairro_oficial",
        featureidkey="properties.nome_bairr",
        color="valor",
        color_continuous_scale=config.ESCALA_AZUL_PETROLEO,
        map_style="carto-positron",
        center={"lat": config.JOINVILLE_LAT, "lon": config.JOINVILLE_LON},
        zoom=10.6,
        opacity=0.85,
        hover_name="bairro_oficial",
        hover_data={"valor": ":.0f", "principal_programa": True, "bairro_oficial": False},
        labels={"valor": "Total", "principal_programa": "Programa principal"},
    )
    fig.update_layout(
        paper_bgcolor=config.COR_FUNDO,
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(title=""),
    )
    return fig


def grafico_evolucao_temporal(df: pd.DataFrame):
    """Barras coloridas em escala de azul petróleo conforme o valor de
    cada período — quanto maior o valor, mais escuro/intenso o azul."""
    if df.empty:
        return None
    dados = df.dropna(subset=["data"]).copy()
    dados["ano_mes"] = dados["data"].dt.to_period("M").dt.to_timestamp()
    serie = dados.groupby("ano_mes", as_index=False)["peso"].sum()

    fig = px.bar(
        serie, x="ano_mes", y="peso",
        color="peso",
        color_continuous_scale=config.ESCALA_AZUL_PETROLEO,
    )
    fig.update_coloraxes(showscale=False)
    fig.update_xaxes(title="Período")
    fig.update_yaxes(title="")
    return _layout_padrao(fig, "Evolução mensal", altura=config.ALTURA_GRAFICO_SECUNDARIO)


def grafico_top15_bairros(df_explodido: pd.DataFrame):
    """Barras horizontais em escala de azul petróleo conforme o valor de
    cada bairro — o 1º colocado fica mais escuro/intenso."""
    if df_explodido.empty:
        return None
    agrupado = (
        df_explodido.groupby("bairro_oficial", as_index=False)["valor"]
        .sum()
        .sort_values("valor", ascending=False)
        .head(15)
        .sort_values("valor", ascending=True)
    )
    fig = px.bar(
        agrupado, x="valor", y="bairro_oficial", orientation="h",
        color="valor",
        color_continuous_scale=config.ESCALA_AZUL_PETROLEO,
    )
    fig.update_coloraxes(showscale=False)
    fig.update_xaxes(title="")
    fig.update_yaxes(title="")
    return _layout_padrao(fig, "Top 15 bairros", altura=config.ALTURA_GRAFICO_SECUNDARIO)
