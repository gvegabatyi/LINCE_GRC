"""
Módulo Evidencias — Registro y gestión de evidencias.
Fase 1: añade campo evaluacion_id opcional.
Las evidencias se registran como URLs externas (Google Drive, SharePoint, etc.).
No se almacenan archivos binarios en la base de datos ni en el servidor.
"""

import streamlit as st

from db.repositories.visitas import get_visitas_df
from db.repositories.evaluaciones import get_evaluaciones_df
from db.repositories.evidencias import (
    add_evidencia,
    delete_evidencia,
    get_evidencias_df,
)
from db.repositories.empresas import get_empresas_df


def render() -> None:
    st.header("Registro y Gestión de Evidencias")
    st.caption(
        "Las evidencias se registran como URLs externas (Google Drive, SharePoint, OneDrive). "
        "No se almacenan archivos en la base de datos."
    )

    df_visitas = get_visitas_df()
    if df_visitas.empty:
        st.warning("Primero debes registrar visitas/auditorías para poder adjuntarles evidencias.")
        return

    tab_lista, tab_crear = st.tabs(["Evidencias Registradas", "Adjuntar Nueva Evidencia"])
    visita_map = {
        f"Auditoría #{r['id']} — {r['empresa']} ({r['fecha_visita']})": r["id"]
        for _, r in df_visitas.iterrows()
    }

    # ── Adjuntar evidencia ────────────────────────────────────────────────────
    with tab_crear:
        st.subheader("Adjuntar Evidencia a una Auditoría")
        with st.form("form_crear_evidencia", clear_on_submit=True):
            vis_ev_key = st.selectbox("Selecciona la Visita Asociada *", list(visita_map.keys()))
            vid_seleccionado = visita_map[vis_ev_key]

            # Evaluación opcional: prefiltrar según la visita seleccionada
            v_row = df_visitas[df_visitas["id"] == vid_seleccionado].iloc[0]
            eval_options = {"Sin evaluación asignada": None}
            df_evals = get_evaluaciones_df()
            if not df_evals.empty:
                for _, r in df_evals.iterrows():
                    eval_options[f"{r['id']} - {r['nombre']}"] = r["id"]

            # Preseleccionar la evaluación de la visita si existe
            eval_default_key = "Sin evaluación asignada"
            if v_row.get("evaluacion_id") is not None:
                for k, v in eval_options.items():
                    if v == v_row["evaluacion_id"]:
                        eval_default_key = k
                        break
            eval_keys = list(eval_options.keys())
            eval_idx = eval_keys.index(eval_default_key) if eval_default_key in eval_keys else 0
            eval_sel_key = st.selectbox("Evaluación GRC (opcional)", eval_keys, index=eval_idx)
            evaluacion_id_form = eval_options[eval_sel_key]

            descripcion_ev = st.text_area(
                "Descripción de la Evidencia *",
                placeholder="Ej. Foto del rack de servidores con chapa de seguridad...",
                height=80,
            )
            foto_url = st.text_input(
                "URL o Enlace de la Foto / Documento",
                placeholder="Ej. https://drive.google.com/... o https://sharepoint.com/...",
            )

            submitted_ev = st.form_submit_button("Guardar Evidencia", use_container_width=True, type="primary")
            if submitted_ev:
                if not descripcion_ev or not descripcion_ev.strip():
                    st.error("La descripción de la evidencia es obligatoria.")
                else:
                    ok, msg = add_evidencia(vid_seleccionado, evaluacion_id_form, descripcion_ev, foto_url)
                    if ok:
                        st.success(f"{msg}")
                        st.rerun()
                    else:
                        st.error(f"{msg}")

    # ── Listado ───────────────────────────────────────────────────────────────
    with tab_lista:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_vis = st.selectbox(
                "Filtrar por Auditoría:",
                ["Todas las auditorías"] + list(visita_map.keys()),
                key="ev_filtro_vis",
            )
        with col_f2:
            eval_ops_filt = {"Todas las evaluaciones": None}
            df_evals_filt = get_evaluaciones_df()
            if not df_evals_filt.empty:
                for _, r in df_evals_filt.iterrows():
                    eval_ops_filt[f"{r['id']} - {r['nombre']}"] = r["id"]
            filtro_eval_key = st.selectbox("Filtrar por Evaluación:", list(eval_ops_filt.keys()), key="ev_filtro_eval")
            eval_id_filt = eval_ops_filt[filtro_eval_key]

        vid_filtro = visita_map[filtro_vis] if filtro_vis != "Todas las auditorías" else None
        df_evidencias = get_evidencias_df(visita_id=vid_filtro, evaluacion_id=eval_id_filt)

        if df_evidencias.empty:
            st.info("No hay evidencias registradas para el filtro seleccionado.")
            return

        st.dataframe(
            df_evidencias[["id", "visita_id", "empresa", "fecha_visita",
                           "descripcion", "foto_url", "evaluacion_nombre", "created_at"]],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")
        st.subheader("Galería y Detalle de Evidencias")
        for _, r in df_evidencias.iterrows():
            with st.container():
                st.markdown(
                    f"**Evidencia #{r['id']}** | Auditoría #{r['visita_id']} — "
                    f"{r['empresa']} ({r['fecha_visita']})"
                )
                if r.get("evaluacion_nombre"):
                    st.caption(f"Evaluación: {r['evaluacion_nombre']}")
                st.write(f"{r['descripcion']}")
                if r["foto_url"]:
                    st.markdown(f"[Abrir Enlace de Evidencia]({r['foto_url']})")
                    if any(r["foto_url"].lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
                        st.image(r["foto_url"], width=400)
                if st.button("Eliminar Evidencia", key=f"del_ev_{r['id']}"):
                    ok, msg = delete_evidencia(r["id"])
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                st.markdown("---")
