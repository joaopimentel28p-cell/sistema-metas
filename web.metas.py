import streamlit as st
import json
import os
import hashlib


# ========================
# FUNÇÕES DO “BANCO DE DADOS”
# ========================

DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({"users": {}}, f)
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)


# ========================
# AUTENTICAÇÃO
# ========================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    db = load_db()

    if username in db["users"]:
        return False  # usuário já existe

    db["users"][username] = {
        "password": hash_password(password),
        "goals": []
    }

    save_db(db)
    return True


def login_user(username, password):
    db = load_db()

    if username not in db["users"]:
        return False

    hashed = hash_password(password)
    return db["users"][username]["password"] == hashed


# ========================
# APP STREAMLIT
# ========================

st.title("Sistema de Metas - Web")

menu = ["Login", "Criar Conta"]
choice = st.sidebar.selectbox("Menu", menu)

if "usuario" not in st.session_state:
    st.session_state.usuario = None


# ========================
# LOGIN
# ========================

if choice == "Login":
    st.subheader("Faça seu login")

    user = st.text_input("Usuário")
    pwd = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if login_user(user, pwd):
            st.success("Login realizado com sucesso!")
            st.session_state.usuario = user
        else:
            st.error("Usuário ou senha incorretos.")


# ========================
# CRIAR CONTA
# ========================

elif choice == "Criar Conta":
    st.subheader("Criar nova conta")

    new_user = st.text_input("Novo usuário")
    new_pwd = st.text_input("Nova senha", type="password")

    if st.button("Cadastrar"):
        if create_user(new_user, new_pwd):
            st.success("Conta criada com sucesso!")
        else:
            st.error("Usuário já existe. Escolha outro nome.")


# ========================
# ÁREA LOGADA
# ========================

if st.session_state.usuario:

    st.header(f"Bem-vindo, {st.session_state.usuario}!")

    db = load_db()
    user_data = db["users"][st.session_state.usuario]

    st.subheader("Suas Metas")

    # LISTAR METAS
    if user_data["goals"]:
        for i, goal in enumerate(user_data["goals"]):
            st.write(f"### 🎯 {goal['titulo']}")
            st.write(f"- Descrição: {goal['descricao']}")
            st.write(f"- Progresso: {goal['progresso']}%")
            novo_prog = st.slider(f"Atualizar progresso ({goal['titulo']})", 0, 100, goal["progresso"])
            if st.button(f"Salvar progresso {i}"):
                user_data["goals"][i]["progresso"] = novo_prog
                save_db(db)
                st.success("Progresso salvo!")
                st.rerun()
    else:
        st.info("Nenhuma meta cadastrada ainda.")

    st.divider()

    # ADICIONAR META
    st.subheader("Adicionar nova meta")

    titulo = st.text_input("Título da meta")
    descricao = st.text_area("Descrição")

    if st.button("Adicionar Meta"):
        if titulo:
            user_data["goals"].append({
                "titulo": titulo,
                "descricao": descricao,
                "progresso": 0
            })
            save_db(db)
            st.success("Meta adicionada!")
            st.rerun()
        else:
            st.error("A meta precisa ter um título!")

    st.divider()

    if st.button("Sair"):
        st.session_state.usuario = None
        st.rerun()
