"""
Repositorio de Tratamientos — Registro de Actividades de Tratamiento (RAT).
Fase 2A: soporte completo para los 11 numerales normativos del Art. 3 letra d)
del Decreto N° 662 y campos complementarios GRC.
"""

import streamlit as st
import pandas as pd

from db.connection import get_connection


def add_tratamiento(
    empresa_id: int,
    evaluacion_id: int | None,
    nombre_tratamiento: str,
    descripcion: str,
    base_legal: str,
    datos_personales: str,
    responsables: str,
    encargados: str,
    transferencias: str,
    # 11 Numerales Normativos (Art. 3 d)
    rat_tipo_datos_sensibles: str = "",
    rat_ambito_territorial: str = "",
    rat_bases_datos_administradas: str = "",
    rat_categorias_titulares: str = "",
    rat_finalidades: str = "",
    rat_fuente_datos_acceso_publico: str = "",
    rat_base_licitud_interes_legitimo: str = "",
    rat_destinatarios_cesiones: str = "",
    rat_transferencias_internacionales_art27: str = "",
    rat_plazo_condicion_supresion: str = "",
    rat_decisiones_automatizadas_perfilamiento: str = "",
    evidencia_id: int | None = None,
) -> tuple[bool, str]:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                INSERT INTO tratamientos (
                    empresa_id, evaluacion_id, nombre_tratamiento, descripcion,
                    base_legal, datos_personales, responsables, encargados, transferencias,
                    rat_tipo_datos_sensibles, rat_ambito_territorial, rat_bases_datos_administradas,
                    rat_categorias_titulares, rat_finalidades, rat_fuente_datos_acceso_publico,
                    rat_base_licitud_interes_legitimo, rat_destinatarios_cesiones,
                    rat_transferencias_internacionales_art27, rat_plazo_condicion_supresion,
                    rat_decisiones_automatizadas_perfilamiento, evidencia_id
                ) VALUES (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                )
                """,
                (
                    empresa_id,
                    evaluacion_id,
                    nombre_tratamiento.strip(),
                    descripcion.strip() if descripcion else None,
                    base_legal.strip() if base_legal else None,
                    datos_personales.strip() if datos_personales else None,
                    responsables.strip() if responsables else None,
                    encargados.strip() if encargados else None,
                    transferencias.strip() if transferencias else None,
                    rat_tipo_datos_sensibles.strip() if rat_tipo_datos_sensibles else None,
                    rat_ambito_territorial.strip() if rat_ambito_territorial else None,
                    rat_bases_datos_administradas.strip() if rat_bases_datos_administradas else None,
                    rat_categorias_titulares.strip() if rat_categorias_titulares else None,
                    rat_finalidades.strip() if rat_finalidades else None,
                    rat_fuente_datos_acceso_publico.strip() if rat_fuente_datos_acceso_publico else None,
                    rat_base_licitud_interes_legitimo.strip() if rat_base_licitud_interes_legitimo else None,
                    rat_destinatarios_cesiones.strip() if rat_destinatarios_cesiones else None,
                    rat_transferencias_internacionales_art27.strip() if rat_transferencias_internacionales_art27 else None,
                    rat_plazo_condicion_supresion.strip() if rat_plazo_condicion_supresion else None,
                    rat_decisiones_automatizadas_perfilamiento.strip() if rat_decisiones_automatizadas_perfilamiento else None,
                    evidencia_id,
                ),
            )
        conn.commit()
        get_tratamientos_df.clear()
        return True, "Tratamiento (RAT) registrado exitosamente."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al guardar tratamiento ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


def update_tratamiento(
    tratamiento_id: int,
    empresa_id: int,
    evaluacion_id: int | None,
    nombre_tratamiento: str,
    descripcion: str,
    base_legal: str,
    datos_personales: str,
    responsables: str,
    encargados: str,
    transferencias: str,
    rat_tipo_datos_sensibles: str = "",
    rat_ambito_territorial: str = "",
    rat_bases_datos_administradas: str = "",
    rat_categorias_titulares: str = "",
    rat_finalidades: str = "",
    rat_fuente_datos_acceso_publico: str = "",
    rat_base_licitud_interes_legitimo: str = "",
    rat_destinatarios_cesiones: str = "",
    rat_transferencias_internacionales_art27: str = "",
    rat_plazo_condicion_supresion: str = "",
    rat_decisiones_automatizadas_perfilamiento: str = "",
    evidencia_id: int | None = None,
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
                    responsables=%s, encargados=%s, transferencias=%s,
                    rat_tipo_datos_sensibles=%s, rat_ambito_territorial=%s,
                    rat_bases_datos_administradas=%s, rat_categorias_titulares=%s,
                    rat_finalidades=%s, rat_fuente_datos_acceso_publico=%s,
                    rat_base_licitud_interes_legitimo=%s, rat_destinatarios_cesiones=%s,
                    rat_transferencias_internacionales_art27=%s, rat_plazo_condicion_supresion=%s,
                    rat_decisiones_automatizadas_perfilamiento=%s, evidencia_id=%s
                WHERE id=%s
                """,
                (
                    empresa_id,
                    evaluacion_id,
                    nombre_tratamiento.strip(),
                    descripcion.strip() if descripcion else None,
                    base_legal.strip() if base_legal else None,
                    datos_personales.strip() if datos_personales else None,
                    responsables.strip() if responsables else None,
                    encargados.strip() if encargados else None,
                    transferencias.strip() if transferencias else None,
                    rat_tipo_datos_sensibles.strip() if rat_tipo_datos_sensibles else None,
                    rat_ambito_territorial.strip() if rat_ambito_territorial else None,
                    rat_bases_datos_administradas.strip() if rat_bases_datos_administradas else None,
                    rat_categorias_titulares.strip() if rat_categorias_titulares else None,
                    rat_finalidades.strip() if rat_finalidades else None,
                    rat_fuente_datos_acceso_publico.strip() if rat_fuente_datos_acceso_publico else None,
                    rat_base_licitud_interes_legitimo.strip() if rat_base_licitud_interes_legitimo else None,
                    rat_destinatarios_cesiones.strip() if rat_destinatarios_cesiones else None,
                    rat_transferencias_internacionales_art27.strip() if rat_transferencias_internacionales_art27 else None,
                    rat_plazo_condicion_supresion.strip() if rat_plazo_condicion_supresion else None,
                    rat_decisiones_automatizadas_perfilamiento.strip() if rat_decisiones_automatizadas_perfilamiento else None,
                    evidencia_id,
                    tratamiento_id,
                ),
            )
        conn.commit()
        get_tratamientos_df.clear()
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
        get_tratamientos_df.clear()
        return True, "Tratamiento eliminado exitosamente."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al eliminar tratamiento ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


@st.cache_data(ttl=30)
def get_tratamientos_df(empresa_id: int = None, evaluacion_id: int = None) -> pd.DataFrame:
    conn = None
    try:
        conn = get_connection()
        query = """
            SELECT
                t.id,
                e.nombre                                        AS empresa,
                COALESCE(e.rut, '')                             AS rut_empresa,
                COALESCE(t.nombre_tratamiento, 'Sin nombre')    AS nombre_tratamiento,
                COALESCE(t.descripcion, '')                     AS descripcion,
                COALESCE(t.base_legal, '')                      AS base_legal,
                COALESCE(t.datos_personales, '')                AS datos_personales,
                COALESCE(t.responsables, '')                    AS responsables,
                COALESCE(t.encargados, '')                      AS encargados,
                COALESCE(t.transferencias, '')                  AS transferencias,
                COALESCE(t.rat_tipo_datos_sensibles, '')        AS rat_tipo_datos_sensibles,
                COALESCE(t.rat_ambito_territorial, '')          AS rat_ambito_territorial,
                COALESCE(t.rat_bases_datos_administradas, '')  AS rat_bases_datos_administradas,
                COALESCE(t.rat_categorias_titulares, '')        AS rat_categorias_titulares,
                COALESCE(t.rat_finalidades, '')                 AS rat_finalidades,
                COALESCE(t.rat_fuente_datos_acceso_publico, '') AS rat_fuente_datos_acceso_publico,
                COALESCE(t.rat_base_licitud_interes_legitimo, '') AS rat_base_licitud_interes_legitimo,
                COALESCE(t.rat_destinatarios_cesiones, '')      AS rat_destinatarios_cesiones,
                COALESCE(t.rat_transferencias_internacionales_art27, '') AS rat_transferencias_internacionales_art27,
                COALESCE(t.rat_plazo_condicion_supresion, '')   AS rat_plazo_condicion_supresion,
                COALESCE(t.rat_decisiones_automatizadas_perfilamiento, '') AS rat_decisiones_automatizadas_perfilamiento,
                t.evidencia_id,
                COALESCE(ev.descripcion, '')                    AS evidencia_descripcion,
                COALESCE(ev.foto_url, '')                       AS evidencia_url,
                COALESCE(eval.nombre, '')                       AS evaluacion_nombre,
                t.empresa_id,
                t.evaluacion_id,
                t.created_at
            FROM tratamientos t
            JOIN empresas e ON t.empresa_id = e.id
            LEFT JOIN evaluaciones eval ON t.evaluacion_id = eval.id
            LEFT JOIN evidencias ev ON t.evidencia_id = ev.id
            WHERE 1=1
        """
        params = []
        if empresa_id:
            query += " AND t.empresa_id = %s"
            params.append(empresa_id)
        if evaluacion_id:
            query += " AND t.evaluacion_id = %s"
            params.append(evaluacion_id)

        query += " ORDER BY t.id DESC"
        df = pd.read_sql_query(query, conn, params=tuple(params) if params else None)
        return df
    except RuntimeError as exc:
        st.error(f"⚠️ {exc}")
        raise
    except Exception as exc:
        st.error(f"Error al consultar tratamientos ({type(exc).__name__}).")
        raise
    finally:
        if conn:
            conn.close()
