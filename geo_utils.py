# -*- coding: utf-8 -*-
"""
Utilitários para carregar a malha geográfica (bairros.geojson) e resolver
nomes de bairro "sujos" (vindos da planilha) para o nome oficial usado
no geojson.
"""

import json
import re
import unicodedata

import streamlit as st

import config


def normalizar(texto) -> str:
    """Remove acentos, espaços extras e coloca em maiúsculas, para permitir
    comparar nomes de bairro escritos de formas diferentes
    (ex.: 'américa', 'AMERICA' e 'América' viram todos 'AMERICA')."""
    if not isinstance(texto, str):
        return ""
    texto = texto.strip().rstrip(":;,.").strip()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"\s+", " ", texto)
    return texto.upper().strip()


@st.cache_resource(show_spinner=False)
def carregar_geojson():
    with open(config.GEOJSON_PATH, encoding="utf-8") as f:
        return json.load(f)


@st.cache_resource(show_spinner=False)
def bairros_oficiais() -> dict:
    """Dicionário {nome_normalizado: nome_oficial_como_no_geojson}."""
    geo = carregar_geojson()
    nomes = [feat["properties"]["nome_bairr"] for feat in geo["features"]]
    return {normalizar(n): n for n in nomes}


@st.cache_resource(show_spinner=False)
def lista_bairros_oficiais() -> list:
    return sorted(bairros_oficiais().values())


def resolver_bairro(nome_bruto: str):
    """Recebe um único nome de bairro (já sem o ';' de múltiplos bairros)
    e devolve (nome_para_exibicao, status), onde status é 'mapeado' ou
    'nao_mapeado'."""
    if not nome_bruto or not str(nome_bruto).strip():
        return config.BAIRRO_NAO_INFORMADO, "nao_informado"

    norm = normalizar(nome_bruto)
    norm = config.BAIRRO_CORRECOES.get(norm, norm)

    oficiais = bairros_oficiais()
    if norm in oficiais:
        return oficiais[norm], "mapeado"

    return config.BAIRRO_NAO_MAPEADO, "nao_mapeado"


def dividir_bairros_citados(texto_bairro: str) -> list:
    """Quebra uma célula 'Bairro' que pode citar mais de um bairro,
    separados por ';' (ex.: 'Fátima; Glória:')."""
    if not texto_bairro or not str(texto_bairro).strip():
        return []
    partes = re.split(r"[;]", str(texto_bairro))
    partes = [p.strip().rstrip(":;,.").strip() for p in partes]
    return [p for p in partes if p]
