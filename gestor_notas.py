import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

NOME_PLANILHA = "notas"

COLUNAS_NOTA = ["teste1", "teste2", "teste3"]
COLUNAS = ["Nome", "Turma", "Classe"] + COLUNAS_NOTA + ["Média"]

st.set_page_config(page_title="Gestor de Notas", page_icon="📚", layout="wide")


# ---------------- LOGIN ----------------
def check_password():
    def password_entered():
        user = st.session_state["username"]
        pwd = st.session_state["password"]
        if user in st.secrets["passwords"] and pwd == st.secrets["passwords"][user]:
            st.session_state["password_correct"] = True
            st.session_state["user"] = user
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input("Utilizador", key="username")
    st.text_input("Password", type="password", key="password", on_change=password_entered)

    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("Utilizador ou password incorretos")

    return False


if not check_password():
    st.stop()
# ----------------------------------------


@st.cache_resource
def obter_aba():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    return gspread.authorize(creds).open_by_key("12lPK894LS8RMpNu8LOeL0UGasjIwX2JKctSsNfSg52E").sheet1


def carregar_dados():
    registos = obter_aba().get_all_records()
    df = pd.DataFrame(registos)
    for col in COLUNAS:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUNAS]
    for col in COLUNAS_NOTA:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Média"] = df[COLUNAS_NOTA].mean(axis=1).round(2)
    return df


def guardar_dados(df):
    aba = obter_aba()
    limpo = df.fillna("").astype(object)
    aba.clear()
    aba.update([COLUNAS] + limpo.values.tolist())


# ---------------- INTERFACE ----------------

st.title("📚 Gestor de Notas")

df = carregar_dados()

if st.session_state["user"] == "admin":
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🔍 Pesquisar", "✏️ Introduzir / Atualizar", "📋 Listar todos", "🗑️ Remover aluno"]
    )
else:
    tab1, tab2, tab3 = st.tabs(["🔍 Pesquisar", "✏️ Introduzir / Atualizar", "📋 Listar todos"])

# --- TAB 1: Pesquisar ---
with tab1:
    st.subheader("Pesquisar aluno")

    tipo_pesquisa = st.radio(
        "Pesquisar por:", ["Nome", "Turma", "Classe"], horizontal=True, key="tipo_pesquisa"
    )

    if tipo_pesquisa == "Nome":
        nome_pesquisa = st.text_input("Nome do aluno", key="pesquisa_nome")
        if nome_pesquisa:
            resultado = df[df["Nome"].str.contains(nome_pesquisa, case=False, na=False)]
        else:
            resultado = None

    elif tipo_pesquisa == "Turma":
        turmas = sorted([t for t in df["Turma"].unique().tolist() if str(t).strip() != ""])
        if turmas:
            turma_escolhida = st.selectbox("Escolhe a turma", turmas, key="pesquisa_turma")
            resultado = df[df["Turma"] == turma_escolhida]
        else:
            st.info("Ainda não há turmas registadas.")
            resultado = None

    else:  # Classe
        classes = sorted([c for c in df["Classe"].unique().tolist() if str(c).strip() != ""])
        if classes:
            classe_escolhida = st.selectbox("Escolhe a classe", classes, key="pesquisa_classe")
            resultado = df[df["Classe"] == classe_escolhida]
        else:
            st.info("Ainda não há classes registadas.")
            resultado = None

    if resultado is not None:
        if resultado.empty:
            st.warning("Nenhum aluno encontrado.")
        else:
            st.dataframe(resultado, use_container_width=True)
    elif tipo_pesquisa == "Nome":
        st.info("Escreve um nome para pesquisar.")

# --- TAB 2: Introduzir / Atualizar ---
with tab2:
    st.subheader("Introduzir ou atualizar aluno")
    with st.form("form_aluno", clear_on_submit=True):
        nome = st.text_input("Nome")
        turma = st.text_input("Turma")
        classe = st.text_input("Classe")

        notas = []
        cols = st.columns(len(COLUNAS_NOTA))
        for i, col_nome in enumerate(COLUNAS_NOTA):
            with cols[i]:
                nota = st.number_input(
                    col_nome.capitalize(), min_value=0.0, max_value=20.0,
                    step=0.1, key=f"nota_{col_nome}"
                )
                notas.append(nota)

        submeter = st.form_submit_button("Guardar")

        if submeter:
            if not nome.strip():
                st.error("O nome é obrigatório.")
            elif not turma.strip():
                st.error("A turma é obrigatória.")
            elif not classe.strip():
                st.error("A classe é obrigatória.")
            else:
                novo_registo = {"Nome": nome, "Turma": turma, "Classe": classe}
                for i, col_nome in enumerate(COLUNAS_NOTA):
                    novo_registo[col_nome] = notas[i]

                # Considera o mesmo aluno só se Nome + Turma + Classe coincidirem
                mascara_existente = (
                    (df["Nome"] == nome) & (df["Turma"] == turma) & (df["Classe"] == classe)
                )
                df_atualizado = df[~mascara_existente]
                df_atualizado = pd.concat(
                    [df_atualizado, pd.DataFrame([novo_registo])], ignore_index=True
                )
                df_atualizado[COLUNAS_NOTA] = df_atualizado[COLUNAS_NOTA].apply(
                    pd.to_numeric, errors="coerce"
                )
                df_atualizado["Média"] = df_atualizado[COLUNAS_NOTA].mean(axis=1).round(2)

                guardar_dados(df_atualizado)
                st.success(f"Aluno '{nome}' guardado com sucesso!")
                st.cache_resource.clear()
                st.rerun()

# --- TAB 3: Listar todos ---
with tab3:
    st.subheader("Todos os alunos")
    if df.empty:
        st.info("Ainda não há alunos registados.")
    else:
        st.dataframe(df, use_container_width=True)

# --- TAB 4: Remover aluno (só admin) ---
if st.session_state["user"] == "admin":
    with tab4:
        st.subheader("Remover aluno")
        if df.empty:
            st.info("Não há alunos para remover.")
        else:
            opcoes = [
                f"{row['Nome']} — Turma {row['Turma']} — Classe {row['Classe']}"
                for _, row in df.iterrows()
            ]
            escolha = st.selectbox("Escolhe o aluno a remover", opcoes)
            indice_remover = opcoes.index(escolha)
            if st.button("🗑️ Remover", type="primary"):
                df_atualizado = df.drop(df.index[indice_remover])
                guardar_dados(df_atualizado)
                st.success(f"Aluno '{escolha}' removido com sucesso!")
                st.cache_resource.clear()
                st.rerun()