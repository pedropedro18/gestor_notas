import base64
import io
from datetime import date

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
from PIL import Image, ImageOps

PLANILHA_ID = "12lPK894LS8RMpNu8LOeL0UGasjIwX2JKctSsNfSg52E"
NOME_ABA_PRESENCAS = "presencas"
COLUNAS_PRESENCAS = ["data", "turma", "classe", "aluno", "presente"]
NOME_ABA_ATIVIDADES = "atividades"
COLUNAS_ATIV = ["data", "turma", "descricao", "foto"]

COLUNAS_NOTA = ["teste1", "teste2", "teste3"]
COLUNAS = ["Nome", "Turma", "Classe"] + COLUNAS_NOTA + ["Média"]

st.set_page_config(page_title="Gestor Escolar", page_icon="🏫", layout="wide")

# ---------------- ESTILO ----------------
CSS = """
<style>
:root {
  --azul: #2563eb;
  --roxo: #7c3aed;
  --texto: #1f2437;
  --suave: #6b7280;
  --borda: #e5e8f0;
}

/* Fundo e largura */
.stApp { background: linear-gradient(180deg, #f5f7fb 0%, #eef1f9 100%); }
.block-container { padding-top: 2rem; max-width: 1150px; }

/* Cabeçalho principal */
.hero {
  background: linear-gradient(135deg, var(--azul), var(--roxo));
  color: #fff;
  padding: 1.6rem 1.8rem;
  border-radius: 20px;
  margin-bottom: 1.2rem;
  box-shadow: 0 10px 30px rgba(37, 99, 235, 0.25);
}
.hero h1 { color: #fff; margin: 0; font-size: 2rem; padding: 0; }
.hero p { color: rgba(255,255,255,0.85); margin: 0.3rem 0 0; font-size: 1rem; }

/* Separadores (tabs) em forma de botões */
.stTabs [data-baseweb="tab-list"] {
  gap: 0.4rem;
  background: #fff;
  padding: 0.4rem;
  border-radius: 14px;
  border: 1px solid var(--borda);
  overflow-x: auto;
}
.stTabs [data-baseweb="tab"] {
  height: 42px;
  padding: 0 1rem;
  border-radius: 10px;
  font-weight: 600;
  color: var(--suave);
  transition: all 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover { background: #eef2ff; color: var(--azul); }
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, var(--azul), var(--roxo));
  color: #fff !important;
}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

/* Cartões de métricas */
[data-testid="stMetric"] {
  background: #fff;
  border: 1px solid var(--borda);
  border-radius: 16px;
  padding: 1rem 1.2rem;
  box-shadow: 0 2px 10px rgba(31, 36, 55, 0.05);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
[data-testid="stMetric"]:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.15);
}
[data-testid="stMetricValue"] { color: var(--azul); font-weight: 800; }

/* Contentores com borda (cartões) */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: #fff;
  border-radius: 16px !important;
  border: 1px solid var(--borda) !important;
  box-shadow: 0 2px 10px rgba(31, 36, 55, 0.04);
}

/* Botões */
.stButton > button, .stFormSubmitButton > button {
  border-radius: 12px;
  font-weight: 600;
  border: 1px solid var(--borda);
  padding: 0.55rem 1.2rem;
  transition: all 0.2s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.25);
  border-color: var(--azul);
  color: var(--azul);
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--azul), var(--roxo));
  color: #fff;
  border: none;
}
.stButton > button[kind="primary"]:hover { color: #fff; }

/* Campos */
.stTextInput input, .stTextArea textarea, .stNumberInput input,
.stSelectbox [data-baseweb="select"] > div, .stDateInput input {
  border-radius: 10px !important;
}

/* Tabelas */
[data-testid="stDataFrame"] {
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid var(--borda);
}

/* Etiquetas */
.badge {
  display: inline-block;
  padding: 0.2rem 0.8rem;
  border-radius: 999px;
  background: #eef2ff;
  color: var(--azul);
  font-weight: 700;
  font-size: 0.85rem;
}
.badge.verde { background: #dcfce7; color: #15803d; }

/* Barra lateral */
[data-testid="stSidebar"] { background: #fff; border-right: 1px solid var(--borda); }
.perfil {
  display: flex; align-items: center; gap: 0.8rem;
  padding: 0.8rem; border-radius: 14px;
  background: #f5f7ff; margin-bottom: 1rem;
}
.avatar {
  width: 44px; height: 44px; border-radius: 50%;
  display: grid; place-items: center;
  background: linear-gradient(135deg, var(--azul), var(--roxo));
  color: #fff; font-weight: 800; font-size: 1.2rem;
}
.perfil b { color: var(--texto); }
.perfil small { color: var(--suave); display: block; }

/* Login */
.login-titulo { text-align: center; margin-bottom: 0.5rem; }
.login-titulo .emoji { font-size: 3rem; }
.login-titulo h2 { margin: 0; color: var(--texto); }
.login-titulo p { color: var(--suave); margin: 0.2rem 0 0; }

/* Entrada suave */
@keyframes subir { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
.block-container > div { animation: subir 0.4s ease; }

@media (max-width: 700px) {
  .hero h1 { font-size: 1.5rem; }
  .stTabs [data-baseweb="tab"] { padding: 0 0.7rem; font-size: 0.85rem; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def cabecalho(titulo, subtitulo=""):
    sub = f"<p>{subtitulo}</p>" if subtitulo else ""
    st.markdown(f'<div class="hero"><h1>{titulo}</h1>{sub}</div>', unsafe_allow_html=True)


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

    _, centro, _ = st.columns([1, 1.3, 1])
    with centro:
        st.markdown(
            '<div class="login-titulo"><div class="emoji">🏫</div>'
            "<h2>Gestor Escolar</h2><p>Entra com o teu utilizador</p></div>",
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            with st.form("form_login"):
                st.text_input("👤 Utilizador", key="username")
                st.text_input("🔒 Password", type="password", key="password")
                st.form_submit_button(
                    "Entrar", type="primary", use_container_width=True,
                    on_click=password_entered,
                )
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


def obter_aba_atividades():
    planilha = obter_planilha()
    try:
        return planilha.worksheet(NOME_ABA_ATIVIDADES)
    except gspread.WorksheetNotFound:
        aba = planilha.add_worksheet(NOME_ABA_ATIVIDADES, rows=2000, cols=4)
        aba.append_row(COLUNAS_ATIV)
        return aba


@st.cache_data(ttl=60)
def carregar_atividades():
    registos = obter_aba_atividades().get_all_records()
    return pd.DataFrame(registos, columns=COLUNAS_ATIV)


def comprimir_foto(ficheiro):
    """Reduz a foto para caber numa célula do Google Sheets (máx. 50 000 caracteres)."""
    img = ImageOps.exif_transpose(Image.open(ficheiro)).convert("RGB")
    for lado in (720, 560, 420, 320):
        copia = img.copy()
        copia.thumbnail((lado, lado))
        for qualidade in (70, 55, 40):
            buf = io.BytesIO()
            copia.save(buf, "JPEG", quality=qualidade, optimize=True)
            b64 = base64.b64encode(buf.getvalue()).decode()
            if len(b64) <= 45000:
                return b64
    return ""


def apagar_atividade(idx, linha):
    """Apaga uma publicação da aba atividades (só admin)."""
    aba = obter_aba_atividades()
    numero_linha = idx + 2  # +1 do cabeçalho, +1 porque o índice começa em 0
    atual = [x.strip() for x in aba.row_values(numero_linha)[:3]]
    esperado = [str(linha["data"]).strip(), str(linha["turma"]).strip(),
                str(linha["descricao"]).strip()]
    st.session_state.pop("apagar_ativ", None)
    carregar_atividades.clear()
    if atual == esperado:
        aba.delete_rows(numero_linha)
        st.toast("Publicação apagada.", icon="🗑️")
    else:
        st.toast("A lista mudou entretanto. Tenta de novo.", icon="⚠️")
    st.rerun()


def mostrar_atividades(atividades, admin=False):
    if atividades.empty:
        st.info("Ainda não há atividades publicadas.", icon="📭")
        return
    for idx, linha in atividades.sort_values("data", ascending=False).iterrows():
        with st.container(border=True):
            st.markdown(
                f'<span class="badge">📅 {linha["data"]}</span> '
                f'<span class="badge verde">Turma {linha["turma"]}</span>',
                unsafe_allow_html=True,
            )
            if str(linha["descricao"]).strip():
                st.write(linha["descricao"])
            if str(linha["foto"]).strip():
                st.image(base64.b64decode(linha["foto"]), use_container_width=True)
            if admin:
                if st.session_state.get("apagar_ativ") == idx:
                    st.warning("Apagar esta publicação? Os pais deixam de a ver.")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Sim, apagar", key=f"sim_{idx}", type="primary"):
                        apagar_atividade(idx, linha)
                    if c2.button("Cancelar", key=f"nao_{idx}"):
                        st.session_state.pop("apagar_ativ", None)
                        st.rerun()
                elif st.button("🗑️ Apagar", key=f"del_{idx}"):
                    st.session_state["apagar_ativ"] = idx
                    st.rerun()


def turma_do_encarregado(utilizador):
    """Devolve a turma se o utilizador for encarregado de educação (secrets [pais_turma])."""
    try:
        return str(st.secrets["pais_turma"][utilizador])
    except Exception:
        return None


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


def tabela_alunos(dados):
    """Mostra a tabela de alunos com barras de progresso nas médias."""
    st.dataframe(
        dados,
        use_container_width=True,
        hide_index=True,
        column_config={
            "teste1": st.column_config.NumberColumn("Teste 1", format="%.1f"),
            "teste2": st.column_config.NumberColumn("Teste 2", format="%.1f"),
            "teste3": st.column_config.NumberColumn("Teste 3", format="%.1f"),
            "Média": st.column_config.ProgressColumn(
                "Média", min_value=0, max_value=20, format="%.1f"
            ),
        },
    )


def marcar_todos(chaves, valor):
    """Callback dos botões 'todos presentes' / 'todos faltaram'."""
    for k in chaves:
        st.session_state[k] = valor


# ---------------- INTERFACE ----------------

utilizador = st.session_state["user"]

with st.sidebar:
    st.markdown(
        f'<div class="perfil"><div class="avatar">{utilizador[:1].upper()}</div>'
        f"<div><b>{utilizador}</b><small>Sessão iniciada</small></div></div>",
        unsafe_allow_html=True,
    )
    if st.button("🚪 Sair / Trocar utilizador", use_container_width=True):
        for chave in ["password_correct", "user", "username"]:
            if chave in st.session_state:
                del st.session_state[chave]
        st.rerun()

turma_pai = turma_do_encarregado(utilizador)
if turma_pai is not None:
    cabecalho("📸 Atividades da turma " + turma_pai, "O que os alunos andam a fazer nas aulas")
    ativ = carregar_atividades()
    mostrar_atividades(ativ[ativ["turma"].astype(str) == turma_pai])
    st.stop()

cabecalho("🏫 Gestor Escolar", "Notas, presenças e atividades num só lugar")

df = carregar_dados()

eh_admin = utilizador == "admin"

nomes_tabs = [
    "📊 Painel",
    "🔍 Pesquisar",
    "✏️ Introduzir / Atualizar",
    "📋 Listar todos",
    "✅ Presenças",
    "📸 Atividades",
]
if eh_admin:
    nomes_tabs.append("🗑️ Remover aluno")

tabs = st.tabs(nomes_tabs)
tab_painel, tab1, tab2, tab3, tab_pres, tab_ativ = tabs[:6]
tab4 = tabs[6] if eh_admin else None

# --- TAB PAINEL ---
with tab_painel:
    alunos_ok = df[df["Nome"].astype(str).str.strip() != ""]
    if alunos_ok.empty:
        st.info("Ainda não há alunos registados. Começa no separador ✏️ Introduzir / Atualizar.", icon="👋")
    else:
        pres_all = carregar_presencas()
        media_geral = alunos_ok["Média"].mean()
        n_turmas = alunos_ok["Turma"].astype(str).nunique()
        if pres_all.empty or pres_all["presente"].dropna().empty:
            pct_pres = None
        else:
            pct_pres = pres_all["presente"].mean() * 100

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("👥 Alunos", len(alunos_ok))
        m2.metric("🏷️ Turmas", n_turmas)
        m3.metric("⭐ Média geral", "-" if pd.isna(media_geral) else f"{media_geral:.1f}")
        m4.metric("✅ Presença", "-" if pct_pres is None else f"{pct_pres:.0f}%")

        g1, g2 = st.columns(2)
        with g1:
            with st.container(border=True):
                st.markdown("Média por turma")
                media_turma = (
                    alunos_ok.assign(Turma=alunos_ok["Turma"].astype(str))
                    .groupby("Turma")["Média"].mean().round(1)
                )
                st.bar_chart(media_turma, color="#2563eb")
        with g2:
            with st.container(border=True):
                st.markdown("Alunos por turma")
                alunos_turma = alunos_ok["Turma"].astype(str).value_counts().sort_index()
                st.bar_chart(alunos_turma, color="#7c3aed")

        with st.container(border=True):
            st.markdown("🏆 Melhores médias")
            top = alunos_ok.dropna(subset=["Média"]).sort_values("Média", ascending=False).head(5)
            tabela_alunos(top)

# --- TAB 1: Pesquisar ---
with tab1:
    st.subheader("Pesquisar aluno")

    tipo_pesquisa = st.radio(
        "Pesquisar por:", ["Nome", "Turma", "Classe"], horizontal=True, key="tipo_pesquisa"
    )

    if tipo_pesquisa == "Nome":
        nome_pesquisa = st.text_input(
            "Nome do aluno", key="pesquisa_nome", placeholder="🔍 Escreve para pesquisar..."
        )
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
            st.warning("Nenhum aluno encontrado.", icon="🔎")
        else:
            r1, r2, r3 = st.columns(3)
            r1.metric("Alunos encontrados", len(resultado))
            media_res = resultado["Média"].mean()
            r2.metric("Média do grupo", "-" if pd.isna(media_res) else f"{media_res:.1f}")
            melhor = resultado["Média"].max()
            r3.metric("Melhor média", "-" if pd.isna(melhor) else f"{melhor:.1f}")
            tabela_alunos(resultado)
    elif tipo_pesquisa == "Nome":
        st.info("Escreve um nome para pesquisar.", icon="💡")

# --- TAB 2: Introduzir / Atualizar ---
with tab2:
    st.subheader("Introduzir ou atualizar aluno")
    with st.container(border=True):
        with st.form("form_aluno", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            nome = c1.text_input("Nome")
            turma = c2.text_input("Turma")
            classe = c3.text_input("Classe")

            st.markdown("Notas (0 a 20)")
            notas = []
            cols = st.columns(len(COLUNAS_NOTA))
            for i, col_nome in enumerate(COLUNAS_NOTA):
                with cols[i]:
                    nota = st.number_input(
                        col_nome.capitalize(), min_value=0.0, max_value=20.0,
                        step=0.1, key=f"nota_{col_nome}"
                    )
                    notas.append(nota)

            submeter = st.form_submit_button("💾 Guardar", type="primary")

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
                    st.toast(f"Aluno '{nome}' guardado com sucesso!", icon="✅")
                    st.cache_resource.clear()
                    st.rerun()

# --- TAB 3: Listar todos ---
with tab3:
    st.subheader("Todos os alunos")
    if df.empty:
        st.info("Ainda não há alunos registados.")
    else:
        st.caption(f"{len(df)} aluno(s) registado(s). Clica no título de uma coluna para ordenar.")
        tabela_alunos(df)

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
                st.info("Ainda não há presenças para esta turma.", icon="📭")
            else:
                pct_turma = ex["presente"].mean() * 100
                v1, v2, v3 = st.columns(3)
                v1.metric("Aulas registadas", ex["data"].nunique())
                v2.metric("Presença da turma", f"{pct_turma:.0f}%")
                v3.metric("Faltas", int((ex["presente"] == 0).sum()))

                with st.container(border=True):
                    st.markdown("% de presença por aluno (toda a turma)")
                    resumo = (
                        ex.groupby(["aluno", "classe"])["presente"]
                        .agg(Aulas="count", Presenças="sum")
                        .reset_index()
                    )
                    resumo["% presença"] = (resumo["Presenças"] / resumo["Aulas"] * 100).round(0)
                    st.dataframe(
                        resumo,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "% presença": st.column_config.ProgressColumn(
                                "% presença", min_value=0, max_value=100, format="%d%%"
                            )
                        },
                    )

                with st.container(border=True):
                    st.markdown("Presenças por dia")
                    por_dia = (
                        ex.groupby(["data", "classe"])["presente"]
                        .agg(Alunos="count", Presentes="sum")
                        .reset_index()
                        .sort_values("data", ascending=False)
                    )
                    por_dia["Faltas"] = por_dia["Alunos"] - por_dia["Presentes"]
                    st.dataframe(por_dia, use_container_width=True, hide_index=True)

                    grafico = (
                        ex.groupby("data")["presente"].mean().mul(100).round(0).sort_index()
                    )
                    st.line_chart(grafico, color="#2563eb")

                with st.expander("Histórico completo"):
                    st.dataframe(
                        ex.sort_values("data", ascending=False),
                        use_container_width=True,
                        hide_index=True,
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
                st.success("A chamada desta turma já está completa para este dia.", icon="🎉")
            else:
                # Chaves de todos os checkboxes desta chamada
                chaves = [
                    f"pres_{turma_p}{c}{dia}_{a}"
                    for c in classes_pendentes
                    for a in da_turma[da_turma["Classe"].astype(str) == c]["Nome"].tolist()
                ]

                st.markdown("Chamada da turma (desmarca quem faltou)")
                b1, b2, _ = st.columns([1, 1, 2])
                b1.button(
                    "✅ Todos presentes", use_container_width=True,
                    on_click=marcar_todos, args=(chaves, True), key="pres_todos",
                )
                b2.button(
                    "❌ Todos faltaram", use_container_width=True,
                    on_click=marcar_todos, args=(chaves, False), key="pres_nenhum",
                )

                marcados = {}
                for c in classes_pendentes:
                    with st.container(border=True):
                        st.markdown(f'<span class="badge">Classe {c}</span>', unsafe_allow_html=True)
                        grupo = da_turma[da_turma["Classe"].astype(str) == c]
                        for a in grupo["Nome"].tolist():
                            marcados[(c, a)] = st.checkbox(
                                a, value=True, key=f"pres_{turma_p}{c}{dia}_{a}"
                            )

                total = len(marcados)
                presentes = sum(1 for p in marcados.values() if p)
                st.progress(presentes / total if total else 0.0)
                st.caption(f"✅ {presentes} presentes · ❌ {total - presentes} faltas · {total} alunos")

                if st.button("💾 Guardar presenças da turma", key="pres_guardar", type="primary"):
                    obter_aba_presencas().append_rows(
                        [
                            [str(dia), str(turma_p), str(c), a, 1 if p else 0]
                            for (c, a), p in marcados.items()
                        ]
                    )
                    st.toast("Presenças guardadas!", icon="✅")
                    st.rerun()

# --- TAB ATIVIDADES (os pais veem estas publicações) ---
with tab_ativ:
    st.subheader("Atividades da turma (visível para os pais)")

    turmas_a = sorted(
        [str(t) for t in df["Turma"].unique().tolist() if str(t).strip() != ""]
    )
    if not turmas_a:
        st.info("Ainda não há turmas registadas.")
    else:
        turma_a = st.selectbox("Turma", turmas_a, key="ativ_turma")

        with st.expander("➕ Nova publicação", expanded=True):
            dia_a = st.date_input("Data", date.today(), key="ativ_data")
            desc_a = st.text_area(
                "O que fizemos hoje", key="ativ_desc",
                placeholder="Ex.: Hoje aprendemos os animais em inglês...",
            )
            foto_a = st.file_uploader(
                "Fotografia da aula", type=["jpg", "jpeg", "png"], key="ativ_foto"
            )
            if st.checkbox("Tirar fotografia com a câmara", key="ativ_cam"):
                foto_a = st.camera_input("Câmara", key="ativ_camfoto") or foto_a

            if foto_a:
                st.image(foto_a, caption="Pré-visualização", width=260)

            if st.button("📤 Publicar para os pais", key="ativ_publicar", type="primary"):
                if not desc_a.strip() and not foto_a:
                    st.error("Escreve uma descrição ou escolhe uma fotografia.")
                else:
                    foto_b64 = comprimir_foto(foto_a) if foto_a else ""
                    if foto_a and not foto_b64:
                        st.error("Não foi possível reduzir a fotografia. Tenta outra.")
                    else:
                        obter_aba_atividades().append_row(
                            [str(dia_a), turma_a, desc_a.strip(), foto_b64]
                        )
                        carregar_atividades.clear()
                        st.toast("Atividade publicada!", icon="📤")
                        st.rerun()

        st.markdown("### Já publicadas")
        ativ = carregar_atividades()
        mostrar_atividades(ativ[ativ["turma"].astype(str) == turma_a], admin=eh_admin)

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
            with st.container(border=True):
                escolha = st.selectbox("Escolhe o aluno a remover", opcoes)
                indice_remover = opcoes.index(escolha)
                confirma = st.checkbox("Tenho a certeza que quero remover este aluno", key="rem_ok")
                if st.button("🗑️ Remover", type="primary", disabled=not confirma):
                    df_atualizado = df.drop(df.index[indice_remover])
                    guardar_dados(df_atualizado)
                    st.toast(f"Aluno '{escolha}' removido com sucesso!", icon="🗑️")
                    st.cache_resource.clear()
                    st.rerun()