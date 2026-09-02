"""
Repositorio de Importaciones Documentales — Fase 2A.2 (Lince GRC).

CRUD para:
- importaciones_documentales
- importacion_tratamientos_candidatos

No almacena archivos ni textos íntegros. Solo persiste metadatos, hash, resumen técnico,
campos mapeados (máx. 4.000 caracteres por campo) y decisiones de revisión humana.
"""

import json
import streamlit as st
import pandas as pd
from datetime import datetime

from db.connection import get_connection


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
        return True
    except Exception:
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


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
    except Exception:
        return pd.DataFrame()
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
        return new_id, "Candidato registrado."
    except Exception as exc:
        if conn:
            conn.rollback()
        return None, f"Error al registrar candidato ({type(exc).__name__})."
    finally:
        if conn:
            conn.close()


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
    except Exception:
        return pd.DataFrame()
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
