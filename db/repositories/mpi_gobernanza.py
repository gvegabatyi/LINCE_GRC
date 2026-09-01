"""
Repositorio de Gobernanza MPI y Delegado de Protección de Datos (Fase 2A).
Gestiona las operaciones CRUD para mpi_perfiles, mpi_delegados y referencias normativas.
"""

import streamlit as st
import pandas as pd
from datetime import date

from db.connection import get_connection


# ==============================================================================
# PERFIL MPI
# ==============================================================================

def get_perfil_activo(empresa_id: int) -> dict | None:
    """Retorna el perfil MPI activo para una empresa o None si no existe."""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                SELECT p.*, e.nombre AS empresa_nombre, e.rut AS empresa_rut,
                       ev.descripcion AS evidencia_descripcion, ev.foto_url AS evidencia_url
                FROM mpi_perfiles p
                JOIN empresas e ON p.empresa_id = e.id
                LEFT JOIN evidencias ev ON p.evidencia_aprobacion_id = ev.id
                WHERE p.empresa_id = %s AND p.activo = TRUE
                LIMIT 1
                """,
                (empresa_id,),
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


def get_perfiles_df(empresa_id: int = None) -> pd.DataFrame:
    """Retorna listado de perfiles MPI (activos e históricos)."""
    conn = None
    try:
        conn = get_connection()
        base_query = """
            SELECT
                p.id,
                e.nombre AS empresa,
                e.rut AS rut_empresa,
                p.representante_legal_nombre,
                p.representante_legal_rut,
                p.representante_legal_email,
                p.fecha_adopcion_modelo,
                p.version_modelo,
                p.estado_implementacion,
                p.estado_certificacion_oficial,
                p.entidad_certificadora,
                p.nro_certificado,
                p.fecha_certificacion,
                p.fecha_vencimiento_certificacion,
                p.nro_registro_agencia,
                p.activo,
                p.empresa_id,
                p.created_at
            FROM mpi_perfiles p
            JOIN empresas e ON p.empresa_id = e.id
        """
        if empresa_id:
            query = base_query + " WHERE p.empresa_id = %s ORDER BY p.id DESC"
            df = pd.read_sql_query(query, conn, params=(empresa_id,))
        else:
            query = base_query + " ORDER BY p.id DESC"
            df = pd.read_sql_query(query, conn)
        return df
    except Exception:
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def save_perfil_mpi(
    empresa_id: int,
    representante_legal_nombre: str,
    representante_legal_rut: str,
    representante_legal_email: str,
    representante_legal_telefono: str,
    fecha_adopcion_modelo,
    version_modelo: str,
    alcance_organizacional: str,
    estado_implementacion: str,
    estado_certificacion_oficial: str,
    entidad_certificadora: str,
    nro_certificado: str,
    fecha_certificacion,
    fecha_vencimiento_certificacion,
    nro_registro_agencia: str,
    evidencia_aprobacion_id: int | None,
    perfil_id: int | None = None,
) -> tuple[bool, str]:
    """Crea o actualiza el perfil MPI de una empresa asegurando que solo haya 1 activo."""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            # Desactivar perfiles anteriores de la empresa si es nuevo o se reactiva
            if not perfil_id:
                c.execute("UPDATE mpi_perfiles SET activo = FALSE WHERE empresa_id = %s", (empresa_id,))

                c.execute(
                    """
                    INSERT INTO mpi_perfiles (
                        empresa_id, representante_legal_nombre, representante_legal_rut,
                        representante_legal_email, representante_legal_telefono,
                        fecha_adopcion_modelo, version_modelo, alcance_organizacional,
                        estado_implementacion, estado_certificacion_oficial,
                        entidad_certificadora, nro_certificado, fecha_certificacion,
                        fecha_vencimiento_certificacion, nro_registro_agencia,
                        evidencia_aprobacion_id, activo
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,TRUE)
                    """,
                    (
                        empresa_id,
                        representante_legal_nombre.strip(),
                        representante_legal_rut.strip(),
                        representante_legal_email.strip() if representante_legal_email else None,
                        representante_legal_telefono.strip() if representante_legal_telefono else None,
                        fecha_adopcion_modelo or date.today(),
                        version_modelo.strip() if version_modelo else "1.0",
                        alcance_organizacional.strip() if alcance_organizacional else None,
                        estado_implementacion or "preparacion",
                        estado_certificacion_oficial or "sin_solicitud",
                        entidad_certificadora.strip() if entidad_certificadora else None,
                        nro_certificado.strip() if nro_certificado else None,
                        fecha_certificacion or None,
                        fecha_vencimiento_certificacion or None,
                        nro_registro_agencia.strip() if nro_registro_agencia else None,
                        evidencia_aprobacion_id,
                    ),
                )
            else:
                c.execute(
                    """
                    UPDATE mpi_perfiles SET
                        representante_legal_nombre = %s,
                        representante_legal_rut = %s,
                        representante_legal_email = %s,
                        representante_legal_telefono = %s,
                        fecha_adopcion_modelo = %s,
                        version_modelo = %s,
                        alcance_organizacional = %s,
                        estado_implementacion = %s,
                        estado_certificacion_oficial = %s,
                        entidad_certificadora = %s,
                        nro_certificado = %s,
                        fecha_certificacion = %s,
                        fecha_vencimiento_certificacion = %s,
                        nro_registro_agencia = %s,
                        evidencia_aprobacion_id = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (
                        representante_legal_nombre.strip(),
                        representante_legal_rut.strip(),
                        representante_legal_email.strip() if representante_legal_email else None,
                        representante_legal_telefono.strip() if representante_legal_telefono else None,
                        fecha_adopcion_modelo or None,
                        version_modelo.strip() if version_modelo else "1.0",
                        alcance_organizacional.strip() if alcance_organizacional else None,
                        estado_implementacion or "preparacion",
                        estado_certificacion_oficial or "sin_solicitud",
                        entidad_certificadora.strip() if entidad_certificadora else None,
                        nro_certificado.strip() if nro_certificado else None,
                        fecha_certificacion or None,
                        fecha_vencimiento_certificacion or None,
                        nro_registro_agencia.strip() if nro_registro_agencia else None,
                        evidencia_aprobacion_id,
                        perfil_id,
                    ),
                )
        conn.commit()
        return True, "Perfil MPI guardado exitosamente."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al guardar Perfil MPI ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


# ==============================================================================
# DELEGADO DE PROTECCIÓN DE DATOS (DPD)
# ==============================================================================

def get_delegado_activo(empresa_id: int) -> dict | None:
    """Retorna el delegado DPD activo de una empresa o None si no existe."""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                SELECT d.*, e.nombre AS empresa_nombre,
                       ev.descripcion AS evidencia_descripcion, ev.foto_url AS evidencia_url
                FROM mpi_delegados d
                JOIN empresas e ON d.empresa_id = e.id
                LEFT JOIN evidencias ev ON d.evidencia_designacion_id = ev.id
                WHERE d.empresa_id = %s AND d.activo = TRUE
                LIMIT 1
                """,
                (empresa_id,),
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


def get_delegados_df(empresa_id: int = None) -> pd.DataFrame:
    """Retorna listado de delegados (activos e históricos)."""
    conn = None
    try:
        conn = get_connection()
        base_query = """
            SELECT
                d.id,
                e.nombre AS empresa,
                d.nombre_completo,
                d.email_contacto_publico,
                d.telefono_contacto,
                d.tipo_vinculo,
                d.persona_juridica_prestadora,
                d.cargo_interno,
                d.autoridad_designacion,
                d.fecha_designacion,
                d.declaracion_autonomia,
                d.activo,
                d.empresa_id,
                d.created_at
            FROM mpi_delegados d
            JOIN empresas e ON d.empresa_id = e.id
        """
        if empresa_id:
            query = base_query + " WHERE d.empresa_id = %s ORDER BY d.id DESC"
            df = pd.read_sql_query(query, conn, params=(empresa_id,))
        else:
            query = base_query + " ORDER BY d.id DESC"
            df = pd.read_sql_query(query, conn)
        return df
    except Exception:
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def save_delegado_dpd(
    empresa_id: int,
    nombre_completo: str,
    email_contacto_publico: str,
    rut_interno: str,
    telefono_contacto: str,
    canal_atencion_detalles: str,
    tipo_vinculo: str,
    persona_juridica_prestadora: str,
    cargo_interno: str,
    autoridad_designacion: str,
    fecha_designacion,
    declaracion_autonomia: bool,
    declaracion_idoneidad: str,
    recursos_materiales_facultades: str,
    evidencia_designacion_id: int | None,
    delegado_id: int | None = None,
) -> tuple[bool, str]:
    """Registra o actualiza el delegado DPD garantizando un solo delegado activo."""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            if not delegado_id:
                # Desactivar delegados anteriores de la empresa
                c.execute("UPDATE mpi_delegados SET activo = FALSE WHERE empresa_id = %s", (empresa_id,))

                c.execute(
                    """
                    INSERT INTO mpi_delegados (
                        empresa_id, nombre_completo, rut_interno, email_contacto_publico,
                        telefono_contacto, canal_atencion_detalles, tipo_vinculo,
                        persona_juridica_prestadora, cargo_interno, autoridad_designacion,
                        fecha_designacion, declaracion_autonomia, declaracion_idoneidad,
                        recursos_materiales_facultades, evidencia_designacion_id, activo
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,TRUE)
                    """,
                    (
                        empresa_id,
                        nombre_completo.strip(),
                        rut_interno.strip() if rut_interno else None,
                        email_contacto_publico.strip(),
                        telefono_contacto.strip() if telefono_contacto else None,
                        canal_atencion_detalles.strip() if canal_atencion_detalles else None,
                        tipo_vinculo or "dependiente",
                        persona_juridica_prestadora.strip() if persona_juridica_prestadora else None,
                        cargo_interno.strip() if cargo_interno else None,
                        autoridad_designacion.strip() if autoridad_designacion else "Directorio",
                        fecha_designacion or date.today(),
                        bool(declaracion_autonomia),
                        declaracion_idoneidad.strip() if declaracion_idoneidad else None,
                        recursos_materiales_facultades.strip() if recursos_materiales_facultades else None,
                        evidencia_designacion_id,
                    ),
                )
            else:
                c.execute(
                    """
                    UPDATE mpi_delegados SET
                        nombre_completo = %s,
                        rut_interno = %s,
                        email_contacto_publico = %s,
                        telefono_contacto = %s,
                        canal_atencion_detalles = %s,
                        tipo_vinculo = %s,
                        persona_juridica_prestadora = %s,
                        cargo_interno = %s,
                        autoridad_designacion = %s,
                        fecha_designacion = %s,
                        declaracion_autonomia = %s,
                        declaracion_idoneidad = %s,
                        recursos_materiales_facultades = %s,
                        evidencia_designacion_id = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (
                        nombre_completo.strip(),
                        rut_interno.strip() if rut_interno else None,
                        email_contacto_publico.strip(),
                        telefono_contacto.strip() if telefono_contacto else None,
                        canal_atencion_detalles.strip() if canal_atencion_detalles else None,
                        tipo_vinculo or "dependiente",
                        persona_juridica_prestadora.strip() if persona_juridica_prestadora else None,
                        cargo_interno.strip() if cargo_interno else None,
                        autoridad_designacion.strip() if autoridad_designacion else "Directorio",
                        fecha_designacion or None,
                        bool(declaracion_autonomia),
                        declaracion_idoneidad.strip() if declaracion_idoneidad else None,
                        recursos_materiales_facultades.strip() if recursos_materiales_facultades else None,
                        evidencia_designacion_id,
                        delegado_id,
                    ),
                )
        conn.commit()
        return True, "Delegado de Protección de Datos guardado exitosamente."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al guardar Delegado DPD ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


# ==============================================================================
# TRAZABILIDAD NORMATIVA (DECRETO N° 662)
# ==============================================================================

def get_referencias_normativas_df() -> pd.DataFrame:
    """Retorna el catálogo de artículos y criterios del Decreto N° 662."""
    conn = None
    try:
        conn = get_connection()
        query = """
            SELECT
                r.id,
                f.codigo AS codigo_fuente,
                f.nombre AS nombre_fuente,
                r.articulo,
                r.numeral_letra,
                r.materia,
                r.descripcion_criterio
            FROM normativa_referencias r
            JOIN normativa_fuentes f ON r.fuente_id = f.id
            ORDER BY r.id ASC
        """
        return pd.read_sql_query(query, conn)
    except Exception:
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()
