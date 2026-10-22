"""
Módulo Dashboard — Panel de control de cumplimiento integral.
Métricas consolidadas, plazos de derechos de los titulares, evaluaciones,
distribución del RAT y auditorías recientes.
"""

import streamlit as st
import pandas as pd

from db.repositories.derechos import get_solicitudes_df, resumen_plazos
from db.repositories.empresas import get_empresas_df
from db.repositories.evaluaciones import get_evaluaciones_df
from db.repositories.tratamientos import get_tratamientos_df
from db.repositories.visitas import get_visitas_df
from utils.constants import (
    ESTADO_EVALUACION_DISPLAY,
)
from services.checklist_service import calcular_porcentaje, nivel_cumplimiento


def render() -> None:
    st.header("◈ Panel de Control GRC")
    st.caption("LINCE GRC // Cumplimiento integral de protección de datos personales · Ley N° 19.628 modificada por la Ley N° 21.719 · Ley N° 21.663")

    df_emp  = get_empresas_df()
    df_eval = get_evaluaciones_df()
    df_trat = get_tratamientos_df()
    df_vis  = get_visitas_df()

    # ── Métricas principales ──────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric("◈ Empresas", len(df_emp))
    with c2:
        st.metric("◬ Evaluaciones GRC", len(df_eval))
    with c3:
        st.metric("☷ Tratamientos (RAT)", len(df_trat))
    with c4:
        st.metric("⌖ Auditorías", len(df_vis))
    with c5:
        if not df_vis.empty and "fecha_visita" in df_vis.columns:
            ultima = str(df_vis.iloc[0]["fecha_visita"])
            empresa_vis = str(df_vis.iloc[0].get("empresa", ""))
            st.metric("◷ Última Visita", ultima, delta=empresa_vis if empresa_vis else None, delta_color="off")
        else:
            st.metric("◷ Última Visita", "Sin registros")

    st.markdown("---")

    # ==========================================================================
    # DERECHOS DE LOS TITULARES: PLAZOS LEGALES (todas las empresas)
    # ==========================================================================
    st.subheader("⚖ Solicitudes de Derechos de los Titulares")
    df_sol = get_solicitudes_df()
    resumen = resumen_plazos(df_sol)
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("En plazo", resumen["en_plazo"])
    d2.metric("Por vencer", resumen["por_vencer"])
    d3.metric("Vencidas", resumen["vencida"])
    d4.metric("Respondidas", resumen["respondida"])
    if resumen["vencida"]:
        st.error(f"Hay {resumen['vencida']} solicitud(es) con plazo legal vencido. Revise el módulo ⚖ Derechos de los Titulares.")
    elif resumen["por_vencer"]:
        st.warning(f"Hay {resumen['por_vencer']} solicitud(es) próximas a vencer.")

    st.markdown("---")

    # ── Evaluaciones activas ──────────────────────────────────────────────────
    if not df_eval.empty:
        col_izq, col_der = st.columns([3, 2])

        with col_izq:
            st.subheader("▸ Evaluaciones GRC Activas")
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
            st.subheader("▸ Distribución RAT por Empresa")
            if not df_trat.empty:
                conteo = df_trat["empresa"].value_counts()
                st.bar_chart(conteo, color="#0EA5E9")
            else:
                st.info("No hay tratamientos registrados.")
    else:
        col_izq, col_der = st.columns([3, 2])
        with col_izq:
            st.subheader("▸ Empresas Registradas Recientes")
            if not df_emp.empty:
                st.dataframe(
                    df_emp.head(5)[["id", "nombre", "rut", "contacto", "email", "created_at"]],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No hay empresas registradas. Ve al módulo **Empresas** para agregar la primera.")
        with col_der:
            st.subheader("▸ Distribución RAT por Empresa")
            if not df_trat.empty:
                st.bar_chart(df_trat["empresa"].value_counts(), color="#0EA5E9")
            else:
                st.info("No hay tratamientos registrados.")

    # ── Auditorías recientes ──────────────────────────────────────────────────
    if not df_vis.empty:
        st.markdown("---")
        st.subheader("▸ Auditorías y Puntajes Recientes")
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
