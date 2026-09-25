import pandas as pd
import streamlit as st
package__icon=""

# Cola aqui o teu link CSV, entre aspas.
# Tem de terminar em: /pub?gid=0&single=true&output=csv
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDwUteKiNMbV3SVjNemowuMObVqkNdGw8naGvxsJfKgLUnJk5wo9ACjL6YI3s6HjJ5tHChqdx-K_Bk/pub?gid=0&single=true&output=csv"


@st.cache_data(ttl=60)
def carregar():
    df = pd.read_csv(URL)
    # remove a coluna "média" da folha (a app calcula a sua)
    df = df.drop(columns=[c for c in df.columns if c.lower() in ("média", "media")])
    # garante que os testes são números
    testes = [c for c in df.columns if c.lower().startswith("teste")]
    df[testes] = df[testes].apply(pd.to_numeric, errors="coerce")
    df["media"] = df[testes].mean(axis=1).round(2)
    return df


df = carregar()

st.title("Gestor de Notas")

st.sidebar.title("Menu")
opcao = st.sidebar.radio(
    "Escolhe uma opção",
    ["Pesquisar aluno", "Introduzir / atualizar nota", "Listar todos os alunos"],
)

if opcao == "Pesquisar aluno":
    nome = st.text_input("Nome do aluno")
    if nome:
        resultado = df[df["Nome"].str.contains(nome, case=False, na=False)]
        if resultado.empty:
            st.warning("Aluno não encontrado.")
        else:
            st.dataframe(resultado, hide_index=True)

elif opcao == "Introduzir / atualizar nota":
    st.info(
        "Com o link publicado (só leitura), a app não consegue gravar notas. "
        "Altera as notas diretamente na folha do Google Sheets e a app "
        "atualiza em cerca de 1 minuto."
    )

else:
    st.dataframe(df, hide_index=True)
    st.caption(f"Total de alunos: {len(df)}")


