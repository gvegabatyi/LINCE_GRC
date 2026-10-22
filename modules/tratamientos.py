"""
Módulo Tratamientos (RAT) — Registro de Actividades de Tratamiento.
Fase 2A: Implementación estricta de los 11 numerales normativos del Art. 3 letra d)
del Decreto N° 662 y separación de campos complementarios GRC.
"""

import streamlit as st

from db.repositories.empresas import get_empresas_df
from db.repositories.evaluaciones import get_evaluaciones_df
from db.repositories.evidencias import get_evidencias_df
from db.repositories.tratamientos import (
    add_tratamiento,
    update_tratamiento,
    delete_tratamiento,
    get_tratamientos_df,
)
from utils.constants import (
    RAT_NUMERALES_INFO,
    BASES_LEGALES,
    TRANSFERENCIAS_OPCIONES,
)


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


def _build_evidencia_options(empresa_id: int) -> dict:
    opciones = {"Sin evidencia adjunta": None}
    if empresa_id:
        df = get_evidencias_df(empresa_id=empresa_id)
        if not df.empty:
            for _, r in df.iterrows():
                desc = r.get("descripcion") or "Sin descripción"
                url = r.get("foto_url") or ""
                label = f"ID {r['id']} - {desc[:35]} ({url[:25]}...)"
                opciones[label] = r["id"]
    return opciones


def _indice_empresa_activa(empresa_map: dict) -> int:
    """Posición de la empresa activa de la sesión en el selector (0 si no hay)."""
    activa = st.session_state.get("empresa_activa_id")
    ids = list(empresa_map.values())
    return ids.index(activa) if activa in ids else 0


def render() -> None:
    st.header("📋 Registro de Actividades de Tratamiento (RAT)")
    st.caption("Estructura conforme al **Art. 3 letra d), numerales i a xi del Decreto N° 662** (Ministerio de Hacienda)")

    df_empresas = get_empresas_df()
    if df_empresas.empty:
        st.warning("⚠️ Primero debes registrar al menos una empresa antes de crear tratamientos.")
        return

    tab_lista, tab_crear = st.tabs(["📋 Listado de Tratamientos (RAT)", "➕ Registrar Nuevo Tratamiento (Art. 3 d)"])
    empresa_map = {
        f"{r['id']} - {r['nombre']} ({r['rut']})": r["id"]
        for _, r in df_empresas.iterrows()
    }

    # ==========================================================================
    # CREAR TRATAMIENTO (RAT AMPLIO)
    # ==========================================================================
    with tab_crear:
        st.subheader("Nuevo Registro de Actividad de Tratamiento (Art. 3 letra d)")
        # Fuera del form: al cambiar de empresa deben recalcularse evaluaciones y evidencias
        empresa_keys = list(empresa_map.keys())
        empresa_key = st.selectbox(
            "Empresa Responsable *",
            empresa_keys,
            index=_indice_empresa_activa(empresa_map),
            key="rat_crear_emp",
        )
        eid_form = empresa_map[empresa_key]
        eval_ops = _build_eval_options(eid_form)
        evidencias_ops = _build_evidencia_options(eid_form)

        with st.form("form_crear_tratamiento", clear_on_submit=True):

            st.markdown("---")
            st.markdown("### 📌 CAMPOS OBLIGATORIOS DEL ART. 3 LETRA d) (Numerales i al xi)")

            # Numeral i y ii
            col1, col2 = st.columns(2)
            with col1:
                rat_i = st.text_area(
                    RAT_NUMERALES_INFO["i"]["label"] + " *",
                    placeholder=RAT_NUMERALES_INFO["i"]["placeholder"],
                    height=85,
                    help=RAT_NUMERALES_INFO["i"]["referencia"],
                )
            with col2:
                rat_ii = st.text_input(
                    RAT_NUMERALES_INFO["ii"]["label"] + " *",
                    placeholder=RAT_NUMERALES_INFO["ii"]["placeholder"],
                    help=RAT_NUMERALES_INFO["ii"]["referencia"],
                )
                rat_iii = st.text_input(
                    RAT_NUMERALES_INFO["iii"]["label"] + " *",
                    placeholder=RAT_NUMERALES_INFO["iii"]["placeholder"],
                    help=RAT_NUMERALES_INFO["iii"]["referencia"],
                )

            # Numeral iv y v
            col3, col4 = st.columns(2)
            with col3:
                rat_iv = st.text_area(
                    RAT_NUMERALES_INFO["iv"]["label"] + " *",
                    placeholder=RAT_NUMERALES_INFO["iv"]["placeholder"],
                    height=85,
                    help=RAT_NUMERALES_INFO["iv"]["referencia"],
                )
            with col4:
                rat_v = st.text_area(
                    RAT_NUMERALES_INFO["v"]["label"] + " *",
                    placeholder=RAT_NUMERALES_INFO["v"]["placeholder"],
                    height=85,
                    help=RAT_NUMERALES_INFO["v"]["referencia"],
                )

            # Numeral vi y vii
            col5, col6 = st.columns(2)
            with col5:
                rat_vi = st.text_area(
                    RAT_NUMERALES_INFO["vi"]["label"] + " *",
                    placeholder=RAT_NUMERALES_INFO["vi"]["placeholder"],
                    height=85,
                    help=RAT_NUMERALES_INFO["vi"]["referencia"],
                )
            with col6:
                rat_vii = st.text_area(
                    RAT_NUMERALES_INFO["vii"]["label"] + " *",
                    placeholder=RAT_NUMERALES_INFO["vii"]["placeholder"],
                    height=85,
                    help=RAT_NUMERALES_INFO["vii"]["referencia"],
                )

            # Numeral viii y ix
            col7, col8 = st.columns(2)
            with col7:
                rat_viii = st.text_area(
                    RAT_NUMERALES_INFO["viii"]["label"] + " *",
                    placeholder=RAT_NUMERALES_INFO["viii"]["placeholder"],
                    height=85,
                    help=RAT_NUMERALES_INFO["viii"]["referencia"],
                )
            with col8:
                rat_ix = st.text_area(
                    RAT_NUMERALES_INFO["ix"]["label"] + " *",
                    placeholder=RAT_NUMERALES_INFO["ix"]["placeholder"],
                    height=85,
                    help=RAT_NUMERALES_INFO["ix"]["referencia"],
                )

            # Numeral x y xi
            col9, col10 = st.columns(2)
            with col9:
                rat_x = st.text_area(
                    RAT_NUMERALES_INFO["x"]["label"] + " *",
                    placeholder=RAT_NUMERALES_INFO["x"]["placeholder"],
                    height=85,
                    help=RAT_NUMERALES_INFO["x"]["referencia"],
                )
            with col10:
                rat_xi = st.text_area(
                    RAT_NUMERALES_INFO["xi"]["label"] + " *",
                    placeholder=RAT_NUMERALES_INFO["xi"]["placeholder"],
                    height=85,
                    help=RAT_NUMERALES_INFO["xi"]["referencia"],
                )

            st.markdown("---")
            st.markdown("### ⚙️ CAMPOS COMPLEMENTARIOS GRC (Opcionales)")
            with st.expander("Ver campos complementarios de gestión GRC", expanded=False):
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    nombre_trat = st.text_input(
                        "Nombre Descriptivo Interno del Tratamiento [Complementario GRC]",
                        placeholder="Ej. Nómina de Trabajadores y Liquidaciones",
                    )
                    descripcion_op = st.text_area(
                        "Descripción Operativa [Complementario GRC]",
                        placeholder="Resumen interno de la operativa del tratamiento",
                        height=70,
                    )
                    base_legal_std = st.selectbox(
                        "Base Legal General [Complementario GRC]",
                        BASES_LEGALES,
                    )
                with col_g2:
                    responsables_int = st.text_input(
                        "Responsables Internos [Complementario GRC]",
                        placeholder="Ej. Gerencia de Personas",
                    )
                    encargados_int = st.text_input(
                        "Encargados del Tratamiento / Proveedores [Complementario GRC]",
                        placeholder="Ej. Proveedor de Software SaaS RRHH",
                    )
                    transf_std = st.selectbox(
                        "Transferencias Internacionales [Complementario GRC]",
                        TRANSFERENCIAS_OPCIONES,
                    )
                eval_key = st.selectbox("Evaluación GRC Vinculada", list(eval_ops.keys()))
                ev_key = st.selectbox("Evidencia Documental Vinculada (Enlace)", list(evidencias_ops.keys()))

            submitted = st.form_submit_button("💾 Guardar Tratamiento en RAT", use_container_width=True, type="primary")
            if submitted:
                # Validar que al menos las finalidades y tipos de datos estén indicados
                if not rat_v or not rat_v.strip() or not rat_i or not rat_i.strip():
                    st.error("Debes completar al menos los Fines del tratamiento (num. v) y el Tipo de datos tratados (num. i) del Art. 3 letra d).")
                else:
                    nombre_final = nombre_trat.strip() if nombre_trat and nombre_trat.strip() else f"Tratamiento: {rat_v[:40]}..."
                    ok, msg = add_tratamiento(
                        empresa_id=eid_form,
                        evaluacion_id=eval_ops[eval_key],
                        nombre_tratamiento=nombre_final,
                        descripcion=descripcion_op,
                        base_legal=base_legal_std,
                        datos_personales=rat_i,
                        responsables=responsables_int,
                        encargados=encargados_int,
                        transferencias=transf_std,
                        rat_tipo_datos_sensibles=rat_i,
                        rat_ambito_territorial=rat_ii,
                        rat_bases_datos_administradas=rat_iii,
                        rat_categorias_titulares=rat_iv,
                        rat_finalidades=rat_v,
                        rat_fuente_datos_acceso_publico=rat_vi,
                        rat_base_licitud_interes_legitimo=rat_vii,
                        rat_destinatarios_cesiones=rat_viii,
                        rat_transferencias_internacionales_art27=rat_ix,
                        rat_plazo_condicion_supresion=rat_x,
                        rat_decisiones_automatizadas_perfilamiento=rat_xi,
                        evidencia_id=evidencias_ops[ev_key],
                    )
                    if ok:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    # ==========================================================================
    # LISTADO Y DETALLE
    # ==========================================================================
    with tab_lista:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_emp = st.selectbox(
                "🔍 Filtrar por Empresa:",
                ["Todas las empresas"] + list(empresa_map.keys()),
                key="trat_filtro_empresa",
            )
        with col_f2:
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
                "id", "empresa", "nombre_tratamiento", "rat_finalidades",
                "rat_base_licitud_interes_legitimo", "rat_tipo_datos_sensibles",
                "rat_categorias_titulares", "evaluacion_nombre", "created_at"
            ]],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")
        st.subheader("⚙️ Detalle de los 11 Numerales Normativos (Art. 3 d)")
        trat_dict = {
            f"{r['id']} - {r['nombre_tratamiento']} ({r['empresa']})": r["id"]
            for _, r in df_trat.iterrows()
        }
        trat_sel_key = st.selectbox("Selecciona un tratamiento para ver o editar:", list(trat_dict.keys()))
        trat_sel_id  = trat_dict[trat_sel_key]
        t_row = df_trat[df_trat["id"] == trat_sel_id].iloc[0]

        with st.expander(f"🔍 Ficha Completa del RAT: {t_row['nombre_tratamiento']}", expanded=True):
            st.markdown(f"**Empresa:** {t_row['empresa']} ({t_row['rut_empresa']}) | **Evaluación:** {t_row['evaluacion_nombre'] or 'Sin evaluación'}")
            st.markdown("---")
            st.markdown("**11 Numerales del Art. 3 letra d) (Decreto N° 662):**")

            c_d1, c_d2 = st.columns(2)
            with c_d1:
                st.markdown(f"**i. Tipo de datos / sensibles:** {t_row['rat_tipo_datos_sensibles'] or 'No especificado'}")
                st.markdown(f"**ii. Ámbito territorial:** {t_row['rat_ambito_territorial'] or 'No especificado'}")
                st.markdown(f"**iii. Bases de datos administradas:** {t_row['rat_bases_datos_administradas'] or 'No especificado'}")
                st.markdown(f"**iv. Categorías de titulares:** {t_row['rat_categorias_titulares'] or 'No especificado'}")
                st.markdown(f"**v. Finalidades del tratamiento:** {t_row['rat_finalidades'] or 'No especificado'}")
                st.markdown(f"**vi. Fuente de procedencia / acceso público:** {t_row['rat_fuente_datos_acceso_publico'] or 'No especificado'}")
            with c_d2:
                st.markdown(f"**vii. Base de licitud / Interés legítimo:** {t_row['rat_base_licitud_interes_legitimo'] or 'No especificado'}")
                st.markdown(f"**viii. Destinatarios / Cesiones:** {t_row['rat_destinatarios_cesiones'] or 'No especificado'}")
                st.markdown(f"**ix. Transferencias internacionales (Art. 27):** {t_row['rat_transferencias_internacionales_art27'] or 'No especificado'}")
                st.markdown(f"**x. Plazo / Condición de supresión:** {t_row['rat_plazo_condicion_supresion'] or 'No especificado'}")
                st.markdown(f"**xi. Decisiones automatizadas / Perfilamiento:** {t_row['rat_decisiones_automatizadas_perfilamiento'] or 'No especificado'}")

            st.markdown("---")
            st.markdown(f"**Evidencia adjunta:** {t_row['evidencia_descripcion'] or 'Sin evidencia vinculada'}")
            if t_row.get("evidencia_url"):
                st.markdown(f"🔗 [Abrir Evidencia Externa]({t_row['evidencia_url']})")

            if st.button("🗑️ Eliminar este Tratamiento", key=f"del_trat_{trat_sel_id}", type="secondary"):
                ok, msg = delete_tratamiento(trat_sel_id)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
