"""
Serviphar GRC Lite - Plataforma Web de Auditoría y Cumplimiento GRC
Diseñada para visitas a clientes en terreno, registro de ROPA, auditorías y exportación a Excel.
Compatible con Neon PostgreSQL y Streamlit.
Incluye migraciones automáticas seguras de esquema SQL.
"""

import streamlit as st
import pandas as pd
import psycopg2
from psycopg2 import extras
from datetime import date, datetime
import io
import os
import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Serviphar GRC Lite",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #1E88E5;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stButton>button {
        border-radius: 6px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# CONEXIÓN Y GESTIÓN DE BASE DE DATOS (POSTGRESQL / NEON)
# ==============================================================================
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_url():
    """Obtiene y normaliza la URL de conexión de la base de datos."""
    if not DATABASE_URL or not DATABASE_URL.strip():
        return None
    url = DATABASE_URL.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url

def get_connection():
    """Establece y retorna una conexión a PostgreSQL con timeout y control de errores."""
    url = get_db_url()
    if not url:
        st.error("⚠️ La variable de entorno **DATABASE_URL** no está configurada. Por favor establécela en Railway o en tu entorno.")
        st.stop()
    try:
        conn = psycopg2.connect(dsn=url, connect_timeout=10)
        return conn
    except psycopg2.Error as e:
        st.error(f"⚠️ Error de conexión a PostgreSQL (Neon): {e}")
        st.info("Verifica que tu base de datos en Neon esté activa y que la URL de conexión incluya `?sslmode=require`.")
        st.stop()
    except Exception as e:
        st.error(f"⚠️ Error inesperado al conectar: {e}")
        st.stop()

def init_db():
    """Inicializa y migra automáticamente las tablas y columnas necesarias sin perder datos."""
    try:
        conn = get_connection()
        with conn.cursor() as c:
            # 1. Tabla empresas
            c.execute("""
            CREATE TABLE IF NOT EXISTS empresas (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                rut VARCHAR(20),
                direccion VARCHAR(255),
                contacto VARCHAR(100),
                email VARCHAR(100),
                telefono VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            # Migraciones seguras para empresas preexistentes
            c.execute("ALTER TABLE empresas ADD COLUMN IF NOT EXISTS direccion VARCHAR(255);")
            c.execute("ALTER TABLE empresas ADD COLUMN IF NOT EXISTS contacto VARCHAR(100);")
            c.execute("ALTER TABLE empresas ADD COLUMN IF NOT EXISTS email VARCHAR(100);")
            c.execute("ALTER TABLE empresas ADD COLUMN IF NOT EXISTS telefono VARCHAR(20);")
            c.execute("ALTER TABLE empresas ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")

            # 2. Tabla tratamientos (ROPA)
            c.execute("""
            CREATE TABLE IF NOT EXISTS tratamientos (
                id SERIAL PRIMARY KEY,
                empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
                nombre_tratamiento VARCHAR(255),
                descripcion TEXT,
                base_legal VARCHAR(100),
                datos_personales TEXT,
                responsables TEXT,
                encargados TEXT,
                transferencias TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            # Migraciones seguras para tratamientos preexistentes
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS nombre_tratamiento VARCHAR(255);")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS descripcion TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS base_legal VARCHAR(100);")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS datos_personales TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS responsables TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS encargados TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS transferencias TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")

            # Migrar datos si existían columnas del esquema anterior
            c.execute("""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tratamientos' AND column_name='nombre') THEN
                    UPDATE tratamientos SET nombre_tratamiento = nombre WHERE nombre_tratamiento IS NULL;
                END IF;
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tratamientos' AND column_name='finalidad') THEN
                    UPDATE tratamientos SET descripcion = finalidad WHERE descripcion IS NULL;
                END IF;
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tratamientos' AND column_name='base_licitud') THEN
                    UPDATE tratamientos SET base_legal = base_licitud WHERE base_legal IS NULL;
                END IF;
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tratamientos' AND column_name='datos') THEN
                    UPDATE tratamientos SET datos_personales = datos WHERE datos_personales IS NULL;
                END IF;
            END $$;
            """)

            # 3. Tabla visitas (Auditorías)
            c.execute("""
            CREATE TABLE IF NOT EXISTS visitas (
                id SERIAL PRIMARY KEY,
                empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
                fecha_visita DATE DEFAULT CURRENT_DATE,
                auditor VARCHAR(100),
                checklist_seguridad JSONB,
                puntaje INTEGER DEFAULT 0,
                observaciones TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            # Migraciones seguras para visitas preexistentes
            c.execute("ALTER TABLE visitas ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;")
            c.execute("ALTER TABLE visitas ADD COLUMN IF NOT EXISTS fecha_visita DATE DEFAULT CURRENT_DATE;")
            c.execute("ALTER TABLE visitas ADD COLUMN IF NOT EXISTS auditor VARCHAR(100);")
            c.execute("ALTER TABLE visitas ADD COLUMN IF NOT EXISTS checklist_seguridad JSONB;")
            c.execute("ALTER TABLE visitas ADD COLUMN IF NOT EXISTS puntaje INTEGER DEFAULT 0;")
            c.execute("ALTER TABLE visitas ADD COLUMN IF NOT EXISTS observaciones TEXT;")
            c.execute("ALTER TABLE visitas ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")

            # Migrar datos si existían columnas del esquema anterior en visitas
            c.execute("""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='visitas' AND column_name='fecha') THEN
                    UPDATE visitas SET fecha_visita = fecha WHERE fecha_visita IS NULL;
                END IF;
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='visitas' AND column_name='hallazgos') THEN
                    UPDATE visitas SET observaciones = hallazgos WHERE observaciones IS NULL;
                END IF;
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='visitas' AND column_name='participantes') THEN
                    UPDATE visitas SET auditor = participantes WHERE auditor IS NULL;
                END IF;
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='visitas' AND column_name='empresa') THEN
                    UPDATE visitas v
                    SET empresa_id = e.id
                    FROM empresas e
                    WHERE v.empresa_id IS NULL AND (v.empresa = e.nombre OR v.empresa = e.rut);
                END IF;
            END $$;
            """)

            # 4. Tabla evidencias
            c.execute("""
            CREATE TABLE IF NOT EXISTS evidencias (
                id SERIAL PRIMARY KEY,
                visita_id INTEGER REFERENCES visitas(id) ON DELETE CASCADE,
                descripcion TEXT,
                foto_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error al inicializar/migrar tablas en la base de datos: {e}")

# ==============================================================================
# PREGUNTAS DEL CHECKLIST DE SEGURIDAD (15 ITEMS)
# ==============================================================================
CHECKLIST_PREGUNTAS = [
    "1. ¿Cuenta con política de seguridad de la información documentada?",
    "2. ¿Existe un responsable de seguridad de la información?",
    "3. ¿Se realizan copias de seguridad periódicas?",
    "4. ¿Los sistemas tienen control de acceso con usuario y contraseña?",
    "5. ¿Las contraseñas cumplen con política de complejidad?",
    "6. ¿Existe control de acceso físico a las instalaciones?",
    "7. ¿El personal ha recibido capacitación en seguridad?",
    "8. ¿Existen procedimientos para gestión de incidentes?",
    "9. ¿Se realiza mantenimiento preventivo de equipos?",
    "10. ¿Existe política de uso aceptable de recursos TI?",
    "11. ¿Los datos sensibles están encriptados?",
    "12. ¿Existe control de cambios en sistemas críticos?",
    "13. ¿Se realizan evaluaciones de riesgo periódicas?",
    "14. ¿Existe plan de continuidad del negocio?",
    "15. ¿Se realizan auditorías internas de seguridad?"
]

# ==============================================================================
# FUNCIONES CRUD: EMPRESAS
# ==============================================================================
def add_empresa(nombre, rut, direccion, contacto, email, telefono):
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute("""
                INSERT INTO empresas (nombre, rut, direccion, contacto, email, telefono)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (nombre.strip(), rut.strip(), direccion.strip() if direccion else None,
                  contacto.strip() if contacto else None, email.strip() if email else None,
                  telefono.strip() if telefono else None))
            conn.commit()
        conn.close()
        return True, "Empresa registrada exitosamente."
    except psycopg2.IntegrityError:
        return False, "Ya existe una empresa con ese RUT."
    except Exception as e:
        return False, f"Error al guardar empresa: {e}"

def update_empresa(empresa_id, nombre, rut, direccion, contacto, email, telefono):
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute("""
                UPDATE empresas
                SET nombre=%s, rut=%s, direccion=%s, contacto=%s, email=%s, telefono=%s
                WHERE id=%s
            """, (nombre.strip(), rut.strip(), direccion.strip() if direccion else None,
                  contacto.strip() if contacto else None, email.strip() if email else None,
                  telefono.strip() if telefono else None, empresa_id))
            conn.commit()
        conn.close()
        return True, "Empresa actualizada exitosamente."
    except Exception as e:
        return False, f"Error al actualizar empresa: {e}"

def delete_empresa(empresa_id):
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute("DELETE FROM empresas WHERE id=%s", (empresa_id,))
            conn.commit()
        conn.close()
        return True, "Empresa y registros asociados eliminados."
    except Exception as e:
        return False, f"Error al eliminar empresa: {e}"

def get_empresas_df(search_term=""):
    try:
        conn = get_connection()
        if search_term:
            query = """
                SELECT id, nombre, COALESCE(rut, '') AS rut, 
                       COALESCE(direccion, '') AS direccion, 
                       COALESCE(contacto, '') AS contacto, 
                       COALESCE(email, '') AS email, 
                       COALESCE(telefono, '') AS telefono, 
                       created_at
                FROM empresas
                WHERE nombre ILIKE %s OR rut ILIKE %s
                ORDER BY id DESC
            """
            term = f"%{search_term}%"
            df = pd.read_sql_query(query, conn, params=(term, term))
        else:
            query = """
                SELECT id, nombre, COALESCE(rut, '') AS rut, 
                       COALESCE(direccion, '') AS direccion, 
                       COALESCE(contacto, '') AS contacto, 
                       COALESCE(email, '') AS email, 
                       COALESCE(telefono, '') AS telefono, 
                       created_at
                FROM empresas
                ORDER BY id DESC
            """
            df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error al listar empresas: {e}")
        return pd.DataFrame()

# ==============================================================================
# FUNCIONES CRUD: TRATAMIENTOS (ROPA)
# ==============================================================================
def add_tratamiento(empresa_id, nombre, descripcion, base_legal, datos_personales, responsables, encargados, transferencias):
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute("""
                INSERT INTO tratamientos 
                (empresa_id, nombre_tratamiento, descripcion, base_legal, datos_personales, responsables, encargados, transferencias)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (empresa_id, nombre.strip(), descripcion.strip() if descripcion else None,
                  base_legal, datos_personales.strip() if datos_personales else None,
                  responsables.strip() if responsables else None, encargados.strip() if encargados else None,
                  transferencias.strip() if transferencias else None))
            conn.commit()
        conn.close()
        return True, "Tratamiento (ROPA) registrado exitosamente."
    except Exception as e:
        return False, f"Error al registrar tratamiento: {e}"

def update_tratamiento(tratamiento_id, empresa_id, nombre, descripcion, base_legal, datos_personales, responsables, encargados, transferencias):
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute("""
                UPDATE tratamientos 
                SET empresa_id=%s, nombre_tratamiento=%s, descripcion=%s, base_legal=%s, 
                    datos_personales=%s, responsables=%s, encargados=%s, transferencias=%s
                WHERE id=%s
            """, (empresa_id, nombre.strip(), descripcion.strip() if descripcion else None,
                  base_legal, datos_personales.strip() if datos_personales else None,
                  responsables.strip() if responsables else None, encargados.strip() if encargados else None,
                  transferencias.strip() if transferencias else None, tratamiento_id))
            conn.commit()
        conn.close()
        return True, "Tratamiento actualizado exitosamente."
    except Exception as e:
        return False, f"Error al actualizar tratamiento: {e}"

def delete_tratamiento(tratamiento_id):
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute("DELETE FROM tratamientos WHERE id=%s", (tratamiento_id,))
            conn.commit()
        conn.close()
        return True, "Tratamiento eliminado exitosamente."
    except Exception as e:
        return False, f"Error al eliminar tratamiento: {e}"

def get_tratamientos_df(empresa_id=None):
    try:
        conn = get_connection()
        if empresa_id:
            query = """
                SELECT t.id, 
                       COALESCE(e.nombre, 'Sin Empresa Asignada') AS empresa, 
                       COALESCE(e.rut, '') AS rut_empresa, 
                       COALESCE(t.nombre_tratamiento, 'Tratamiento sin nombre') AS nombre_tratamiento, 
                       COALESCE(t.descripcion, '') AS descripcion, 
                       COALESCE(t.base_legal, '') AS base_legal, 
                       COALESCE(t.datos_personales, '') AS datos_personales, 
                       COALESCE(t.responsables, '') AS responsables, 
                       COALESCE(t.encargados, '') AS encargados, 
                       COALESCE(t.transferencias, '') AS transferencias, 
                       t.created_at, t.empresa_id
                FROM tratamientos t
                LEFT JOIN empresas e ON t.empresa_id = e.id
                WHERE t.empresa_id = %s
                ORDER BY t.id DESC
            """
            df = pd.read_sql_query(query, conn, params=(empresa_id,))
        else:
            query = """
                SELECT t.id, 
                       COALESCE(e.nombre, 'Sin Empresa Asignada') AS empresa, 
                       COALESCE(e.rut, '') AS rut_empresa, 
                       COALESCE(t.nombre_tratamiento, 'Tratamiento sin nombre') AS nombre_tratamiento, 
                       COALESCE(t.descripcion, '') AS descripcion, 
                       COALESCE(t.base_legal, '') AS base_legal, 
                       COALESCE(t.datos_personales, '') AS datos_personales, 
                       COALESCE(t.responsables, '') AS responsables, 
                       COALESCE(t.encargados, '') AS encargados, 
                       COALESCE(t.transferencias, '') AS transferencias, 
                       t.created_at, t.empresa_id
                FROM tratamientos t
                LEFT JOIN empresas e ON t.empresa_id = e.id
                ORDER BY t.id DESC
            """
            df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error al listar tratamientos: {e}")
        return pd.DataFrame()

# ==============================================================================
# FUNCIONES CRUD: VISITAS / AUDITORÍAS
# ==============================================================================
def add_visita(empresa_id, fecha_visita, auditor, checklist_dict, puntaje, observaciones):
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute("""
                INSERT INTO visitas (empresa_id, fecha_visita, auditor, checklist_seguridad, puntaje, observaciones)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (empresa_id, fecha_visita, auditor.strip() if auditor else None,
                  extras.Json(checklist_dict), puntaje, observaciones.strip() if observaciones else None))
            conn.commit()
        conn.close()
        return True, "Visita de auditoría guardada exitosamente."
    except Exception as e:
        return False, f"Error al registrar visita: {e}"

def update_visita(visita_id, empresa_id, fecha_visita, auditor, checklist_dict, puntaje, observaciones):
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute("""
                UPDATE visitas 
                SET empresa_id=%s, fecha_visita=%s, auditor=%s, checklist_seguridad=%s, puntaje=%s, observaciones=%s
                WHERE id=%s
            """, (empresa_id, fecha_visita, auditor.strip() if auditor else None,
                  extras.Json(checklist_dict), puntaje, observaciones.strip() if observaciones else None, visita_id))
            conn.commit()
        conn.close()
        return True, "Visita actualizada exitosamente."
    except Exception as e:
        return False, f"Error al actualizar visita: {e}"

def delete_visita(visita_id):
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute("DELETE FROM visitas WHERE id=%s", (visita_id,))
            conn.commit()
        conn.close()
        return True, "Visita y evidencias eliminadas."
    except Exception as e:
        return False, f"Error al eliminar visita: {e}"

def get_visitas_df(empresa_id=None):
    try:
        conn = get_connection()
        if empresa_id:
            query = """
                SELECT v.id, 
                       COALESCE(e.nombre, 'Sin Empresa Asignada') AS empresa, 
                       COALESCE(e.rut, '') AS rut_empresa, 
                       COALESCE(v.fecha_visita, CURRENT_DATE) AS fecha_visita, 
                       COALESCE(v.auditor, '') AS auditor, 
                       COALESCE(v.puntaje, 0) AS puntaje, 
                       COALESCE(v.observaciones, '') AS observaciones, 
                       v.checklist_seguridad, v.created_at, v.empresa_id
                FROM visitas v
                LEFT JOIN empresas e ON v.empresa_id = e.id
                WHERE v.empresa_id = %s
                ORDER BY v.fecha_visita DESC, v.id DESC
            """
            df = pd.read_sql_query(query, conn, params=(empresa_id,))
        else:
            query = """
                SELECT v.id, 
                       COALESCE(e.nombre, 'Sin Empresa Asignada') AS empresa, 
                       COALESCE(e.rut, '') AS rut_empresa, 
                       COALESCE(v.fecha_visita, CURRENT_DATE) AS fecha_visita, 
                       COALESCE(v.auditor, '') AS auditor, 
                       COALESCE(v.puntaje, 0) AS puntaje, 
                       COALESCE(v.observaciones, '') AS observaciones, 
                       v.checklist_seguridad, v.created_at, v.empresa_id
                FROM visitas v
                LEFT JOIN empresas e ON v.empresa_id = e.id
                ORDER BY v.fecha_visita DESC, v.id DESC
            """
            df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error al listar visitas: {e}")
        return pd.DataFrame()

# ==============================================================================
# FUNCIONES CRUD: EVIDENCIAS
# ==============================================================================
def add_evidencia(visita_id, descripcion, foto_url):
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute("""
                INSERT INTO evidencias (visita_id, descripcion, foto_url)
                VALUES (%s, %s, %s)
            """, (visita_id, descripcion.strip() if descripcion else None, foto_url.strip() if foto_url else None))
            conn.commit()
        conn.close()
        return True, "Evidencia registrada exitosamente."
    except Exception as e:
        return False, f"Error al registrar evidencia: {e}"

def delete_evidencia(evidencia_id):
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute("DELETE FROM evidencias WHERE id=%s", (evidencia_id,))
            conn.commit()
        conn.close()
        return True, "Evidencia eliminada exitosamente."
    except Exception as e:
        return False, f"Error al eliminar evidencia: {e}"

def get_evidencias_df(visita_id=None):
    try:
        conn = get_connection()
        if visita_id:
            query = """
                SELECT ev.id, ev.visita_id, 
                       COALESCE(e.nombre, 'Sin Empresa') AS empresa, 
                       COALESCE(v.fecha_visita, CURRENT_DATE) AS fecha_visita, 
                       COALESCE(ev.descripcion, '') AS descripcion, 
                       COALESCE(ev.foto_url, '') AS foto_url, 
                       ev.created_at
                FROM evidencias ev
                LEFT JOIN visitas v ON ev.visita_id = v.id
                LEFT JOIN empresas e ON v.empresa_id = e.id
                WHERE ev.visita_id = %s
                ORDER BY ev.id DESC
            """
            df = pd.read_sql_query(query, conn, params=(visita_id,))
        else:
            query = """
                SELECT ev.id, ev.visita_id, 
                       COALESCE(e.nombre, 'Sin Empresa') AS empresa, 
                       COALESCE(v.fecha_visita, CURRENT_DATE) AS fecha_visita, 
                       COALESCE(ev.descripcion, '') AS descripcion, 
                       COALESCE(ev.foto_url, '') AS foto_url, 
                       ev.created_at
                FROM evidencias ev
                LEFT JOIN visitas v ON ev.visita_id = v.id
                LEFT JOIN empresas e ON v.empresa_id = e.id
                ORDER BY ev.id DESC
            """
            df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error al listar evidencias: {e}")
        return pd.DataFrame()

# ==============================================================================
# GENERACIÓN DE INFORME EXCEL COMPLETO (OPENPYXL)
# ==============================================================================
def generar_excel_completo():
    """Genera un archivo Excel en memoria con 5 hojas estilizadas profesionalmente."""
    wb = openpyxl.Workbook()
    default_sheet = wb.active
    wb.remove(default_sheet)

    # Estilos estándar
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=14, bold=True, color="1F4E79")
    bold_font = Font(name="Calibri", size=11, bold=True)
    regular_font = Font(name="Calibri", size=10)
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    # 1. Hoja EMPRESAS
    ws1 = wb.create_sheet(title="EMPRESAS")
    df_emp = get_empresas_df()
    ws1.append(["ID", "Nombre Empresa", "RUT", "Dirección", "Contacto", "Email", "Teléfono", "Fecha Registro"])
    for _, r in df_emp.iterrows():
        ws1.append([
            r['id'], r['nombre'], r['rut'], r['direccion'] or "", 
            r['contacto'] or "", r['email'] or "", r['telefono'] or "",
            str(r['created_at'])[:19] if pd.notnull(r['created_at']) else ""
        ])

    # 2. Hoja TRATAMIENTOS
    ws2 = wb.create_sheet(title="TRATAMIENTOS")
    df_trat = get_tratamientos_df()
    ws2.append(["ID", "Empresa", "RUT Empresa", "Tratamiento", "Descripción", "Base Legal", "Datos Personales", "Responsables", "Encargados", "Transferencias", "Fecha Registro"])
    for _, r in df_trat.iterrows():
        ws2.append([
            r['id'], r['empresa'], r['rut_empresa'], r['nombre_tratamiento'],
            r['descripcion'] or "", r['base_legal'] or "", r['datos_personales'] or "",
            r['responsables'] or "", r['encargados'] or "", r['transferencias'] or "",
            str(r['created_at'])[:19] if pd.notnull(r['created_at']) else ""
        ])

    # 3. Hoja VISITAS
    ws3 = wb.create_sheet(title="VISITAS")
    df_vis = get_visitas_df()
    headers_vis = ["ID", "Empresa", "RUT Empresa", "Fecha Visita", "Auditor", "Puntaje (/15)", "% Cumplimiento", "Observaciones"]
    for q in CHECKLIST_PREGUNTAS:
        headers_vis.append(q[:30] + "...")
    ws3.append(headers_vis)
    
    for _, r in df_vis.iterrows():
        puntaje = r['puntaje'] if pd.notnull(r['puntaje']) else 0
        porcentaje = f"{(puntaje / 15) * 100:.1f}%" if puntaje else "0.0%"
        row_data = [
            r['id'], r['empresa'], r['rut_empresa'], str(r['fecha_visita']),
            r['auditor'] or "", puntaje, porcentaje, r['observaciones'] or ""
        ]
        
        chk = r['checklist_seguridad']
        if isinstance(chk, str):
            try:
                chk = json.loads(chk)
            except:
                chk = {}
        elif not isinstance(chk, dict):
            chk = {}
            
        for q in CHECKLIST_PREGUNTAS:
            row_data.append(chk.get(q, "N/A"))
        ws3.append(row_data)

    # 4. Hoja EVIDENCIAS
    ws4 = wb.create_sheet(title="EVIDENCIAS")
    df_ev = get_evidencias_df()
    ws4.append(["ID", "ID Visita", "Empresa", "Fecha Visita", "Descripción", "URL Foto / Archivo", "Fecha Registro"])
    for _, r in df_ev.iterrows():
        ws4.append([
            r['id'], r['visita_id'], r['empresa'], str(r['fecha_visita']),
            r['descripcion'] or "", r['foto_url'] or "",
            str(r['created_at'])[:19] if pd.notnull(r['created_at']) else ""
        ])

    # 5. Hoja RESUMEN
    ws5 = wb.create_sheet(title="RESUMEN")
    ws5.append(["INFORME CONSOLIDADO DE CUMPLIMIENTO Y AUDITORÍA GRC"])
    ws5.append([f"Fecha de Generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
    ws5.append([])
    ws5.append(["Métrica General", "Valor"])
    ws5.append(["Total de Empresas Registradas", len(df_emp)])
    ws5.append(["Total de Tratamientos (ROPA)", len(df_trat)])
    ws5.append(["Total de Visitas de Auditoría Realizadas", len(df_vis)])
    ws5.append(["Total de Evidencias Adjuntas", len(df_ev)])
    
    promedio_puntaje = df_vis['puntaje'].mean() if not df_vis.empty and 'puntaje' in df_vis.columns else 0
    ws5.append(["Promedio de Puntaje de Seguridad (/15)", f"{promedio_puntaje:.2f}"])
    ws5.append(["Porcentaje Promedio de Cumplimiento", f"{(promedio_puntaje / 15) * 100:.1f}%" if promedio_puntaje else "0%"])

    # Aplicar estilos y anchos de columna en todas las hojas
    for ws in [ws1, ws2, ws3, ws4, ws5]:
        ws.views.sheetView[0].showGridLines = True
        if ws != ws5:
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            ws.row_dimensions[1].height = 28
        else:
            ws["A1"].font = title_font
            ws["A2"].font = regular_font
            ws["A4"].font = bold_font
            ws["B4"].font = bold_font
            ws["A4"].fill = header_fill
            ws["B4"].fill = header_fill
            ws["A4"].font = header_font
            ws["B4"].font = header_font

        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                cell.border = thin_border
                val_str = str(cell.value or '')
                if len(val_str) > max_len:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()

# ==============================================================================
# INICIALIZACIÓN Y MENÚ
# ==============================================================================
init_db()

# Menú lateral
st.sidebar.image("https://img.icons8.com/fluency/96/shield.png", width=70)
st.sidebar.title("Serviphar GRC Lite")
st.sidebar.caption("Plataforma de Auditoría y Cumplimiento Legal")

menu_opcion = st.sidebar.radio(
    "Menú Principal",
    [
        "🏠 Dashboard",
        "🏢 Empresas",
        "📋 Tratamientos (ROPA)",
        "🔍 Visitas / Auditorías",
        "📸 Evidencias",
        "📊 Exportar Informe"
    ]
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reparar / Sincronizar Base de Datos"):
    init_db()
    st.sidebar.success("Estructura de base de datos sincronizada.")
    st.rerun()

st.sidebar.info("💡 **Tip Terreno:** Todos los cambios se guardan directamente en Neon PostgreSQL y quedan sincronizados en tiempo real.")

# ==============================================================================
# MÓDULO 1: DASHBOARD
# ==============================================================================
if menu_opcion == "🏠 Dashboard":
    st.header("📊 Panel de Control GRC")
    
    df_emp = get_empresas_df()
    df_trat = get_tratamientos_df()
    df_vis = get_visitas_df()
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🏢 Total Empresas", len(df_emp))
    with c2:
        st.metric("📋 Total Tratamientos (ROPA)", len(df_trat))
    with c3:
        st.metric("🔍 Auditorías Realizadas", len(df_vis))
    with c4:
        if not df_vis.empty:
            ultima_fecha = str(df_vis.iloc[0]['fecha_visita'])
            ultima_empresa = str(df_vis.iloc[0]['empresa'])
            st.metric("🗓️ Última Visita", ultima_fecha, delta=ultima_empresa, delta_color="off")
        else:
            st.metric("🗓️ Última Visita", "Sin registros")

    st.markdown("---")

    col_izq, col_der = st.columns([3, 2])

    with col_izq:
        st.subheader("🏢 Últimas 5 Empresas Registradas")
        if not df_emp.empty:
            ultimas_empresas = df_emp.head(5)[['id', 'nombre', 'rut', 'contacto', 'email', 'created_at']]
            st.dataframe(ultimas_empresas, use_container_width=True, hide_index=True)
        else:
            st.info("No hay empresas registradas aún. Ve al módulo **Empresas** para agregar la primera.")

    with col_der:
        st.subheader("📈 Tratamientos por Empresa")
        if not df_trat.empty:
            conteo_trat = df_trat['empresa'].value_counts()
            st.bar_chart(conteo_trat, color="#1E88E5")
        else:
            st.info("No hay tratamientos registrados para generar gráficos.")

    if not df_vis.empty:
        st.markdown("---")
        st.subheader("🛡️ Últimas Auditorías de Seguridad y Puntajes")
        vis_display = df_vis[['id', 'empresa', 'fecha_visita', 'auditor', 'puntaje', 'observaciones']].head(5).copy()
        vis_display['Cumplimiento'] = vis_display['puntaje'].apply(lambda p: f"{(p/15)*100:.0f}% ({p}/15)" if pd.notnull(p) else "N/A")
        st.dataframe(vis_display[['empresa', 'fecha_visita', 'auditor', 'Cumplimiento', 'observaciones']], use_container_width=True, hide_index=True)

# ==============================================================================
# MÓDULO 2: EMPRESAS
# ==============================================================================
elif menu_opcion == "🏢 Empresas":
    st.header("🏢 Gestión de Empresas del Grupo / Clientes")

    tab_lista, tab_crear = st.tabs(["📋 Listado de Empresas", "➕ Registrar Nueva Empresa"])

    with tab_crear:
        st.subheader("Registrar Nueva Empresa")
        with st.form("form_crear_empresa", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                nombre = st.text_input("Nombre / Razón Social *", placeholder="Ej. Serviphar Chile SpA")
                rut = st.text_input("RUT *", placeholder="Ej. 76.123.456-7")
                direccion = st.text_input("Dirección", placeholder="Ej. Av. Providencia 1234, Santiago")
            with col_b:
                contacto = st.text_input("Persona de Contacto", placeholder="Ej. Juan Pérez")
                email = st.text_input("Correo Electrónico", placeholder="Ej. contacto@empresa.cl")
                telefono = st.text_input("Teléfono", placeholder="Ej. +56 9 1234 5678")

            submitted = st.form_submit_button("💾 Guardar Empresa", use_container_width=True, type="primary")
            if submitted:
                if not nombre or not rut:
                    st.error("Por favor completa los campos obligatorios: **Nombre** y **RUT**.")
                else:
                    ok, msg = add_empresa(nombre, rut, direccion, contacto, email, telefono)
                    if ok:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    with tab_lista:
        buscador = st.text_input("🔍 Buscar empresa por Nombre o RUT:", placeholder="Escribe para filtrar...")
        df_empresas = get_empresas_df(search_term=buscador)

        if df_empresas.empty:
            st.info("No se encontraron empresas registradas.")
        else:
            st.caption(f"Total: **{len(df_empresas)}** empresas encontradas.")
            st.dataframe(
                df_empresas[['id', 'nombre', 'rut', 'contacto', 'email', 'telefono', 'direccion', 'created_at']],
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")
            st.subheader("⚙️ Acciones por Empresa")
            
            empresa_opciones = {f"{r['id']} - {r['nombre']} ({r['rut']})": r['id'] for _, r in df_empresas.iterrows()}
            seleccion_empresa_str = st.selectbox("Selecciona una empresa para gestionar:", list(empresa_opciones.keys()))
            empresa_sel_id = empresa_opciones[seleccion_empresa_str]
            empresa_data = df_empresas[df_empresas['id'] == empresa_sel_id].iloc[0]

            col_edit, col_del = st.columns([2, 1])

            with col_edit:
                with st.expander(f"✏️ Editar: {empresa_data['nombre']}", expanded=False):
                    with st.form(f"form_edit_empresa_{empresa_sel_id}"):
                        e_nombre = st.text_input("Nombre", value=empresa_data['nombre'])
                        e_rut = st.text_input("RUT", value=empresa_data['rut'])
                        e_dir = st.text_input("Dirección", value=empresa_data['direccion'] or "")
                        e_cont = st.text_input("Contacto", value=empresa_data['contacto'] or "")
                        e_mail = st.text_input("Email", value=empresa_data['email'] or "")
                        e_tel = st.text_input("Teléfono", value=empresa_data['telefono'] or "")
                        
                        btn_update = st.form_submit_button("Actualizar Cambios", type="primary")
                        if btn_update:
                            ok, msg = update_empresa(empresa_sel_id, e_nombre, e_rut, e_dir, e_cont, e_mail, e_tel)
                            if ok:
                                st.success(f"✅ {msg}")
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")

            with col_del:
                with st.expander("🗑️ Eliminar Empresa"):
                    st.warning("⚠️ **Atención:** Eliminar esta empresa borrará también sus tratamientos, visitas y evidencias vinculadas.")
                    confirmar = st.checkbox("Confirmo que deseo eliminar permanentemente esta empresa.", key=f"del_chk_{empresa_sel_id}")
                    if st.button("Eliminar Empresa Definitivamente", type="secondary", disabled=not confirmar, key=f"del_btn_{empresa_sel_id}"):
                        ok, msg = delete_empresa(empresa_sel_id)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

# ==============================================================================
# MÓDULO 3: TRATAMIENTOS (ROPA)
# ==============================================================================
elif menu_opcion == "📋 Tratamientos (ROPA)":
    st.header("📋 Registro de Actividades de Tratamiento (ROPA)")
    
    df_empresas = get_empresas_df()
    if df_empresas.empty:
        st.warning("⚠️ Primero debes registrar al menos una empresa en el módulo **Empresas** antes de crear tratamientos de datos.")
    else:
        tab_trat_lista, tab_trat_crear = st.tabs(["📋 Listado de Tratamientos", "➕ Registrar Nuevo Tratamiento"])

        empresa_map = {f"{r['id']} - {r['nombre']} ({r['rut']})": r['id'] for _, r in df_empresas.iterrows()}

        with tab_trat_crear:
            st.subheader("Nuevo Tratamiento de Datos")
            with st.form("form_crear_tratamiento", clear_on_submit=True):
                empresa_sel_key = st.selectbox("Empresa Responsable *", list(empresa_map.keys()))
                nombre_trat = st.text_input("Nombre del Tratamiento *", placeholder="Ej. Gestión de Nómina y Recursos Humanos")
                
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    base_legal = st.selectbox(
                        "Base Legal de Licitud *",
                        ["Consentimiento", "Ejecución de Contrato", "Obligación Legal", "Interés Legítimo", "Interés Público", "Protección de Intereses Vitales"]
                    )
                    datos_personales = st.text_area("Categorías de Datos Personales", placeholder="Ej. Nombre, RUT, cuenta bancaria, domicilio, remuneración...", height=80)
                    responsables = st.text_input("Responsables del Tratamiento", placeholder="Ej. Gerencia de RRHH / DPO")
                with col_t2:
                    transferencias = st.selectbox("Transferencias Internacionales", ["No aplica", "Sí - Servidores Cloud (EE.UU.)", "Sí - Proveedores en UE", "Sí - Otros países"])
                    descripcion = st.text_area("Descripción y Finalidad del Tratamiento", placeholder="Ej. Procesamiento y pago de remuneraciones, imposiciones y contratos...", height=80)
                    encargados = st.text_input("Encargados del Tratamiento (Proveedores)", placeholder="Ej. Software de RRHH en la nube (Talana, Buk, etc.)")

                submitted_trat = st.form_submit_button("💾 Guardar Tratamiento", use_container_width=True, type="primary")
                if submitted_trat:
                    if not nombre_trat:
                        st.error("El nombre del tratamiento es obligatorio.")
                    else:
                        eid = empresa_map[empresa_sel_key]
                        ok, msg = add_tratamiento(eid, nombre_trat, descripcion, base_legal, datos_personales, responsables, encargados, transferencias)
                        if ok:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

        with tab_trat_lista:
            col_f1, col_f2 = st.columns([2, 2])
            with col_f1:
                filtro_empresa = st.selectbox("🔍 Filtrar por Empresa:", ["Todas las empresas"] + list(empresa_map.keys()))
            
            emp_id_filtro = empresa_map[filtro_empresa] if filtro_empresa != "Todas las empresas" else None
            df_tratamientos = get_tratamientos_df(empresa_id=emp_id_filtro)

            if df_tratamientos.empty:
                st.info("No hay tratamientos registrados para el filtro seleccionado.")
            else:
                st.dataframe(
                    df_tratamientos[['id', 'empresa', 'nombre_tratamiento', 'base_legal', 'datos_personales', 'responsables', 'transferencias', 'created_at']],
                    use_container_width=True,
                    hide_index=True
                )

                st.markdown("---")
                st.subheader("⚙️ Detalle y Edición de Tratamiento")
                trat_dict = {f"{r['id']} - {r['nombre_tratamiento']} ({r['empresa']})": r['id'] for _, r in df_tratamientos.iterrows()}
                trat_sel_key = st.selectbox("Selecciona un tratamiento para ver detalle o editar:", list(trat_dict.keys()))
                trat_sel_id = trat_dict[trat_sel_key]
                t_row = df_tratamientos[df_tratamientos['id'] == trat_sel_id].iloc[0]

                with st.expander(f"🔍 Detalle completo: {t_row['nombre_tratamiento']}", expanded=True):
                    st.markdown(f"**Empresa:** {t_row['empresa']} ({t_row['rut_empresa']})")
                    st.markdown(f"**Base Legal:** `{t_row['base_legal']}`")
                    st.markdown(f"**Finalidad / Descripción:** {t_row['descripcion'] or 'No especificado'}")
                    st.markdown(f"**Datos Tratados:** {t_row['datos_personales'] or 'No especificado'}")
                    st.markdown(f"**Responsables:** {t_row['responsables'] or 'No especificado'}")
                    st.markdown(f"**Encargados:** {t_row['encargados'] or 'No especificado'}")
                    st.markdown(f"**Transferencias Internacionales:** {t_row['transferencias'] or 'No especificado'}")

                    if st.button("🗑️ Eliminar este Tratamiento", key=f"del_trat_{trat_sel_id}", type="secondary"):
                        ok, msg = delete_tratamiento(trat_sel_id)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

# ==============================================================================
# MÓDULO 4: VISITAS / AUDITORÍAS (CHECKLIST)
# ==============================================================================
elif menu_opcion == "🔍 Visitas / Auditorías":
    st.header("🔍 Auditorías en Terreno y Checklist de Seguridad")

    df_empresas = get_empresas_df()
    if df_empresas.empty:
        st.warning("⚠️ Debes registrar empresas antes de poder realizar auditorías.")
    else:
        tab_vis_lista, tab_vis_crear = st.tabs(["📋 Historial de Auditorías", "➕ Nueva Auditoría en Terreno"])
        empresa_map = {f"{r['id']} - {r['nombre']} ({r['rut']})": r['id'] for _, r in df_empresas.iterrows()}

        with tab_vis_crear:
            st.subheader("Formulario de Auditoría en Terreno")
            
            with st.form("form_nueva_visita"):
                col_v1, col_v2, col_v3 = st.columns(3)
                with col_v1:
                    vis_empresa_key = st.selectbox("Empresa Auditada *", list(empresa_map.keys()))
                with col_v2:
                    vis_fecha = st.date_input("Fecha de Visita *", value=date.today())
                with col_v3:
                    vis_auditor = st.text_input("Nombre del Auditor *", placeholder="Ej. Gonzalo Vega (Lead Auditor)")

                st.markdown("#### 📝 Checklist de Seguridad de la Información (15 Puntos)")
                st.caption("Selecciona el estado de cumplimiento de cada control. **Sí = 1 pto**, **No = 0 ptos**, **N/A = 0 ptos**.")

                respuestas_checklist = {}
                for idx, pregunta in enumerate(CHECKLIST_PREGUNTAS, start=1):
                    resp = st.radio(
                        pregunta,
                        options=["Sí", "No", "N/A"],
                        index=1,
                        horizontal=True,
                        key=f"chk_q_{idx}"
                    )
                    respuestas_checklist[pregunta] = resp

                st.markdown("---")
                vis_observaciones = st.text_area("Observaciones y Hallazgos Principales", placeholder="Anotaciones de la reunión, evidencias pendientes, riesgos detectados...", height=100)

                btn_guardar_visita = st.form_submit_button("💾 Guardar Auditoría", use_container_width=True, type="primary")

                if btn_guardar_visita:
                    puntaje = sum(1 for v in respuestas_checklist.values() if v == "Sí")
                    eid = empresa_map[vis_empresa_key]
                    ok, msg = add_visita(eid, vis_fecha, vis_auditor, respuestas_checklist, puntaje, vis_observaciones)
                    if ok:
                        porcentaje = (puntaje / 15) * 100
                        st.success(f"✅ {msg} Puntaje obtenido: **{puntaje}/15 ({porcentaje:.1f}%)**")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

        with tab_vis_lista:
            filtro_vis_emp = st.selectbox("Filtrar auditorías por empresa:", ["Todas las empresas"] + list(empresa_map.keys()), key="filtro_vis_emp")
            eid_vis_filtro = empresa_map[filtro_vis_emp] if filtro_vis_emp != "Todas las empresas" else None
            df_visitas = get_visitas_df(empresa_id=eid_vis_filtro)

            if df_visitas.empty:
                st.info("No hay auditorías registradas.")
            else:
                df_visitas_view = df_visitas[['id', 'empresa', 'fecha_visita', 'auditor', 'puntaje', 'observaciones']].copy()
                df_visitas_view['Cumplimiento'] = df_visitas_view['puntaje'].apply(lambda p: f"{(p/15)*100:.0f}% ({p}/15)" if pd.notnull(p) else "0%")
                
                st.dataframe(
                    df_visitas_view[['id', 'empresa', 'fecha_visita', 'auditor', 'Cumplimiento', 'observaciones']],
                    use_container_width=True,
                    hide_index=True
                )

                st.markdown("---")
                st.subheader("🔍 Detalle del Checklist de Auditoría")
                vis_opciones = {f"ID {r['id']} - {r['empresa']} ({r['fecha_visita']})": r['id'] for _, r in df_visitas.iterrows()}
                vis_sel_str = st.selectbox("Selecciona una visita para ver el desglose del checklist:", list(vis_opciones.keys()))
                vis_sel_id = vis_opciones[vis_sel_str]
                v_row = df_visitas[df_visitas['id'] == vis_sel_id].iloc[0]

                with st.expander(f"📊 Desglose de Respuestas: Auditoría #{vis_sel_id}", expanded=True):
                    p = v_row['puntaje'] or 0
                    pct = (p / 15) * 100
                    st.metric("Puntaje Obtenido", f"{p} de 15 controles", f"{pct:.1f}% de cumplimiento")
                    
                    chk_data = v_row['checklist_seguridad']
                    if isinstance(chk_data, str):
                        try:
                            chk_data = json.loads(chk_data)
                        except:
                            chk_data = {}
                    elif not isinstance(chk_data, dict):
                        chk_data = {}

                    col_q1, col_q2 = st.columns(2)
                    items = list(chk_data.items())
                    mitad = len(items) // 2
                    
                    with col_q1:
                        for preg, r in items[:mitad]:
                            icono = "✅" if r == "Sí" else ("❌" if r == "No" else "⚪")
                            st.write(f"{icono} **{preg}**: `{r}`")
                    with col_q2:
                        for preg, r in items[mitad:]:
                            icono = "✅" if r == "Sí" else ("❌" if r == "No" else "⚪")
                            st.write(f"{icono} **{preg}**: `{r}`")

                    if st.button("🗑️ Eliminar esta Auditoría", key=f"del_vis_{vis_sel_id}", type="secondary"):
                        ok, msg = delete_visita(vis_sel_id)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

# ==============================================================================
# MÓDULO 5: EVIDENCIAS
# ==============================================================================
elif menu_opcion == "📸 Evidencias":
    st.header("📸 Registro y Gestión de Evidencias")

    df_visitas = get_visitas_df()
    if df_visitas.empty:
        st.warning("⚠️ Primero debes registrar visitas/auditorías para poder asociarles evidencias fotográficas o documentales.")
    else:
        tab_ev_lista, tab_ev_crear = st.tabs(["📋 Evidencias Registradas", "➕ Adjuntar Nueva Evidencia"])
        visita_map = {f"Auditoría #{r['id']} - {r['empresa']} ({r['fecha_visita']})": r['id'] for _, r in df_visitas.iterrows()}

        with tab_ev_crear:
            st.subheader("Adjuntar Evidencia a una Auditoría")
            with st.form("form_crear_evidencia", clear_on_submit=True):
                vis_ev_key = st.selectbox("Selecciona la Visita Asociada *", list(visita_map.keys()))
                descripcion_ev = st.text_area("Descripción de la Evidencia *", placeholder="Ej. Foto del rack de servidores con chapa de seguridad...", height=80)
                foto_url = st.text_input("URL o Enlace de la Foto / Documento", placeholder="Ej. https://storage.googleapis.com/... o https://drive.google.com/...")
                
                submitted_ev = st.form_submit_button("💾 Guardar Evidencia", use_container_width=True, type="primary")
                if submitted_ev:
                    if not descripcion_ev:
                        st.error("La descripción de la evidencia es obligatoria.")
                    else:
                        vid = visita_map[vis_ev_key]
                        ok, msg = add_evidencia(vid, descripcion_ev, foto_url)
                        if ok:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

        with tab_ev_lista:
            filtro_ev_vis = st.selectbox("Filtrar por Auditoría:", ["Todas las auditorías"] + list(visita_map.keys()))
            vid_filtro = visita_map[filtro_ev_vis] if filtro_ev_vis != "Todas las auditorías" else None
            df_evidencias = get_evidencias_df(visita_id=vid_filtro)

            if df_evidencias.empty:
                st.info("No hay evidencias registradas.")
            else:
                st.dataframe(
                    df_evidencias[['id', 'visita_id', 'empresa', 'fecha_visita', 'descripcion', 'foto_url', 'created_at']],
                    use_container_width=True,
                    hide_index=True
                )

                st.markdown("---")
                st.subheader("🖼️ Galería y Detalle de Evidencias")
                for _, r in df_evidencias.iterrows():
                    with st.container():
                        st.markdown(f"**Evidencia #{r['id']}** | Auditoría #{r['visita_id']} - {r['empresa']} ({r['fecha_visita']})")
                        st.write(f"📝 {r['descripcion']}")
                        if r['foto_url']:
                            st.markdown(f"🔗 [Abrir Enlace de Evidencia]({r['foto_url']})")
                            if any(r['foto_url'].lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                                st.image(r['foto_url'], width=400)
                        if st.button("🗑️ Eliminar Evidencia", key=f"del_ev_{r['id']}"):
                            ok, msg = delete_evidencia(r['id'])
                            if ok:
                                st.success(msg)
                                st.rerun()
                        st.markdown("---")

# ==============================================================================
# MÓDULO 6: EXPORTAR INFORME EXCEL
# ==============================================================================
elif menu_opcion == "📊 Exportar Informe":
    st.header("📊 Generación y Descarga de Informe Completo")
    st.write("Genera un libro Excel consolidado (`.xlsx`) con 5 hojas formateadas profesionalmente:")
    
    st.markdown("""
    - **Hoja 1 - EMPRESAS:** Catálogo completo de empresas del grupo.
    - **Hoja 2 - TRATAMIENTOS:** Registro de Actividades de Tratamiento (ROPA).
    - **Hoja 3 - VISITAS:** Auditorías realizadas con puntaje y desglose del checklist.
    - **Hoja 4 - EVIDENCIAS:** Registro y enlaces de evidencias levantadas en terreno.
    - **Hoja 5 - RESUMEN:** Métricas ejecutivas, porcentajes de cumplimiento y fecha de emisión.
    """)

    st.markdown("---")

    col_exp1, col_exp2 = st.columns([1, 2])
    with col_exp1:
        if st.button("🔄 Generar Informe Excel", type="primary", use_container_width=True):
            with st.spinner("Generando libro Excel..."):
                excel_bytes = generar_excel_completo()
                st.session_state['excel_informe'] = excel_bytes
                st.success("✅ ¡Informe generado con éxito!")

    with col_exp2:
        if 'excel_informe' in st.session_state:
            nombre_archivo = f"Serviphar_GRC_Informe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            st.download_button(
                label="📥 Descargar Informe Completo Excel (.xlsx)",
                data=st.session_state['excel_informe'],
                file_name=nombre_archivo,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
