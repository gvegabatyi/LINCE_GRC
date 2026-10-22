"""
Repositorio de Empresas.
Funciones CRUD para la tabla 'empresas'.
La tabla NO se crea ni altera desde aquí: solo se consulta y modifica.
"""

import streamlit as st
import pandas as pd
import psycopg2

from db.connection import get_connection


def _invalidar_cache_dependiente() -> None:
    """
    Invalida lecturas cacheadas que dependen de empresas: el nombre de la empresa
    aparece en sus JOIN y el DELETE en cascada elimina sus filas.
    Import perezoso para evitar dependencias circulares entre repositorios.
    """
    from db.repositories import derechos, importaciones, tratamientos

    derechos.get_solicitudes_df.clear()
    tratamientos.get_tratamientos_df.clear()
    importaciones.get_importaciones_df.clear()
    importaciones.get_importaciones_reabribles_df.clear()
    importaciones.get_importacion_por_id.clear()
    importaciones.get_candidatos_df.clear()


# ==============================================================================
# ESCRITURA (retornan tuple[bool, str])
# ==============================================================================

def add_empresa(nombre: str, rut: str, direccion: str, contacto: str,
                email: str, telefono: str) -> tuple[bool, str]:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                INSERT INTO empresas (nombre, rut, direccion, contacto, email, telefono)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    nombre.strip(),
                    rut.strip(),
                    direccion.strip() if direccion else None,
                    contacto.strip() if contacto else None,
                    email.strip() if email else None,
                    telefono.strip() if telefono else None,
                ),
            )
        conn.commit()
        get_empresas_df.clear()
        return True, "Empresa registrada exitosamente."
    except psycopg2.IntegrityError:
        if conn:
            conn.rollback()
        return False, "Ya existe una empresa con ese RUT."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al guardar empresa ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


def update_empresa(empresa_id: int, nombre: str, rut: str, direccion: str,
                   contacto: str, email: str, telefono: str) -> tuple[bool, str]:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                UPDATE empresas
                SET nombre=%s, rut=%s, direccion=%s, contacto=%s, email=%s, telefono=%s
                WHERE id=%s
                """,
                (
                    nombre.strip(),
                    rut.strip(),
                    direccion.strip() if direccion else None,
                    contacto.strip() if contacto else None,
                    email.strip() if email else None,
                    telefono.strip() if telefono else None,
                    empresa_id,
                ),
            )
        conn.commit()
        get_empresas_df.clear()
        _invalidar_cache_dependiente()
        return True, "Empresa actualizada exitosamente."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al actualizar empresa ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


def delete_empresa(empresa_id: int) -> tuple[bool, str]:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute("DELETE FROM empresas WHERE id=%s", (empresa_id,))
        conn.commit()
        get_empresas_df.clear()
        _invalidar_cache_dependiente()
        return True, "Empresa y registros asociados eliminados."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al eliminar empresa ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


# ==============================================================================
# LECTURA (retornan pd.DataFrame — muestran st.error en caso de fallo)
# ==============================================================================

@st.cache_data(ttl=60)
def get_empresas_df(search_term: str = "") -> pd.DataFrame:
    conn = None
    try:
        conn = get_connection()
        base_select = """
            SELECT
                id,
                nombre,
                COALESCE(rut, '')       AS rut,
                COALESCE(direccion, '') AS direccion,
                COALESCE(contacto, '')  AS contacto,
                COALESCE(email, '')     AS email,
                COALESCE(telefono, '')  AS telefono,
                created_at
            FROM empresas
        """
        if search_term:
            query = base_select + " WHERE nombre ILIKE %s OR rut ILIKE %s ORDER BY id DESC"
            term = f"%{search_term}%"
            df = pd.read_sql_query(query, conn, params=(term, term))
        else:
            query = base_select + " ORDER BY id DESC"
            df = pd.read_sql_query(query, conn)
        return df
    except RuntimeError as exc:
        st.error(f"⚠️ {exc}")
        raise
    except Exception as exc:
        st.error(f"Error al listar empresas ({type(exc).__name__}).")
        raise
    finally:
        if conn:
            conn.close()
