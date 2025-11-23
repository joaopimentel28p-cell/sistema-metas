import streamlit as st
from deta import Deta
from datetime import datetime

# -----------------------------
# CONFIGURAÇÃO DA DETA (NUVEM)
# -----------------------------
DETA_KEY = "COLOQUE_SUA_CHAVE_AQUI"

deta = Deta(DETA_KEY)
metas_db = deta.Base("metas_db")
sub_metas_db = deta.Base("sub_metas_db")

# -----------------------------
# SISTEMA DE LOGIN
# -----------------------------
st.title("🔐 Login no Sistema de Metas")

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    opcao = st.radio("Acessar:", ["Entrar", "Criar Conta"])

    email = st.text_input("Email:")
    senha = st.text_input("Senha:", type="password")

    if opcao == "Criar Conta":
        if st.button("Registrar"):
            metas_db.put({"key": f"user_{email}", "email": email, "senha": senha})
            st.success("Conta criada!")
    
    if opcao == "Entrar":
        if st.button("Login"):
            user = metas_db.get(f"user_{email}")
            if user and user["senha"] == senha:
                st.session_state.usuario = email
                st.success("Login efetuado!")
                st.rerun()
            else:
                st.error("Email ou senha incorretos.")
        
    st.stop()

# -----------------------------
# SISTEMA PRINCIPAL
# -----------------------------
st.title(f"🎯 Sistema de Metas — Usuário: {st.session_state.usuario}")

menu = st.sidebar.radio("Menu", ["Adicionar Meta", "Ver Metas", "Sair"])

if menu == "Sair":
    st.session_state.usuario = None
    st.rerun()

# -----------------------------
# CARREGAR METAS
# -----------------------------
def carregar_metas():
    return metas_db.fetch({"usuario": st.session_state.usuario}).items

def carregar_sub_metas(meta_id):
    return sub_metas_db.fetch({"meta_id": meta_id}).items

# -----------------------------
# ADICIONAR META
# -----------------------------
if menu == "Adicionar Meta":
    st.subheader("Criar nova meta")

    nome = st.text_input("Nome da meta:")
    prazo = st.date_input("Prazo final:")

    if st.button("Salvar Meta"):
        metas_db.put({
            "usuario": st.session_state.usuario,
            "nome": nome,
            "prazo": str(prazo),
            "progresso": 0
        })
        st.success("Meta criada!")

# -----------------------------
# VER METAS
# -----------------------------
if menu == "Ver Metas":
    st.subheader("Progresso das Metas")

    metas = carregar_metas()

    for meta in metas:
        meta_id = meta["key"]
        nome = meta["nome"]
        prazo = meta["prazo"]
        progresso = meta["progresso"]

        st.write(f"### {nome}")
        st.write(f"📅 Prazo: {prazo}")
        st.progress(progresso / 100)

        # Cabeçalhos
        col1, col2, col3 = st.columns(3)
        col1.write("**Sub-metas**")
        col2.write("**Concluído?**")
        col3.write("**Ação**")

        sub_metas = carregar_sub_metas(meta_id)

        # LISTAGEM DE SUB-METAS
        for sub in sub_metas:
            sub_id = sub["key"]
            nome_sub = sub["nome"]
            concluido = sub["concluido"]

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(nome_sub)

            with col2:
                check = st.checkbox("", value=bool(concluido), key=f"check_{sub_id}")

            with col3:
                if st.button("🗑️", key=f"del_{sub_id}"):
                    sub_metas_db.delete(sub_id)
                    st.rerun()

            # Atualizar status
            if check != bool(concluido):
                sub_metas_db.put(
                    {
                        "meta_id": meta_id,
                        "nome": nome_sub,
                        "concluido": 1 if check else 0
                    },
                    sub_id
                )

        # CALCULAR PROGRESSO
        if sub_metas:
            total = len(sub_metas)
            feitas = sum([1 for s in sub_metas if s["concluido"] == 1])
            novo_progresso = int((feitas / total) * 100)

            if novo_progresso != progresso:
                metas_db.put(
                    {
                        "usuario": st.session_state.usuario,
                        "nome": nome,
                        "prazo": prazo,
                        "progresso": novo_progresso,
                    },
                    meta_id
                )
                st.rerun()

        st.write("---")

        # ADICIONAR SUB-META
        nome_sub = st.text_input(f"Adicionar sub-meta para '{nome}'", key=f"add_{meta_id}")
        if st.button(f"Salvar sub-meta {meta_id}"):
            sub_metas_db.put({
                "meta_id": meta_id,
                "nome": nome_sub,
                "concluido": 0
            })
            st.success("Sub-meta adicionada!")
            st.rerun()



