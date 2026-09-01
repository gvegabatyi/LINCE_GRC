"""
Módulo Visitas / Auditorías.
Fase 1: añade campos evaluacion_id (opcional) y tipo_visita al formulario.
El checklist de 15 preguntas Sí/No/N/A se mantiene sin cambios.
Los registros históricos sin evaluacion_id siguen siendo visibles.
"""

import streamlit as st
from datetime import date
import json

from db.repositories.empresas import get_empresas_df
from db.repositories.evaluaciones import get_evaluaciones_df
from db.repositories.visitas import (
    add_visita,
    delete_visita,
    get_visitas_df,
)
from services.checklist_service import (
    calcular_puntaje,
    calcular_porcentaje,
    nivel_cumplimiento,
    get_preguntas,
    opciones_respuesta,
    icono_respuesta,
)
from utils.constants import TIPOS_VISITA


def _build_eval_options(empresa_id: int) -> dict:
    """Devuelve dict label→id con 'Sin evaluación' como primera opción."""
    opciones = {"Sin evaluación (historial)": None}
    if empresa_id:
        df = get_evaluaciones_df(empresa_id=empresa_id)
        if not df.empty:
            for _, r in df.iterrows():
                label = f"{r['id']} - {r['nombre']} ({r.get('estado', '')})"
                opciones[label] = r["id"]
    return opciones


def render() -> None:
    st.header("🔍 Auditorías en Terreno y Checklist de Seguridad")

    df_empresas = get_empresas_df()
    if df_empresas.empty:
        st.warning("⚠️ Debes registrar empresas antes de poder realizar auditorías.")
        return

    tab_lista, tab_crear = st.tabs(["📋 Historial de Auditorías", "➕ Nueva Auditoría en Terreno"])
    empresa_map = {
        f"{r['id']} - {r['nombre']} ({r['rut']})": r["id"]
        for _, r in df_empresas.iterrows()
    }
    PREGUNTAS = get_preguntas()
    OPCIONES  = opciones_respuesta()

    # ── Nueva auditoría ───────────────────────────────────────────────────────
    with tab_crear:
        st.subheader("Formulario de Auditoría en Terreno")

        with st.form("form_nueva_visita"):
            col_v1, col_v2, col_v3 = st.columns(3)
            with col_v1:
                vis_empresa_key = st.selectbox("Empresa Auditada *", list(empresa_map.keys()))
            with col_v2:
                vis_fecha = st.date_input("Fecha de Visita *", value=date.today())
            with col_v3:
                vis_auditor = st.text_input("Nombre del Auditor *", placeholder="Ej. Gonzalo Vega (Lead Auditor)")

            col_ev, col_tv = st.columns(2)
            with col_ev:
                eid_seleccionado = empresa_map[vis_empresa_key]
                eval_ops = _build_eval_options(eid_seleccionado)
                eval_key = st.selectbox("Evaluación GRC (recomendado para registros nuevos)", list(eval_ops.keys()))
                evaluacion_id_form = eval_ops[eval_key]
            with col_tv:
                tipo_visita_sel = st.selectbox("Tipo de Visita", TIPOS_VISITA)

            st.markdown("#### 📝 Checklist de Seguridad de la Información (15 Puntos)")
            st.caption("Selecciona el estado de cumplimiento de cada control. **Sí = 1 pto**, **No = 0 ptos**, **N/A = 0 ptos**.")

            respuestas_checklist = {}
            for idx, pregunta in enumerate(PREGUNTAS, start=1):
                resp = st.radio(
                    pregunta,
                    options=OPCIONES,
                    index=1,   # default: "No"
                    horizontal=True,
                    key=f"chk_q_{idx}",
                )
                respuestas_checklist[pregunta] = resp

            st.markdown("---")
            vis_observaciones = st.text_area(
                "Observaciones y Hallazgos Principales",
                placeholder="Anotaciones de la reunión, evidencias pendientes, riesgos detectados...",
                height=100,
            )

            btn_guardar = st.form_submit_button("💾 Guardar Auditoría", use_container_width=True, type="primary")

            if btn_guardar:
                if not vis_auditor or not vis_auditor.strip():
                    st.error("El nombre del auditor es obligatorio.")
                else:
                    puntaje = calcular_puntaje(respuestas_checklist)
                    eid = empresa_map[vis_empresa_key]
                    ok, msg = add_visita(
                        empresa_id=eid,
                        evaluacion_id=evaluacion_id_form,
                        fecha_visita=vis_fecha,
                        tipo_visita=tipo_visita_sel,
                        auditor=vis_auditor,
                        checklist_dict=respuestas_checklist,
                        puntaje=puntaje,
                        observaciones=vis_observaciones,
                    )
                    if ok:
                        porcentaje = calcular_porcentaje(puntaje)
                        st.success(
                            f"✅ {msg} Resultado: **{puntaje}/15 — {nivel_cumplimiento(porcentaje)}**"
                        )
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    # ── Historial ─────────────────────────────────────────────────────────────
    with tab_lista:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_emp = st.selectbox(
                "Filtrar por empresa:",
                ["Todas las empresas"] + list(empresa_map.keys()),
                key="vis_filtro_empresa",
            )
        with col_f2:
            emp_id_filtro = empresa_map[filtro_emp] if filtro_emp != "Todas las empresas" else None
            eval_ops_filt = {"Todas las evaluaciones": None}
            if emp_id_filtro:
                df_evals = get_evaluaciones_df(empresa_id=emp_id_filtro)
                if not df_evals.empty:
                    for _, r in df_evals.iterrows():
                        eval_ops_filt[f"{r['id']} - {r['nombre']}"] = r["id"]
            filtro_eval_key = st.selectbox("Filtrar por evaluación:", list(eval_ops_filt.keys()), key="vis_filtro_eval")
            eval_id_filtro = eval_ops_filt[filtro_eval_key]

        df_visitas = get_visitas_df(empresa_id=emp_id_filtro, evaluacion_id=eval_id_filtro)

        if df_visitas.empty:
            st.info("No hay auditorías registradas para el filtro seleccionado.")
            return

        df_vis_view = df_visitas[[
            "id", "empresa", "fecha_visita", "tipo_visita", "auditor",
            "puntaje", "evaluacion_nombre", "observaciones",
        ]].copy()
        df_vis_view["Cumplimiento"] = df_vis_view["puntaje"].apply(
            lambda p: nivel_cumplimiento(calcular_porcentaje(int(p or 0)))
        )
        st.dataframe(
            df_vis_view[["id", "empresa", "fecha_visita", "tipo_visita", "auditor", "Cumplimiento", "evaluacion_nombre", "observaciones"]],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")
        st.subheader("🔍 Detalle del Checklist de Auditoría")
        vis_opciones = {
            f"ID {r['id']} — {r['empresa']} ({r['fecha_visita']}) {r.get('tipo_visita', '')}": r["id"]
            for _, r in df_visitas.iterrows()
        }
        vis_sel_str = st.selectbox("Selecciona una visita para ver el desglose:", list(vis_opciones.keys()))
        vis_sel_id  = vis_opciones[vis_sel_str]
        v_row = df_visitas[df_visitas["id"] == vis_sel_id].iloc[0]

        with st.expander(f"📊 Desglose: Auditoría #{vis_sel_id}", expanded=True):
            p   = int(v_row["puntaje"] or 0)
            pct = calcular_porcentaje(p)
            dc1, dc2 = st.columns(2)
            with dc1:
                st.metric("Puntaje Obtenido", f"{p} de 15 controles")
            with dc2:
                st.metric("Nivel de Cumplimiento", nivel_cumplimiento(pct))

            chk_data = v_row["checklist_seguridad"]
            if isinstance(chk_data, str):
                try:
                    chk_data = json.loads(chk_data)
                except Exception:
                    chk_data = {}
            elif not isinstance(chk_data, dict):
                chk_data = {}

            col_q1, col_q2 = st.columns(2)
            items = list(chk_data.items())
            mitad = len(items) // 2
            with col_q1:
                for preg, r in items[:mitad]:
                    st.write(f"{icono_respuesta(r)} **{preg}**: `{r}`")
            with col_q2:
                for preg, r in items[mitad:]:
                    st.write(f"{icono_respuesta(r)} **{preg}**: `{r}`")

            if st.button("🗑️ Eliminar esta Auditoría", key=f"del_vis_{vis_sel_id}", type="secondary"):
                ok, msg = delete_visita(vis_sel_id)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
