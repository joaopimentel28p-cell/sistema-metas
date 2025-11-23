# app.py
import streamlit as st
import json
import os
import hashlib
import uuid
from datetime import date, datetime
from tempfile import NamedTemporaryFile
from shutil import move

DB_FILE = "database.json"

# -------------------------
# UTIL (carregar/gravar)
# -------------------------
def load_db():
    if not os.path.exists(DB_FILE):
        initial = {"users": {}}
        save_db(initial)
        return initial
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(db):
    # grava de forma atômica: escreve em arquivo temporário e substitui
    tmp = NamedTemporaryFile("w", delete=False, encoding="utf-8")
    try:
        json.dump(db, tmp, ensure_ascii=False, indent=2)
        tmp.close()
        move(tmp.name, DB_FILE)
    except Exception:
        try:
            os.remove(tmp.name)
        except Exception:
            pass
        raise

# -------------------------
# AUTENTICAÇÃO
# -------------------------
def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

def create_user(username: str, password: str):
    db = load_db()
    if username in db["users"]:
        return False, "Usuário já existe"
    salt = uuid.uuid4().hex
    pwd = hash_password(password, salt) + ":" + salt
    db["users"][username] = {
        "pwd": pwd,
        "created_at": datetime.utcnow().isoformat(),
        "metas": []
    }
    save_db(db)
    return True, "Conta criada"

def verify_user(username: str, password: str):
    db = load_db()
    u = db["users"].get(username)
    if not u:
        return False
    try:
        stored, salt = u["pwd"].split(":", 1)
    except Exception:
        return False
    return hash_password(password, salt) == stored

# -------------------------
# CRUD Metas & Submetas
# -------------------------
def new_id():
    return uuid.uuid4().hex

def add_meta_for_user(username: str, title: str, due: str = None):
    db = load_db()
    meta = {
        "id": new_id(),
        "title": title,
        "due": due,
        "created_at": datetime.utcnow().isoformat(),
        "submetas": []  # cada submeta: {id,title,points,done,due}
    }
    db["users"][username]["metas"].insert(0, meta)
    save_db(db)
    return meta

def delete_meta_for_user(username: str, meta_id: str):
    db = load_db()
    metas = db["users"][username]["metas"]
    metas = [m for m in metas if m["id"] != meta_id]
    db["users"][username]["metas"] = metas
    save_db(db)

def add_submeta_for_user(username: str, meta_id: str, title: str, points: int = 1, due: str = None):
    db = load_db()
    for m in db["users"][username]["metas"]:
        if m["id"] == meta_id:
            s = {
                "id": new_id(),
                "title": title,
                "points": int(points) if points and int(points) > 0 else 1,
                "done": False,
                "due": due,
                "created_at": datetime.utcnow().isoformat()
            }
            m["submetas"].append(s)
            save_db(db)
            return s
    return None

def toggle_submeta_for_user(username: str, meta_id: str, sub_id: str, value: bool):
    db = load_db()
    for m in db["users"][username]["metas"]:
        if m["id"] == meta_id:
            for s in m["submetas"]:
                if s["id"] == sub_id:
                    s["done"] = bool(value)
                    save_db(db)
                    return True
    return False

def delete_submeta_for_user(username: str, meta_id: str, sub_id: str):
    db = load_db()
    for m in db["users"][username]["metas"]:
        if m["id"] == meta_id:
            m["submetas"] = [s for s in m["submetas"] if s["id"] != sub_id]
            save_db(db)
            return True
    return False

def progress_of_meta(meta):
    subs = meta.get("submetas", [])
    total = sum([s.get("points", 1) for s in subs]) or 0
    if total == 0:
        return 0
    done = sum([s.get("points", 1) for s in subs if s.get("done")])
    return int(round((done / total) * 100))

# -------------------------
# EXPORT / IMPORT USER
# -------------------------
def export_user(username: str, path: str):
    db = load_db()
    user = db["users"].get(username)
    if not user:
        return False
    with open(path, "w", encoding="utf-8") as f:
        json.dump(user, f, ensure_ascii=False, indent=2)
    return True

def import_user(username: str, path: str):
    if not os.path.exists(path):
        return False, "Arquivo não encontrado"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    db = load_db()
    db["users"][username]["metas"] = data.get("metas", [])
    save_db(db)
    return True, "Importado"

# -------------------------
# UI - STREAMLIT
# -------------------------
st.set_page_config(page_title="Roadmap Titan", layout="wide")
st.title("🚀 Roadmap Titan — Metas & Submetas")

# session
if "user" not in st.session_state:
    st.session_state.user = None

# ---------- AUTH ----------
with st.sidebar:
    st.write("## Conta")
    if st.session_state.user is None:
        auth_mode = st.selectbox("Ação", ["Entrar", "Criar conta"])
        if auth_mode == "Criar conta":
            new_user = st.text_input("Usuário (apenas letras/números)", key="reg_user")
            new_pwd = st.text_input("Senha", type="password", key="reg_pwd")
            if st.button("Criar conta"):
                if not new_user or not new_pwd:
                    st.sidebar.error("Preencha usuário e senha")
                else:
                    ok, msg = create_user(new_user, new_pwd), None
                    if ok:
                        st.sidebar.success("Conta criada! Faça o login.")
                    else:
                        st.sidebar.error("Usuário já existe. Escolha outro.")
        else:
            login_user = st.text_input("Usuário", key="login_user")
            login_pwd = st.text_input("Senha", type="password", key="login_pwd")
            if st.button("Entrar"):
                if verify_user(login_user, login_pwd):
                    st.session_state.user = login_user
                    st.rerun()
                else:
                    st.sidebar.error("Usuário ou senha inválidos")
    else:
        st.write(f"Conectado como: **{st.session_state.user}**")
        if st.button("Sair"):
            st.session_state.user = None
            st.experimental_rerun()
        st.markdown("---")
        # Export / Import
        if st.button("Exportar backup (JSON)"):
            path = f"backup_{st.session_state.user}.json"
            export_user(st.session_state.user, path)
            st.sidebar.success(f"Exportado para {path}")
        uploaded = st.file_uploader("Importar backup (JSON)", type=["json"])
        if uploaded:
            tmp_path = f"import_{st.session_state.user}.json"
            with open(tmp_path, "wb") as f:
                f.write(uploaded.getbuffer())
            ok, msg = import_user(st.session_state.user, tmp_path)
            if ok:
                st.sidebar.success("Importado com sucesso")
            else:
                st.sidebar.error(msg)

# ---------- MAIN ----------
if st.session_state.user is None:
    st.info("Faça login ou crie uma conta usando o painel à esquerda.")
    st.stop()

username = st.session_state.user
st.write(f"### Usuário: {username}")

# Add meta form
with st.expander("➕ Adicionar nova meta", expanded=False):
    new_title = st.text_input("Título da meta", key="meta_title")
    new_due = st.date_input("Prazo (opcional)", value=None)
    if new_due is not None:
        new_due_str = new_due.isoformat()
    else:
        new_due_str = None
    if st.button("Salvar meta"):
        if not new_title or new_title.strip() == "":
            st.error("A meta precisa de título.")
        else:
            add_meta_for_user(username, new_title.strip(), new_due_str)
            st.success("Meta salva.")
            st.rerun()

# show metas
db = load_db()
user_metas = db["users"][username].get("metas", [])

if not user_metas:
    st.info("Você não tem metas ainda. Crie uma com 'Adicionar nova meta'.")
else:
    # show in columns: left list, right detail
    left, right = st.columns([1, 2])

    with left:
        st.subheader("Metas")
        for m in user_metas:
            prog = progress_of_meta(m)
            label = f"{m['title']} — {prog}%"
            if st.button(label, key=f"open_{m['id']}"):
                st.session_state["open_meta"] = m["id"]

    with right:
        open_meta_id = st.session_state.get("open_meta", user_metas[0]["id"] if user_metas else None)
        # find meta
        open_meta = next((x for x in user_metas if x["id"] == open_meta_id), None)
        if open_meta:
            st.header(open_meta["title"])
            if open_meta.get("due"):
                st.write("Prazo:", open_meta["due"])
            st.progress(progress_of_meta(open_meta) / 100)

            st.subheader("Sub-metas")
            # list sub-metas
            for s in open_meta.get("submetas", []):
                cols = st.columns([6, 1, 1])
                cols[0].write(s["title"])
                cols[0].write(f"Pontos: {s.get('points',1)}")
                done = cols[1].checkbox("", value=bool(s.get("done")), key=f"chk_{s['id']}")
                if done != bool(s.get("done")):
                    toggle_submeta_for_user(username, open_meta["id"], s["id"], done)
                    st.experimental_rerun()
                if cols[2].button("🗑", key=f"delsub_{s['id']}"):
                    delete_submeta_for_user(username, open_meta["id"], s["id"])
                    st.experimental_rerun()

            st.markdown("—")
            # add submeta
            sub_title = st.text_input("Nova sub-meta", key=f"subt_{open_meta['id']}")
            sub_points = st.number_input("Pontos (peso)", min_value=1, value=1, key=f"subp_{open_meta['id']}")
            sub_due = st.date_input("Prazo (opcional)", value=None, key=f"subd_{open_meta['id']}")
            sub_due_str = sub_due.isoformat() if sub_due else None
            if st.button("Salvar sub-meta", key=f"savesub_{open_meta['id']}"):
                if not sub_title or sub_title.strip() == "":
                    st.error("Sub-meta precisa de título")
                else:
                    add_submeta_for_user(username, open_meta["id"], sub_title.strip(), int(sub_points), sub_due_str)
                    st.success("Sub-meta adicionada")
                    rerun

            st.markdown("---")
            # actions: delete meta
            if st.button("Excluir meta"):
                delete_meta_for_user(username, open_meta["id"])
                st.success("Meta removida")
                st.experimental_rerun()



