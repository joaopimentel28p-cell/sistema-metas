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
# FUNÇÕES
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
        cursor.execute(
            "INSERT INTO metas (nome, prazo) VALUES (?, ?)",
            (nome, str(prazo))
        )
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

        # Colunas para layout
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("**Sub-metas**")
        with col2:
            st.write("**Concluído?**")
        with col3:
            st.write("**Ação**")

        # Exibir sub-metas
        sub_metas = carregar_sub_metas(id_meta)

        for sub in sub_metas:
            id_sub, meta_id, nome_sub, concluido = sub

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(nome_sub)

            with col2:
                check = st.checkbox(
                    "",
                    value=bool(concluido),
                    key=f"check_{id_sub}"
                )

            with col3:
                if st.button("🗑️", key=f"del_{id_sub}"):
                    cursor.execute("DELETE FROM sub_metas WHERE id = ?", (id_sub,))
                    conn.commit()
                    st.rerun()

            if check != bool(concluido):
                cursor.execute(
                    "UPDATE sub_metas SET concluido = ? WHERE id = ?",
                    (1 if check else 0, id_sub)
                )
                conn.commit()

        # Atualizar progresso automaticamente
        if sub_metas:
            total = len(sub_metas)
            feitas = sum([1 for s in sub_metas if s[3] == 1])
            novo_progresso = int((feitas / total) * 100)

            if novo_progresso != progresso:
                cursor.execute(
                    "UPDATE metas SET progresso = ? WHERE id = ?",
                    (novo_progresso, id_meta)
                )
                conn.commit()
                st.rerun()

        st.write("---")

        # Adi

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


