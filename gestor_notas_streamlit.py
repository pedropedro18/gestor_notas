from datetime import date

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

NOME_PLANILHA = "notas"
NOME_ABA_PRESENCAS = "presencas"

COLUNAS_NOTA = ["teste1", "teste2"]
COLUNAS = ["Nome", "Turma", "Nivel"] + COLUNAS_NOTA + ["presença"]

st.set_page_config(page_title="Gestor de Notas", page_icon="📚", layout="wide")


# ---------- Ligação ao Google Sheets ----------
@st.cache_resource
def obter_planilha():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    return gspread.authorize(creds).open(NOME_PLANILHA)


def obter_aba():
    return obter_planilha().sheet1


def obter_aba_presencas():
    planilha = obter_planilha()
    try:
        return planilha.worksheet(NOME_ABA_PRESENCAS)
    except gspread.WorksheetNotFound:
        aba = planilha.add_worksheet(NOME_ABA_PRESENCAS, rows=1000, cols=3)
        aba.append_row(["data", "aluno", "presente"])
        return aba


# ---------- Notas: carregar e guardar ----------
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


# ---------- Presenças ----------
def carregar_presencas():
    registos = obter_aba_presencas().get_all_records()
    df = pd.DataFrame(registos, columns=["data", "aluno", "presente"])
    df["presente"] = pd.to_numeric(df["presente"], errors="coerce")
    return df


def atualizar_coluna_presenca(df_notas, df_presencas):
    """Preenche a coluna 'presença' com a % de presenças de cada aluno."""
    if df_presencas.empty:
        return df_notas
    pct = (df_presencas.groupby("aluno")["presente"].mean() * 100).round(0)
    df_notas = df_notas.copy()
    df_notas["presença"] = df_notas["Nome"].map(pct).combine_first(
        df_notas["presença"]
    )
    return df_notas


def pagina_presencas():
    st.title("📋 Presenças")
    df = carregar_dados()

    if df.empty or df["Nome"].eq("").all():
        st.info("Ainda não há alunos. Adiciona alunos na página Notas.")
        return

    turmas = sorted(df["Turma"].astype(str).unique())
    turma = st.selectbox("Turma", turmas)
    alunos = df[df["Turma"].astype(str) == turma]["Nome"].tolist()
    dia = st.date_input("Data", date.today())

    existentes = carregar_presencas()
    ja_existe = (
        not existentes.empty
        and (
            (existentes["data"].astype(str) == str(dia))
            & existentes["aluno"].isin(alunos)
        ).any()
    )
    if ja_existe:
        st.warning("Já há presenças guardadas para esta turma neste dia.")

    st.subheader("Chamada")
    marcados = {
        a: st.checkbox(a, value=True, key=f"p_{turma}{dia}{a}") for a in alunos
    }

    if st.button("Guardar presenças", disabled=ja_existe):
        obter_aba_presencas().append_rows(
            [[str(dia), a, 1 if p else 0] for a, p in marcados.items()]
        )
        # atualiza a coluna "presença" na folha de notas
        novas = carregar_presencas()
        guardar_dados(atualizar_coluna_presenca(df, novas))
        st.success("Presenças guardadas!")
        st.rerun()

    if not existentes.empty:
        st.subheader("% de presenças")
        resumo = existentes.groupby("aluno")["presente"].mean() * 100
        st.dataframe(resumo.round(0).rename("% presença"), use_container_width=True)

        with st.expander("Histórico"):
            st.dataframe(existentes.sort_values("data", ascending=False),
                         use_container_width=True)


# ---------- Notas ----------
def pagina_notas():
    st.title("📚 Gestor de Notas")
    df = carregar_dados()

    filtro = st.selectbox(
        "Filtrar por turma",
        ["Todas"] + sorted(df["Turma"].astype(str).unique().tolist()),
    )
    vista = df if filtro == "Todas" else df[df["Turma"].astype(str) == filtro]

    st.subheader("Editar notas")
    editado = st.data_editor(
        vista,
        num_rows="dynamic",
        use_container_width=True,
        key="editor_notas",
    )

    if st.button("Guardar alterações"):
        if filtro == "Todas":
            final = editado
        else:
            resto = df[df["Turma"].astype(str) != filtro]
            final = pd.concat([resto, editado], ignore_index=True)
        guardar_dados(final)
        st.success("Notas guardadas!")
        st.rerun()

    st.subheader("Médias")
    medias = vista.copy()
    medias["Média"] = medias[COLUNAS_NOTA].mean(axis=1).round(1)
    st.dataframe(medias[["Nome", "Turma", "Média"]], use_container_width=True)


# ---------- Menu ----------
pagina = st.sidebar.radio("Menu", ["Notas", "Presenças"])

if pagina == "Presenças":
    pagina_presencas()
else:
    pagina_notas()