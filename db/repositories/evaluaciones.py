"""
Repositorio de Evaluaciones GRC.
Funciones CRUD para la tabla 'evaluaciones' (creada en Fase 1).
Una evaluación es el contenedor GRC principal: empresa → evaluación → todo lo demás.
"""

import streamlit as st
import pandas as pd
from datetime import date

from db.connection import get_connection


# ==============================================================================
# ESCRITURA
# ==============================================================================

def add_evaluacion(
    empresa_id: int,
    nombre: str,
    tipo_evaluacion: str,
    periodo: str,
    alcance: str,
    objetivo: str,
    marco_normativo: str,
    auditor_responsable: str,
    fecha_inicio,
    fecha_cierre_planificada,
    estado: str,
    observaciones: str,
) -> tuple[bool, str]:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                INSERT INTO evaluaciones (
                    empresa_id, nombre, tipo_evaluacion, periodo,
                    alcance, objetivo, marco_normativo, auditor_responsable,
                    fecha_inicio, fecha_cierre_planificada, estado, observaciones
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    empresa_id,
                    nombre.strip(),
                    tipo_evaluacion or None,
                    periodo.strip() if periodo else None,
                    alcance.strip() if alcance else None,
                    objetivo.strip() if objetivo else None,
                    marco_normativo.strip() if marco_normativo else None,
                    auditor_responsable.strip() if auditor_responsable else None,
                    fecha_inicio or date.today(),
                    fecha_cierre_planificada or None,
                    estado or "borrador",
                    observaciones.strip() if observaciones else None,
                ),
            )
        conn.commit()
        return True, "Evaluación GRC registrada exitosamente."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al guardar evaluación ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


def update_evaluacion(
    evaluacion_id: int,
    empresa_id: int,
    nombre: str,
    tipo_evaluacion: str,
    periodo: str,
    alcance: str,
    objetivo: str,
    marco_normativo: str,
    auditor_responsable: str,
    fecha_inicio,
    fecha_cierre_planificada,
    fecha_cierre_real,
    estado: str,
    porcentaje_avance: float,
    puntaje_total,
    max_puntaje,
    observaciones: str,
) -> tuple[bool, str]:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                UPDATE evaluaciones SET
                    empresa_id=%s, nombre=%s, tipo_evaluacion=%s, periodo=%s,
                    alcance=%s, objetivo=%s, marco_normativo=%s, auditor_responsable=%s,
                    fecha_inicio=%s, fecha_cierre_planificada=%s, fecha_cierre_real=%s,
                    estado=%s, porcentaje_avance=%s, puntaje_total=%s, max_puntaje=%s,
                    observaciones=%s, updated_at=CURRENT_TIMESTAMP
                WHERE id=%s
                """,
                (
                    empresa_id,
                    nombre.strip(),
                    tipo_evaluacion or None,
                    periodo.strip() if periodo else None,
                    alcance.strip() if alcance else None,
                    objetivo.strip() if objetivo else None,
                    marco_normativo.strip() if marco_normativo else None,
                    auditor_responsable.strip() if auditor_responsable else None,
                    fecha_inicio or None,
                    fecha_cierre_planificada or None,
                    fecha_cierre_real or None,
                    estado or "borrador",
                    porcentaje_avance if porcentaje_avance is not None else 0,
                    puntaje_total if puntaje_total is not None else None,
                    max_puntaje if max_puntaje is not None else None,
                    observaciones.strip() if observaciones else None,
                    evaluacion_id,
                ),
            )
        conn.commit()
        return True, "Evaluación actualizada exitosamente."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al actualizar evaluación ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


def delete_evaluacion(evaluacion_id: int) -> tuple[bool, str]:
    """
    Elimina una evaluación.
    Las visitas, tratamientos y evidencias asociadas NO se eliminan:
    su evaluacion_id queda en NULL (ON DELETE SET NULL).
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute("DELETE FROM evaluaciones WHERE id=%s", (evaluacion_id,))
        conn.commit()
        return True, (
            "Evaluación eliminada. Las visitas, tratamientos y evidencias "
            "asociadas conservan sus datos con evaluación en blanco."
        )
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al eliminar evaluación ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


# ==============================================================================
# LECTURA
# ==============================================================================

def get_evaluaciones_df(empresa_id: int = None) -> pd.DataFrame:
    conn = None
    try:
        conn = get_connection()
        base_query = """
            SELECT
                ev.id,
                emp.nombre                             AS empresa,
                COALESCE(emp.rut, '')                  AS rut_empresa,
                ev.nombre                              AS nombre,
                COALESCE(ev.tipo_evaluacion, '')       AS tipo_evaluacion,
                COALESCE(ev.periodo, '')               AS periodo,
                COALESCE(ev.estado, 'borrador')        AS estado,
                COALESCE(ev.auditor_responsable, '')   AS auditor_responsable,
                ev.fecha_inicio,
                ev.fecha_cierre_planificada,
                ev.fecha_cierre_real,
                COALESCE(ev.porcentaje_avance, 0)      AS porcentaje_avance,
                ev.puntaje_total,
                ev.max_puntaje,
                COALESCE(ev.alcance, '')               AS alcance,
                COALESCE(ev.objetivo, '')              AS objetivo,
                COALESCE(ev.marco_normativo, '')       AS marco_normativo,
                COALESCE(ev.observaciones, '')         AS observaciones,
                ev.empresa_id,
                ev.created_at,
                ev.updated_at
            FROM evaluaciones ev
            JOIN empresas emp ON ev.empresa_id = emp.id
        """
        if empresa_id:
            query = base_query + " WHERE ev.empresa_id = %s ORDER BY ev.id DESC"
            df = pd.read_sql_query(query, conn, params=(empresa_id,))
        else:
            query = base_query + " ORDER BY ev.id DESC"
            df = pd.read_sql_query(query, conn)
        return df
    except RuntimeError as exc:
        st.error(f"⚠️ {exc}")
        return pd.DataFrame()
    except Exception as exc:
        st.error(f"Error al listar evaluaciones ({type(exc).__name__}).")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def get_evaluacion_by_id(evaluacion_id: int) -> dict | None:
    """Retorna una evaluación como dict, o None si no existe."""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                SELECT ev.*, emp.nombre AS empresa_nombre
                FROM evaluaciones ev
                JOIN empresas emp ON ev.empresa_id = emp.id
                WHERE ev.id = %s
                """,
                (evaluacion_id,),
            )
            row = c.fetchone()
            if not row:
                return None
            cols = [desc[0] for desc in c.description]
            return dict(zip(cols, row))
    except Exception:
        return None
    finally:
        if conn:
            conn.close()


def contar_elementos_evaluacion(evaluacion_id: int) -> dict:
    """
    Retorna conteos de visitas y tratamientos vinculados a una evaluación.
    Usado en el módulo de detalle para mostrar registros asociados.
    """
    conn = None
    resultado = {"visitas": 0, "tratamientos": 0, "evidencias": 0}
    try:
        conn = get_connection()
        with conn.cursor() as c:
            for tabla, clave in resultado.items():
                c.execute(
                    f"SELECT COUNT(*) FROM {tabla} WHERE evaluacion_id = %s",
                    (evaluacion_id,),
                )
                resultado[tabla] = c.fetchone()[0]
        return resultado
    except Exception:
        return resultado
    finally:
        if conn:
            conn.close()
