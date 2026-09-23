import pandas as pd
import streamlit as st
import os

CSV_PATH = "alunos.csv"
SEP = ";"

COLUNAS_NOTA = ["teste1", "teste2"]
COLUNAS = ["Nome", "Turma", "Nivel"] + COLUNAS_NOTA + ["presença"]

st.set_page_config(page_title="Gestor de Notas", page_icon="📚", layout="wide")


def carregar_dados():
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH, sep=SEP)
        for col in COLUNAS:
            if col not in df.columns:
                df[col] = "" if col in ("Nome", "Turma", "Nivel") else pd.NA
        return df
    else:
        return pd.DataFrame(columns=COLUNAS)


def guardar_dados(df):
    df.to_csv(CSV_PATH, sep=SEP, index=False)


# Mantém os dados na sessão para não reler o ficheiro a cada clique
if "df" not in st.session_state:
    st.session_state.df = carregar_dados()

df = st.session_state.df

st.title("📚 Gestor de Notas")

aba_pesquisar, aba_editar, aba_listar = st.tabs(
    ["🔍 Pesquisar", "✏️ Introduzir / Atualizar", "📋 Listar todos"]
)

# ---------- ABA 1: PESQUISAR ----------
with aba_pesquisar:
    nome_pesquisa = st.text_input("Nome do aluno a pesquisar")
    if nome_pesquisa:
        resultado = df[df["Nome"].str.contains(nome_pesquisa, case=False, na=False)]
        if resultado.empty:
            st.warning(f"Nenhum aluno encontrado com o nome '{nome_pesquisa}'.")
        else:
            st.dataframe(resultado, use_container_width=True, hide_index=True)

# ---------- ABA 2: INTRODUZIR / ATUALIZAR ----------
with aba_editar:
    nome_editar = st.text_input("Nome do aluno", key="nome_editar")

    if nome_editar:
        correspondencias = df[df["Nome"].str.lower() == nome_editar.lower()]

        if correspondencias.empty:
            st.info(f"Aluno '{nome_editar}' não encontrado. Preencha os dados para o adicionar.")
            with st.form("form_novo_aluno"):
                turma = st.text_input("Turma")
                nivel = st.text_input("Nível")
                presenca = st.number_input("Presença", step=1.0)
                teste1 = st.number_input("teste1", step=0.5)
                teste2 = st.number_input("teste2", step=0.5)
                submitted = st.form_submit_button("Adicionar aluno")

                if submitted:
                    novo = {
                        "Nome": nome_editar,
                        "Turma": turma,
                        "Nivel": nivel,
                        "presença": presenca,
                        "teste1": teste1,
                        "teste2": teste2,
                    }
                    st.session_state.df = pd.concat(
                        [df, pd.DataFrame([novo])], ignore_index=True
                    )
                    guardar_dados(st.session_state.df)
                    st.success(f"Aluno '{nome_editar}' adicionado.")
                    st.rerun()
        else:
            idx = correspondencias.index[0]
            st.write("Dados atuais:")
            st.dataframe(correspondencias, use_container_width=True, hide_index=True)

            with st.form("form_atualizar_nota"):
                coluna = st.selectbox("Qual coluna atualizar?", COLUNAS_NOTA)
                novo_valor = st.number_input(f"Novo valor para {coluna}", step=0.5)
                submitted = st.form_submit_button("Atualizar")

                if submitted:
                    st.session_state.df.loc[idx, coluna] = novo_valor
                    guardar_dados(st.session_state.df)
                    st.success(f"{coluna} de '{nome_editar}' atualizado para {novo_valor}.")
                    st.rerun()

# ---------- ABA 3: LISTAR TODOS ----------
with aba_listar:
    if df.empty:
        st.info("(sem alunos registados)")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"Total: {len(df)} alunos")