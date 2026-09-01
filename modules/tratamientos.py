"""
Módulo Tratamientos (ROPA) — Registro de Actividades de Tratamiento.
Fase 1: añade campo evaluacion_id opcional al formulario.
Los tratamientos históricos sin evaluacion_id siguen siendo visibles y editables.
"""

import streamlit as st

from db.repositories.empresas import get_empresas_df
from db.repositories.evaluaciones import get_evaluaciones_df
from db.repositories.tratamientos import (
    add_tratamiento,
    update_tratamiento,
    delete_tratamiento,
    get_tratamientos_df,
)
from utils.constants import BASES_LEGALES, TRANSFERENCIAS_OPCIONES


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
    st.header("📋 Registro de Actividades de Tratamiento (ROPA)")

    df_empresas = get_empresas_df()
    if df_empresas.empty:
        st.warning("⚠️ Primero debes registrar al menos una empresa antes de crear tratamientos.")
        return

    tab_lista, tab_crear = st.tabs(["📋 Listado de Tratamientos", "➕ Registrar Nuevo Tratamiento"])
    empresa_map = {
        f"{r['id']} - {r['nombre']} ({r['rut']})": r["id"]
        for _, r in df_empresas.iterrows()
    }

    # ── Crear tratamiento ─────────────────────────────────────────────────────
    with tab_crear:
        st.subheader("Nuevo Tratamiento de Datos")
        with st.form("form_crear_tratamiento", clear_on_submit=True):
            empresa_key = st.selectbox("Empresa Responsable *", list(empresa_map.keys()))
            eid_form = empresa_map[empresa_key]

            # Evaluación (opcional — obligatorio solo para registros nuevos desde UI)
            eval_ops = _build_eval_options(eid_form)
            eval_key = st.selectbox(
                "Evaluación GRC (obligatoria para registros nuevos; 'Sin evaluación' solo para historial)",
                list(eval_ops.keys()),
            )
            evaluacion_id_form = eval_ops[eval_key]

            nombre_trat = st.text_input(
                "Nombre del Tratamiento *",
                placeholder="Ej. Gestión de Nómina y Recursos Humanos",
            )

            col_t1, col_t2 = st.columns(2)
            with col_t1:
                base_legal     = st.selectbox("Base Legal de Licitud *", BASES_LEGALES)
                datos_personales = st.text_area(
                    "Categorías de Datos Personales",
                    placeholder="Ej. Nombre, RUT, cuenta bancaria, domicilio, remuneración...",
                    height=80,
                )
                responsables = st.text_input(
                    "Responsables del Tratamiento",
                    placeholder="Ej. Gerencia de RRHH / DPO",
                )
            with col_t2:
                transferencias = st.selectbox("Transferencias Internacionales", TRANSFERENCIAS_OPCIONES)
                descripcion    = st.text_area(
                    "Descripción y Finalidad del Tratamiento",
                    placeholder="Ej. Procesamiento y pago de remuneraciones...",
                    height=80,
                )
                encargados = st.text_input(
                    "Encargados del Tratamiento (Proveedores)",
                    placeholder="Ej. Software RRHH en la nube (Talana, Buk, etc.)",
                )

            submitted = st.form_submit_button("💾 Guardar Tratamiento", use_container_width=True, type="primary")
            if submitted:
                if not nombre_trat or not nombre_trat.strip():
                    st.error("El nombre del tratamiento es obligatorio.")
                else:
                    ok, msg = add_tratamiento(
                        eid_form, evaluacion_id_form, nombre_trat, descripcion,
                        base_legal, datos_personales, responsables, encargados, transferencias,
                    )
                    if ok:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    # ── Listado ───────────────────────────────────────────────────────────────
    with tab_lista:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_emp = st.selectbox(
                "🔍 Filtrar por Empresa:",
                ["Todas las empresas"] + list(empresa_map.keys()),
                key="trat_filtro_empresa",
            )
        with col_f2:
            filtro_eval_label = "Todas las evaluaciones"
            emp_id_filtro = empresa_map[filtro_emp] if filtro_emp != "Todas las empresas" else None
            eval_ops_filtro = {"Todas las evaluaciones": None}
            if emp_id_filtro:
                df_evals = get_evaluaciones_df(empresa_id=emp_id_filtro)
                if not df_evals.empty:
                    for _, r in df_evals.iterrows():
                        eval_ops_filtro[f"{r['id']} - {r['nombre']}"] = r["id"]
            filtro_eval_key = st.selectbox("🔍 Filtrar por Evaluación:", list(eval_ops_filtro.keys()), key="trat_filtro_eval")
            eval_id_filtro = eval_ops_filtro[filtro_eval_key]

        df_trat = get_tratamientos_df(empresa_id=emp_id_filtro, evaluacion_id=eval_id_filtro)

        if df_trat.empty:
            st.info("No hay tratamientos registrados para el filtro seleccionado.")
            return

        st.dataframe(
            df_trat[[
                "id", "empresa", "nombre_tratamiento", "base_legal",
                "datos_personales", "responsables", "transferencias",
                "evaluacion_nombre", "created_at",
            ]],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")
        st.subheader("⚙️ Detalle y Edición de Tratamiento")
        trat_dict = {
            f"{r['id']} - {r['nombre_tratamiento']} ({r['empresa']})": r["id"]
            for _, r in df_trat.iterrows()
        }
        trat_sel_key = st.selectbox("Selecciona un tratamiento:", list(trat_dict.keys()))
        trat_sel_id  = trat_dict[trat_sel_key]
        t_row = df_trat[df_trat["id"] == trat_sel_id].iloc[0]

        with st.expander(f"🔍 Detalle completo: {t_row['nombre_tratamiento']}", expanded=True):
            st.markdown(f"**Empresa:** {t_row['empresa']} ({t_row['rut_empresa']})")
            st.markdown(f"**Evaluación:** {t_row['evaluacion_nombre'] or '— (sin evaluación asignada)'}")
            st.markdown(f"**Base Legal:** `{t_row['base_legal']}`")
            st.markdown(f"**Finalidad / Descripción:** {t_row['descripcion'] or 'No especificado'}")
            st.markdown(f"**Datos Tratados:** {t_row['datos_personales'] or 'No especificado'}")
            st.markdown(f"**Responsables:** {t_row['responsables'] or 'No especificado'}")
            st.markdown(f"**Encargados:** {t_row['encargados'] or 'No especificado'}")
            st.markdown(f"**Transferencias Internacionales:** {t_row['transferencias'] or 'No especificado'}")

            if st.button("🗑️ Eliminar este Tratamiento", key=f"del_trat_{trat_sel_id}", type="secondary"):
                ok, msg = delete_tratamiento(trat_sel_id)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
