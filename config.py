# -*- coding: utf-8 -*-
"""
Configurações centrais do Dashboard EPTRAN.
Altere aqui o que for necessário (fonte de dados, cores, textos, etc.)
sem precisar mexer no resto do código.
"""

from pathlib import Path

BASE_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# Fonte de dados
# ---------------------------------------------------------------------------
# "google_sheets" -> lê da planilha online (produção / Streamlit Cloud)
# "local_ods"      -> lê do arquivo .ods local (teste/desenvolvimento, sem
#                      precisar configurar credenciais do Google)
DATA_SOURCE = "google_sheets"

# ID da planilha (extraído da URL compartilhada)
# https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit
SHEET_ID = "13pLTKJgZRnA6cA4ZaxSZDm7wtvPBbI41Rx-pijOhNK0"

# Abas consideradas no pipeline (nome exato da aba -> ano correspondente)
SHEET_TABS = {
    "Base de Dados_2022": 2022,
    "Base de Dados_2023": 2023,
    "Base de Dados_2024": 2024,
    "Base de Dados_2025": 2025,
    "Base de Dados_2026": 2026,
}

# Arquivo local usado quando DATA_SOURCE = "local_ods"
LOCAL_ODS_PATH = BASE_DIR / "dados_locais_teste.ods"

# Malha geográfica dos bairros (arquivo local, conforme a especificação)
GEOJSON_PATH = BASE_DIR / "bairros.geojson"

# Tempo (segundos) que os dados ficam em cache antes de recarregar da planilha
CACHE_TTL_SEGUNDOS = 600

# ---------------------------------------------------------------------------
# Posições das colunas relevantes na planilha (0-indexado, A=0, B=1, ...)
# Confirmado por inspeção real dos dados: a posição é estável em todas as
# abas (2022-2026), mesmo quando o texto do cabeçalho varia um pouco
# (ex.: "Ação" vs "Açao" em 2026). Por isso lemos por POSIÇÃO, não por nome.
# ---------------------------------------------------------------------------
COL_DIA = 1        # B - Dia
COL_MES = 2        # C - Mês
COL_PROGRAMA = 3   # D - Programa
COL_ACAO = 4       # E - Ação
COL_BAIRRO = 8     # I - Bairro
COL_PUBLICO = 9    # J - Público
COL_TOTAL = 12     # M - Total - Dia
N_COLUNAS_RELEVANTES = 13  # de A (0) até M (12)

# ---------------------------------------------------------------------------
# Meses em português -> número (chave já normalizada: maiúscula, sem acento)
# ---------------------------------------------------------------------------
MESES_PT = {
    "JANEIRO": 1, "FEVEREIRO": 2, "MARCO": 3, "ABRIL": 4,
    "MAIO": 5, "JUNHO": 6, "JULHO": 7, "AGOSTO": 8,
    "SETEMBRO": 9, "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12,
}

# ---------------------------------------------------------------------------
# Correções manuais de bairros com erro de digitação claro na planilha,
# mapeando para o nome oficial (normalizado) presente no bairros.geojson.
# Bairros que NÃO existem no geojson (ex.: "Garuva" é outro município;
# "Distrito Industrial", "Palmeiras", "Morro do Amaral", "Zona Rural",
# "Zona Industrial" sem especificar Norte/Tupy, "Guimarães") ficam de fora
# desta lista de propósito: caem no grupo "Não mapeado" (aparecem nos
# totais e filtros gerais, mas não no mapa / Top 15), conforme definido.
# ---------------------------------------------------------------------------
BAIRRO_CORRECOES = {
    "AVENTREIRO": "AVENTUREIRO",
    "PARAAGUAMIRIM": "PARANAGUAMIRIM",
    "PIRABEIRADA": "PIRABEIRABA",
    "SANTA CATARIA": "SANTA CATARINA",
    "ZONA IND NORTE": "ZONA INDUSTRIAL NORTE",
    "CUBATAO": "VILA CUBATAO",
    "CENTRO (PIRABEIRABA)": "PIRABEIRABA",
    "CENTRO(PIRAEIRABA)": "PIRABEIRABA",
}

BAIRRO_NAO_MAPEADO = "Não mapeado"
BAIRRO_NAO_INFORMADO = "Não informado"

# ---------------------------------------------------------------------------
# Paleta de cores (conforme especificação do documento)
# ---------------------------------------------------------------------------
COR_FUNDO = "#FFFFFF"
COR_FUNDO_ALT = "#F8F9FA"
COR_BORDA = "#E9ECEF"
COR_TEXTO = "#212529"

AZUL_ESCURO = "#002B49"
AZUL_PETROLEO = "#004C6D"
AZUL_MEDIO = "#257D9D"
AZUL_CLARO = "#4A90E2"

ESCALA_AZUL_PETROLEO = [
    [0.0, "#E9ECEF"],
    [0.25, "#4A90E2"],
    [0.55, "#257D9D"],
    [0.8, "#004C6D"],
    [1.0, "#002B49"],
]

CORES_SANKEY = [AZUL_ESCURO, AZUL_PETROLEO, AZUL_MEDIO, AZUL_CLARO]

# ---------------------------------------------------------------------------
# Comportamento do modo kiosk
# ---------------------------------------------------------------------------
INTERVALO_AUTOPLAY_MS = 15_000
NOMES_TELAS = [
    "Tela 1 · Visão Geral",
    "Tela 2 · Mapa por Bairro",
    "Tela 3 · Comparativos e Evolução",
]

# Centro aproximado de Joinville/SC, usado no mapa
JOINVILLE_LAT = -26.3045
JOINVILLE_LON = -48.8487
