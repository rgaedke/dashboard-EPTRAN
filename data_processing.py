# -*- coding: utf-8 -*-
"""
Limpeza e transformação dos dados brutos vindos de data_loader.py.

Regras de negócio aplicadas aqui (definidas a partir da inspeção real dos
dados + decisões confirmadas com o responsável pelo projeto):

- Linhas sem "Programa" preenchido são descartadas (são linhas em branco
  ou de totalização que existem no fim de cada aba da planilha).
- A coluna "Data" de 2022 vem quebrada na planilha (#VALUE! em todas as
  linhas), então a data é sempre reconstruída a partir de Dia + Mês + o
  ano da aba, para todas as abas (mais robusto e consistente).
- "Total - Dia" que não é numérico é tratado como 0.
- Bairros: nomes são normalizados (maiúsculas, sem acento) e comparados
  com o bairros.geojson. Bairros que não existem no geojson (outro
  município, digitação não identificável, etc.) recebem o rótulo
  "Não mapeado": continuam entrando nos totais gerais e nos filtros,
  mas ficam de fora do mapa e do Top 15 bairros.
- Quando uma célula cita mais de um bairro (ex. "Fátima; Glória"), o
  valor da linha é dividido igualmente entre os bairros citados — essa
  divisão só é usada nos gráficos por bairro (mapa e Top 15); nos
  demais indicadores (KPIs, Sankey, evolução temporal) a linha conta
  inteira, uma única vez.
"""

import pandas as pd
import streamlit as st

import config
from geo_utils import normalizar, resolver_bairro, dividir_bairros_citados


def _mes_para_numero(texto_mes) -> "int | None":
    norm = normalizar(texto_mes)
    return config.MESES_PT.get(norm)


def _bairros_para_filtro(bairro_bruto: str) -> frozenset:
    """Conjunto de nomes (oficiais ou 'Não mapeado'/'Não informado') que
    essa linha deve "responder" quando o filtro de bairro é aplicado."""
    partes = dividir_bairros_citados(bairro_bruto)
    if not partes:
        return frozenset({config.BAIRRO_NAO_INFORMADO})
    nomes = {resolver_bairro(p)[0] for p in partes}
    return frozenset(nomes)


@st.cache_data(show_spinner="Limpando e organizando os dados...")
def limpar_dados(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(
            columns=[
                "data", "ano", "mes_num", "programa", "acao", "local",
                "bairro_bruto", "bairro_oficial", "bairro_status", "publico",
                "total_dia", "bairros_filtro",
            ]
        )

    df = raw_df.copy()

    # fillna ANTES do astype(str): em versões recentes do pandas, converter
    # NaN direto para string pode preservar um valor nulo em vez do texto
    # "nan", então tratamos células vazias primeiro para não escapar das
    # checagens de texto vazio feitas logo abaixo.
    for c in [config.COL_PROGRAMA, config.COL_ACAO, config.COL_LOCAL, config.COL_BAIRRO, config.COL_PUBLICO, config.COL_TOTAL]:
        df[c] = df[c].fillna("")

    programa = df[config.COL_PROGRAMA].astype(str).str.strip()
    valido = (programa != "") & (programa.str.lower() != "nan")
    df = df[valido].copy()

    df["programa"] = df[config.COL_PROGRAMA].astype(str).str.strip()
    df["acao"] = df[config.COL_ACAO].astype(str).str.strip()
    df["publico"] = df[config.COL_PUBLICO].astype(str).str.strip()
    df.loc[df["publico"].str.lower().isin(["nan", ""]), "publico"] = "Não informado"

    # Local/Escola: só uma limpeza básica (espaços) — ao contrário do
    # Bairro, aqui não existe uma lista oficial pra comparar, então nomes
    # quase iguais (ex. "E.M Laura Andrade" vs "Escola Municipal Laura
    # Andrade") podem aparecer como locais diferentes no ranking.
    df["local"] = df[config.COL_LOCAL].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    df.loc[df["local"].str.lower().isin(["nan", ""]), "local"] = "Não informado"

    df["bairro_bruto"] = df[config.COL_BAIRRO].astype(str).str.strip()
    df.loc[df["bairro_bruto"].str.lower() == "nan", "bairro_bruto"] = ""

    total_texto = df[config.COL_TOTAL].astype(str).str.strip()
    total_texto = total_texto.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    df["total_dia"] = pd.to_numeric(total_texto, errors="coerce").fillna(0)

    df["mes_num"] = df[config.COL_MES].apply(_mes_para_numero)
    df["dia_num"] = pd.to_numeric(df[config.COL_DIA], errors="coerce")
    df["ano"] = pd.to_numeric(df["ano_aba"], errors="coerce").astype("Int64")

    df["data"] = pd.to_datetime(
        {"year": df["ano"], "month": df["mes_num"], "day": df["dia_num"]},
        errors="coerce",
    )

    primeiro_bairro = df["bairro_bruto"].apply(
        lambda v: (dividir_bairros_citados(v) or [""])[0]
    )
    resolvido = primeiro_bairro.apply(resolver_bairro)
    df["bairro_oficial"] = resolvido.apply(lambda t: t[0])
    df["bairro_status"] = resolvido.apply(lambda t: t[1])

    df["bairros_filtro"] = df["bairro_bruto"].apply(_bairros_para_filtro)

    colunas = [
        "data", "ano", "mes_num", "programa", "acao", "local", "bairro_bruto",
        "bairro_oficial", "bairro_status", "publico", "total_dia",
        "bairros_filtro",
    ]
    return df[colunas].reset_index(drop=True)


def aplicar_metrica(df: pd.DataFrame, metrica: str) -> pd.DataFrame:
    """Adiciona a coluna 'peso': o que cada linha vale, conforme o switch
    global Pessoas Impactadas x Programas. Todo o resto do app (KPIs,
    gráficos, mapa) soma essa coluna, então o comportamento do switch é
    aplicado de forma consistente em todos os lugares."""
    df = df.copy()
    if metrica == "Pessoas Impactadas":
        df["peso"] = df["total_dia"]
    else:
        df["peso"] = 1
    return df


def explodir_por_bairro(df: pd.DataFrame) -> pd.DataFrame:
    """Usado apenas para o mapa coroplético e o Top 15 bairros: quando uma
    linha cita mais de um bairro, o valor ('peso') é dividido igualmente
    entre eles. Linhas sem bairro identificável não entram aqui."""
    registros = []
    for row in df.itertuples(index=False):
        partes = dividir_bairros_citados(row.bairro_bruto)
        if not partes:
            # Nenhum bairro informado nessa linha: entra no grupo "Não
            # informado" com o valor cheio, para que os totais de
            # "excluído do mapa" batam com os totais gerais.
            registros.append(
                {
                    "data": row.data,
                    "ano": row.ano,
                    "programa": row.programa,
                    "acao": row.acao,
                    "bairro_oficial": config.BAIRRO_NAO_INFORMADO,
                    "bairro_status": "nao_informado",
                    "valor": row.peso,
                }
            )
            continue
        valor_parte = row.peso / len(partes)
        for parte in partes:
            nome, status = resolver_bairro(parte)
            registros.append(
                {
                    "data": row.data,
                    "ano": row.ano,
                    "programa": row.programa,
                    "acao": row.acao,
                    "bairro_oficial": nome,
                    "bairro_status": status,
                    "valor": valor_parte,
                }
            )
    if not registros:
        return pd.DataFrame(columns=["data", "ano", "programa", "acao", "bairro_oficial", "bairro_status", "valor"])
    return pd.DataFrame(registros)
