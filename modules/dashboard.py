"""
Módulo Dashboard — Panel de Control GRC.
Muestra métricas consolidadas de empresas, evaluaciones, tratamientos,
visitas y últimas actividades. Compatible con la nueva estructura de evaluaciones.
"""

import streamlit as st
import pandas as pd

from db.repositories.empresas import get_empresas_df
from db.repositories.evaluaciones import get_evaluaciones_df
from db.repositories.tratamientos import get_tratamientos_df
from db.repositories.visitas import get_visitas_df
from utils.constants import ESTADO_EVALUACION_DISPLAY
from services.checklist_service import calcular_porcentaje, nivel_cumplimiento


def render() -> None:
    st.header("📊 Panel de Control GRC")

    df_emp  = get_empresas_df()
    df_eval = get_evaluaciones_df()
    df_trat = get_tratamientos_df()
    df_vis  = get_visitas_df()

    # ── Métricas principales ──────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric("🏢 Empresas", len(df_emp))
    with c2:
        st.metric("📁 Evaluaciones", len(df_eval))
    with c3:
        st.metric("📋 Tratamientos (ROPA)", len(df_trat))
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

    # ── Evaluaciones activas ──────────────────────────────────────────────────
    if not df_eval.empty:
        col_izq, col_der = st.columns([3, 2])

        with col_izq:
            st.subheader("📁 Evaluaciones Activas")
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
        # Si no hay evaluaciones, mostrar layout original
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

    # ── Resumen de evaluaciones ───────────────────────────────────────────────
    if not df_eval.empty:
        st.markdown("---")
        st.subheader("📁 Últimas 5 Evaluaciones")
        cols_display = ["empresa", "nombre", "tipo_evaluacion", "estado",
                        "auditor_responsable", "fecha_inicio", "porcentaje_avance"]
        cols_present = [c for c in cols_display if c in df_eval.columns]
        df_eval_view = df_eval[cols_present].head(5).copy()
        df_eval_view["estado"] = df_eval_view["estado"].map(
            lambda s: ESTADO_EVALUACION_DISPLAY.get(s, s)
        )
        st.dataframe(df_eval_view, use_container_width=True, hide_index=True)

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
