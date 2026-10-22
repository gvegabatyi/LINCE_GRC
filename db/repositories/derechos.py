"""
Repositorio de Solicitudes de Derechos de los Titulares.

Toda escritura filtra por id Y empresa_id: una solicitud no puede modificarse
desde el contexto de otra empresa. Los plazos se calculan en
services/plazos_service.py según el régimen de la fecha de ingreso.
"""

from datetime import date

import pandas as pd
import streamlit as st

from db.connection import get_connection
from services import plazos_service as plazos


def _ejecutar(sql: str, params: tuple, mensaje_ok: str, contexto: str) -> tuple[bool, str]:
    """Ejecuta una escritura acotada a una solicitud de la empresa e invalida la caché."""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(sql, params)
            if c.rowcount == 0:
                conn.rollback()
                return False, "La solicitud no existe o no pertenece a la empresa seleccionada."
        conn.commit()
        get_solicitudes_df.clear()
        return True, mensaje_ok
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al {contexto} ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


# ==============================================================================
# ESCRITURA (retornan tuple[bool, str])
# ==============================================================================

def crear_solicitud(
    empresa_id: int,
    derecho: str,
    fecha_ingreso: date,
    titular_nombre: str,
    canal: str = "",
    titular_contacto: str = "",
    representante: str = "",
    identidad_verificada: bool = False,
    metodo_verificacion: str = "",
    descripcion: str = "",
    bloqueo_solicitado: bool = False,
    tratamiento_id: int | None = None,
) -> tuple[bool, str]:
    regimen = plazos.regimen_aplicable(fecha_ingreso)
    vencimiento = plazos.calcular_vencimiento(fecha_ingreso)
    bloqueo_venc = plazos.calcular_vencimiento_bloqueo(fecha_ingreso) if bloqueo_solicitado else None
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                INSERT INTO solicitudes_derechos (
                    empresa_id, tratamiento_id, derecho, canal, fecha_ingreso, regimen,
                    titular_nombre, titular_contacto, representante, identidad_verificada,
                    metodo_verificacion, descripcion, bloqueo_solicitado, bloqueo_vencimiento,
                    fecha_vencimiento
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    empresa_id, tratamiento_id, derecho, canal or None, fecha_ingreso, regimen,
                    titular_nombre.strip(), (titular_contacto or "").strip() or None,
                    (representante or "").strip() or None, identidad_verificada,
                    (metodo_verificacion or "").strip() or None, (descripcion or "").strip() or None,
                    bloqueo_solicitado, bloqueo_venc, vencimiento,
                ),
            )
            nuevo_id = c.fetchone()[0]
            folio = f"SD-{fecha_ingreso.year}-{nuevo_id:05d}"
            c.execute("UPDATE solicitudes_derechos SET folio=%s WHERE id=%s", (folio, nuevo_id))
        conn.commit()
        get_solicitudes_df.clear()
        return True, f"Solicitud {folio} registrada. Vence el {vencimiento:%d-%m-%Y}."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al registrar la solicitud ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


def registrar_acuse(solicitud_id: int, empresa_id: int, fecha_acuse: date) -> tuple[bool, str]:
    return _ejecutar(
        "UPDATE solicitudes_derechos SET fecha_acuse=%s, "
        "estado=CASE WHEN estado='recibida' THEN 'en_analisis' ELSE estado END, "
        "updated_at=CURRENT_TIMESTAMP WHERE id=%s AND empresa_id=%s",
        (fecha_acuse, solicitud_id, empresa_id),
        "Acuse de recibo registrado.", "registrar el acuse",
    )


def prorrogar_solicitud(solicitud_id: int, empresa_id: int, fecha_ingreso: date,
                        motivo: str) -> tuple[bool, str]:
    """Prórroga única (sólo régimen Ley 21.719)."""
    if not plazos.admite_prorroga(plazos.regimen_aplicable(fecha_ingreso)):
        return False, "La Ley 19.628 vigente no contempla prórroga del plazo de respuesta."
    if not (motivo or "").strip():
        return False, "Debe indicar el motivo de la prórroga."
    nuevo_venc = plazos.calcular_vencimiento(fecha_ingreso, prorrogada=True)
    return _ejecutar(
        "UPDATE solicitudes_derechos SET prorrogada=TRUE, prorroga_motivo=%s, fecha_vencimiento=%s, "
        "updated_at=CURRENT_TIMESTAMP WHERE id=%s AND empresa_id=%s AND prorrogada=FALSE",
        (motivo.strip(), nuevo_venc, solicitud_id, empresa_id),
        f"Plazo prorrogado hasta el {nuevo_venc:%d-%m-%Y}.", "prorrogar la solicitud",
    )


def resolver_bloqueo(solicitud_id: int, empresa_id: int, resultado: str,
                     fecha: date) -> tuple[bool, str]:
    return _ejecutar(
        "UPDATE solicitudes_derechos SET bloqueo_resultado=%s, bloqueo_resuelto_en=%s, "
        "updated_at=CURRENT_TIMESTAMP WHERE id=%s AND empresa_id=%s AND bloqueo_solicitado=TRUE",
        (resultado, fecha, solicitud_id, empresa_id),
        "Resolución del bloqueo temporal registrada.", "registrar el bloqueo",
    )


def registrar_respuesta(
    solicitud_id: int,
    empresa_id: int,
    estado: str,
    fecha_respuesta: date,
    medio_respuesta: str,
    fundamento: str = "",
    evidencia_id: int | None = None,
) -> tuple[bool, str]:
    """Respuesta al titular. La denegación (total o parcial) exige fundamento (Ley 21.719 art. 11)."""
    if estado not in ("acogida", "acogida_parcial", "denegada", "cerrada"):
        return False, "Estado de respuesta no válido."
    if estado in ("denegada", "acogida_parcial") and not (fundamento or "").strip():
        return False, "La denegación total o parcial debe ser fundada: indique la causa y los antecedentes."
    return _ejecutar(
        "UPDATE solicitudes_derechos SET estado=%s, fecha_respuesta=%s, medio_respuesta=%s, "
        "fundamento_respuesta=%s, evidencia_respuesta_id=%s, updated_at=CURRENT_TIMESTAMP "
        "WHERE id=%s AND empresa_id=%s",
        (estado, fecha_respuesta, medio_respuesta or None, (fundamento or "").strip() or None,
         evidencia_id, solicitud_id, empresa_id),
        "Respuesta registrada.", "registrar la respuesta",
    )


# ==============================================================================
# LECTURA
# ==============================================================================

@st.cache_data(ttl=30)
def get_solicitudes_df(empresa_id: int | None = None) -> pd.DataFrame:
    """Solicitudes de una empresa (o de todas, sólo para dashboard y exportación)."""
    conn = None
    try:
        conn = get_connection()
        query = """
            SELECT
                s.id, s.folio, s.empresa_id, e.nombre AS empresa,
                s.derecho, COALESCE(s.canal, '') AS canal, s.fecha_ingreso, s.regimen,
                s.titular_nombre, COALESCE(s.titular_contacto, '') AS titular_contacto,
                COALESCE(s.representante, '') AS representante,
                s.identidad_verificada, COALESCE(s.metodo_verificacion, '') AS metodo_verificacion,
                COALESCE(s.descripcion, '') AS descripcion,
                s.tratamiento_id, COALESCE(t.nombre_tratamiento, '') AS tratamiento,
                s.bloqueo_solicitado, s.bloqueo_vencimiento, s.bloqueo_resuelto_en,
                COALESCE(s.bloqueo_resultado, '') AS bloqueo_resultado,
                s.fecha_vencimiento, s.prorrogada, COALESCE(s.prorroga_motivo, '') AS prorroga_motivo,
                s.estado, s.fecha_acuse, s.fecha_respuesta,
                COALESCE(s.medio_respuesta, '') AS medio_respuesta,
                COALESCE(s.fundamento_respuesta, '') AS fundamento_respuesta,
                s.evidencia_respuesta_id, s.created_at
            FROM solicitudes_derechos s
            JOIN empresas e ON s.empresa_id = e.id
            LEFT JOIN tratamientos t ON s.tratamiento_id = t.id
        """
        params = None
        if empresa_id:
            query += " WHERE s.empresa_id = %s"
            params = (empresa_id,)
        query += " ORDER BY s.fecha_vencimiento ASC, s.id DESC"
        return pd.read_sql_query(query, conn, params=params)
    except RuntimeError as exc:
        st.error(f"⚠️ {exc}")
        return pd.DataFrame()
    except Exception as exc:
        st.error(f"Error al consultar solicitudes de derechos ({type(exc).__name__}).")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def resumen_plazos(df: pd.DataFrame, hoy: date | None = None) -> dict:
    """Conteo por estado de plazo (en_plazo, por_vencer, vencida, respondida)."""
    resumen = {"en_plazo": 0, "por_vencer": 0, "vencida": 0, "respondida": 0}
    if df is None or df.empty:
        return resumen
    for _, r in df.iterrows():
        ep = plazos.estado_plazo(r["estado"], pd.to_datetime(r["fecha_vencimiento"]).date(), r["regimen"], hoy)
        resumen[ep.codigo] += 1
    return resumen
