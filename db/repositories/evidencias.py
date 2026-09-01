"""
Repositorio de Evidencias.
Funciones CRUD para la tabla 'evidencias'.
Fase 1: soporta evaluacion_id opcional (nullable).
Las evidencias se adjuntan como URLs externas; no se almacenan archivos binarios.
"""

import streamlit as st
import pandas as pd

from db.connection import get_connection


# ==============================================================================
# ESCRITURA
# ==============================================================================

def add_evidencia(
    visita_id: int,
    evaluacion_id,
    descripcion: str,
    foto_url: str,
) -> tuple[bool, str]:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                INSERT INTO evidencias (visita_id, evaluacion_id, descripcion, foto_url)
                VALUES (%s,%s,%s,%s)
                """,
                (
                    visita_id,
                    evaluacion_id or None,
                    descripcion.strip() if descripcion else None,
                    foto_url.strip() if foto_url else None,
                ),
            )
        conn.commit()
        return True, "Evidencia registrada exitosamente."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al registrar evidencia ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


def delete_evidencia(evidencia_id: int) -> tuple[bool, str]:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute("DELETE FROM evidencias WHERE id=%s", (evidencia_id,))
        conn.commit()
        return True, "Evidencia eliminada exitosamente."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al eliminar evidencia ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


# ==============================================================================
# LECTURA
# ==============================================================================

def get_evidencias_df(
    visita_id: int = None,
    evaluacion_id: int = None,
    empresa_id: int = None,
) -> pd.DataFrame:
    conn = None
    try:
        conn = get_connection()
        base_query = """
            SELECT
                ev.id,
                ev.visita_id,
                COALESCE(e.nombre, 'Sin Empresa')              AS empresa,
                COALESCE(v.fecha_visita, CURRENT_DATE)         AS fecha_visita,
                COALESCE(ev.descripcion, '')                   AS descripcion,
                COALESCE(ev.foto_url, '')                      AS foto_url,
                ev.evaluacion_id,
                COALESCE(eval.nombre, '')                      AS evaluacion_nombre,
                ev.created_at
            FROM evidencias ev
            LEFT JOIN visitas     v    ON ev.visita_id    = v.id
            LEFT JOIN empresas    e    ON v.empresa_id    = e.id
            LEFT JOIN evaluaciones eval ON ev.evaluacion_id = eval.id
        """
        conditions = []
        params = []
        if visita_id:
            conditions.append("ev.visita_id = %s")
            params.append(visita_id)
        if evaluacion_id:
            conditions.append("ev.evaluacion_id = %s")
            params.append(evaluacion_id)
        if empresa_id:
            conditions.append("(v.empresa_id = %s OR eval.empresa_id = %s)")
            params.extend([empresa_id, empresa_id])

        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        base_query += " ORDER BY ev.id DESC"

        df = pd.read_sql_query(base_query, conn, params=params if params else None)
        return df
    except RuntimeError as exc:
        st.error(f"⚠️ {exc}")
        return pd.DataFrame()
    except Exception as exc:
        st.error(f"Error al listar evidencias ({type(exc).__name__}).")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()
