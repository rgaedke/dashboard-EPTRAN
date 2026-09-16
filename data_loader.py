# -*- coding: utf-8 -*-
"""
Carregamento dos dados brutos das abas "Base de Dados_AAAA".

Duas fontes possíveis (controladas por config.DATA_SOURCE):
  - "google_sheets": lê a planilha online via API do Google (conta de
    serviço). É o modo de produção, usado no deploy no Streamlit Cloud.
  - "local_ods": lê o arquivo .ods local (dados_locais_teste.ods). Útil
    para testar o dashboard sem precisar configurar credenciais do Google.

As duas funções devolvem o MESMO formato: um DataFrame "cru", com uma
linha por linha da planilha (texto puro, sem limpeza), contendo as
colunas 0..N_COLUNAS_RELEVANTES-1 (posição = letra da coluna) mais a
coluna 'ano_aba' com o ano identificado pelo nome da aba. A limpeza e
a tipagem ficam por conta de data_processing.py.
"""

import pandas as pd
import streamlit as st

import config


def _preencher_linha(linha: list, largura: int = config.N_COLUNAS_RELEVANTES) -> list:
    """Garante que toda linha tenha 'largura' colunas (o Google Sheets/ODF
    pode devolver linhas mais curtas quando as últimas células estão vazias)."""
    linha = list(linha)[:largura]
    if len(linha) < largura:
        linha = linha + [""] * (largura - len(linha))
    return linha


# ---------------------------------------------------------------------------
# Fonte: Google Sheets (produção)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def _cliente_google_sheets():
    """Autentica com a conta de serviço configurada em st.secrets.

    Espera um bloco no secrets.toml (local) ou no gerenciador de Secrets
    do Streamlit Cloud (produção) assim:

        [gcp_service_account]
        type = "service_account"
        project_id = "..."
        private_key_id = "..."
        private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
        client_email = "...@....iam.gserviceaccount.com"
        client_id = "..."
        token_uri = "https://oauth2.googleapis.com/token"

    (são exatamente os campos do JSON baixado ao criar a conta de serviço
    no Google Cloud — veja o README.md para o passo a passo completo).
    """
    import gspread
    from google.oauth2.service_account import Credentials

    escopos = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    info = dict(st.secrets["gcp_service_account"])
    credenciais = Credentials.from_service_account_info(info, scopes=escopos)
    return gspread.authorize(credenciais)


@st.cache_data(ttl=config.CACHE_TTL_SEGUNDOS, show_spinner="Carregando dados da planilha...")
def carregar_dados_google_sheets() -> pd.DataFrame:
    import gspread

    cliente = _cliente_google_sheets()
    planilha = cliente.open_by_key(config.SHEET_ID)

    blocos = []
    for nome_aba, ano in config.SHEET_TABS.items():
        try:
            aba = planilha.worksheet(nome_aba)
        except gspread.exceptions.WorksheetNotFound:
            st.warning(f"Aba '{nome_aba}' não encontrada na planilha — ignorada.")
            continue

        valores = aba.get_all_values()
        if len(valores) < 2:
            continue  # só cabeçalho ou aba vazia

        linhas = [_preencher_linha(v) for v in valores[1:]]  # pula cabeçalho
        df_aba = pd.DataFrame(linhas)
        df_aba["ano_aba"] = ano
        blocos.append(df_aba)

    if not blocos:
        return pd.DataFrame()

    return pd.concat(blocos, ignore_index=True)


# ---------------------------------------------------------------------------
# Fonte: arquivo .ods local (teste/desenvolvimento)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=config.CACHE_TTL_SEGUNDOS, show_spinner="Carregando dados do arquivo local...")
def carregar_dados_ods_local() -> pd.DataFrame:
    blocos = []
    for nome_aba, ano in config.SHEET_TABS.items():
        try:
            df_aba = pd.read_excel(
                config.LOCAL_ODS_PATH, engine="odf", sheet_name=nome_aba,
                header=None, skiprows=1,
            )
        except ValueError:
            st.warning(f"Aba '{nome_aba}' não encontrada no arquivo local — ignorada.")
            continue

        df_aba = df_aba.iloc[:, :config.N_COLUNAS_RELEVANTES]
        # Garante largura fixa mesmo se a aba tiver menos colunas
        for i in range(df_aba.shape[1], config.N_COLUNAS_RELEVANTES):
            df_aba[i] = ""
        df_aba.columns = range(config.N_COLUNAS_RELEVANTES)
        # fillna ANTES do astype(str): em versões recentes do pandas,
        # converter NaN direto para string pode preservar um valor nulo
        # em vez do texto "nan", então tratamos o vazio primeiro.
        df_aba = df_aba.fillna("").astype(str)
        df_aba["ano_aba"] = ano
        blocos.append(df_aba)

    if not blocos:
        return pd.DataFrame()

    return pd.concat(blocos, ignore_index=True)


def carregar_dados_brutos() -> pd.DataFrame:
    """Ponto único de entrada: decide a fonte conforme config.DATA_SOURCE."""
    if config.DATA_SOURCE == "local_ods":
        return carregar_dados_ods_local()
    return carregar_dados_google_sheets()
