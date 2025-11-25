
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# -----------------------------
# BANCO DE DADOS
# -----------------------------
conn = sqlite3.connect("metas.db", check_same_thread=False)
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
# CARREGADORES
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
st.title("🎯 Sistema de Metas — João")

menu = st.sidebar.radio("Menu", ["Adicionar Meta", "Ver e Editar Metas", "Gráficos"])

# -----------------------------
# ADICIONAR META
# -----------------------------
if menu == "Adicionar Meta":
    st.header("➕ Criar nova meta")

    nome = st.text_input("Nome da meta:")
    prazo = st.date_input("Prazo final:")

    if st.button("Salvar Meta"):
        cursor.execute("INSERT INTO metas (nome, prazo) VALUES (?, ?)", (nome, str(prazo)))
        conn.commit()
        st.success("Meta criada!")

# -----------------------------
# VER E EDITAR METAS
# -----------------------------
if menu == "Ver e Editar Metas":
    st.header("📋 Gerenciamento de metas")

    metas = carregar_metas()

    for meta in metas:
        meta_id, nome, prazo, progresso = meta

        st.subheader(f"🎯 {nome}")
        st.write(f"📅 Prazo: **{prazo}**")

        st.progress(progresso / 100)

        # Submetas
        st.write("**Sub-metas:**")
        sub_metas = carregar_sub_metas(meta_id)

        for sub in sub_metas:
            sub_id, m_id, sub_nome, concluido = sub
            check = st.checkbox(sub_nome, value=bool(concluido), key=f"sub_{sub_id}")

            if check != bool(concluido):
                cursor.execute(
                    "UPDATE sub_metas SET concluido = ? WHERE id = ?",
                    (1 if check else 0, sub_id)
                )
                conn.commit()

        # Atualiza progresso automaticamente
        if sub_metas:
            total = len(sub_metas)
            feitas = sum([1 for s in sub_metas if s[3] == 1])
            novo_progresso = int((feitas / total) * 100)

            if novo_progresso != progresso:
                cursor.execute("UPDATE metas SET progresso = ? WHERE id = ?", (novo_progresso, meta_id))
                conn.commit()

        st.write("---")

        # Adicionar nova sub-meta
        nova_sub = st.text_input(f"Adicionar sub-meta para '{nome}'", key=f"add_{meta_id}")
        if st.button(f"Salvar sub-meta {meta_id}"):
            cursor.execute("INSERT INTO sub_metas (meta_id, nome) VALUES (?, ?)", (meta_id, nova_sub))
            conn.commit()
            st.success("Sub-meta adicionada!")

# -----------------------------
# GRÁFICOS
# -----------------------------
if menu == "Gráficos":
    st.header("📊 Visualização das Metas")

    metas = carregar_metas()
    df = pd.DataFrame(metas, columns=["id", "nome", "prazo", "progresso"])

    if df.empty:
        st.warning("Nenhuma meta adicionada ainda.")
    else:
        tipo = st.selectbox(
            "Escolha o tipo de gráfico:",
            ["Barra", "Pizza", "Linha"]
        )

        if tipo == "Barra":
            fig = px.bar(df, x="nome", y="progresso", title="Progresso das Metas (%)")
            st.plotly_chart(fig)

        elif tipo == "Pizza":
            fig = px.pie(df, names="nome", values="progresso", title="Distribuição de Progresso")
            st.plotly_chart(fig)

        elif tipo == "Linha":
            fig = px.line(df, x="nome", y="progresso", title="Evolução do Progresso")
            st.plotly_chart(fig
