"""
Módulo Evaluaciones GRC — Contenedor principal del proyecto GRC.
Una evaluación agrupa visitas, tratamientos, hallazgos, riesgos y evidencias
de un proyecto de diagnóstico para una empresa en un período específico.

Flujo UI:
  Tab 1: Listado de evaluaciones (filtrable por empresa) + detalle + edición + eliminación
  Tab 2: Nueva evaluación

Regla de datos:
  - evaluacion_id es nullable en BD pero obligatorio en formularios de creación
  - Registros históricos con evaluacion_id=NULL se gestionan desde sus propios módulos
"""

import streamlit as st
from datetime import date

from db.repositories.empresas import get_empresas_df
from db.repositories.evaluaciones import (
    add_evaluacion,
    update_evaluacion,
    delete_evaluacion,
    get_evaluaciones_df,
    contar_elementos_evaluacion,
)
from utils.constants import (
    TIPOS_EVALUACION,
    ESTADOS_EVALUACION,
    ESTADO_EVALUACION_DISPLAY,
    semaforo_porcentaje,
)


def _estado_label(estado: str) -> str:
    return ESTADO_EVALUACION_DISPLAY.get(estado, estado)


def render() -> None:
    st.header("📁 Evaluaciones GRC")
    st.caption(
        "Una evaluación es el contenedor principal de un proyecto GRC (diagnóstico, "
        "seguimiento o cierre). Agrupa visitas, tratamientos, hallazgos y riesgos "
        "para una empresa y un período específico."
    )

    df_empresas = get_empresas_df()
    if df_empresas.empty:
        st.warning("⚠️ Primero debes registrar al menos una empresa antes de crear evaluaciones.")
        return

    tab_lista, tab_crear = st.tabs(["📋 Listado de Evaluaciones", "➕ Nueva Evaluación"])

    # Mapa empresa_str → empresa_id (reutilizado en ambas pestañas)
    empresa_map = {
        f"{r['id']} - {r['nombre']} ({r['rut']})": r["id"]
        for _, r in df_empresas.iterrows()
    }

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2: NUEVA EVALUACIÓN
    # ══════════════════════════════════════════════════════════════════════════
    with tab_crear:
        st.subheader("Registrar Nueva Evaluación GRC")
        with st.form("form_crear_evaluacion", clear_on_submit=True):

            col1, col2 = st.columns(2)
            with col1:
                empresa_key = st.selectbox("Empresa *", list(empresa_map.keys()))
                nombre_eval = st.text_input(
                    "Nombre de la Evaluación *",
                    placeholder="Ej. Diagnóstico Ley 21.719 — Serviphar Chile SpA 2025",
                )
                tipo_eval = st.selectbox("Tipo de Evaluación", TIPOS_EVALUACION)
                periodo   = st.text_input("Período", placeholder="Ej. 2025-Q1 o Semestral 2025")
                auditor   = st.text_input(
                    "Auditor Responsable",
                    placeholder="Ej. Gonzalo Vega (Lead GRC)",
                )

            with col2:
                estado_idx = ESTADOS_EVALUACION.index("borrador")
                estado = st.selectbox(
                    "Estado inicial",
                    ESTADOS_EVALUACION,
                    index=estado_idx,
                    format_func=_estado_label,
                )
                fecha_inicio     = st.date_input("Fecha de Inicio", value=date.today())
                fecha_cierre_pl  = st.date_input("Fecha de Cierre Planificada", value=None)

            alcance         = st.text_area("Alcance", placeholder="Empresas y procesos incluidos en el diagnóstico...", height=70)
            objetivo        = st.text_area("Objetivo", placeholder="Objetivo principal del proyecto GRC...", height=70)
            marco_normativo = st.text_input(
                "Marco Normativo (campo libre)",
                placeholder="Ej. Ley 21.719, ISO 27001, NIST — pendiente validación jurídica",
            )
            observaciones   = st.text_area("Observaciones iniciales", height=60)

            submitted = st.form_submit_button("💾 Crear Evaluación", use_container_width=True, type="primary")
            if submitted:
                if not nombre_eval or not nombre_eval.strip():
                    st.error("El nombre de la evaluación es obligatorio.")
                elif fecha_cierre_pl and fecha_cierre_pl < fecha_inicio:
                    st.error("La fecha de cierre planificada no puede ser anterior a la fecha de inicio.")
                else:
                    eid = empresa_map[empresa_key]
                    ok, msg = add_evaluacion(
                        empresa_id=eid,
                        nombre=nombre_eval,
                        tipo_evaluacion=tipo_eval,
                        periodo=periodo,
                        alcance=alcance,
                        objetivo=objetivo,
                        marco_normativo=marco_normativo,
                        auditor_responsable=auditor,
                        fecha_inicio=fecha_inicio,
                        fecha_cierre_planificada=fecha_cierre_pl,
                        estado=estado,
                        observaciones=observaciones,
                    )
                    if ok:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1: LISTADO DE EVALUACIONES
    # ══════════════════════════════════════════════════════════════════════════
    with tab_lista:
        col_f1, col_f2 = st.columns([2, 2])
        with col_f1:
            filtro_emp_key = st.selectbox(
                "🔍 Filtrar por Empresa:",
                ["Todas las empresas"] + list(empresa_map.keys()),
                key="eval_filtro_empresa",
            )

        emp_id_filtro = empresa_map[filtro_emp_key] if filtro_emp_key != "Todas las empresas" else None
        df_eval = get_evaluaciones_df(empresa_id=emp_id_filtro)

        if df_eval.empty:
            st.info("No hay evaluaciones registradas para el filtro seleccionado.")
            return

        # Preparar vista de tabla
        df_view = df_eval[[
            "id", "empresa", "nombre", "tipo_evaluacion", "periodo",
            "estado", "auditor_responsable", "fecha_inicio",
            "fecha_cierre_planificada", "porcentaje_avance",
        ]].copy()
        df_view["estado"] = df_view["estado"].map(_estado_label)
        df_view["porcentaje_avance"] = df_view["porcentaje_avance"].apply(
            lambda v: semaforo_porcentaje(float(v) if v is not None else 0)
        )
        df_view = df_view.rename(columns={
            "tipo_evaluacion":      "Tipo",
            "auditor_responsable":  "Auditor",
            "fecha_inicio":         "Inicio",
            "fecha_cierre_planificada": "Cierre Plan.",
            "porcentaje_avance":    "Avance",
        })

        st.caption(f"Total: **{len(df_eval)}** evaluaciones encontradas.")
        st.dataframe(df_view, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("⚙️ Detalle y Gestión de Evaluación")

        eval_opciones = {
            f"ID {r['id']} — {r['nombre']} | {r['empresa']} | {_estado_label(r['estado'])}": r["id"]
            for _, r in df_eval.iterrows()
        }
        eval_sel_str = st.selectbox("Selecciona una evaluación:", list(eval_opciones.keys()))
        eval_sel_id  = eval_opciones[eval_sel_str]
        e_row = df_eval[df_eval["id"] == eval_sel_id].iloc[0]

        # ── Detalle ────────────────────────────────────────────────────────────
        with st.expander(f"📋 Detalle: {e_row['nombre']}", expanded=True):
            dc1, dc2, dc3 = st.columns(3)
            with dc1:
                st.markdown(f"**Empresa:** {e_row['empresa']} ({e_row['rut_empresa']})")
                st.markdown(f"**Tipo:** {e_row['tipo_evaluacion'] or '—'}")
                st.markdown(f"**Período:** {e_row['periodo'] or '—'}")
                st.markdown(f"**Auditor:** {e_row['auditor_responsable'] or '—'}")
            with dc2:
                estado_lbl = _estado_label(e_row["estado"])
                st.markdown(f"**Estado:** {estado_lbl}")
                avance = float(e_row.get("porcentaje_avance") or 0)
                st.markdown(f"**Avance:** {semaforo_porcentaje(avance)}")
                st.markdown(f"**Inicio:** {e_row['fecha_inicio'] or '—'}")
                st.markdown(f"**Cierre planificado:** {e_row['fecha_cierre_planificada'] or '—'}")
                st.markdown(f"**Cierre real:** {e_row['fecha_cierre_real'] or '—'}")
            with dc3:
                conteos = contar_elementos_evaluacion(eval_sel_id)
                st.markdown(f"**Visitas asociadas:** {conteos['visitas']}")
                st.markdown(f"**Tratamientos asociados:** {conteos['tratamientos']}")
                st.markdown(f"**Evidencias asociadas:** {conteos['evidencias']}")

            if e_row["alcance"]:
                st.markdown(f"**Alcance:** {e_row['alcance']}")
            if e_row["objetivo"]:
                st.markdown(f"**Objetivo:** {e_row['objetivo']}")
            if e_row["marco_normativo"]:
                st.markdown(f"**Marco normativo:** _{e_row['marco_normativo']}_ *(campo libre — pendiente de validación jurídica)*")
            if e_row["observaciones"]:
                st.markdown(f"**Observaciones:** {e_row['observaciones']}")

        # ── Editar ─────────────────────────────────────────────────────────────
        with st.expander(f"✏️ Editar evaluación: {e_row['nombre']}", expanded=False):
            with st.form(f"form_edit_eval_{eval_sel_id}"):
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    e_emp_key = st.selectbox(
                        "Empresa",
                        list(empresa_map.keys()),
                        index=list(empresa_map.values()).index(int(e_row["empresa_id"]))
                        if int(e_row["empresa_id"]) in empresa_map.values() else 0,
                    )
                    e_nombre  = st.text_input("Nombre", value=e_row["nombre"])
                    e_tipo    = st.selectbox(
                        "Tipo",
                        TIPOS_EVALUACION,
                        index=TIPOS_EVALUACION.index(e_row["tipo_evaluacion"])
                        if e_row["tipo_evaluacion"] in TIPOS_EVALUACION else 0,
                    )
                    e_periodo = st.text_input("Período", value=e_row["periodo"] or "")
                    e_auditor = st.text_input("Auditor", value=e_row["auditor_responsable"] or "")

                with col_e2:
                    e_estado = st.selectbox(
                        "Estado",
                        ESTADOS_EVALUACION,
                        index=ESTADOS_EVALUACION.index(e_row["estado"])
                        if e_row["estado"] in ESTADOS_EVALUACION else 0,
                        format_func=_estado_label,
                    )
                    e_avance = st.slider(
                        "% Avance",
                        0, 100,
                        value=int(float(e_row.get("porcentaje_avance") or 0)),
                    )
                    e_inicio  = st.date_input(
                        "Fecha Inicio",
                        value=e_row["fecha_inicio"] if e_row["fecha_inicio"] else date.today(),
                    )
                    e_cierre_pl = st.date_input(
                        "Cierre Planificado",
                        value=e_row["fecha_cierre_planificada"] if e_row["fecha_cierre_planificada"] else None,
                    )
                    e_cierre_re = st.date_input(
                        "Cierre Real",
                        value=e_row["fecha_cierre_real"] if e_row["fecha_cierre_real"] else None,
                    )

                e_alcance  = st.text_area("Alcance", value=e_row["alcance"] or "", height=60)
                e_objetivo = st.text_area("Objetivo", value=e_row["objetivo"] or "", height=60)
                e_marco    = st.text_input("Marco Normativo", value=e_row["marco_normativo"] or "")
                e_obs      = st.text_area("Observaciones", value=e_row["observaciones"] or "", height=60)

                if st.form_submit_button("Actualizar Evaluación", type="primary"):
                    if not e_nombre or not e_nombre.strip():
                        st.error("El nombre de la evaluación es obligatorio.")
                    elif e_cierre_pl and e_cierre_pl < e_inicio:
                        st.error("La fecha de cierre planificada no puede ser anterior a la fecha de inicio.")
                    else:
                        ok, msg = update_evaluacion(
                            evaluacion_id=eval_sel_id,
                            empresa_id=empresa_map[e_emp_key],
                            nombre=e_nombre,
                            tipo_evaluacion=e_tipo,
                            periodo=e_periodo,
                            alcance=e_alcance,
                            objetivo=e_objetivo,
                            marco_normativo=e_marco,
                            auditor_responsable=e_auditor,
                            fecha_inicio=e_inicio,
                            fecha_cierre_planificada=e_cierre_pl,
                            fecha_cierre_real=e_cierre_re,
                            estado=e_estado,
                            porcentaje_avance=float(e_avance),
                            puntaje_total=e_row.get("puntaje_total"),
                            max_puntaje=e_row.get("max_puntaje"),
                            observaciones=e_obs,
                        )
                        if ok:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

        # ── Eliminar ───────────────────────────────────────────────────────────
        with st.expander("🗑️ Eliminar esta Evaluación", expanded=False):
            conteos = contar_elementos_evaluacion(eval_sel_id)
            total_vinculados = conteos["visitas"] + conteos["tratamientos"] + conteos["evidencias"]

            if total_vinculados > 0:
                st.info(
                    f"ℹ️ Esta evaluación tiene registros vinculados: "
                    f"{conteos['visitas']} visita(s), "
                    f"{conteos['tratamientos']} tratamiento(s), "
                    f"{conteos['evidencias']} evidencia(s). "
                    "Al eliminarla, esos registros conservan sus datos pero quedan sin evaluación asignada."
                )
            st.warning(
                "⚠️ Esta acción es permanente. "
                "Las visitas, tratamientos y evidencias vinculadas NO se eliminarán; "
                "solo perderán la referencia a esta evaluación."
            )
            confirmar = st.checkbox(
                "Confirmo que deseo eliminar esta evaluación.",
                key=f"del_eval_chk_{eval_sel_id}",
            )
            if st.button(
                "Eliminar Evaluación",
                type="secondary",
                disabled=not confirmar,
                key=f"del_eval_btn_{eval_sel_id}",
            ):
                ok, msg = delete_evaluacion(eval_sel_id)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
