"""
Repositorio de Visitas / Auditorías.
Funciones CRUD para la tabla 'visitas'.
Fase 1: soporta evaluacion_id (nullable) y tipo_visita (nullable).
El checklist JSONB de 15 preguntas se mantiene sin cambios.
"""

import streamlit as st
import pandas as pd
from psycopg2 import extras

from db.connection import get_connection


# ==============================================================================
# ESCRITURA
# ==============================================================================

def add_visita(
    empresa_id: int,
    evaluacion_id,
    fecha_visita,
    tipo_visita: str,
    auditor: str,
    checklist_dict: dict,
    puntaje: int,
    observaciones: str,
) -> tuple[bool, str]:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                INSERT INTO visitas (
                    empresa_id, evaluacion_id, fecha_visita, tipo_visita,
                    auditor, checklist_seguridad, puntaje, observaciones
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    empresa_id,
                    evaluacion_id or None,
                    fecha_visita,
                    tipo_visita if tipo_visita and tipo_visita != "Sin especificar" else None,
                    auditor.strip() if auditor else None,
                    extras.Json(checklist_dict),
                    puntaje,
                    observaciones.strip() if observaciones else None,
                ),
            )
        conn.commit()
        return True, "Visita de auditoría guardada exitosamente."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al registrar visita ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


def update_visita(
    visita_id: int,
    empresa_id: int,
    evaluacion_id,
    fecha_visita,
    tipo_visita: str,
    auditor: str,
    checklist_dict: dict,
    puntaje: int,
    observaciones: str,
) -> tuple[bool, str]:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                UPDATE visitas SET
                    empresa_id=%s, evaluacion_id=%s, fecha_visita=%s, tipo_visita=%s,
                    auditor=%s, checklist_seguridad=%s, puntaje=%s, observaciones=%s
                WHERE id=%s
                """,
                (
                    empresa_id,
                    evaluacion_id or None,
                    fecha_visita,
                    tipo_visita if tipo_visita and tipo_visita != "Sin especificar" else None,
                    auditor.strip() if auditor else None,
                    extras.Json(checklist_dict),
                    puntaje,
                    observaciones.strip() if observaciones else None,
                    visita_id,
                ),
            )
        conn.commit()
        return True, "Visita actualizada exitosamente."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al actualizar visita ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


def delete_visita(visita_id: int) -> tuple[bool, str]:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute("DELETE FROM visitas WHERE id=%s", (visita_id,))
        conn.commit()
        return True, "Visita y evidencias eliminadas."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al eliminar visita ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


# ==============================================================================
# LECTURA
# ==============================================================================

def get_visitas_df(empresa_id: int = None, evaluacion_id: int = None) -> pd.DataFrame:
    conn = None
    try:
        conn = get_connection()
        base_query = """
            SELECT
                v.id,
                COALESCE(e.nombre, 'Sin Empresa Asignada')    AS empresa,
                COALESCE(e.rut, '')                           AS rut_empresa,
                COALESCE(v.fecha_visita, CURRENT_DATE)        AS fecha_visita,
                COALESCE(v.auditor, '')                       AS auditor,
                COALESCE(v.puntaje, 0)                        AS puntaje,
                COALESCE(v.observaciones, '')                 AS observaciones,
                COALESCE(v.tipo_visita, 'Sin especificar')    AS tipo_visita,
                v.checklist_seguridad,
                v.empresa_id,
                v.evaluacion_id,
                COALESCE(ev.nombre, '')                       AS evaluacion_nombre,
                v.created_at
            FROM visitas v
            LEFT JOIN empresas e     ON v.empresa_id    = e.id
            LEFT JOIN evaluaciones ev ON v.evaluacion_id = ev.id
        """
        conditions = []
        params = []
        if empresa_id:
            conditions.append("v.empresa_id = %s")
            params.append(empresa_id)
        if evaluacion_id:
            conditions.append("v.evaluacion_id = %s")
            params.append(evaluacion_id)

        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        base_query += " ORDER BY v.fecha_visita DESC, v.id DESC"

        df = pd.read_sql_query(base_query, conn, params=params if params else None)
        return df
    except RuntimeError as exc:
        st.error(f"⚠️ {exc}")
        return pd.DataFrame()
    except Exception as exc:
        st.error(f"Error al listar visitas ({type(exc).__name__}).")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()
