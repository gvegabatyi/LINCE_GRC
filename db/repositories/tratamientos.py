"""
Repositorio de Tratamientos (ROPA).
Funciones CRUD para la tabla 'tratamientos'.
Fase 1: lectura/escritura incluye la columna evaluacion_id (nullable).
"""

import streamlit as st
import pandas as pd
import psycopg2

from db.connection import get_connection


# ==============================================================================
# ESCRITURA
# ==============================================================================

def add_tratamiento(
    empresa_id: int,
    evaluacion_id,
    nombre: str,
    descripcion: str,
    base_legal: str,
    datos_personales: str,
    responsables: str,
    encargados: str,
    transferencias: str,
) -> tuple[bool, str]:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                INSERT INTO tratamientos (
                    empresa_id, evaluacion_id, nombre_tratamiento, descripcion,
                    base_legal, datos_personales, responsables, encargados, transferencias
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    empresa_id,
                    evaluacion_id or None,
                    nombre.strip(),
                    descripcion.strip() if descripcion else None,
                    base_legal,
                    datos_personales.strip() if datos_personales else None,
                    responsables.strip() if responsables else None,
                    encargados.strip() if encargados else None,
                    transferencias,
                ),
            )
        conn.commit()
        return True, "Tratamiento (ROPA) registrado exitosamente."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al registrar tratamiento ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


def update_tratamiento(
    tratamiento_id: int,
    empresa_id: int,
    evaluacion_id,
    nombre: str,
    descripcion: str,
    base_legal: str,
    datos_personales: str,
    responsables: str,
    encargados: str,
    transferencias: str,
) -> tuple[bool, str]:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                UPDATE tratamientos SET
                    empresa_id=%s, evaluacion_id=%s, nombre_tratamiento=%s,
                    descripcion=%s, base_legal=%s, datos_personales=%s,
                    responsables=%s, encargados=%s, transferencias=%s
                WHERE id=%s
                """,
                (
                    empresa_id,
                    evaluacion_id or None,
                    nombre.strip(),
                    descripcion.strip() if descripcion else None,
                    base_legal,
                    datos_personales.strip() if datos_personales else None,
                    responsables.strip() if responsables else None,
                    encargados.strip() if encargados else None,
                    transferencias,
                    tratamiento_id,
                ),
            )
        conn.commit()
        return True, "Tratamiento actualizado exitosamente."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al actualizar tratamiento ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


def delete_tratamiento(tratamiento_id: int) -> tuple[bool, str]:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute("DELETE FROM tratamientos WHERE id=%s", (tratamiento_id,))
        conn.commit()
        return True, "Tratamiento eliminado exitosamente."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al eliminar tratamiento ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


# ==============================================================================
# LECTURA
# ==============================================================================

def get_tratamientos_df(empresa_id: int = None, evaluacion_id: int = None) -> pd.DataFrame:
    conn = None
    try:
        conn = get_connection()
        base_query = """
            SELECT
                t.id,
                COALESCE(e.nombre, 'Sin Empresa Asignada')       AS empresa,
                COALESCE(e.rut, '')                              AS rut_empresa,
                COALESCE(t.nombre_tratamiento, 'Sin nombre')     AS nombre_tratamiento,
                COALESCE(t.descripcion, '')                      AS descripcion,
                COALESCE(t.base_legal, '')                       AS base_legal,
                COALESCE(t.datos_personales, '')                 AS datos_personales,
                COALESCE(t.responsables, '')                     AS responsables,
                COALESCE(t.encargados, '')                       AS encargados,
                COALESCE(t.transferencias, '')                   AS transferencias,
                t.empresa_id,
                t.evaluacion_id,
                COALESCE(ev.nombre, '')                          AS evaluacion_nombre,
                t.created_at
            FROM tratamientos t
            LEFT JOIN empresas e  ON t.empresa_id    = e.id
            LEFT JOIN evaluaciones ev ON t.evaluacion_id = ev.id
        """
        conditions = []
        params = []
        if empresa_id:
            conditions.append("t.empresa_id = %s")
            params.append(empresa_id)
        if evaluacion_id:
            conditions.append("t.evaluacion_id = %s")
            params.append(evaluacion_id)

        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        base_query += " ORDER BY t.id DESC"

        df = pd.read_sql_query(base_query, conn, params=params if params else None)
        return df
    except RuntimeError as exc:
        st.error(f"⚠️ {exc}")
        return pd.DataFrame()
    except Exception as exc:
        st.error(f"Error al listar tratamientos ({type(exc).__name__}).")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()
