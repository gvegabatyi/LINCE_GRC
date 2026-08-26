import streamlit as st
import pandas as pd
from datetime import date
import io
import os
import psycopg2
from psycopg2 import sql

# Leer URL de la base de datos desde variable de entorno
DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    if not DATABASE_URL or not DATABASE_URL.strip():
        st.error("⚠️ La variable de entorno DATABASE_URL no está configurada o está vacía. Por favor configúrala en el panel de Render (Environment Variables).")
        st.stop()
    
    url = DATABASE_URL.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
        
    try:
        return psycopg2.connect(dsn=url)
    except psycopg2.Error as e:
        st.error(f"⚠️ Error de conexión a PostgreSQL: {e}")
        st.info("Verifica que la variable DATABASE_URL tenga el formato: postgresql://usuario:contraseña@host:puerto/base_de_datos")
        st.stop()
    except Exception as e:
        st.error(f"⚠️ Error inesperado al conectar con la base de datos: {e}")
        st.stop()

def init_db():
    try:
        conn = get_conn()
        c = conn.cursor()
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            rut TEXT,
            estado TEXT DEFAULT 'activa'
        )
        """)
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS tratamientos (
            id SERIAL PRIMARY KEY,
            empresa_id INTEGER,
            nombre TEXT,
            finalidad TEXT,
            datos TEXT,
            titulares TEXT,
            base_licitud TEXT,
            riesgo TEXT,
            FOREIGN KEY(empresa_id) REFERENCES empresas(id)
        )
        """)
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS visitas (
            id SERIAL PRIMARY KEY,
            tipo TEXT,
            empresa TEXT,
            fecha DATE,
            participantes TEXT,
            hallazgos TEXT
        )
        """)
        
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error al inicializar la base de datos PostgreSQL: {e}")

def add_empresa(nombre, rut):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO empresas (nombre, rut) VALUES (%s, %s)", (nombre, rut))
    conn.commit()
    conn.close()

def list_empresas():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM empresas ORDER BY id ASC", conn)
    conn.close()
    return df

def add_tratamiento(empresa_id, nombre, finalidad, datos, titulares, base_licitud, riesgo):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    INSERT INTO tratamientos (empresa_id, nombre, finalidad, datos, titulares, base_licitud, riesgo)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (empresa_id, nombre, finalidad, datos, titulares, base_licitud, riesgo))
    conn.commit()
    conn.close()

def list_tratamientos():
    conn = get_conn()
    df = pd.read_sql_query("""
    SELECT t.id, e.nombre as empresa, t.nombre, t.finalidad, t.datos, t.titulares, t.base_licitud, t.riesgo
    FROM tratamientos t
    JOIN empresas e ON t.empresa_id = e.id
    ORDER BY t.id ASC
    """, conn)
    conn.close()
    return df

def add_visita(tipo, empresa, fecha, participantes, hallazgos):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    INSERT INTO visitas (tipo, empresa, fecha, participantes, hallazgos)
    VALUES (%s, %s, %s, %s, %s)
    """, (tipo, empresa, fecha, participantes, hallazgos))
    conn.commit()
    conn.close()

def list_visitas():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM visitas ORDER BY fecha DESC, id DESC", conn)
    conn.close()
    return df

def get_excel_bytes():
    conn = get_conn()
    tablas = ["empresas", "tratamientos", "visitas"]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for tabla in tablas:
            df = pd.read_sql_query(f"SELECT * FROM {tabla}", conn)
            df.to_excel(writer, sheet_name=tabla, index=False)
    conn.close()
    return output.getvalue()

# Interfaz Streamlit
st.set_page_config(page_title="Serviphar GRC Lite", layout="wide")
st.title("Serviphar GRC Lite")

init_db()

menu = st.sidebar.selectbox(
    "Módulo",
    ["Empresas", "Tratamientos (ROPA)", "Visitas", "Exportar"]
)

if menu == "Empresas":
    st.header("Empresas del Grupo")
    with st.form("add_empresa"):
        nombre = st.text_input("Nombre de la empresa")
        rut = st.text_input("RUT")
        submitted = st.form_submit_button("Agregar empresa")
        if submitted and nombre:
            add_empresa(nombre, rut)
            st.success("Empresa agregada exitosamente")
    st.subheader("Listado de empresas")
    st.dataframe(list_empresas(), use_container_width=True)

elif menu == "Tratamientos (ROPA)":
    st.header("Tratamientos (ROPA)")
    empresas = list_empresas()
    if empresas.empty:
        st.warning("Primero registra empresas en el módulo Empresas.")
    else:
        with st.form("add_tratamiento"):
            empresa_id = st.selectbox("Empresa", empresas["id"].astype(str) + " - " + empresas["nombre"])
            nombre = st.text_input("Nombre del tratamiento")
            finalidad = st.text_area("Finalidad", height=50)
            datos = st.text_area("Categorías de datos", height=50)
            titulares = st.text_area("Categorías de titulares", height=50)
            base_licitud = st.text_input("Base de licitud")
            riesgo = st.selectbox("Riesgo", ["bajo", "medio", "alto", "crítico"])
            submitted = st.form_submit_button("Agregar tratamiento")
            if submitted and nombre and empresa_id:
                eid = int(empresa_id.split(" - ")[0])
                add_tratamiento(eid, nombre, finalidad, datos, titulares, base_licitud, riesgo)
                st.success("Tratamiento agregado exitosamente")
    st.subheader("Listado de tratamientos")
    st.dataframe(list_tratamientos(), use_container_width=True)

elif menu == "Visitas":
    st.header("Visitas y Entrevistas")
    with st.form("add_visita"):
        tipo = st.selectbox("Tipo", ["visita bodega", "visita farmacia", "entrevista RRHH", "entrevista TI", "entrevista operaciones", "otra"])
        empresa = st.text_input("Empresa / Lugar")
        fecha = st.date_input("Fecha", value=date.today())
        participantes = st.text_area("Participantes", height=50)
        hallazgos = st.text_area("Hallazgos principales", height=80)
        submitted = st.form_submit_button("Agregar visita")
        if submitted and empresa:
            add_visita(tipo, empresa, fecha, participantes, hallazgos)
            st.success("Visita agregada exitosamente")
    st.subheader("Listado de visitas")
    st.dataframe(list_visitas(), use_container_width=True)

elif menu == "Exportar":
    st.header("Exportar datos")
    st.write("Haz clic en el botón para descargar el archivo Excel con todas las tablas.")
    try:
        excel_data = get_excel_bytes()
        st.download_button(
            label="📥 Descargar serviphar_grc_lite_export.xlsx",
            data=excel_data,
            file_name="serviphar_grc_lite_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"Error al generar el archivo Excel: {e}")
