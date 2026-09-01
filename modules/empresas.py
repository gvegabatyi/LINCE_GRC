"""
Módulo Empresas — Gestión de empresas del grupo / clientes.
Funcionalidad extraída de app.py sin cambios de comportamiento.
"""

import streamlit as st

from db.repositories.empresas import (
    add_empresa,
    update_empresa,
    delete_empresa,
    get_empresas_df,
)


def render() -> None:
    st.header("🏢 Gestión de Empresas del Grupo / Clientes")

    tab_lista, tab_crear = st.tabs(["📋 Listado de Empresas", "➕ Registrar Nueva Empresa"])

    # ── Crear empresa ─────────────────────────────────────────────────────────
    with tab_crear:
        st.subheader("Registrar Nueva Empresa")
        with st.form("form_crear_empresa", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                nombre   = st.text_input("Nombre / Razón Social *", placeholder="Ej. Serviphar Chile SpA")
                rut      = st.text_input("RUT *", placeholder="Ej. 76.123.456-7")
                direccion = st.text_input("Dirección", placeholder="Ej. Av. Providencia 1234, Santiago")
            with col_b:
                contacto = st.text_input("Persona de Contacto", placeholder="Ej. Juan Pérez")
                email    = st.text_input("Correo Electrónico", placeholder="Ej. contacto@empresa.cl")
                telefono = st.text_input("Teléfono", placeholder="Ej. +56 9 1234 5678")

            submitted = st.form_submit_button("💾 Guardar Empresa", use_container_width=True, type="primary")
            if submitted:
                if not nombre or not rut:
                    st.error("Por favor completa los campos obligatorios: **Nombre** y **RUT**.")
                else:
                    ok, msg = add_empresa(nombre, rut, direccion, contacto, email, telefono)
                    if ok:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    # ── Listado y acciones ────────────────────────────────────────────────────
    with tab_lista:
        buscador = st.text_input(
            "🔍 Buscar empresa por Nombre o RUT:",
            placeholder="Escribe para filtrar...",
        )
        df_empresas = get_empresas_df(search_term=buscador)

        if df_empresas.empty:
            st.info("No se encontraron empresas registradas.")
            return

        st.caption(f"Total: **{len(df_empresas)}** empresas encontradas.")
        st.dataframe(
            df_empresas[["id", "nombre", "rut", "contacto", "email", "telefono", "direccion", "created_at"]],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")
        st.subheader("⚙️ Acciones por Empresa")

        empresa_opciones = {
            f"{r['id']} - {r['nombre']} ({r['rut']})": r["id"]
            for _, r in df_empresas.iterrows()
        }
        seleccion_str = st.selectbox("Selecciona una empresa para gestionar:", list(empresa_opciones.keys()))
        empresa_sel_id = empresa_opciones[seleccion_str]
        empresa_data = df_empresas[df_empresas["id"] == empresa_sel_id].iloc[0]

        col_edit, col_del = st.columns([2, 1])

        with col_edit:
            with st.expander(f"✏️ Editar: {empresa_data['nombre']}", expanded=False):
                with st.form(f"form_edit_empresa_{empresa_sel_id}"):
                    e_nombre  = st.text_input("Nombre", value=empresa_data["nombre"])
                    e_rut     = st.text_input("RUT", value=empresa_data["rut"])
                    e_dir     = st.text_input("Dirección", value=empresa_data["direccion"] or "")
                    e_cont    = st.text_input("Contacto", value=empresa_data["contacto"] or "")
                    e_mail    = st.text_input("Email", value=empresa_data["email"] or "")
                    e_tel     = st.text_input("Teléfono", value=empresa_data["telefono"] or "")
                    if st.form_submit_button("Actualizar Cambios", type="primary"):
                        ok, msg = update_empresa(empresa_sel_id, e_nombre, e_rut, e_dir, e_cont, e_mail, e_tel)
                        if ok:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

        with col_del:
            with st.expander("🗑️ Eliminar Empresa"):
                st.warning(
                    "⚠️ **Atención:** Eliminar esta empresa borrará también sus "
                    "evaluaciones, tratamientos, visitas y evidencias vinculadas."
                )
                confirmar = st.checkbox(
                    "Confirmo que deseo eliminar permanentemente esta empresa.",
                    key=f"del_chk_{empresa_sel_id}",
                )
                if st.button(
                    "Eliminar Empresa Definitivamente",
                    type="secondary",
                    disabled=not confirmar,
                    key=f"del_btn_{empresa_sel_id}",
                ):
                    ok, msg = delete_empresa(empresa_sel_id)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
