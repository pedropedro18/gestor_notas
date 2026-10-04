from datetime import date

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

PLANILHA_ID = "12lPK894LS8RMpNu8LOeL0UGasjIwX2JKctSsNfSg52E"
NOME_ABA_PRESENCAS = "presencas"
COLUNAS_PRESENCAS = ["data", "turma", "classe", "aluno", "presente"]

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
def obter_planilha():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    return gspread.authorize(creds).open_by_key(PLANILHA_ID)


def obter_aba():
    return obter_planilha().sheet1


def obter_aba_presencas():
    planilha = obter_planilha()
    try:
        return planilha.worksheet(NOME_ABA_PRESENCAS)
    except gspread.WorksheetNotFound:
        aba = planilha.add_worksheet(NOME_ABA_PRESENCAS, rows=2000, cols=5)
        aba.append_row(COLUNAS_PRESENCAS)
        return aba


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


def carregar_presencas():
    registos = obter_aba_presencas().get_all_records()
    df = pd.DataFrame(registos, columns=COLUNAS_PRESENCAS)
    df["presente"] = pd.to_numeric(df["presente"], errors="coerce")
    return df


# ---------------- INTERFACE ----------------

with st.sidebar:
    st.markdown(f"👤 Utilizador: {st.session_state['user']}")
    if st.button("🚪 Sair / Trocar utilizador"):
        for chave in ["password_correct", "user", "username"]:
            if chave in st.session_state:
                del st.session_state[chave]
        st.rerun()

st.title("📚 Gestor de Notas")

df = carregar_dados()

eh_admin = st.session_state["user"] == "admin"

nomes_tabs = ["🔍 Pesquisar", "✏️ Introduzir / Atualizar", "📋 Listar todos", "✅ Presenças"]
if eh_admin:
    nomes_tabs.append("🗑️ Remover aluno")

tabs = st.tabs(nomes_tabs)
tab1, tab2, tab3, tab_pres = tabs[0], tabs[1], tabs[2], tabs[3]
tab4 = tabs[4] if eh_admin else None

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

# --- TAB PRESENÇAS ---
with tab_pres:
    st.subheader("Presenças")

    modo = st.radio(
        "Opção:", ["Marcar chamada por turma", "Ver por turma"],
        horizontal=True, key="pres_modo"
    )

    alunos_validos = df[df["Nome"].astype(str).str.strip() != ""]
    if alunos_validos.empty:
        st.info("Ainda não há alunos registados.")
    else:
        turmas_p = sorted(alunos_validos["Turma"].astype(str).unique().tolist())
        turma_p = st.selectbox("Turma", turmas_p, key="pres_turma")
        da_turma = alunos_validos[alunos_validos["Turma"].astype(str) == turma_p]
        existentes = carregar_presencas()

        # ---------- VER POR TURMA ----------
        if modo == "Ver por turma":
            ex = existentes[existentes["turma"].astype(str) == str(turma_p)]
            if ex.empty:
                st.info("Ainda não há presenças para esta turma.")
            else:
                st.markdown("*% de presença por aluno (toda a turma)*")
                resumo = (
                    ex.groupby(["aluno", "classe"])["presente"]
                    .agg(Aulas="count", Presenças="sum")
                    .reset_index()
                )
                resumo["% presença"] = (resumo["Presenças"] / resumo["Aulas"] * 100).round(0)
                st.dataframe(resumo, use_container_width=True)

                st.markdown("*Presenças por dia*")
                por_dia = (
                    ex.groupby(["data", "classe"])["presente"]
                    .agg(Alunos="count", Presentes="sum")
                    .reset_index()
                    .sort_values("data", ascending=False)
                )
                por_dia["Faltas"] = por_dia["Alunos"] - por_dia["Presentes"]
                st.dataframe(por_dia, use_container_width=True)

                with st.expander("Histórico completo"):
                    st.dataframe(
                        ex.sort_values("data", ascending=False),
                        use_container_width=True,
                    )

        # ---------- MARCAR CHAMADA POR TURMA ----------
        else:
            dia = st.date_input("Data", date.today(), key="pres_data")

            # Classes da turma que já têm presenças guardadas neste dia
            if existentes.empty:
                classes_feitas = set()
            else:
                feitas = existentes[
                    (existentes["data"].astype(str) == str(dia))
                    & (existentes["turma"].astype(str) == str(turma_p))
                ]
                classes_feitas = set(feitas["classe"].astype(str).unique().tolist())

            classes_p = sorted(da_turma["Classe"].astype(str).unique().tolist())
            classes_pendentes = [c for c in classes_p if c not in classes_feitas]

            if classes_feitas:
                st.warning(
                    "Já há presenças guardadas neste dia para a(s) classe(s): "
                    + ", ".join(sorted(classes_feitas))
                )

            if not classes_pendentes:
                st.success("A chamada desta turma já está completa para este dia.")
            else:
                st.markdown("*Chamada da turma* (desmarca quem faltou)")
                marcados = {}
                for c in classes_pendentes:
                    st.markdown(f"*Classe {c}*")
                    grupo = da_turma[da_turma["Classe"].astype(str) == c]
                    for a in grupo["Nome"].tolist():
                        marcados[(c, a)] = st.checkbox(
                            a, value=True, key=f"pres_{turma_p}{c}{dia}_{a}"
                        )

                if st.button("💾 Guardar presenças da turma", key="pres_guardar"):
                    obter_aba_presencas().append_rows(
                        [
                            [str(dia), str(turma_p), str(c), a, 1 if p else 0]
                            for (c, a), p in marcados.items()
                        ]
                    )
                    st.success("Presenças guardadas!")
                    st.rerun()

# --- TAB 4: Remover aluno (só admin) ---
if eh_admin:
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