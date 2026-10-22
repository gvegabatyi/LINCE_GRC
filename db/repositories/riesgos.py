"""
Repositorio de Análisis de Riesgos: registro de riesgos y evaluaciones de impacto (EIPD).

Toda escritura filtra por id Y empresa_id. Las propuestas del diagnóstico se
registran en lote (una lectura de claves existentes + inserciones en una sola
transacción), sin consultas por fila.
"""

from datetime import date

import pandas as pd
import streamlit as st

from db.connection import get_connection


def _ejecutar(sql: str, params: tuple, mensaje_ok: str, contexto: str, cache) -> tuple[bool, str]:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(sql, params)
            if c.rowcount == 0:
                conn.rollback()
                return False, "El registro no existe o no pertenece a la empresa seleccionada."
        conn.commit()
        cache.clear()
        return True, mensaje_ok
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al {contexto} ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


# ==============================================================================
# RIESGOS
# ==============================================================================

def registrar_propuestos(empresa_id: int, propuestos: list) -> tuple[bool, str]:
    """Registra riesgos propuestos por el diagnóstico (omite los ya registrados)."""
    if not propuestos:
        return False, "No hay riesgos seleccionados."
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                "SELECT codigo_regla, COALESCE(tratamiento_id, 0) FROM riesgos "
                "WHERE empresa_id = %s AND codigo_regla IS NOT NULL",
                (empresa_id,),
            )
            existentes = {(r[0], r[1]) for r in c.fetchall()}
            nuevos = [p for p in propuestos if p.clave not in existentes]
            for p in nuevos:
                c.execute(
                    """
                    INSERT INTO riesgos (empresa_id, tratamiento_id, origen, codigo_regla, titulo,
                        descripcion, categoria, infraccion_ref, gravedad_legal, probabilidad, impacto)
                    VALUES (%s, %s, 'diagnostico', %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (empresa_id, p.tratamiento_id, p.codigo_regla, p.titulo[:255], p.descripcion,
                     p.categoria, p.infraccion, p.gravedad, p.probabilidad, p.impacto),
                )
        conn.commit()
        get_riesgos_df.clear()
        omitidos = len(propuestos) - len(nuevos)
        msg = f"{len(nuevos)} riesgo(s) incorporados al registro."
        if omitidos:
            msg += f" {omitidos} ya estaban registrados."
        return True, msg
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al registrar los riesgos ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


def crear_riesgo(empresa_id: int, titulo: str, probabilidad: int, impacto: int, descripcion: str = "",
                 categoria: str = "", infraccion_ref: str = "", gravedad_legal: str = "",
                 tratamiento_id: int | None = None, eipd_id: int | None = None) -> tuple[bool, str]:
    if not (titulo or "").strip():
        return False, "El título del riesgo es obligatorio."
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                INSERT INTO riesgos (empresa_id, tratamiento_id, eipd_id, origen, titulo, descripcion,
                    categoria, infraccion_ref, gravedad_legal, probabilidad, impacto)
                VALUES (%s, %s, %s, 'manual', %s, %s, %s, %s, %s, %s, %s)
                """,
                (empresa_id, tratamiento_id, eipd_id, titulo.strip()[:255], (descripcion or "").strip() or None,
                 categoria or None, infraccion_ref or None, gravedad_legal or None, probabilidad, impacto),
            )
        conn.commit()
        get_riesgos_df.clear()
        return True, "Riesgo registrado."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al registrar el riesgo ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


def actualizar_riesgo(riesgo_id: int, empresa_id: int, probabilidad: int, impacto: int,
                      controles: str, probabilidad_residual: int | None, impacto_residual: int | None,
                      respuesta: str, plan_accion: str, responsable: str, plazo: date | None,
                      estado: str, evidencia_id: int | None, eipd_id: int | None = None) -> tuple[bool, str]:
    return _ejecutar(
        """
        UPDATE riesgos SET probabilidad=%s, impacto=%s, controles=%s, probabilidad_residual=%s,
            impacto_residual=%s, respuesta=%s, plan_accion=%s, responsable=%s, plazo=%s, estado=%s,
            evidencia_id=%s, eipd_id=%s, updated_at=CURRENT_TIMESTAMP
        WHERE id=%s AND empresa_id=%s
        """,
        (probabilidad, impacto, (controles or "").strip() or None, probabilidad_residual, impacto_residual,
         respuesta or None, (plan_accion or "").strip() or None, (responsable or "").strip() or None,
         plazo, estado, evidencia_id, eipd_id, riesgo_id, empresa_id),
        "Evaluación del riesgo actualizada.", "actualizar el riesgo", get_riesgos_df,
    )


@st.cache_data(ttl=30)
def get_riesgos_df(empresa_id: int | None = None) -> pd.DataFrame:
    conn = None
    try:
        conn = get_connection()
        query = """
            SELECT r.*, e.nombre AS empresa, COALESCE(t.nombre_tratamiento, '') AS tratamiento
            FROM riesgos r
            JOIN empresas e ON r.empresa_id = e.id
            LEFT JOIN tratamientos t ON r.tratamiento_id = t.id
        """
        params = None
        if empresa_id:
            query += " WHERE r.empresa_id = %s"
            params = (empresa_id,)
        query += " ORDER BY (r.probabilidad * r.impacto) DESC, r.id"
        return pd.read_sql_query(query, conn, params=params)
    except RuntimeError as exc:
        st.error(f"{exc}")
        return pd.DataFrame()
    except Exception as exc:
        st.error(f"Error al consultar riesgos ({type(exc).__name__}).")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


# ==============================================================================
# EIPD (Ley 21.719 art. 15 ter)
# ==============================================================================

def guardar_eipd(empresa_id: int, tratamiento_id: int | None, disparadores: set,
                 descripcion_operaciones: str, finalidad: str, necesidad_proporcionalidad: str,
                 medidas_mitigacion: str, conclusion: str, consulta_agencia: bool, estado: str,
                 responsable: str, evidencia_id: int | None, eipd_id: int | None = None) -> tuple[bool, str]:
    """Crea (eipd_id None) o actualiza una EIPD de la empresa."""
    campos_minimos = [descripcion_operaciones, finalidad, necesidad_proporcionalidad, medidas_mitigacion]
    if estado == "aprobada" and not all((c or "").strip() for c in campos_minimos):
        return False, ("Para aprobar la EIPD deben completarse los contenidos mínimos del art. 15 ter: "
                       "descripción, finalidad, necesidad y proporcionalidad, y medidas de mitigación.")
    valores = (
        tratamiento_id, "a" in disparadores, "b" in disparadores, "c" in disparadores, "d" in disparadores,
        (descripcion_operaciones or "").strip() or None, (finalidad or "").strip() or None,
        (necesidad_proporcionalidad or "").strip() or None, (medidas_mitigacion or "").strip() or None,
        conclusion or None, consulta_agencia, estado, (responsable or "").strip() or None, evidencia_id,
    )
    if eipd_id:
        return _ejecutar(
            """
            UPDATE eipd SET tratamiento_id=%s, disparador_a=%s, disparador_b=%s, disparador_c=%s,
                disparador_d=%s, descripcion_operaciones=%s, finalidad=%s, necesidad_proporcionalidad=%s,
                medidas_mitigacion=%s, conclusion=%s, consulta_agencia=%s, estado=%s, responsable=%s,
                evidencia_id=%s, updated_at=CURRENT_TIMESTAMP
            WHERE id=%s AND empresa_id=%s
            """,
            valores + (eipd_id, empresa_id), "EIPD actualizada.", "actualizar la EIPD", get_eipd_df,
        )
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                INSERT INTO eipd (empresa_id, tratamiento_id, disparador_a, disparador_b, disparador_c,
                    disparador_d, descripcion_operaciones, finalidad, necesidad_proporcionalidad,
                    medidas_mitigacion, conclusion, consulta_agencia, estado, responsable, evidencia_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (empresa_id,) + valores,
            )
        conn.commit()
        get_eipd_df.clear()
        return True, "EIPD registrada."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al registrar la EIPD ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


@st.cache_data(ttl=30)
def get_eipd_df(empresa_id: int | None = None) -> pd.DataFrame:
    conn = None
    try:
        conn = get_connection()
        query = """
            SELECT x.*, e.nombre AS empresa, COALESCE(t.nombre_tratamiento, '') AS tratamiento
            FROM eipd x
            JOIN empresas e ON x.empresa_id = e.id
            LEFT JOIN tratamientos t ON x.tratamiento_id = t.id
        """
        params = None
        if empresa_id:
            query += " WHERE x.empresa_id = %s"
            params = (empresa_id,)
        query += " ORDER BY x.id DESC"
        return pd.read_sql_query(query, conn, params=params)
    except RuntimeError as exc:
        st.error(f"{exc}")
        return pd.DataFrame()
    except Exception as exc:
        st.error(f"Error al consultar evaluaciones de impacto ({type(exc).__name__}).")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()
