"""
Repositorio de Importaciones Documentales — Fase 2A.2 / 2A.3 (Lince GRC).

CRUD para:
- importaciones_documentales
- importacion_tratamientos_candidatos

No almacena archivos ni textos íntegros. Solo persiste metadatos, hash, resumen técnico,
campos mapeados (máx. 4.000 caracteres por campo) y decisiones de revisión humana.

Fase 2A.3 agrega persistencia de previsualización y mapeo (JSONB) para reapertura sin archivo.
"""

import json
import math
import streamlit as st
import pandas as pd
from datetime import datetime, date

from db.connection import get_connection
from db.repositories.tratamientos import get_tratamientos_df


# ==============================================================================
# IMPORTACIONES_DOCUMENTALES
# ==============================================================================

def crear_importacion(
    empresa_id: int,
    nombre_archivo: str,
    tipo_archivo: str,
    mime_detectado: str,
    tamano_bytes: int,
    hash_sha256: str,
    evaluacion_id: int | None = None,
    evidencia_id: int | None = None,
    tiene_evidencia_url: bool = False,
    descripcion_origen: str = "",
    advertencias: str = "",
    resumen_extraccion: str = "",
) -> tuple[int | None, str]:
    """
    Registra una nueva importación documental.
    resumen_extraccion contiene exclusivamente metadatos técnicos.
    Retorna (id_importacion, mensaje).
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                INSERT INTO importaciones_documentales (
                    empresa_id, evaluacion_id, nombre_archivo, tipo_archivo,
                    mime_detectado, tamano_bytes, hash_sha256, estado,
                    evidencia_id, tiene_evidencia_url, descripcion_origen,
                    advertencias, resumen_extraccion
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, 'recibido',
                    %s, %s, %s, %s, %s
                ) RETURNING id
                """,
                (
                    empresa_id, evaluacion_id, nombre_archivo, tipo_archivo,
                    mime_detectado, tamano_bytes, hash_sha256,
                    evidencia_id, tiene_evidencia_url,
                    descripcion_origen.strip() if descripcion_origen else None,
                    advertencias.strip() if advertencias else None,
                    resumen_extraccion.strip() if resumen_extraccion else None,
                ),
            )
            new_id = c.fetchone()[0]
        conn.commit()
        get_importaciones_df.clear()
        get_importaciones_reabribles_df.clear()
        return new_id, "Importación registrada."
    except Exception as exc:
        if conn:
            conn.rollback()
        return None, f"Error al registrar importación ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


def actualizar_estado_importacion(
    importacion_id: int,
    estado: str,
    resumen_extraccion: str | None = None,
    advertencias: str | None = None,
    total_candidatos: int | None = None,
) -> bool:
    """Actualiza estado, resumen y advertencias de una importación."""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            updates = ["estado = %s", "updated_at = CURRENT_TIMESTAMP"]
            params = [estado]
            if resumen_extraccion is not None:
                updates.append("resumen_extraccion = %s")
                params.append(resumen_extraccion)
            if advertencias is not None:
                updates.append("advertencias = %s")
                params.append(advertencias)
            if total_candidatos is not None:
                updates.append("total_candidatos = %s")
                params.append(total_candidatos)
            params.append(importacion_id)
            c.execute(
                f"UPDATE importaciones_documentales SET {', '.join(updates)} WHERE id = %s",
                tuple(params),
            )
        conn.commit()
        get_importaciones_df.clear()
        get_importaciones_reabribles_df.clear()
        get_importacion_por_id.clear()
        return True
    except Exception:
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def actualizar_contadores_importacion(importacion_id: int) -> bool:
    """Recalcula y actualiza candidatos_creados e candidatos_ignorados desde la BD."""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                UPDATE importaciones_documentales SET
                    candidatos_creados  = (
                        SELECT COUNT(*) FROM importacion_tratamientos_candidatos
                        WHERE importacion_id = %s AND accion_humana IN ('crear_borrador', 'proponer_actualizacion')
                    ),
                    candidatos_ignorados = (
                        SELECT COUNT(*) FROM importacion_tratamientos_candidatos
                        WHERE importacion_id = %s AND accion_humana = 'ignorar'
                    ),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (importacion_id, importacion_id, importacion_id),
            )
        conn.commit()
        get_importaciones_df.clear()
        get_importaciones_reabribles_df.clear()
        get_importacion_por_id.clear()
        return True
    except Exception:
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


@st.cache_data(ttl=30)
def get_importaciones_df(empresa_id: int = None) -> pd.DataFrame:
    """Retorna el historial de importaciones, opcionalmente filtrado por empresa."""
    conn = None
    try:
        conn = get_connection()
        query = """
            SELECT
                imp.id,
                e.nombre                                    AS empresa,
                COALESCE(eval.nombre, '')                   AS evaluacion,
                imp.nombre_archivo,
                imp.tipo_archivo,
                ROUND(imp.tamano_bytes / 1024.0, 1)        AS tamano_kb,
                LEFT(imp.hash_sha256, 12) || '…'           AS hash_abreviado,
                imp.estado,
                CASE WHEN imp.tiene_evidencia_url THEN 'Sí' ELSE 'No' END AS evidencia_permanente,
                imp.total_candidatos,
                imp.candidatos_creados,
                imp.candidatos_ignorados,
                COALESCE(imp.advertencias, '')              AS advertencias,
                COALESCE(imp.resumen_extraccion, '')        AS resumen_extraccion,
                imp.empresa_id,
                imp.created_at
            FROM importaciones_documentales imp
            JOIN empresas e ON imp.empresa_id = e.id
            LEFT JOIN evaluaciones eval ON imp.evaluacion_id = eval.id
        """
        params = []
        if empresa_id:
            query += " WHERE imp.empresa_id = %s"
            params.append(empresa_id)
        query += " ORDER BY imp.id DESC"
        return pd.read_sql_query(query, conn, params=tuple(params) if params else None)
    except RuntimeError as exc:
        st.error(f"⚠️ {exc}")
        raise
    except Exception as exc:
        st.error(f"Error al consultar importaciones ({type(exc).__name__}).")
        raise
    finally:
        if conn:
            conn.close()


# ==============================================================================
# IMPORTACION_TRATAMIENTOS_CANDIDATOS
# ==============================================================================

def _sanitizar_json_candidato(datos: dict) -> dict:
    """Aplica límite de 4.000 caracteres a cada campo y preserva estructura limpia."""
    limpio = {}
    for k, v in datos.items():
        if k == "campos_adicionales" and isinstance(v, dict):
            limpio["campos_adicionales"] = {
                sub_k: str(sub_v)[:4000] for sub_k, sub_v in v.items() if sub_v
            }
        elif v:
            limpio[k] = str(v)[:4000]
    return limpio


def crear_candidato(
    importacion_id: int,
    empresa_id: int,
    datos_extraidos_json: dict,
    nro_hoja: str | None = None,
    nro_fila: int | None = None,
    nro_pagina: int | None = None,
    seccion_origen: str | None = None,
) -> tuple[int | None, str]:
    """
    Registra un candidato de tratamiento RAT en estado 'pendiente'.
    datos_extraidos_json es un dict con los campos mapeados (borrador no validado).
    """
    conn = None
    try:
        conn = get_connection()
        datos_limpios = _sanitizar_json_candidato(datos_extraidos_json)
        with conn.cursor() as c:
            c.execute(
                """
                INSERT INTO importacion_tratamientos_candidatos (
                    importacion_id, empresa_id,
                    nro_hoja, nro_fila, nro_pagina, seccion_origen,
                    datos_extraidos_json, estado_revision
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, 'pendiente'
                ) RETURNING id
                """,
                (
                    importacion_id, empresa_id,
                    nro_hoja, nro_fila, nro_pagina, seccion_origen,
                    json.dumps(datos_limpios, ensure_ascii=False),
                ),
            )
            new_id = c.fetchone()[0]
        conn.commit()
        get_candidatos_df.clear()
        get_importaciones_df.clear()
        get_importaciones_reabribles_df.clear()
        return new_id, "Candidato registrado."
    except Exception as exc:
        if conn:
            conn.rollback()
        return None, f"Error al registrar candidato ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


@st.cache_data(ttl=15)
def get_candidatos_df(
    empresa_id: int = None,
    importacion_id: int = None,
    estado_revision: str = None,
) -> pd.DataFrame:
    """
    Retorna candidatos RAT, opcionalmente filtrados.
    Incluye datos_extraidos_json como texto para visualización en UI interna.
    """
    conn = None
    try:
        conn = get_connection()
        query = """
            SELECT
                c.id,
                e.nombre                                            AS empresa,
                imp.nombre_archivo,
                COALESCE(c.nro_hoja, '')                           AS hoja,
                c.nro_fila,
                c.nro_pagina,
                COALESCE(c.seccion_origen, '')                     AS seccion_origen,
                c.datos_extraidos_json::text                       AS datos_json,
                c.estado_revision,
                COALESCE(c.accion_humana, '')                      AS accion_humana,
                c.tratamiento_existente_id,
                c.tratamiento_creado_id,
                COALESCE(c.observacion_revision, '')               AS observacion_revision,
                c.revisado_en,
                c.importacion_id,
                c.empresa_id,
                c.created_at
            FROM importacion_tratamientos_candidatos c
            JOIN importaciones_documentales imp ON c.importacion_id = imp.id
            JOIN empresas e ON c.empresa_id = e.id
            WHERE 1=1
        """
        params = []
        if empresa_id:
            query += " AND c.empresa_id = %s"
            params.append(empresa_id)
        if importacion_id:
            query += " AND c.importacion_id = %s"
            params.append(importacion_id)
        if estado_revision:
            query += " AND c.estado_revision = %s"
            params.append(estado_revision)
        query += " ORDER BY c.id DESC"
        return pd.read_sql_query(query, conn, params=tuple(params) if params else None)
    except RuntimeError as exc:
        st.error(f"⚠️ {exc}")
        raise
    except Exception as exc:
        st.error(f"Error al consultar candidatos RAT ({type(exc).__name__}).")
        raise
    finally:
        if conn:
            conn.close()


def aplicar_accion_candidato(
    candidato_id: int,
    accion: str,                          # 'crear_borrador' | 'proponer_actualizacion' | 'ignorar'
    empresa_id: int,
    campos_confirmados: dict | None,      # para crear nuevo tratamiento
    tratamiento_existente_id: int | None, # para conciliación
    evaluacion_id: int | None,
    observacion: str = "",
) -> tuple[bool, str]:
    """
    Aplica la decisión explícita del revisor humano sobre un candidato.

    - 'crear_borrador': INSERT en tratamientos con los campos confirmados.
      El tratamiento queda como: "Creado desde importación; pendiente de caracterización y validación en Tratamientos (RAT)".
      El candidato queda con estado_revision = 'aprobado_borrador'.
    - 'proponer_actualizacion': solo actualiza el candidato con tratamiento_existente_id.
    - 'ignorar': marca como ignorado sin tocar tratamientos.
    """
    if accion not in ("crear_borrador", "proponer_actualizacion", "ignorar"):
        return False, f"Acción desconocida: {accion}"

    conn = None
    try:
        conn = get_connection()
        tratamiento_creado_id = None

        with conn.cursor() as c:

            if accion == "crear_borrador":
                campos = campos_confirmados or {}
                c.execute(
                    """
                    INSERT INTO tratamientos (
                        empresa_id, evaluacion_id,
                        nombre_tratamiento, descripcion, base_legal,
                        datos_personales, responsables, encargados, transferencias,
                        rat_tipo_datos_sensibles, rat_ambito_territorial,
                        rat_bases_datos_administradas, rat_categorias_titulares,
                        rat_finalidades, rat_fuente_datos_acceso_publico,
                        rat_base_licitud_interes_legitimo, rat_destinatarios_cesiones,
                        rat_transferencias_internacionales_art27,
                        rat_plazo_condicion_supresion,
                        rat_decisiones_automatizadas_perfilamiento
                    ) VALUES (
                        %s, %s,
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) RETURNING id
                    """,
                    (
                        empresa_id,
                        evaluacion_id,
                        _v(campos, "nombre_tratamiento"),
                        _v(campos, "descripcion"),
                        _v(campos, "base_legal"),
                        _v(campos, "datos_personales"),
                        _v(campos, "responsables"),
                        _v(campos, "encargados"),
                        _v(campos, "transferencias"),
                        _v(campos, "rat_tipo_datos_sensibles"),
                        _v(campos, "rat_ambito_territorial"),
                        _v(campos, "rat_bases_datos_administradas"),
                        _v(campos, "rat_categorias_titulares"),
                        _v(campos, "rat_finalidades"),
                        _v(campos, "rat_fuente_datos_acceso_publico"),
                        _v(campos, "rat_base_licitud_interes_legitimo"),
                        _v(campos, "rat_destinatarios_cesiones"),
                        _v(campos, "rat_transferencias_internacionales_art27"),
                        _v(campos, "rat_plazo_condicion_supresion"),
                        _v(campos, "rat_decisiones_automatizadas_perfilamiento"),
                    ),
                )
                tratamiento_creado_id = c.fetchone()[0]
                nuevo_estado = "aprobado_borrador"

            elif accion == "proponer_actualizacion":
                nuevo_estado = "propuesto_actualizacion"

            else:  # ignorar
                nuevo_estado = "ignorado"

            c.execute(
                """
                UPDATE importacion_tratamientos_candidatos SET
                    estado_revision          = %s,
                    accion_humana            = %s,
                    tratamiento_existente_id = %s,
                    tratamiento_creado_id    = %s,
                    observacion_revision     = %s,
                    revisado_en              = CURRENT_TIMESTAMP,
                    updated_at               = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    nuevo_estado,
                    accion,
                    tratamiento_existente_id,
                    tratamiento_creado_id,
                    observacion.strip() if observacion else None,
                    candidato_id,
                ),
            )

        conn.commit()
        get_candidatos_df.clear()
        get_importaciones_df.clear()
        get_importaciones_reabribles_df.clear()
        if accion == "crear_borrador":
            get_tratamientos_df.clear()

        if accion == "crear_borrador":
            return (
                True,
                f"Tratamiento #{tratamiento_creado_id} creado desde importación; "
                "pendiente de caracterización y validación en Tratamientos (RAT).",
            )
        elif accion == "proponer_actualizacion":
            return True, "Propuesta registrada. Se actualizará solo tras confirmación explícita."
        else:
            return True, "Candidato ignorado. Permanece en el historial para trazabilidad."

    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al aplicar acción ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


def registrar_actualizacion_candidato_confirmada(
    candidato_id: int,
    tratamiento_existente_id: int,
    campos_actualizados: list[str],
    observacion_usuario: str = "",
) -> tuple[bool, str]:
    """
    Registra en importacion_tratamientos_candidatos que el usuario confirmó
    la actualización de campos específicos sobre un tratamiento existente.
    Guarda la lista de campos en la observación textual acotada (sin migración de esquema).
    """
    conn = None
    try:
        conn = get_connection()
        obs_texto = f"Campos actualizados: [{', '.join(campos_actualizados)}]."
        if observacion_usuario.strip():
            obs_texto += f" Nota: {observacion_usuario.strip()}"

        with conn.cursor() as c:
            c.execute(
                """
                UPDATE importacion_tratamientos_candidatos SET
                    estado_revision          = 'propuesto_actualizacion',
                    accion_humana            = 'proponer_actualizacion',
                    tratamiento_existente_id = %s,
                    observacion_revision     = %s,
                    revisado_en              = CURRENT_TIMESTAMP,
                    updated_at               = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (tratamiento_existente_id, obs_texto, candidato_id),
            )
        conn.commit()
        get_candidatos_df.clear()
        get_importaciones_df.clear()
        get_importaciones_reabribles_df.clear()
        get_tratamientos_df.clear()
        return True, "Trazabilidad de conciliación registrada en el candidato."
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Error al registrar trazabilidad ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


def candidato_duplicado_en_importacion(importacion_id: int, nro_hoja: str, nro_fila: int) -> bool:
    """Verifica si ya existe un candidato con el mismo origen exacto dentro de la misma importación."""
    if nro_hoja is None or nro_fila is None:
        return False
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                SELECT 1 FROM importacion_tratamientos_candidatos
                WHERE importacion_id = %s AND nro_hoja = %s AND nro_fila = %s
                LIMIT 1
                """,
                (importacion_id, nro_hoja, nro_fila),
            )
            return c.fetchone() is not None
    except Exception:
        return False
    finally:
        if conn:
            conn.close()


def _v(campos: dict, clave: str) -> str | None:
    """Extrae, limita y limpia un valor del dict de campos, o retorna None si está vacío."""
    val = campos.get(clave, "")
    if isinstance(val, str) and val.strip():
        return val.strip()[:4000]
    return None


# ==============================================================================
# FASE 2A.3: PERSISTENCIA DE REAPERTURA
# Guardar y recuperar previsualización, encabezados y mapeo sin archivo binario
# ==============================================================================

def _sanitizar_valor(v) -> str:
    """Convierte cualquier valor no serializable a string vacío o string limpio."""
    if v is None:
        return ""
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return ""
    if isinstance(v, (datetime, date)):
        return str(v)
    try:
        # Detecta pd.NA, pd.NaT y similares sin importar pandas aquí
        if str(type(v)) in ("<class 'pandas._libs.missing.NAType'>",
                            "<class 'pandas._libs.tslibs.nattype.NaTType'>"):
            return ""
    except Exception:
        pass
    try:
        s = str(v).strip()
        return s
    except Exception:
        return ""


def _sanitizar_matriz(filas: list[list]) -> list[list]:
    """
    Convierte todos los valores de la matriz a strings seguros para JSONB.
    NaN, None, pd.NA, fechas y objetos no serializables se convierten a ''.
    """
    return [[_sanitizar_valor(celda) for celda in fila] for fila in filas]


def _sanitizar_encabezados(encabezados: list) -> list[str]:
    """Convierte encabezados a strings seguros para JSONB."""
    return [_sanitizar_valor(e) if _sanitizar_valor(e) else "Sin encabezado" for e in encabezados]


def _sanitizar_mapeo(mapeo: dict) -> dict:
    """
    Convierte el mapeo de columnas a dict serializable con claves de columna (str)
    y como valor el identificador interno canónico ('nombre_tratamiento', 'rat_tipo_datos_sensibles', etc.)
    o '(No mapear)'. Si recibe una etiqueta decorada con ' — ', extrae solo el identificador canónico.
    """
    resultado = {}
    for k, v in mapeo.items():
        clave_str = str(k)
        if v is None or v == "(No mapear)" or v == "":
            resultado[clave_str] = "(No mapear)"
        else:
            val_str = str(v).strip()
            if " — " in val_str:
                val_str = val_str.split(" — ")[0].strip()
            resultado[clave_str] = val_str
    return resultado


def guardar_importacion_completa(
    empresa_id: int,
    nombre_archivo: str,
    tipo_archivo: str,
    hash_sha256: str,
    tamano_bytes: int,
    tabla_origen: str,
    encabezados: list,
    filas_datos: list[list],
    mapeo_columnas: dict,
    total_filas_origen: int,
    total_filas_utiles: int,
    evaluacion_id: int | None = None,
    descripcion_origen: str = "",
    resumen_extraccion: str = "",
    advertencias: str = "",
    importacion_id_existente: int | None = None,
) -> tuple[int | None, str]:
    """
    Persiste o actualiza la estructura completa de una importación RAT.

    - Si importacion_id_existente es válido y pertenece a la empresa, ejecuta UPDATE.
    - Si ya existe un registro con (empresa_id, hash_sha256), ejecuta UPDATE sobre ese ID.
    - Si no existe, ejecuta INSERT.
    - Sanitiza encabezados, filas y mapeo antes de serializar a JSONB.
    - Retorna (importacion_id, mensaje).
    """
    conn = None
    try:
        enc_limpio = _sanitizar_encabezados(encabezados)
        filas_limpias = _sanitizar_matriz(filas_datos)
        mapeo_limpio = _sanitizar_mapeo(mapeo_columnas)
        tabla_limpia = (tabla_origen or "").strip()[:255]

        conn = get_connection()
        with conn.cursor() as c:
            # Resolver ID de importación a actualizar
            imp_id = None

            if importacion_id_existente:
                c.execute(
                    "SELECT id FROM importaciones_documentales WHERE id = %s AND empresa_id = %s",
                    (importacion_id_existente, empresa_id),
                )
                row = c.fetchone()
                if row:
                    imp_id = row[0]

            if imp_id is None:
                c.execute(
                    "SELECT id FROM importaciones_documentales WHERE empresa_id = %s AND hash_sha256 = %s ORDER BY id DESC LIMIT 1",
                    (empresa_id, hash_sha256),
                )
                row = c.fetchone()
                if row:
                    imp_id = row[0]

            if imp_id is not None:
                c.execute(
                    """
                    UPDATE importaciones_documentales SET
                        tabla_origen          = %s,
                        encabezados_json      = %s,
                        datos_extraidos_json  = %s,
                        mapeo_columnas_json   = %s,
                        total_filas_origen    = %s,
                        total_filas_utiles    = %s,
                        descripcion_origen    = COALESCE(NULLIF(%s, ''), descripcion_origen),
                        resumen_extraccion    = COALESCE(NULLIF(%s, ''), resumen_extraccion),
                        advertencias          = COALESCE(NULLIF(%s, ''), advertencias),
                        updated_at            = CURRENT_TIMESTAMP
                    WHERE id = %s AND empresa_id = %s
                    """,
                    (
                        tabla_limpia,
                        json.dumps(enc_limpio, ensure_ascii=False),
                        json.dumps(filas_limpias, ensure_ascii=False),
                        json.dumps(mapeo_limpio, ensure_ascii=False),
                        total_filas_origen,
                        total_filas_utiles,
                        descripcion_origen.strip() if descripcion_origen else "",
                        resumen_extraccion.strip() if resumen_extraccion else "",
                        advertencias.strip() if advertencias else "",
                        imp_id,
                        empresa_id,
                    ),
                )
                conn.commit()
                get_importaciones_df.clear()
                get_importaciones_reabribles_df.clear()
                get_importacion_por_id.clear()
                return imp_id, f"Importación #{imp_id} actualizada con previsualización y mapeo."

            else:
                c.execute(
                    """
                    INSERT INTO importaciones_documentales (
                        empresa_id, evaluacion_id, nombre_archivo, tipo_archivo,
                        mime_detectado, tamano_bytes, hash_sha256, estado,
                        descripcion_origen, advertencias, resumen_extraccion,
                        tabla_origen, encabezados_json, datos_extraidos_json,
                        mapeo_columnas_json, total_filas_origen, total_filas_utiles
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, 'recibido',
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) RETURNING id
                    """,
                    (
                        empresa_id,
                        evaluacion_id,
                        nombre_archivo,
                        tipo_archivo,
                        tipo_archivo,
                        tamano_bytes,
                        hash_sha256,
                        descripcion_origen.strip() if descripcion_origen else None,
                        advertencias.strip() if advertencias else None,
                        resumen_extraccion.strip() if resumen_extraccion else None,
                        tabla_limpia,
                        json.dumps(enc_limpio, ensure_ascii=False),
                        json.dumps(filas_limpias, ensure_ascii=False),
                        json.dumps(mapeo_limpio, ensure_ascii=False),
                        total_filas_origen,
                        total_filas_utiles,
                    ),
                )
                new_id = c.fetchone()[0]
                conn.commit()
                get_importaciones_df.clear()
                get_importaciones_reabribles_df.clear()
                get_importacion_por_id.clear()
                return new_id, f"Importación #{new_id} guardada con previsualización y mapeo."

    except Exception as exc:
        if conn:
            conn.rollback()
        return None, f"Error al guardar importación ({type(exc).__name__}): {exc}"
    finally:
        if conn:
            conn.close()


@st.cache_data(ttl=30)
def get_importacion_por_id(importacion_id: int, empresa_id: int) -> dict | None:
    """
    Recupera una importación completa (incluyendo JSONB de Fase 2A.3) validando
    que pertenezca estrictamente a la empresa_id indicada.
    Si el ID no existe o pertenece a otra empresa, retorna None sin exponer datos.
    Los campos JSONB se decodifican a estructuras Python nativas.
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                SELECT
                    id,
                    empresa_id,
                    nombre_archivo,
                    tipo_archivo,
                    tamano_bytes,
                    hash_sha256,
                    estado,
                    descripcion_origen,
                    resumen_extraccion,
                    advertencias,
                    tabla_origen,
                    encabezados_json,
                    datos_extraidos_json,
                    mapeo_columnas_json,
                    total_filas_origen,
                    total_filas_utiles,
                    total_candidatos,
                    candidatos_creados,
                    candidatos_ignorados,
                    created_at,
                    updated_at
                FROM importaciones_documentales
                WHERE id = %s AND empresa_id = %s
                """,
                (importacion_id, empresa_id),
            )
            row = c.fetchone()
            if row is None:
                return None

            (
                r_id, r_empresa_id, r_nombre, r_tipo, r_tamano, r_hash,
                r_estado, r_desc, r_resumen, r_adv,
                r_tabla, r_enc_raw, r_datos_raw, r_mapeo_raw,
                r_total_origen, r_total_utiles,
                r_total_cand, r_cand_creados, r_cand_ign,
                r_created, r_updated,
            ) = row

            def _parse_json(raw):
                if raw is None:
                    return None
                if isinstance(raw, (list, dict)):
                    return raw
                try:
                    return json.loads(raw)
                except Exception:
                    return None

            return {
                "id": r_id,
                "empresa_id": r_empresa_id,
                "nombre_archivo": r_nombre,
                "tipo_archivo": r_tipo,
                "tamano_bytes": r_tamano,
                "hash_sha256": r_hash,
                "estado": r_estado,
                "descripcion_origen": r_desc or "",
                "resumen_extraccion": r_resumen or "",
                "advertencias": r_adv or "",
                "tabla_origen": r_tabla or "",
                "encabezados": _parse_json(r_enc_raw) or [],
                "filas_datos": _parse_json(r_datos_raw) or [],
                "mapeo_columnas": _parse_json(r_mapeo_raw) or {},
                "total_filas_origen": r_total_origen or 0,
                "total_filas_utiles": r_total_utiles or 0,
                "total_candidatos": r_total_cand or 0,
                "candidatos_creados": r_cand_creados or 0,
                "candidatos_ignorados": r_cand_ign or 0,
                "created_at": r_created,
                "updated_at": r_updated,
            }
    except RuntimeError as exc:
        st.error(f"⚠️ {exc}")
        raise
    except Exception as exc:
        st.error(f"Error al recuperar importación #{importacion_id} ({type(exc).__name__}).")
        raise
    finally:
        if conn:
            conn.close()


@st.cache_data(ttl=30)
def get_importaciones_reabribles_df(empresa_id: int) -> pd.DataFrame:
    """
    Retorna las importaciones de la empresa que tienen datos de reapertura
    (encabezados y datos_extraidos_json no nulos), ordenadas por más recientes primero.
    Solo expone campos seguros para el selector de interfaz — nunca datos de otra empresa.
    """
    conn = None
    try:
        conn = get_connection()
        query = """
            SELECT
                id,
                nombre_archivo,
                tipo_archivo,
                estado,
                tabla_origen,
                total_filas_origen,
                total_filas_utiles,
                total_candidatos,
                created_at,
                updated_at
            FROM importaciones_documentales
            WHERE empresa_id = %s
              AND encabezados_json IS NOT NULL
              AND datos_extraidos_json IS NOT NULL
            ORDER BY id DESC
        """
        return pd.read_sql_query(query, conn, params=(empresa_id,))
    except RuntimeError as exc:
        st.error(f"⚠️ {exc}")
        raise
    except Exception as exc:
        st.error(f"Error al listar importaciones guardadas ({type(exc).__name__}).")
        raise
    finally:
        if conn:
            conn.close()
