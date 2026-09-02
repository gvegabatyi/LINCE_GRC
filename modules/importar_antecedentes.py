"""
Módulo Importar Antecedentes RAT — Fase 2A.2 (Lince GRC).
Bandeja documental para cargar, extraer y conciliar antecedentes históricos del RAT.

PRINCIPIO FUNDAMENTAL:
- Todo dato extraído es un BORRADOR NO VALIDADO.
- No se crea ni modifica un tratamiento de forma automática.
- La revisión humana es obligatoria antes de cada acción.
- La importación no afecta la completitud documental MPI hasta validación manual.
- Las actualizaciones a tratamientos existentes requieren comparación campo a campo
  y confirmación humana explícita campo por campo.
- Previsualización completa: las tablas interactivas reciben todas las filas detectadas
  con desplazamiento vertical y horizontal (soporta ampliación en pantalla completa sin recortes).

Normativa de referencia:
- Decreto N° 662, Art. 3 letra d), numerales i a xi (estructura del RAT).
- Decreto N° 662, Art. 3 letra e) (contexto de actividades y procesos).
"""

import json
import streamlit as st
import pandas as pd

from db.repositories.empresas import get_empresas_df
from db.repositories.evaluaciones import get_evaluaciones_df
from db.repositories.evidencias import get_evidencias_df
from db.repositories.tratamientos import get_tratamientos_df, update_tratamiento
from db.repositories.importaciones import (
    crear_importacion,
    crear_candidato,
    get_importaciones_df,
    get_candidatos_df,
    aplicar_accion_candidato,
    registrar_actualizacion_candidato_confirmada,
    actualizar_estado_importacion,
    actualizar_contadores_importacion,
    candidato_duplicado_en_importacion,
)
from services.deduplicacion_service import (
    calcular_hash_sha256,
    validar_archivo,
    detectar_duplicado_empresa,
    detectar_candidato_similar_en_tratamientos,
    EXTENSIONES_PERMITIDAS,
    MENSAJE_FORMATO_NO_SOPORTADO,
)
from services.extraccion_service import (
    CAMPOS_RAT_DECRETO,
    CAMPOS_RAT_CLAVES,
    CAMPOS_RAT_ETIQUETAS,
    MAX_CANDIDATOS_POR_VISTA,
    MAX_CARACTERES_CAMPO,
    NOMBRE_TRATAMIENTO_DEFECTO,
    extraer_xlsx_hojas,
    extraer_xlsx_encabezados_preview,
    generar_candidatos_xlsx,
    extraer_csv_encabezados_preview,
    generar_candidatos_csv,
    extraer_docx_estructura,
    generar_candidatos_docx_tabla,
    extraer_pdf_paginas,
    crear_candidato_manual_pdf,
    extraer_texto_plano,
    crear_candidato_manual_texto,
    resumen_extraccion,
)

LIMITE_SESION_ARCHIVOS = 5
LIMITE_SESION_BYTES = 30 * 1024 * 1024  # 30 MB


# ==============================================================================
# RENDER PRINCIPAL
# ==============================================================================

def render() -> None:
    st.header("📥 Importar Antecedentes RAT")
    st.caption(
        "Bandeja documental para importar antecedentes históricos útiles para el levantamiento del "
        "RAT *(Decreto N° 662, Art. 3 letra d)*. "
        "Los datos extraídos son borradores no validados y requieren revisión humana obligatoria."
    )

    st.info(
        "⚠️ **Los datos extraídos de documentos son borradores no validados.** "
        "No acreditan cumplimiento y no modifican automáticamente tratamientos existentes. "
        "Un candidato importado no cuenta para la completitud documental MPI hasta que "
        "el usuario lo revise, complete y valide en el módulo 📋 Tratamientos.",
        icon="🛡️",
    )

    tab_nueva, tab_revisar, tab_historial = st.tabs([
        "📤 Nueva Importación",
        "🔍 Revisar y Conciliar Candidatos",
        "📋 Historial de Importaciones",
    ])

    with tab_nueva:
        _tab_nueva_importacion()

    with tab_revisar:
        _tab_revisar_candidatos()

    with tab_historial:
        _tab_historial()


# ==============================================================================
# TAB 1: NUEVA IMPORTACIÓN
# ==============================================================================

def _tab_nueva_importacion() -> None:
    # ── PASO 1: Contexto ──────────────────────────────────────────────────────
    st.subheader("Paso 1 — Seleccionar contexto")
    df_emp = get_empresas_df()
    if df_emp.empty:
        st.warning("No hay empresas registradas. Regístrelas primero en 📁 Empresas.")
        return

    col1, col2 = st.columns(2)
    with col1:
        opciones_emp = {r["nombre"]: r["id"] for _, r in df_emp.iterrows()}
        empresa_nombre = st.selectbox("Empresa *", list(opciones_emp.keys()), key="imp_empresa")
        empresa_id = opciones_emp[empresa_nombre]

    with col2:
        df_eval = get_evaluaciones_df(empresa_id=empresa_id)
        opciones_eval = {"(Sin evaluación asociada)": None}
        if not df_eval.empty:
            for _, r in df_eval.iterrows():
                opciones_eval[f"{r['nombre']} ({r.get('periodo','')})"] = r["id"]
        eval_nombre = st.selectbox("Evaluación GRC (opcional)", list(opciones_eval.keys()), key="imp_eval")
        evaluacion_id = opciones_eval[eval_nombre]

    descripcion_origen = st.text_area(
        "Descripción del origen documental",
        placeholder="Ej: RAT histórico 2023 elaborado por área de cumplimiento.",
        max_chars=500,
        key="imp_desc_origen",
        help="Describe brevemente el origen y propósito del archivo que vas a importar.",
    )

    st.markdown("---")

    # ── AVISO OBLIGATORIO DE PRIVACIDAD Y LEGITIMIDAD ──────────────────────────
    st.warning(
        "🔒 **Aviso de Privacidad y Legitimidad:**\n\n"
        "Antes de cargar un antecedente, confirme que cuenta con autorización y finalidad legítima "
        "para tratar los datos contenidos en el documento. No cargue credenciales, secretos, "
        "datos sensibles innecesarios ni documentos cuyo contenido no deba procesarse en esta plataforma.",
        icon="🔐",
    )

    # ── PASO 2: Subida del archivo ────────────────────────────────────────────
    st.subheader("Paso 2 — Cargar archivo de antecedentes")
    st.markdown(
        f"**Formatos aceptados:** XLSX, CSV, DOCX, PDF (con texto), MD, TXT · "
        f"**Límite:** 10 MB por archivo · **Máximo por sesión:** {LIMITE_SESION_ARCHIVOS} archivos / 30 MB acumulado."
    )

    archivo = st.file_uploader(
        "Seleccionar archivo",
        type=list(EXTENSIONES_PERMITIDAS),
        key="imp_archivo",
    )

    if archivo is None:
        st.caption("Aguardando archivo…")
        return

    contenido = archivo.read()

    # Control de sesión: contador acumulado
    bytes_sesion = st.session_state.get("imp_bytes_sesion", 0)
    archivos_sesion = st.session_state.get("imp_archivos_sesion", 0)

    if archivos_sesion >= LIMITE_SESION_ARCHIVOS:
        st.error(f"⛔ Límite de sesión alcanzado: máximo {LIMITE_SESION_ARCHIVOS} archivos por sesión.")
        return

    if bytes_sesion + len(contenido) > LIMITE_SESION_BYTES:
        st.error(
            f"⛔ Límite de sesión acumulado alcanzado (30 MB). "
            f"Usado: {bytes_sesion / 1024 / 1024:.2f} MB. "
            f"Este archivo: {len(contenido) / 1024 / 1024:.2f} MB."
        )
        return

    # ── PASO 3: Validación y resumen del archivo ──────────────────────────────
    st.subheader("Paso 3 — Validación de formato y seguridad")

    es_valido, errores, advertencias_formato, tipo_detectado = validar_archivo(archivo.name, contenido)

    if not es_valido:
        for err in errores:
            st.error(f"⛔ {err}")
        st.stop()

    for adv in advertencias_formato:
        st.warning(f"⚠️ {adv}")

    hash_archivo = calcular_hash_sha256(contenido)
    tamano_kb = len(contenido) / 1024

    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.metric("Tipo confirmado", tipo_detectado.upper())
    col_r2.metric("Tamaño", f"{tamano_kb:.1f} KB")
    col_r3.metric("Hash SHA-256 (abreviado)", hash_archivo[:12] + "…")

    dup = detectar_duplicado_empresa(empresa_id, hash_archivo)
    advertencias_list = list(advertencias_formato)
    if dup:
        msg_dup = (
            f"⚠️ **Importación previa detectada:** Este archivo ya fue registrado el "
            f"{str(dup['created_at'])[:10]} (Importación #{dup['id']} — {dup['nombre_archivo']}, "
            f"estado: {dup['estado']}). Al guardar, el sistema completará automáticamente "
            "los candidatos faltantes sin duplicar los ya existentes."
        )
        st.warning(msg_dup)
        advertencias_list.append(f"Importación previa #{dup['id']} ({dup['nombre_archivo']})")

    st.success(f"✅ Archivo '{archivo.name}' validado correctamente en memoria.")
    st.markdown("---")

    # ── CONTROL OPT-IN DE PRIVACIDAD: CAMPOS NO MAPEADOS ───────────────────────
    st.subheader("Configuración de Privacidad para Extracción")
    conservar_adicionales = st.checkbox(
        "Conservar campos adicionales no mapeados como borrador de revisión",
        value=False,
        key=f"opt_adicionales_{hash_archivo}",
        help="Desactivado por defecto por principio de minimización de datos. Si se activa, las columnas que no mapee a campos RAT se guardarán como borrador adicional (máx. 4.000 caracteres por campo).",
    )
    if not conservar_adicionales:
        st.caption("🔒 **Minimización activa:** Solo se guardarán los campos que mapee explícitamente a la normativa RAT.")

    st.markdown("---")

    # ── PASO 4 y 5: Mapeo y extracción de candidatos ──────────────────────────
    st.subheader("Paso 4 — Mapeo y extracción de candidatos")

    candidatos_generados = st.session_state.get(f"imp_candidatos_{hash_archivo}", [])
    columnas_detectadas_archivo = st.session_state.get(f"imp_cols_{hash_archivo}", [])
    campos_rat_mapeados = st.session_state.get(f"imp_campos_{hash_archivo}", [])
    truncados_contador = st.session_state.get(f"imp_truncados_{hash_archivo}", 0)
    filas_utiles_totales = st.session_state.get(f"imp_filas_utiles_{hash_archivo}", len(candidatos_generados))

    if tipo_detectado == "xlsx":
        candidatos_generados, columnas_detectadas_archivo, campos_rat_mapeados, truncados_contador, filas_utiles_totales = _flujo_xlsx(
            contenido, hash_archivo, candidatos_generados, conservar_adicionales
        )
    elif tipo_detectado == "csv":
        candidatos_generados, columnas_detectadas_archivo, campos_rat_mapeados, truncados_contador, filas_utiles_totales = _flujo_csv(
            contenido, hash_archivo, candidatos_generados, conservar_adicionales
        )
    elif tipo_detectado == "docx":
        candidatos_generados, columnas_detectadas_archivo, campos_rat_mapeados, truncados_contador, filas_utiles_totales = _flujo_docx(
            contenido, hash_archivo, candidatos_generados, conservar_adicionales
        )
    elif tipo_detectado == "pdf":
        candidatos_generados, columnas_detectadas_archivo, campos_rat_mapeados, truncados_contador, filas_utiles_totales = _flujo_pdf(
            contenido, hash_archivo, candidatos_generados, empresa_id
        )
    elif tipo_detectado in ("md", "txt"):
        candidatos_generados, columnas_detectadas_archivo, campos_rat_mapeados, truncados_contador, filas_utiles_totales = _flujo_texto(
            contenido, hash_archivo, candidatos_generados, tipo_detectado
        )
    else:
        st.error(MENSAJE_FORMATO_NO_SOPORTADO)
        return

    if truncados_contador > 0:
        st.warning(
            f"ℹ️ **Límite de tamaño por campo aplicado:** {truncados_contador} valor(es) superaban los "
            f"{MAX_CARACTERES_CAMPO} caracteres y fueron truncados de forma controlada para cumplir "
            "con las políticas de almacenamiento y privacidad."
        )

    if not candidatos_generados:
        return

    # ── PASO 6: Previsualización completa de candidatos ───────────────────────
    st.markdown("---")
    st.subheader("Paso 6 — Previsualización de candidatos generados")
    n = len(candidatos_generados)

    st.markdown(f"#### Candidatos generados: {n} de {filas_utiles_totales} filas útiles detectadas")
    st.info(
        "Todos están catalogados como **⚠️ DATOS NO VALIDADOS** y no alteran la base de datos "
        "hasta que los revise individualmente en la pestaña de conciliación.",
        icon="🛡️",
    )

    resumen_cands = []
    for idx_c, cand in enumerate(candidatos_generados, start=1):
        dj = cand["datos_extraidos_json"]
        nom = dj.get("nombre_tratamiento", NOMBRE_TRATAMIENTO_DEFECTO)
        origen = f"{cand.get('nro_hoja') or 'Tabla'} — Fila {cand.get('nro_fila') or cand.get('nro_pagina') or '—'}"
        campos_con_dato = len([k for k, v in dj.items() if k != "campos_adicionales" and v])
        resumen_cands.append({
            "#": idx_c,
            "Origen": origen,
            "Nombre del Tratamiento (candidato)": nom,
            "Campos RAT con dato": campos_con_dato,
        })
    st.dataframe(pd.DataFrame(resumen_cands), use_container_width=True, height=350)

    # ── PASO 7: Evidencia URL ──────────────────────────────────────────────────
    st.subheader("Paso 7 — Vincular evidencia documental de origen (opcional)")
    df_ev_emp = get_evidencias_df(empresa_id=empresa_id)
    opciones_ev = {"(Sin evidencia permanente vinculada)": None}
    if not df_ev_emp.empty:
        for _, r in df_ev_emp.iterrows():
            label = f"#{r['id']} — {r.get('descripcion','')[:40]} ({r.get('foto_url','')[:30]})"
            opciones_ev[label] = r["id"]

    ev_label = st.selectbox("Evidencia URL existente", list(opciones_ev.keys()), key=f"imp_evidencia_{hash_archivo}")
    evidencia_id = opciones_ev[ev_label]
    tiene_evidencia_url = evidencia_id is not None

    if not tiene_evidencia_url:
        st.caption("ℹ️ Esta importación quedará marcada como 'Sin evidencia permanente vinculada'.")

    st.markdown("---")

    # ── PASO 8: Registrar o completar importación en bandeja ───────────────────
    st.subheader("Paso 8 — Confirmar y guardar candidatos en la bandeja")

    cands_previos_en_bd = 0
    id_importacion_existente = None
    if dup:
        id_importacion_existente = dup["id"]
        df_cands_bd = get_candidatos_df(importacion_id=id_importacion_existente)
        cands_previos_en_bd = len(df_cands_bd)

    if cands_previos_en_bd > 0:
        cands_nuevos_estimados = max(n - cands_previos_en_bd, 0)
        st.info(
            f"ℹ️ **Estado de la bandeja:**\n"
            f"- Filas útiles detectadas: **{n}**\n"
            f"- Candidatos ya existentes en BD (Importación #{id_importacion_existente}): **{cands_previos_en_bd}**\n"
            f"- Candidatos nuevos a crear: **{cands_nuevos_estimados}**\n"
            f"- Total esperado: **{n}**"
        )

    texto_boton = (
        f"💾 Completar candidatos faltantes ({n - cands_previos_en_bd} nuevos)"
        if cands_previos_en_bd > 0
        else f"💾 Guardar {n} candidatos en la bandeja para revisión"
    )

    if st.button(texto_boton, type="primary", key=f"btn_registrar_{hash_archivo}"):
        with st.spinner("Guardando candidatos en la bandeja documental…"):
            resumen_txt = resumen_extraccion(
                formato=tipo_detectado,
                tamano_kb=tamano_kb,
                total_filas_o_paginas=n,
                columnas_detectadas=columnas_detectadas_archivo,
                campos_mapeados=campos_rat_mapeados,
                advertencias=advertencias_list,
            )

            if id_importacion_existente:
                imp_id = id_importacion_existente
            else:
                imp_id, msg_imp = crear_importacion(
                    empresa_id=empresa_id,
                    nombre_archivo=archivo.name,
                    tipo_archivo=tipo_detectado,
                    mime_detectado=tipo_detectado,
                    tamano_bytes=len(contenido),
                    hash_sha256=hash_archivo,
                    evaluacion_id=evaluacion_id,
                    evidencia_id=evidencia_id,
                    tiene_evidencia_url=tiene_evidencia_url,
                    descripcion_origen=descripcion_origen,
                    advertencias="; ".join(advertencias_list) if advertencias_list else "",
                    resumen_extraccion=resumen_txt,
                )
                if imp_id is None:
                    st.error(f"Error al registrar la importación: {msg_imp}")
                    return

            insertados = 0
            omitidos_duplicados = 0
            errores_cand = 0

            for cand in candidatos_generados:
                hoja = cand.get("nro_hoja")
                fila = cand.get("nro_fila")
                if candidato_duplicado_en_importacion(imp_id, hoja, fila):
                    omitidos_duplicados += 1
                    continue

                cid, _ = crear_candidato(
                    importacion_id=imp_id,
                    empresa_id=empresa_id,
                    datos_extraidos_json=cand["datos_extraidos_json"],
                    nro_hoja=hoja,
                    nro_fila=fila,
                    nro_pagina=cand.get("nro_pagina"),
                    seccion_origen=cand.get("seccion_origen"),
                )
                if cid:
                    insertados += 1
                else:
                    errores_cand += 1

            total_en_bd = omitidos_duplicados + insertados
            actualizar_estado_importacion(imp_id, "con_candidatos", total_candidatos=total_en_bd)
            actualizar_contadores_importacion(imp_id)

            st.session_state["imp_bytes_sesion"] = bytes_sesion + len(contenido)
            st.session_state["imp_archivos_sesion"] = archivos_sesion + 1

            st.session_state.pop(f"imp_candidatos_{hash_archivo}", None)
            st.session_state.pop(f"imp_cols_{hash_archivo}", None)
            st.session_state.pop(f"imp_campos_{hash_archivo}", None)
            st.session_state.pop(f"imp_truncados_{hash_archivo}", None)
            st.session_state.pop(f"imp_filas_utiles_{hash_archivo}", None)

            st.success(
                f"✅ **Importación completada:** {insertados} candidatos nuevos creados "
                f"({omitidos_duplicados} ya existían). Total registrado: {total_en_bd} candidatos.\n\n"
                "Pase a la pestaña **🔍 Revisar y Conciliar Candidatos** para procesarlos individualmente."
            )
            st.rerun()


# ==============================================================================
# FLUJOS DE EXTRACCIÓN POR FORMATO
# ==============================================================================

def _flujo_xlsx(contenido: bytes, hash_archivo: str, candidatos_previos: list, conservar_adicionales: bool) -> tuple[list, list, list, int, int]:
    """Flujo interactivo de extracción para XLSX con previsualización completa."""
    try:
        hojas = extraer_xlsx_hojas(contenido)
    except ValueError as exc:
        st.error(str(exc))
        return [], [], [], 0, 0

    hoja_sel = st.selectbox("Seleccionar hoja", hojas, key=f"xlsx_hoja_{hash_archivo}")

    try:
        encabezados, datos, total_datos = extraer_xlsx_encabezados_preview(contenido, hoja_sel)
    except ValueError as exc:
        st.error(str(exc))
        return [], [], [], 0, 0

    if not encabezados:
        st.warning("No se detectaron encabezados en la hoja seleccionada.")
        return [], [], [], 0, 0

    st.markdown(f"**Total filas de datos detectadas:** {total_datos} | **Columnas:** {len(encabezados)}")
    st.markdown("**Encabezados:**")
    st.code(", ".join(encabezados))

    if datos:
        if total_datos <= 100:
            st.caption(f"Mostrando las {total_datos} filas de datos detectadas. Usa el desplazamiento vertical y horizontal para recorrer la tabla completa.")
            df_mostrar = pd.DataFrame(datos, columns=encabezados)
        else:
            st.caption(f"Mostrando 100 de {total_datos} filas de datos por rendimiento. La extracción procesará todas las filas útiles detectadas.")
            df_mostrar = pd.DataFrame(datos[:100], columns=encabezados)

        st.dataframe(
            df_mostrar,
            use_container_width=True,
            height=380,
            hide_index=False,
        )

    mapeo = _selector_mapeo_columnas(encabezados, hash_archivo)
    campos_mapeados = [v for v in mapeo.values() if v]

    if not campos_mapeados:
        st.info("Mapee al menos una columna a un campo RAT para generar candidatos.")
        return [], encabezados, [], 0, total_datos

    truncados = 0
    total_utiles = total_datos

    if st.button("▶ Generar candidatos desde XLSX", key=f"btn_gen_xlsx_{hash_archivo}"):
        try:
            candidatos, truncados, total_utiles = generar_candidatos_xlsx(
                contenido, hoja_sel, mapeo, conservar_adicionales=conservar_adicionales
            )
            st.session_state[f"imp_candidatos_{hash_archivo}"] = candidatos
            st.session_state[f"imp_cols_{hash_archivo}"] = encabezados
            st.session_state[f"imp_campos_{hash_archivo}"] = campos_mapeados
            st.session_state[f"imp_truncados_{hash_archivo}"] = truncados
            st.session_state[f"imp_filas_utiles_{hash_archivo}"] = total_utiles
            st.success(f"✅ Candidatos generados: {len(candidatos)} de {total_utiles} filas útiles detectadas.")
        except Exception as exc:
            st.error(f"Error al generar candidatos: {exc}")

    cands = st.session_state.get(f"imp_candidatos_{hash_archivo}", candidatos_previos)
    tot = st.session_state.get(f"imp_filas_utiles_{hash_archivo}", total_utiles)
    return cands, encabezados, campos_mapeados, truncados, tot


def _flujo_csv(contenido: bytes, hash_archivo: str, candidatos_previos: list, conservar_adicionales: bool) -> tuple[list, list, list, int, int]:
    """Flujo interactivo de extracción para CSV con previsualización completa."""
    try:
        encabezados, datos, delimitador, total_datos = extraer_csv_encabezados_preview(contenido)
    except Exception as exc:
        st.error(f"Error al leer el CSV: {exc}")
        return [], [], [], 0, 0

    st.markdown(f"**Delimitador:** `{repr(delimitador)}` | **Total filas:** {total_datos} | **Columnas:** {len(encabezados)}")
    if encabezados:
        st.code(", ".join(encabezados))

    if datos:
        if total_datos <= 100:
            st.caption(f"Mostrando las {total_datos} filas de datos detectadas. Usa el desplazamiento vertical y horizontal para recorrer la tabla completa.")
            df_mostrar = pd.DataFrame(datos, columns=encabezados)
        else:
            st.caption(f"Mostrando 100 de {total_datos} filas de datos por rendimiento. La extracción procesará todas las filas útiles detectadas.")
            df_mostrar = pd.DataFrame(datos[:100], columns=encabezados)

        st.dataframe(
            df_mostrar,
            use_container_width=True,
            height=380,
            hide_index=False,
        )

    mapeo = _selector_mapeo_columnas(encabezados, hash_archivo)
    campos_mapeados = [v for v in mapeo.values() if v]

    if not campos_mapeados:
        st.info("Mapee al menos una columna a un campo RAT para generar candidatos.")
        return [], encabezados, [], 0, total_datos

    truncados = 0
    total_utiles = total_datos

    if st.button("▶ Generar candidatos desde CSV", key=f"btn_gen_csv_{hash_archivo}"):
        try:
            candidatos, truncados, total_utiles = generar_candidatos_csv(
                contenido, mapeo, conservar_adicionales=conservar_adicionales
            )
            st.session_state[f"imp_candidatos_{hash_archivo}"] = candidatos
            st.session_state[f"imp_cols_{hash_archivo}"] = encabezados
            st.session_state[f"imp_campos_{hash_archivo}"] = campos_mapeados
            st.session_state[f"imp_truncados_{hash_archivo}"] = truncados
            st.session_state[f"imp_filas_utiles_{hash_archivo}"] = total_utiles
            st.success(f"✅ Candidatos generados: {len(candidatos)} de {total_utiles} filas útiles detectadas.")
        except Exception as exc:
            st.error(f"Error al generar candidatos: {exc}")

    cands = st.session_state.get(f"imp_candidatos_{hash_archivo}", candidatos_previos)
    tot = st.session_state.get(f"imp_filas_utiles_{hash_archivo}", total_utiles)
    return cands, encabezados, campos_mapeados, truncados, tot


def _flujo_docx(contenido: bytes, hash_archivo: str, candidatos_previos: list, conservar_adicionales: bool) -> tuple[list, list, list, int, int]:
    """Flujo interactivo de extracción para DOCX con previsualización completa de todas las filas."""
    try:
        estructura = extraer_docx_estructura(contenido)
    except ImportError:
        st.error("La biblioteca 'python-docx' no está disponible en este entorno.")
        return [], [], [], 0, 0
    except ValueError as exc:
        st.error(str(exc))
        return [], [], [], 0, 0

    tablas = estructura.get("tablas", [])
    secciones = estructura.get("secciones", [])

    st.markdown(f"**Tablas detectadas:** {len(tablas)} · **Secciones de texto:** {len(secciones)}")

    modo = st.radio(
        "Fuente a usar",
        ["Tabla estándar (mapeo de columnas)", "Texto libre (creación manual de candidato)"],
        key=f"docx_modo_{hash_archivo}",
    )

    candidatos = list(candidatos_previos)
    encabezados = []
    campos_mapeados = []
    truncados = 0
    total_utiles = 0

    if modo.startswith("Tabla"):
        if not tablas:
            st.warning("No se detectaron tablas en el documento.")
            return candidatos, [], [], 0, 0

        idx_tabla = st.selectbox(
            "Seleccionar tabla",
            [t["indice"] for t in tablas],
            format_func=lambda i: f"Tabla {i + 1} ({tablas[i]['total_filas']} filas de datos, {len(tablas[i]['encabezados'])} columnas)",
            key=f"docx_tabla_{hash_archivo}",
        )
        tabla_sel = tablas[idx_tabla]
        encabezados = tabla_sel["encabezados"]
        total_datos = tabla_sel["total_filas"]
        filas_datos = tabla_sel.get("filas_datos") or (tabla_sel["filas_texto"][1:] if len(tabla_sel.get("filas_texto", [])) > 1 else [])

        st.markdown(f"**Total filas de datos detectadas:** {total_datos} | **Columnas:** {len(encabezados)}")
        st.markdown("**Encabezados:**")
        st.code(", ".join(encabezados))

        # Previsualización COMPLETA con scroll vertical y horizontal
        if filas_datos:
            if total_datos <= 100:
                st.caption(f"Mostrando las {total_datos} filas de datos detectadas. Usa el desplazamiento vertical y horizontal para recorrer la tabla completa.")
                df_mostrar = pd.DataFrame(filas_datos, columns=encabezados)
            else:
                st.caption(f"Mostrando 100 de {total_datos} filas de datos por rendimiento. La extracción procesará todas las filas útiles detectadas.")
                df_mostrar = pd.DataFrame(filas_datos[:100], columns=encabezados)

            st.dataframe(
                df_mostrar,
                use_container_width=True,
                height=380,
                hide_index=False,
            )

        mapeo = _selector_mapeo_columnas(encabezados, hash_archivo)
        campos_mapeados = [v for v in mapeo.values() if v]

        if not campos_mapeados:
            st.info("Mapee al menos una columna.")
            return candidatos, encabezados, [], 0, total_datos

        if st.button("▶ Generar candidatos desde tabla DOCX", key=f"btn_gen_docx_{hash_archivo}"):
            nuevos, truncados, total_utiles, combinaciones = generar_candidatos_docx_tabla(
                estructura, idx_tabla, mapeo, conservar_adicionales=conservar_adicionales
            )
            candidatos = nuevos
            st.session_state[f"imp_candidatos_{hash_archivo}"] = candidatos
            st.session_state[f"imp_cols_{hash_archivo}"] = encabezados
            st.session_state[f"imp_campos_{hash_archivo}"] = campos_mapeados
            st.session_state[f"imp_truncados_{hash_archivo}"] = truncados
            st.session_state[f"imp_filas_utiles_{hash_archivo}"] = total_utiles

            if combinaciones > 0:
                st.info(f"ℹ️ Se combinaron valores de columnas con el mismo destino usando el separador ' / ' en {combinaciones} campo(s).")

            st.success(f"✅ Candidatos generados: {len(candidatos)} de {total_utiles} filas útiles detectadas.")

    else:
        if not secciones:
            st.warning("No se detectaron secciones de texto en el documento.")
        else:
            sel_seccion = st.selectbox(
                "Sección a consultar",
                [s["titulo"] for s in secciones],
                key=f"docx_seccion_{hash_archivo}",
            )
            sec_data = next(s for s in secciones if s["titulo"] == sel_seccion)
            st.text_area("Texto de la sección (referencia)", sec_data["texto_preview"], height=150, disabled=True)

        st.markdown("**Crear candidato manual desde este texto:**")
        cand_data = _formulario_candidato_manual(f"docx_manual_{hash_archivo}", seccion_origen=sel_seccion if secciones else "Texto libre DOCX")
        if cand_data:
            candidatos.append(crear_candidato_manual_texto(sel_seccion if secciones else "Texto libre DOCX", cand_data))
            st.session_state[f"imp_candidatos_{hash_archivo}"] = candidatos
            st.success("✅ Candidato manual añadido.")

    cands = st.session_state.get(f"imp_candidatos_{hash_archivo}", candidatos)
    tot = st.session_state.get(f"imp_filas_utiles_{hash_archivo}", total_utiles or len(cands))
    return cands, encabezados, campos_mapeados, truncados, tot


def _flujo_pdf(contenido: bytes, hash_archivo: str, candidatos_previos: list, empresa_id: int) -> tuple[list, list, list, int, int]:
    """Flujo interactivo de extracción para PDF con texto."""
    try:
        paginas = extraer_pdf_paginas(contenido)
    except ImportError:
        st.error("La biblioteca 'pdfplumber' no está disponible en este entorno.")
        return [], [], [], 0, 0
    except ValueError as exc:
        st.error(str(exc))
        return [], [], [], 0, 0

    paginas_con_texto = [p for p in paginas if p["tiene_texto"]]
    paginas_sin_texto = [p for p in paginas if not p["tiene_texto"]]

    st.markdown(
        f"**Total páginas:** {len(paginas)} · "
        f"**Con texto extraíble:** {len(paginas_con_texto)} · "
        f"**Sin texto (diferidas):** {len(paginas_sin_texto)}"
    )

    if paginas_sin_texto:
        st.warning(
            f"⚠️ {len(paginas_sin_texto)} página(s) sin texto extraíble: "
            f"{[p['nro_pagina'] for p in paginas_sin_texto]}. Formato diferido."
        )

    if not paginas_con_texto:
        st.error("Este PDF no tiene texto extraíble. Conviértalo a formato con texto o regístrelo como evidencia.")
        return [], [], [], 0, 0

    nro_pagina = st.selectbox(
        "Seleccionar página para crear candidato",
        [p["nro_pagina"] for p in paginas_con_texto],
        format_func=lambda n: f"Página {n}",
        key=f"pdf_pagina_{hash_archivo}",
    )

    pag_data = next(p for p in paginas_con_texto if p["nro_pagina"] == nro_pagina)
    st.text_area(
        f"Texto extraído — Página {nro_pagina} (referencia no editable)",
        pag_data["texto_preview"],
        height=200,
        disabled=True,
    )

    candidatos = list(candidatos_previos)
    cand_data = _formulario_candidato_manual(f"pdf_manual_{hash_archivo}_{nro_pagina}", seccion_origen=f"Página {nro_pagina}")
    if cand_data:
        candidatos.append(crear_candidato_manual_pdf(nro_pagina, cand_data))
        st.session_state[f"imp_candidatos_{hash_archivo}"] = candidatos
        st.success(f"✅ Candidato manual añadido desde Página {nro_pagina}.")

    cands = st.session_state.get(f"imp_candidatos_{hash_archivo}", candidatos)
    return cands, [f"Página {nro_pagina}"], list(cand_data.keys()) if cand_data else [], 0, len(cands)


def _flujo_texto(contenido: bytes, hash_archivo: str, candidatos_previos: list, tipo: str) -> tuple[list, list, list, int, int]:
    """Flujo interactivo de extracción para MD y TXT."""
    texto = extraer_texto_plano(contenido)
    st.text_area(
        f"Contenido del archivo ({tipo.upper()}) — solo lectura",
        texto[:3000] + (" …[truncado para visualización]" if len(texto) > 3000 else ""),
        height=250,
        disabled=True,
    )

    candidatos = list(candidatos_previos)
    cand_data = _formulario_candidato_manual(f"txt_manual_{hash_archivo}", seccion_origen=f"Bloque {tipo.upper()}")
    if cand_data:
        candidatos.append(crear_candidato_manual_texto(f"Bloque {tipo.upper()}", cand_data))
        st.session_state[f"imp_candidatos_{hash_archivo}"] = candidatos
        st.success("✅ Candidato manual añadido.")

    cands = st.session_state.get(f"imp_candidatos_{hash_archivo}", candidatos)
    return cands, [f"Bloque {tipo.upper()}"], list(cand_data.keys()) if cand_data else [], 0, len(cands)


# ==============================================================================
# WIDGETS AUXILIARES
# ==============================================================================

def _selector_mapeo_columnas(encabezados: list[str], key_base: str) -> dict:
    """Muestra un selector para mapear cada columna del archivo a un campo RAT."""
    st.markdown("**Mapeo de columnas → campos RAT** *(Decreto N° 662, Art. 3 d)*:")
    opciones_rat = ["(No mapear)"] + [f"{k} — {v}" for k, v in CAMPOS_RAT_ETIQUETAS.items()]
    claves_rat = [None] + CAMPOS_RAT_CLAVES

    mapeo = {}
    cols = st.columns(min(len(encabezados), 3))
    for idx, enc in enumerate(encabezados):
        col = cols[idx % len(cols)]
        sel = col.selectbox(
            f"Col. {idx}: `{enc[:25]}`",
            opciones_rat,
            key=f"mapeo_{key_base}_{idx}",
        )
        mapeo[idx] = claves_rat[opciones_rat.index(sel)]
    return mapeo


def _formulario_candidato_manual(key_base: str, seccion_origen: str = "") -> dict | None:
    """Formulario para crear un candidato manualmente campo por campo."""
    with st.expander("📝 Crear candidato manualmente desde este texto", expanded=False):
        st.caption("⚠️ **Datos no validados.** Complete solo los campos que el texto indica expresamente.")
        campos = {}
        for i in range(0, len(CAMPOS_RAT_DECRETO), 2):
            par = CAMPOS_RAT_DECRETO[i: i + 2]
            cols = st.columns(len(par))
            for j, (clave, etiqueta) in enumerate(par):
                campos[clave] = cols[j].text_area(
                    etiqueta,
                    height=70,
                    key=f"{key_base}_campo_{clave}",
                    placeholder="(dejar vacío si no consta en el texto)",
                )

        if st.button("➕ Agregar candidato", key=f"btn_{key_base}"):
            no_vacios = {k: v for k, v in campos.items() if v and v.strip()}
            if not no_vacios:
                st.warning("Complete al menos un campo antes de agregar el candidato.")
                return None
            return no_vacios

    return None


# ==============================================================================
# TAB 2: REVISAR Y CONCILIAR CANDIDATOS (CONCILIACIÓN CAMPO A CAMPO)
# ==============================================================================

def _tab_revisar_candidatos() -> None:
    st.subheader("Revisión y Conciliación de Candidatos RAT")

    df_emp = get_empresas_df()
    if df_emp.empty:
        st.info("No hay empresas registradas.")
        return

    opciones_emp = {r["nombre"]: r["id"] for _, r in df_emp.iterrows()}
    empresa_sel = st.selectbox("Empresa", list(opciones_emp.keys()), key="rev_empresa")
    empresa_id = opciones_emp[empresa_sel]

    # Contadores por estado de la empresa
    df_todos = get_candidatos_df(empresa_id=empresa_id)
    if not df_todos.empty:
        c_pend = len(df_todos[df_todos["estado_revision"] == "pendiente"])
        c_aprob = len(df_todos[df_todos["estado_revision"] == "aprobado_borrador"])
        c_prop = len(df_todos[df_todos["estado_revision"] == "propuesto_actualizacion"])
        c_ign = len(df_todos[df_todos["estado_revision"] == "ignorado"])

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Pendientes", c_pend)
        col_m2.metric("Creados (Pendiente Caracterización)", c_aprob)
        col_m3.metric("Propuestos Act.", c_prop)
        col_m4.metric("Ignorados", c_ign)
        st.markdown("---")

    df_cand = get_candidatos_df(empresa_id=empresa_id, estado_revision="pendiente")

    if df_cand.empty:
        st.success("✅ No hay candidatos pendientes de revisión para esta empresa.")
        _mostrar_historial_revisados(empresa_id)
        return

    col_hdr1, col_hdr2 = st.columns([3, 1])
    with col_hdr1:
        st.info(f"**{len(df_cand)} candidato(s) pendiente(s)** de revisión para **{empresa_sel}**.")
    with col_hdr2:
        cant_mostrar = st.selectbox(
            "Mostrar:",
            ["10", "25", "50", "Todos"],
            index=3,
            key="rev_cant_mostrar",
        )

    limite_vis = len(df_cand) if cant_mostrar == "Todos" else int(cant_mostrar)
    candidatos_visibles = df_cand.iloc[:limite_vis]

    if len(df_cand) > limite_vis:
        st.caption(f"Mostrando {limite_vis} de {len(df_cand)} candidatos pendientes.")

    df_trat = get_tratamientos_df(empresa_id=empresa_id)
    opciones_trat = {"(Seleccionar tratamiento existente)": None}
    if not df_trat.empty:
        for _, r in df_trat.iterrows():
            opciones_trat[f"#{r['id']} — {r['nombre_tratamiento'][:55]}"] = int(r["id"])

    df_eval = get_evaluaciones_df(empresa_id=empresa_id)
    opciones_eval_rev = {"(Sin evaluación)": None}
    if not df_eval.empty:
        for _, r in df_eval.iterrows():
            opciones_eval_rev[f"{r['nombre']} ({r.get('periodo','')})"] = r["id"]

    for _, cand in candidatos_visibles.iterrows():
        cand_id = int(cand["id"])
        importacion_id = int(cand["importacion_id"])

        origen_info = (
            f"Archivo: {cand['nombre_archivo']} | "
            f"Hoja: {cand['hoja'] or '—'} | "
            f"Fila: {cand['nro_fila'] or cand['nro_pagina'] or cand['seccion_origen'] or '—'}"
        )

        with st.expander(f"⚠️ Candidato #{cand_id} — {origen_info}", expanded=False):
            try:
                datos_json = json.loads(cand["datos_json"]) if isinstance(cand["datos_json"], str) else {}
            except Exception:
                datos_json = {}

            st.caption(f"📍 **Origen documental:** {origen_info}")
            st.caption("⚠️ **DATOS EXTRAÍDOS NO VALIDADOS — Requieren confirmación humana explícita**")

            nombre_cand = datos_json.get("nombre_tratamiento", "")
            similar = (
                detectar_candidato_similar_en_tratamientos(empresa_id, nombre_cand)
                if nombre_cand and nombre_cand != NOMBRE_TRATAMIENTO_DEFECTO
                else None
            )
            if similar:
                st.warning(
                    f"⚠️ **Coincidencia detectada:** Existe tratamiento ID #{similar['id']} — "
                    f"**{similar['nombre_tratamiento']}** con nombre coincidente. "
                    "Considere conciliarlo en lugar de crear un tratamiento duplicado."
                )

            st.markdown("---")
            st.markdown("#### Seleccione la acción para este candidato:")

            modo_accion = st.radio(
                "Acción a tomar:",
                [
                    "1. Crear nuevo tratamiento (pendiente de caracterización en RAT)",
                    "2. Conciliar / Actualizar tratamiento existente (comparación campo a campo)",
                    "3. Ignorar candidato (descartar y conservar trazabilidad)",
                ],
                key=f"modo_accion_{cand_id}",
            )

            # ──────────────────────────────────────────────────────────────────
            # ACCIÓN 1: CREAR NUEVO TRATAMIENTO
            # ──────────────────────────────────────────────────────────────────
            if modo_accion.startswith("1."):
                st.markdown("##### Vista de datos extraídos para nuevo tratamiento:")
                col_a, col_b = st.columns(2)
                items = [(k, v) for k, v in datos_json.items() if k != "campos_adicionales" and v]
                for i, (k, v) in enumerate(items):
                    col = col_a if i % 2 == 0 else col_b
                    col.markdown(f"**{CAMPOS_RAT_ETIQUETAS.get(k, k)}:** {v}")

                eval_rev = st.selectbox(
                    "Evaluación GRC asociada (opcional)",
                    list(opciones_eval_rev.keys()),
                    key=f"cand_eval_{cand_id}",
                )
                eval_id_rev = opciones_eval_rev[eval_rev]

                obs_crear = st.text_input(
                    "Observación de creación (opcional)",
                    key=f"obs_crear_{cand_id}",
                    max_chars=500,
                )

                st.caption(
                    "ℹ️ El tratamiento se creará en la base de datos con el estado: "
                    "*'Creado desde importación; pendiente de caracterización y validación en Tratamientos (RAT)'*. "
                    "No cuenta para la completitud documental MPI hasta su validación formal."
                )

                if st.button("✅ Crear Tratamiento", type="primary", key=f"btn_crear_{cand_id}"):
                    ok, msg = aplicar_accion_candidato(
                        candidato_id=cand_id,
                        accion="crear_borrador",
                        empresa_id=empresa_id,
                        campos_confirmados=datos_json,
                        tratamiento_existente_id=None,
                        evaluacion_id=eval_id_rev,
                        observacion=obs_crear,
                    )
                    if ok:
                        actualizar_contadores_importacion(importacion_id)
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            # ──────────────────────────────────────────────────────────────────
            # ACCIÓN 2: CONCILIAR CON TRATAMIENTO EXISTENTE (LADO A LADO)
            # ──────────────────────────────────────────────────────────────────
            elif modo_accion.startswith("2."):
                st.markdown("##### ⚖️ Conciliación campo a campo")
                st.write(
                    "Seleccione el tratamiento existente. Podrá comparar el valor actual de cada campo "
                    "contra el valor extraído y elegir **manualmente** cuáles desea actualizar."
                )

                index_defecto = 0
                if similar:
                    for idx_opc, (txt, tid) in enumerate(opciones_trat.items()):
                        if tid == similar["id"]:
                            index_defecto = idx_opc
                            break

                trat_sel_label = st.selectbox(
                    "Tratamiento existente a conciliar *",
                    list(opciones_trat.keys()),
                    index=index_defecto,
                    key=f"conciliar_trat_sel_{cand_id}",
                )
                trat_id_sel = opciones_trat[trat_sel_label]

                if trat_id_sel is None:
                    st.info("Seleccione un tratamiento existente para habilitar la comparativa campo a campo.")
                else:
                    trat_actual = df_trat[df_trat["id"] == trat_id_sel]
                    if trat_actual.empty:
                        st.error("No se encontró el tratamiento seleccionado en la base de datos.")
                    else:
                        r_actual = trat_actual.iloc[0].to_dict()

                        st.markdown("---")
                        st.markdown("**Comparativa campo a campo — Marque explícitamente los campos a aplicar:**")

                        c_hdr1, c_hdr2, c_hdr3, c_hdr4 = st.columns([3, 4, 4, 2])
                        c_hdr1.markdown("**Campo RAT**")
                        c_hdr2.markdown("**Valor Actual en BD**")
                        c_hdr3.markdown("**Valor Extraído (no validado)**")
                        c_hdr4.markdown("**¿Aplicar?**")

                        campos_seleccionados_actualizar = {}

                        for clave_campo, etiqueta_campo in CAMPOS_RAT_DECRETO:
                            val_actual = str(r_actual.get(clave_campo) or "").strip()
                            val_extraido = str(datos_json.get(clave_campo) or "").strip()

                            if not val_actual and not val_extraido:
                                continue

                            c_col1, c_col2, c_col3, c_col4 = st.columns([3, 4, 4, 2])
                            c_col1.caption(f"**{etiqueta_campo}**")
                            c_col2.write(val_actual if val_actual else "*(Vacío)*")

                            if val_extraido:
                                c_col3.write(f"`{val_extraido}`")
                                chk = c_col4.checkbox(
                                    "Aplicar",
                                    value=False,
                                    key=f"chk_{cand_id}_{clave_campo}",
                                    help=f"Marque para reemplazar '{val_actual}' por '{val_extraido}' en este tratamiento.",
                                )
                                if chk:
                                    campos_seleccionados_actualizar[clave_campo] = val_extraido
                            else:
                                c_col3.write("*(No extraído)*")
                                c_col4.write("—")

                        st.markdown("---")
                        st.markdown("##### Vista previa de cambios a confirmar:")

                        if not campos_seleccionados_actualizar:
                            st.warning(
                                "⚠️ **Ningún campo seleccionado.** Marque al menos una casilla '¿Aplicar?' "
                                "para habilitar la confirmación. Ningún dato se modificará automáticamente."
                            )
                        else:
                            st.success(
                                f"Se actualizarán **{len(campos_seleccionados_actualizar)} campo(s)** "
                                f"en el tratamiento ID #{trat_id_sel}: "
                                f"{', '.join([CAMPOS_RAT_ETIQUETAS.get(k, k) for k in campos_seleccionados_actualizar.keys()])}."
                            )

                            obs_conciliacion = st.text_input(
                                "Nota del revisor para la trazabilidad (opcional)",
                                key=f"obs_concil_{cand_id}",
                                max_chars=500,
                            )

                            if st.button("💾 Aplicar cambios confirmados", type="primary", key=f"btn_aplicar_concil_{cand_id}"):
                                payload_final = {}
                                for clave_c, _ in CAMPOS_RAT_DECRETO:
                                    if clave_c in campos_seleccionados_actualizar:
                                        payload_final[clave_c] = campos_seleccionados_actualizar[clave_c]
                                    else:
                                        payload_final[clave_c] = str(r_actual.get(clave_c) or "").strip()

                                ok_upd, msg_upd = update_tratamiento(
                                    tratamiento_id=trat_id_sel,
                                    empresa_id=empresa_id,
                                    evaluacion_id=r_actual.get("evaluacion_id"),
                                    nombre_tratamiento=payload_final.get("nombre_tratamiento") or r_actual.get("nombre_tratamiento", ""),
                                    descripcion=payload_final.get("descripcion", ""),
                                    base_legal=payload_final.get("base_legal", ""),
                                    datos_personales=payload_final.get("datos_personales", ""),
                                    responsables=payload_final.get("responsables", ""),
                                    encargados=payload_final.get("encargados", ""),
                                    transferencias=payload_final.get("transferencias", ""),
                                    rat_tipo_datos_sensibles=payload_final.get("rat_tipo_datos_sensibles", ""),
                                    rat_ambito_territorial=payload_final.get("rat_ambito_territorial", ""),
                                    rat_bases_datos_administradas=payload_final.get("rat_bases_datos_administradas", ""),
                                    rat_categorias_titulares=payload_final.get("rat_categorias_titulares", ""),
                                    rat_finalidades=payload_final.get("rat_finalidades", ""),
                                    rat_fuente_datos_acceso_publico=payload_final.get("rat_fuente_datos_acceso_publico", ""),
                                    rat_base_licitud_interes_legitimo=payload_final.get("rat_base_licitud_interes_legitimo", ""),
                                    rat_destinatarios_cesiones=payload_final.get("rat_destinatarios_cesiones", ""),
                                    rat_transferencias_internacionales_art27=payload_final.get("rat_transferencias_internacionales_art27", ""),
                                    rat_plazo_condicion_supresion=payload_final.get("rat_plazo_condicion_supresion", ""),
                                    rat_decisiones_automatizadas_perfilamiento=payload_final.get("rat_decisiones_automatizadas_perfilamiento", ""),
                                    evidencia_id=r_actual.get("evidencia_id"),
                                )

                                if not ok_upd:
                                    st.error(f"Error al actualizar tratamiento: {msg_upd}")
                                else:
                                    nombres_campos_aplicados = [
                                        CAMPOS_RAT_ETIQUETAS.get(k, k) for k in campos_seleccionados_actualizar.keys()
                                    ]
                                    registrar_actualizacion_candidato_confirmada(
                                        candidato_id=cand_id,
                                        tratamiento_existente_id=trat_id_sel,
                                        campos_actualizados=nombres_campos_aplicados,
                                        observacion_usuario=obs_conciliacion,
                                    )
                                    actualizar_contadores_importacion(importacion_id)
                                    st.success(
                                        f"✅ Tratamiento #{trat_id_sel} actualizado exitosamente con los campos confirmados. "
                                        "Trazabilidad registrada en el candidato."
                                    )
                                    st.rerun()

            # ──────────────────────────────────────────────────────────────────
            # ACCIÓN 3: IGNORAR CANDIDATO
            # ──────────────────────────────────────────────────────────────────
            else:
                st.markdown("##### Descartar candidato:")
                st.caption(
                    "El candidato se marcará como 'ignorado'. No modificará la tabla de tratamientos "
                    "y se conservará en el historial de importaciones para fines de auditoría y trazabilidad."
                )
                obs_ign = st.text_input(
                    "Motivo de descarte (opcional)",
                    key=f"obs_ign_{cand_id}",
                    max_chars=500,
                )
                if st.button("🗑️ Confirmar e Ignorar Candidato", key=f"btn_conf_ign_{cand_id}"):
                    ok, msg = aplicar_accion_candidato(
                        candidato_id=cand_id,
                        accion="ignorar",
                        empresa_id=empresa_id,
                        campos_confirmados=None,
                        tratamiento_existente_id=None,
                        evaluacion_id=None,
                        observacion=obs_ign,
                    )
                    if ok:
                        actualizar_contadores_importacion(importacion_id)
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)


def _mostrar_historial_revisados(empresa_id: int) -> None:
    """Muestra tabla de candidatos ya revisados de la empresa."""
    df_revisados = get_candidatos_df(empresa_id=empresa_id)
    if not df_revisados.empty:
        st.markdown("---")
        st.subheader("Historial de candidatos de la empresa")
        st.dataframe(
            df_revisados[[
                "id", "nombre_archivo", "hoja", "nro_fila", "estado_revision",
                "accion_humana", "tratamiento_existente_id", "tratamiento_creado_id", "observacion_revision",
            ]].rename(columns={
                "id": "ID", "nombre_archivo": "Archivo", "hoja": "Hoja",
                "nro_fila": "Fila", "estado_revision": "Estado",
                "accion_humana": "Acción", "tratamiento_existente_id": "Trat. conciliar",
                "tratamiento_creado_id": "Trat. creado", "observacion_revision": "Observación",
            }),
            use_container_width=True,
        )


# ==============================================================================
# TAB 3: HISTORIAL DE IMPORTACIONES
# ==============================================================================

def _tab_historial() -> None:
    st.subheader("Historial de importaciones documentales")

    df_emp = get_empresas_df()
    opciones_emp = {"(Todas las empresas)": None}
    if not df_emp.empty:
        opciones_emp.update({r["nombre"]: r["id"] for _, r in df_emp.iterrows()})

    empresa_sel = st.selectbox("Filtrar por empresa", list(opciones_emp.keys()), key="hist_empresa")
    empresa_id_hist = opciones_emp[empresa_sel]

    df_imp = get_importaciones_df(empresa_id=empresa_id_hist)

    if df_imp.empty:
        st.info("No hay importaciones registradas aún.")
        return

    st.dataframe(
        df_imp[[
            "id", "empresa", "evaluacion", "nombre_archivo", "tipo_archivo",
            "tamano_kb", "hash_abreviado", "estado", "evidencia_permanente",
            "total_candidatos", "candidatos_creados", "candidatos_ignorados",
            "advertencias", "created_at",
        ]].rename(columns={
            "id": "ID", "empresa": "Empresa", "evaluacion": "Evaluación",
            "nombre_archivo": "Archivo", "tipo_archivo": "Tipo",
            "tamano_kb": "Tamaño (KB)", "hash_abreviado": "Hash",
            "estado": "Estado", "evidencia_permanente": "Evidencia permanente",
            "total_candidatos": "Candidatos", "candidatos_creados": "Creados/Conciliados",
            "candidatos_ignorados": "Ignorados",
            "advertencias": "Advertencias", "created_at": "Fecha",
        }),
        use_container_width=True,
    )

    st.markdown("---")
    ids_imp = list(df_imp["id"].astype(int))
    if ids_imp:
        imp_sel = st.selectbox(
            "Ver candidatos de la importación #",
            ids_imp,
            format_func=lambda i: f"#{i} — {df_imp[df_imp['id'] == i]['nombre_archivo'].values[0]}",
            key="hist_imp_sel",
        )
        df_cand_hist = get_candidatos_df(importacion_id=imp_sel)
        if df_cand_hist.empty:
            st.info("Esta importación no tiene candidatos registrados.")
        else:
            st.dataframe(
                df_cand_hist[[
                    "id", "hoja", "nro_fila", "nro_pagina", "seccion_origen",
                    "estado_revision", "accion_humana", "tratamiento_existente_id", "tratamiento_creado_id", "observacion_revision",
                ]].rename(columns={
                    "id": "ID", "hoja": "Hoja", "nro_fila": "Fila",
                    "nro_pagina": "Página", "seccion_origen": "Sección",
                    "estado_revision": "Estado", "accion_humana": "Acción",
                    "tratamiento_existente_id": "Trat. conciliar",
                    "tratamiento_creado_id": "Trat. creado",
                    "observacion_revision": "Observación",
                }),
                use_container_width=True,
            )
