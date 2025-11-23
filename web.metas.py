import streamlit as st
import sqlite3
from datetime import date

###############################
# BANCO DE DADOS
###############################
def init_db():
    conn = sqlite3.connect("metas.db")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS metas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            prazo TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS submetas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meta_id INTEGER,
            titulo TEXT,
            concluida INTEGER DEFAULT 0,
            pontos INTEGER DEFAULT 1,
            prazo TEXT,
            FOREIGN KEY(meta_id) REFERENCES metas(id)
        )
    """)

    conn.commit()
    conn.close()

def get_metas():
    conn = sqlite3.connect("metas.db")
    cur = conn.cursor()
    cur.execute("SELECT id, titulo, prazo FROM metas")
    data = cur.fetchall()
    conn.close()
    return data

def add_meta(titulo, prazo):
    conn = sqlite3.connect("metas.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO metas (titulo, prazo) VALUES (?, ?)", (titulo, prazo))
    conn.commit()
    conn.close()

def delete_meta(meta_id):
    conn = sqlite3.connect("metas.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM submetas WHERE meta_id=?", (meta_id,))
    cur.execute("DELETE FROM metas WHERE id=?", (meta_id,))
    conn.commit()
    conn.close()

def get_submetas(meta_id):
    conn = sqlite3.connect("metas.db")
    cur = conn.cursor()
    cur.execute("SELECT id, titulo, concluida, pontos, prazo FROM submetas WHERE meta_id=?", (meta_id,))
    data = cur.fetchall()
    conn.close()
    return data

def add_submeta(meta_id, titulo, pontos, prazo):
    conn = sqlite3.connect("metas.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO submetas (meta_id, titulo, pontos, prazo) VALUES (?, ?, ?, ?)",
                (meta_id, titulo, pontos, prazo))
    conn.commit()
    conn.close()

def toggle_submeta(sub_id, value):
    conn = sqlite3.connect("metas.db")
    cur = conn.cursor()
    cur.execute("UPDATE submetas SET concluida=? WHERE id=?", (value, sub_id))
    conn.commit()
    conn.close()


###############################
# INTERFACE STREAMLIT
###############################
st.set_page_config(page_title="Sistema de Metas", page_icon="🔥", layout="wide")

st.title("🔥 Sistema de Metas com Submetas e Progresso Automático")

init_db()

###############################
# ADICIONAR META
###############################
st.subheader("Adicionar Meta")
... col1, col2, col3 = st.columns(3)
... 
... with col1:
...     titulo_meta = st.text_input("Título da Meta")
... 
... with col2:
...     prazo_meta = st.date_input("Prazo da Meta", date.today())
... 
... with col3:
...     if st.button("Criar Meta"):
...         if titulo_meta.strip() != "":
...             add_meta(titulo_meta, str(prazo_meta))
...             st.success("Meta criada!")
...         else:
...             st.error("O título não pode ser vazio.")
... 
... st.markdown("---")
... 
... ###############################
... # LISTA DE METAS
... ###############################
... st.header("📌 Suas Metas")
... 
... metas = get_metas()
... 
... for meta_id, titulo, prazo in metas:
...     with st.container():
...         st.subheader(f"🎯 {titulo} — Prazo: {prazo}")
... 
...         submetas = get_submetas(meta_id)
... 
...         # Calcular progresso
...         total_pontos = sum(s[3] for s in submetas)
...         pontos_feitos = sum(s[3] for s in submetas if s[2] == 1)
...         progresso = round((pontos_feitos / total_pontos) * 100, 2) if total_pontos > 0 else 0
... 
...         # Cor do progresso
...         if progresso >= 100:
...             cor = "blue"
        elif progresso >= 80:
            cor = "green"
        elif progresso >= 40:
            cor = "yellow"
        else:
            cor = "red"

        st.write(f"**Progresso:** {progresso}% 🔵🟢🟡🔴".replace("blue","🔵").replace("green","🟢").replace("yellow","🟡").replace("red","🔴"))

        # Mostrar submetas
        for sub_id, sub_titulo, concluida, pontos, prazo_sub in submetas:
            colA, colB = st.columns([6,1])
            with colA:
                st.write(f"- {sub_titulo} (Pontos: {pontos}) — Prazo: {prazo_sub}")
            with colB:
                novo_valor = st.checkbox("Feita", value=bool(concluida), key=f"sub{sub_id}")
                toggle_submeta(sub_id, 1 if novo_valor else 0)

        st.markdown("### ➕ Adicionar Submeta")
        with st.form(f"form_submeta_{meta_id}"):
            sub_titulo = st.text_input("Título da Submeta", key=f"t{sub_id}")
            pontos = st.number_input("Pontos", min_value=1, max_value=100, value=1, step=1, key=f"p{sub_id}")
            prazo_sub = st.date_input("Prazo da Submeta", date.today(), key=f"d{sub_id}")
            enviar = st.form_submit_button("Adicionar")

            if enviar:
                add_submeta(meta_id, sub_titulo, pontos, str(prazo_sub))
                st.success("Submeta adicionada!")

        st.error("Excluir Meta")
        if st.button(f"Excluir Meta {meta_id}"):
            delete_meta(meta_id)
            st.warning("Meta removida!")

        st.markdown("---")

