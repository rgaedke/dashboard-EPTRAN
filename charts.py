# -*- coding: utf-8 -*-
"""Funções que montam cada gráfico do dashboard (todas em Plotly)."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import config


def _layout_padrao(fig, titulo=None):
    fig.update_layout(
        title=titulo,
        paper_bgcolor=config.COR_FUNDO,
        plot_bgcolor=config.COR_FUNDO,
        font=dict(color=config.COR_TEXTO, family="Segoe UI, Arial, sans-serif"),
        margin=dict(l=10, r=10, t=50 if titulo else 20, b=10),
    )
    return fig


def grafico_sankey(df: pd.DataFrame):
    """Programa -> Ação -> Público, ponderado pela coluna 'peso'."""
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

    def cor_no(i):
        if i < off_acao:
            return config.AZUL_ESCURO
        if i < off_publico:
            return config.AZUL_PETROLEO
        return config.AZUL_MEDIO

    cores_nos = [cor_no(i) for i in range(len(labels))]

    source, target, value = [], [], []
    for r in nivel1.itertuples(index=False):
        source.append(idx_programa[r.programa])
        target.append(idx_acao[r.acao])
        value.append(r.peso)
    for r in nivel2.itertuples(index=False):
        source.append(idx_acao[r.acao])
        target.append(idx_publico[r.publico])
        value.append(r.peso)

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
            link=dict(
                source=source,
                target=target,
                value=value,
                color=config.AZUL_CLARO + "55",  # com transparência
            ),
        )
    )
    return _layout_padrao(fig)


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
    if df.empty:
        return None
    dados = df.dropna(subset=["data"]).copy()
    dados["ano_mes"] = dados["data"].dt.to_period("M").dt.to_timestamp()
    serie = dados.groupby("ano_mes", as_index=False)["peso"].sum()

    fig = px.bar(
        serie, x="ano_mes", y="peso",
        color_discrete_sequence=[config.AZUL_PETROLEO],
    )
    fig.update_traces(marker_color=config.AZUL_PETROLEO)
    fig.update_xaxes(title="Período")
    fig.update_yaxes(title="")
    return _layout_padrao(fig, "Evolução mensal")


def grafico_top15_bairros(df_explodido: pd.DataFrame):
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
        color_discrete_sequence=[config.AZUL_MEDIO],
    )
    fig.update_traces(marker_color=config.AZUL_MEDIO)
    fig.update_xaxes(title="")
    fig.update_yaxes(title="")
    return _layout_padrao(fig, "Top 15 bairros")
