import streamlit as st
import sqlite3
from datetime import datetime

# -----------------------------
# BANCO DE DADOS
# -----------------------------
conn = sqlite3.connect("metas.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS metas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    prazo TEXT,
    progresso INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sub_metas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meta_id INTEGER,
    nome TEXT NOT NULL,
    concluido INTEGER DEFAULT 0,
    FOREIGN KEY(meta_id) REFERENCES metas(id)
)
""")

conn.commit()

# -----------------------------
# FUNÇÃO PARA CARREGAR DADOS
# -----------------------------
def carregar_metas():
    cursor.execute("SELECT * FROM metas")
    return cursor.fetchall()

def carregar_sub_metas(meta_id):
    cursor.execute("SELECT * FROM sub_metas WHERE meta_id = ?", (meta_id,))
    return cursor.fetchall()

# -----------------------------
# INTERFACE
# -----------------------------
st.title("🎯 Sistema de Metas do João")

menu = st.sidebar.radio("Menu", ["Adicionar Meta", "Ver Metas"])

# -----------------------------
# ADICIONAR META
# -----------------------------
if menu == "Adicionar Meta":
    st.subheader("Criar nova meta")

    nome = st.text_input("Nome da meta:")
    prazo = st.date_input("Prazo final:")

    if st.button("Salvar Meta"):
        cursor.execute("INSERT INTO metas (nome, prazo) VALUES (?, ?)", (nome, str(prazo)))
        conn.commit()
        st.success("Meta criada!")

# -----------------------------
# VER METAS
# -----------------------------
if menu == "Ver Metas":
    st.subheader("Progresso das Metas")

    metas = carregar_metas()

    for meta in metas:
        id_meta, nome, prazo, progresso = meta

        st.write(f"### {nome}")
        st.write(f"📅 Prazo: {prazo}")
        st.progress(progresso / 100)

        # Exibir sub-metas
        sub_metas = carregar_sub_metas(id_meta)

        st.write("**Sub-metas:**")
        for sub in sub_metas:
            id_sub, meta_id, nome_sub, concluido = sub
            check = st.checkbox(nome_sub, value=bool(concluido), key=f"{id_sub}")

            # Atualizar sub-meta
            if check != bool(concluido):
                cursor.execute("UPDATE sub_metas SET concluido = ? WHERE id = ?", (1 if check else 0, id_sub))
                conn.commit()

        # Cálculo automático do progresso
        if sub_metas:
            total = len(sub_metas)
            feitas = sum([1 for s in sub_metas if s[3] == 1])
            novo_progresso = int((feitas / total) * 100)

            if novo_progresso != progresso:
                cursor.execute("UPDATE metas SET progresso = ? WHERE id = ?", (novo_progresso, id_meta))
                conn.commit()

        st.write("---")

        nome_sub = st.text_input(f"Adicionar sub-meta para '{nome}'", key=f"add_{id_meta}")
        if st.button(f"Salvar sub-meta {id_meta}"):
            cursor.execute("INSERT INTO sub_metas (meta_id, nome) VALUES (?, ?)", (id_meta, nome_sub))
            conn.commit()
            st.success("Sub-meta adicionada!")
