import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

NOME_PLANILHA = "notas"

COLUNAS_NOTA = ["teste1", "teste2"]
COLUNAS = ["Nome", "Turma", "Nivel"] + COLUNAS_NOTA + ["presença"]

st.set_page_config(page_title="Gestor de Notas", page_icon="📚", layout="wide")


@st.cache_resource
def obter_aba():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    return gspread.authorize(creds).open(NOME_PLANILHA).sheet1


def carregar_dados():
    registos = obter_aba().get_all_records()
    df = pd.DataFrame(registos)
    for col in COLUNAS:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUNAS]
    for col in COLUNAS_NOTA + ["presença"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def guardar_dados(df):
    aba = obter_aba()
    limpo = df.fillna("").astype(object)
    aba.clear()
    aba.update([COLUNAS] + limpo.values.tolist())
