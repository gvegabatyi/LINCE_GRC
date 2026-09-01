"""
Módulo Dashboard — Panel de Control GRC y Estado MPI (Fase 2A).
Muestra métricas consolidadas y el indicador interno de completitud documental del MPI.
"""

import streamlit as st
import pandas as pd

from db.repositories.empresas import get_empresas_df
from db.repositories.evaluaciones import get_evaluaciones_df
from db.repositories.tratamientos import get_tratamientos_df
from db.repositories.visitas import get_visitas_df
from services.mpi_service import calcular_completitud_mpi
from utils.constants import (
    ESTADO_EVALUACION_DISPLAY,
    AVISO_COMPLETITUD_DOCUMENTAL,
    semaforo_porcentaje,
)
from services.checklist_service import calcular_porcentaje, nivel_cumplimiento


def render() -> None:
    st.header("📊 Panel de Control GRC")
    st.caption("Lince GRC — Gobierno, Riesgo y Cumplimiento (Foco inicial: Ley N° 21.719 / Decreto N° 662)")

    df_emp  = get_empresas_df()
    df_eval = get_evaluaciones_df()
    df_trat = get_tratamientos_df()
    df_vis  = get_visitas_df()

    # ── Métricas principales ──────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric("🏢 Empresas", len(df_emp))
    with c2:
        st.metric("📁 Evaluaciones GRC", len(df_eval))
    with c3:
        st.metric("📋 Tratamientos (RAT)", len(df_trat))
    with c4:
        st.metric("🔍 Auditorías", len(df_vis))
    with c5:
        if not df_vis.empty and "fecha_visita" in df_vis.columns:
            ultima = str(df_vis.iloc[0]["fecha_visita"])
            empresa_vis = str(df_vis.iloc[0].get("empresa", ""))
            st.metric("🗓️ Última Visita", ultima, delta=empresa_vis, delta_color="off")
        else:
            st.metric("🗓️ Última Visita", "Sin registros")

    st.markdown("---")

    # ==========================================================================
    # SECCIÓN FASE 2A: COMPLETITUD DOCUMENTAL DEL MPI
    # ==========================================================================
    st.subheader("🛡️ Estado de Completitud Documental del MPI (Decreto N° 662)")
    st.caption(AVISO_COMPLETITUD_DOCUMENTAL)

    if not df_emp.empty:
        empresa_map = {f"{r['id']} - {r['nombre']} ({r['rut']})": r["id"] for _, r in df_emp.iterrows()}
        emp_sel_label = st.selectbox("Selecciona una empresa para revisar su estado MPI:", list(empresa_map.keys()), key="dash_mpi_emp")
        emp_id = empresa_map[emp_sel_label]

        info_mpi = calcular_completitud_mpi(emp_id)
        pct = info_mpi["porcentaje"]

        col_m1, col_m2 = st.columns([1, 2])
        with col_m1:
            st.metric("Nivel de Completitud Fase 2A", f"{pct:.1f}%", delta=semaforo_porcentaje(pct), delta_color="off")
            st.progress(int(pct), text=f"{pct:.0f}% completado")

        with col_m2:
            st.markdown("##### Desglose de Requisitos Documentales (Art. 3 Decreto N° 662):")
            reqs = info_mpi["requisitos"]
            c_r1, c_r2 = st.columns(2)
            with c_r1:
                st.markdown(f"{'✅' if reqs['perfil_activo'] else '❌'} **Perfil MPI y Rep. Legal (Art. 3 a)**")
                st.markdown(f"{'✅' if reqs['delegado_activo'] else '❌'} **Delegado DPD Designado (Arts. 3 b, 6 y 11)**")
                st.markdown(f"{'✅' if reqs['rat_registrado'] else '❌'} **Tratamientos en RAT (Art. 3 d)**")
            with c_r2:
                st.markdown(f"{'✅' if reqs['rat_11_numerales_completos'] else '❌'} **11 Numerales del RAT Completos**")
                st.markdown(f"{'✅' if reqs['evidencia_vinculada'] else '❌'} **Evidencia de Respaldo Adjunta**")

            if info_mpi["detalles"]:
                with st.expander("⚠️ Pendientes para completar la documentación", expanded=False):
                    for det in info_mpi["detalles"]:
                        st.markdown(f"- {det}")
    else:
        st.info("Registra al menos una empresa para habilitar el seguimiento del MPI.")

    st.markdown("---")

    # ── Evaluaciones activas ──────────────────────────────────────────────────
    if not df_eval.empty:
        col_izq, col_der = st.columns([3, 2])

        with col_izq:
            st.subheader("📁 Evaluaciones GRC Activas")
            activas = df_eval[df_eval["estado"].isin(["en_progreso", "en_revision"])]
            if activas.empty:
                st.info("No hay evaluaciones en progreso. Las evaluaciones finalizadas o en borrador no se muestran aquí.")
            else:
                for _, row in activas.head(5).iterrows():
                    estado_label = ESTADO_EVALUACION_DISPLAY.get(row["estado"], row["estado"])
                    avance = float(row.get("porcentaje_avance") or 0)
                    with st.container():
                        st.markdown(
                            f"**{row['nombre']}** · {row['empresa']}  \n"
                            f"{estado_label} · Auditor: {row['auditor_responsable'] or '—'}"
                        )
                        st.progress(int(avance), text=f"{avance:.0f}% de avance")
                        st.markdown("")

        with col_der:
            st.subheader("📈 Tratamientos por Empresa")
            if not df_trat.empty:
                conteo = df_trat["empresa"].value_counts()
                st.bar_chart(conteo, color="#1E88E5")
            else:
                st.info("No hay tratamientos registrados.")
    else:
        col_izq, col_der = st.columns([3, 2])
        with col_izq:
            st.subheader("🏢 Últimas 5 Empresas Registradas")
            if not df_emp.empty:
                st.dataframe(
                    df_emp.head(5)[["id", "nombre", "rut", "contacto", "email", "created_at"]],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No hay empresas registradas. Ve al módulo **Empresas** para agregar la primera.")
        with col_der:
            st.subheader("📈 Tratamientos por Empresa")
            if not df_trat.empty:
                st.bar_chart(df_trat["empresa"].value_counts(), color="#1E88E5")
            else:
                st.info("No hay tratamientos registrados.")

    # ── Auditorías recientes ──────────────────────────────────────────────────
    if not df_vis.empty:
        st.markdown("---")
        st.subheader("🛡️ Últimas 5 Auditorías y Puntajes")
        vis_view = df_vis[
            ["empresa", "fecha_visita", "tipo_visita", "auditor", "puntaje", "observaciones"]
        ].head(5).copy()
        vis_view["Cumplimiento"] = vis_view["puntaje"].apply(
            lambda p: nivel_cumplimiento(calcular_porcentaje(int(p or 0)))
        )
        st.dataframe(
            vis_view[["empresa", "fecha_visita", "tipo_visita", "auditor", "Cumplimiento", "observaciones"]],
            use_container_width=True,
            hide_index=True,
        )
