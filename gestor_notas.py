import pandas as pd
import os
import streamlit as st

CSV_PATH = "alunos.csv"
SEP = ";"

COLUNAS_NOTA = ["teste1", "teste2", "teste3"]
COLUNAS = ["Nome", "Turma", "Nivel"] + COLUNAS_NOTA + ["media"]


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


# --- estado inicial ---
if "df" not in st.session_state:
    st.session_state.df = carregar_dados()

df = st.session_state.df

st.title("Gestor de Notas")

aba = st.sidebar.radio(
    "Menu",
    ["Pesquisar aluno", "Introduzir / atualizar nota", "Listar todos os alunos"],
)

# --- 1. Pesquisar ---
if aba == "Pesquisar aluno":
    nome = st.text_input("Nome do aluno a pesquisar")
    if nome:
        resultado = df[df["Nome"].str.contains(nome, case=False, na=False)]
        if resultado.empty:
            st.warning(f"Nenhum aluno encontrado com o nome '{nome}'.")
        else:
            st.dataframe(resultado, use_container_width=True)

# --- 2. Introduzir / atualizar ---
elif aba == "Introduzir / atualizar nota":
    nome = st.text_input("Nome do aluno")

    if nome:
        correspondencias = df[df["Nome"].str.lower() == nome.lower()]

        if correspondencias.empty:
            st.info(f"Aluno '{nome}' não encontrado.")
            with st.form("novo_aluno"):
                turma = st.text_input("Turma")
                nivel = st.text_input("Nível")
                notas = {}
                for col in COLUNAS_NOTA:
                    notas[col] = st.number_input(col, step=0.5)
                submitted = st.form_submit_button("Adicionar aluno")

                if submitted:
                    media = sum(notas.values()) / len(notas) if notas else 0
                    novo = {"Nome": nome, "Turma": turma, "Nivel": nivel, "media": media}
                    novo.update(notas)
                    st.session_state.df = pd.concat(
                        [df, pd.DataFrame([novo])], ignore_index=True
                    )
                    guardar_dados(st.session_state.df)
                    st.success(f"Aluno '{nome}' adicionado.")
                    st.rerun()
        else:
            idx = correspondencias.index[0]
            coluna = st.selectbox("Qual coluna?", COLUNAS_NOTA)
            valor = st.number_input(f"Novo valor para {coluna}", step=0.5)

            if st.button("Atualizar"):
                st.session_state.df.loc[idx, coluna] = valor
                notas_atuais = [st.session_state.df.loc[idx, c] for c in COLUNAS_NOTA]
                st.session_state.df.loc[idx, "media"] = sum(notas_atuais) / len(notas_atuais)
                guardar_dados(st.session_state.df)
                st.success(f"{coluna} de '{df.loc[idx, 'Nome']}' atualizado para {valor}.")
                st.rerun()

# --- 3. Listar todos ---
elif aba == "Listar todos os alunos":
    if df.empty:
        st.info("(sem alunos registados)")
    else:
        st.dataframe(df, use_container_width=True)
