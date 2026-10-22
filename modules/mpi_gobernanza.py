"""
Módulo UI de Perfil MPI y Delegado de Protección de Datos (Fase 2A).
Implementa la gestión de gobernanza y trazabilidad conforme al Decreto N° 662.
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta

from db.repositories.empresas import get_empresas_df
from db.repositories.evidencias import get_evidencias_df
from db.repositories.mpi_gobernanza import (
    get_perfil_activo,
    get_perfiles_df,
    save_perfil_mpi,
    get_delegado_activo,
    get_delegados_df,
    save_delegado_dpd,
    get_referencias_normativas_df,
)
from utils.constants import (
    ESTADOS_MPI_INTERNOS,
    ESTADOS_MPI_INTERNOS_MAP,
    ESTADOS_MPI_OFICIALES,
    ESTADOS_MPI_OFICIALES_MAP,
    TIPOS_VINCULO_DELEGADO,
    AUTORIDADES_DESIGNACION_DPD,
    AVISO_ESTADOS_OFICIALES,
)


def _build_evidencia_options(empresa_id: int) -> dict:
    """Retorna dict {label: id} para evidencias de la empresa."""
    opciones = {"Sin evidencia adjunta": None}
    if empresa_id:
        df = get_evidencias_df(empresa_id=empresa_id)
        if not df.empty:
            for _, r in df.iterrows():
                desc = r.get("descripcion") or "Sin descripción"
                url = r.get("foto_url") or ""
                label = f"ID {r['id']} - {desc[:40]} ({url[:30]}...)"
                opciones[label] = r["id"]
    return opciones


def render() -> None:
    st.header("🛡️ Perfil MPI y Delegado de Protección de Datos")
    st.caption("Implementación de Gobernanza conforme al Decreto N° 662 (Ministerio de Hacienda / Ley N° 21.719)")

    df_empresas = get_empresas_df()
    if df_empresas.empty:
        st.warning("⚠️ Debes registrar al menos una empresa antes de configurar el Perfil MPI.")
        return

    empresa_map = {
        f"{r['id']} - {r['nombre']} ({r['rut']})": r["id"]
        for _, r in df_empresas.iterrows()
    }

    # Selector superior de empresa
    col_sel, _ = st.columns([2, 2])
    with col_sel:
        empresa_sel_label = st.selectbox("🏢 Selecciona la Empresa a gestionar:", list(empresa_map.keys()))
        empresa_id = empresa_map[empresa_sel_label]

    tab_perfil, tab_dpd, tab_normativa = st.tabs([
        "🏢 Perfil MPI (Art. 3 a)",
        "🛡️ Delegado DPD (Arts. 3 b, c; 6-13)",
        "📖 Trazabilidad Normativa (Decreto N° 662)",
    ])

    # ==========================================================================
    # PESTAÑA 1: PERFIL MPI
    # ==========================================================================
    with tab_perfil:
        st.subheader("Individualización del Responsable y Perfil del Modelo")
        st.info("📌 **Referencia:** Decreto N° 662, Art. 3 letra a) (Individualización del responsable y representante legal).")

        perfil_actual = get_perfil_activo(empresa_id)
        evidencias_ops = _build_evidencia_options(empresa_id)

        with st.form("form_perfil_mpi", clear_on_submit=False):
            st.markdown("#### 1. Datos del Representante Legal *(Art. 3 letra a)*")
            c1, c2 = st.columns(2)
            with c1:
                rep_nombre = st.text_input(
                    "Nombre Completo del Representante Legal *",
                    value=perfil_actual["representante_legal_nombre"] if perfil_actual else "",
                    placeholder="Ej. Juan Pérez González",
                )
                rep_rut = st.text_input(
                    "RUT del Representante Legal *",
                    value=perfil_actual["representante_legal_rut"] if perfil_actual else "",
                    placeholder="Ej. 12.345.678-9",
                )
            with c2:
                rep_email = st.text_input(
                    "Correo Electrónico de Contacto",
                    value=perfil_actual["representante_legal_email"] if perfil_actual else "",
                    placeholder="Ej. representante@empresa.cl",
                )
                rep_tel = st.text_input(
                    "Teléfono de Contacto",
                    value=perfil_actual["representante_legal_telefono"] if perfil_actual else "",
                    placeholder="Ej. +56 9 1234 5678",
                )

            st.markdown("---")
            st.markdown("#### 2. Datos del Modelo y Estados de Implementación")
            c3, c4 = st.columns(2)
            with c3:
                f_adopcion = st.date_input(
                    "Fecha de Adopción Formal del Modelo",
                    value=perfil_actual["fecha_adopcion_modelo"] if perfil_actual and perfil_actual.get("fecha_adopcion_modelo") else date.today(),
                )
                version_mod = st.text_input(
                    "Versión del Modelo [Diseño GRC complementario]",
                    value=perfil_actual["version_modelo"] if perfil_actual else "1.0",
                )
                alcance = st.text_area(
                    "Alcance Organizacional del Modelo [Diseño GRC complementario]",
                    value=perfil_actual["alcance_organizacional"] if perfil_actual else "",
                    placeholder="Ej. Aplica a todas las operaciones, filiales y áreas comerciales de la empresa.",
                    height=70,
                )

            with c4:
                # Estado Interno
                idx_int = 0
                if perfil_actual:
                    val_int = perfil_actual.get("estado_implementacion", "preparacion")
                    for i, (k, _) in enumerate(ESTADOS_MPI_INTERNOS):
                        if k == val_int:
                            idx_int = i
                estado_int_sel = st.selectbox(
                    "Estado Interno de Implementación",
                    options=[k for k, _ in ESTADOS_MPI_INTERNOS],
                    format_func=lambda x: ESTADOS_MPI_INTERNOS_MAP.get(x, x),
                    index=idx_int,
                )

                # Estado Oficial
                idx_of = 0
                if perfil_actual:
                    val_of = perfil_actual.get("estado_certificacion_oficial", "sin_solicitud")
                    for i, (k, _) in enumerate(ESTADOS_MPI_OFICIALES):
                        if k == val_of:
                            idx_of = i
                estado_of_sel = st.selectbox(
                    "Estado Registral Oficial (Decreto N° 662, Arts. 15 y 17)",
                    options=[k for k, _ in ESTADOS_MPI_OFICIALES],
                    format_func=lambda x: ESTADOS_MPI_OFICIALES_MAP.get(x, x),
                    index=idx_of,
                )

            # Sección condicional para estados oficiales
            st.markdown(AVISO_ESTADOS_OFICIALES)

            c5, c6 = st.columns(2)
            with c5:
                entidad_cert = st.text_input(
                    "Organismo certificador (DS 662 arts. 14-15)",
                    value=perfil_actual["entidad_certificadora"] if perfil_actual and perfil_actual.get("entidad_certificadora") else "",
                    placeholder="Agencia de Protección de Datos Personales",
                    help="Según el DS 662 sólo la Agencia certifica los modelos de prevención; "
                         "puede contratar a terceros únicamente para revisar antecedentes.",
                )
                nro_cert = st.text_input(
                    "Número de Certificado Emitido (Art. 15)",
                    value=perfil_actual["nro_certificado"] if perfil_actual and perfil_actual.get("nro_certificado") else "",
                )
                f_cert = st.date_input(
                    "Fecha de Emisión del Certificado (Art. 15)",
                    value=perfil_actual["fecha_certificacion"] if perfil_actual and perfil_actual.get("fecha_certificacion") else date.today(),
                )
            with c6:
                f_venc = st.date_input(
                    "Fecha de Vencimiento de Certificación (Vigencia 3 años, Art. 15)",
                    value=perfil_actual["fecha_vencimiento_certificacion"] if perfil_actual and perfil_actual.get("fecha_vencimiento_certificacion") else date.today() + timedelta(days=3*365),
                )
                nro_reg = st.text_input(
                    "N° Inscripción Registro Nacional de Sanciones y Cumplimiento (Art. 17)",
                    value=perfil_actual["nro_registro_agencia"] if perfil_actual and perfil_actual.get("nro_registro_agencia") else "",
                )
                ev_id_perfil = st.selectbox(
                    "Evidencia Documental de Adopción / Certificado (Enlace Externo)",
                    options=list(evidencias_ops.keys()),
                )

            sub_perfil = st.form_submit_button("💾 Guardar Perfil MPI", type="primary", use_container_width=True)
            if sub_perfil:
                evidencia_seleccionada = evidencias_ops[ev_id_perfil]

                if not rep_nombre or not rep_nombre.strip() or not rep_rut or not rep_rut.strip():
                    st.error("El nombre y RUT del representante legal son obligatorios (Art. 3 letra a).")
                elif estado_of_sel == "certificado_agencia":
                    if not evidencia_seleccionada:
                        st.error("Para registrar estado 'Certificado por la Agencia (Art. 15)' debes adjuntar la evidencia documental de respaldo.")
                    elif not nro_cert or not nro_cert.strip():
                        st.error("Para registrar estado de Certificación Oficial, debes ingresar el N° de Certificado emitido (Art. 15).")
                    elif not f_cert or not f_venc:
                        st.error("Debes registrar la fecha de emisión y vencimiento del certificado (Art. 15).")
                    else:
                        ok, msg = save_perfil_mpi(
                            empresa_id=empresa_id,
                            representante_legal_nombre=rep_nombre,
                            representante_legal_rut=rep_rut,
                            representante_legal_email=rep_email,
                            representante_legal_telefono=rep_tel,
                            fecha_adopcion_modelo=f_adopcion,
                            version_modelo=version_mod,
                            alcance_organizacional=alcance,
                            estado_implementacion=estado_int_sel,
                            estado_certificacion_oficial=estado_of_sel,
                            entidad_certificadora=entidad_cert,
                            nro_certificado=nro_cert,
                            fecha_certificacion=f_cert,
                            fecha_vencimiento_certificacion=f_venc,
                            nro_registro_agencia=nro_reg,
                            evidencia_aprobacion_id=evidencia_seleccionada,
                            perfil_id=perfil_actual["id"] if perfil_actual else None,
                        )
                        if ok:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                elif estado_of_sel == "inscrito_registro_agencia":
                    if not evidencia_seleccionada:
                        st.error("Para registrar estado 'Inscrito en Registro Nacional (Art. 17)' debes adjuntar la evidencia documental de respaldo.")
                    elif not nro_cert or not nro_cert.strip():
                        st.error("Debes ingresar el N° de Certificado emitido (Art. 15).")
                    elif not f_cert or not f_venc:
                        st.error("Debes registrar la fecha de emisión y vencimiento del certificado (Art. 15).")
                    elif not nro_reg or not nro_reg.strip():
                        st.error("Para registrar estado de Inscripción Oficial, debes ingresar el N° de Inscripción en el Registro Nacional de la Agencia (Art. 17).")
                    else:
                        ok, msg = save_perfil_mpi(
                            empresa_id=empresa_id,
                            representante_legal_nombre=rep_nombre,
                            representante_legal_rut=rep_rut,
                            representante_legal_email=rep_email,
                            representante_legal_telefono=rep_tel,
                            fecha_adopcion_modelo=f_adopcion,
                            version_modelo=version_mod,
                            alcance_organizacional=alcance,
                            estado_implementacion=estado_int_sel,
                            estado_certificacion_oficial=estado_of_sel,
                            entidad_certificadora=entidad_cert,
                            nro_certificado=nro_cert,
                            fecha_certificacion=f_cert,
                            fecha_vencimiento_certificacion=f_venc,
                            nro_registro_agencia=nro_reg,
                            evidencia_aprobacion_id=evidencia_seleccionada,
                            perfil_id=perfil_actual["id"] if perfil_actual else None,
                        )
                        if ok:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                elif estado_of_sel in ["vencido", "revocado"]:
                    if not evidencia_seleccionada and (not alcance or not alcance.strip()):
                        st.error("Para registrar estado 'Vencido' o 'Revocado' debes adjuntar la evidencia documental o ingresar un comentario justificativo en el alcance organizacional.")
                    else:
                        ok, msg = save_perfil_mpi(
                            empresa_id=empresa_id,
                            representante_legal_nombre=rep_nombre,
                            representante_legal_rut=rep_rut,
                            representante_legal_email=rep_email,
                            representante_legal_telefono=rep_tel,
                            fecha_adopcion_modelo=f_adopcion,
                            version_modelo=version_mod,
                            alcance_organizacional=alcance,
                            estado_implementacion=estado_int_sel,
                            estado_certificacion_oficial=estado_of_sel,
                            entidad_certificadora=entidad_cert,
                            nro_certificado=nro_cert,
                            fecha_certificacion=f_cert if nro_cert else None,
                            fecha_vencimiento_certificacion=f_venc if nro_cert else None,
                            nro_registro_agencia=nro_reg,
                            evidencia_aprobacion_id=evidencia_seleccionada,
                            perfil_id=perfil_actual["id"] if perfil_actual else None,
                        )
                        if ok:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                else:
                    # sin_solicitud o solicitud_en_tramite
                    ok, msg = save_perfil_mpi(
                        empresa_id=empresa_id,
                        representante_legal_nombre=rep_nombre,
                        representante_legal_rut=rep_rut,
                        representante_legal_email=rep_email,
                        representante_legal_telefono=rep_tel,
                        fecha_adopcion_modelo=f_adopcion,
                        version_modelo=version_mod,
                        alcance_organizacional=alcance,
                        estado_implementacion=estado_int_sel,
                        estado_certificacion_oficial=estado_of_sel,
                        entidad_certificadora=entidad_cert,
                        nro_certificado=nro_cert,
                        fecha_certificacion=f_cert if nro_cert else None,
                        fecha_vencimiento_certificacion=f_venc if nro_cert else None,
                        nro_registro_agencia=nro_reg,
                        evidencia_aprobacion_id=evidencia_seleccionada,
                        perfil_id=perfil_actual["id"] if perfil_actual else None,
                    )
                    if ok:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

        # Historial de Perfiles de la empresa
        df_perfiles = get_perfiles_df(empresa_id=empresa_id)
        if not df_perfiles.empty:
            st.markdown("---")
            st.subheader("📜 Historial de Perfiles y Versiones del Modelo")
            st.dataframe(
                df_perfiles[[
                    "id", "version_modelo", "representante_legal_nombre",
                    "fecha_adopcion_modelo", "estado_implementacion",
                    "estado_certificacion_oficial", "activo", "created_at"
                ]],
                use_container_width=True,
                hide_index=True,
            )

    # ==========================================================================
    # PESTAÑA 2: DELEGADO DE PROTECCIÓN DE DATOS (DPD)
    # ==========================================================================
    with tab_dpd:
        st.subheader("Designación y Facultades del Delegado de Protección de Datos (DPD)")
        st.info(
            "📌 **Referencias Decreto N° 662:**  \n"
            "- **Art. 3 b) y Art. 6:** Obligatoriedad de designación del delegado en el marco del MPI.  \n"
            "- **Art. 7:** Calidad del delegado (trabajador dependiente o prestación de servicios).  \n"
            "- **Art. 8:** Designación por máxima autoridad y autonomía respecto de la administración.  \n"
            "- **Art. 9:** Medios, recursos y facultades suficientes.  \n"
            "- **Art. 10:** Conocimientos especializados e idoneidad profesional.  \n"
            "- **Art. 11:** Publicación y disponibilidad de datos de contacto para titulares y Agencia.  \n"
            "- **Art. 12:** Deber estricto de secreto, reserva y confidencialidad."
        )

        delegado_actual = get_delegado_activo(empresa_id)

        with st.form("form_delegado_dpd", clear_on_submit=False):
            st.markdown("#### 1. Identificación y Canal de Contacto Público *(Arts. 3 b, 7 y 11)*")
            d1, d2 = st.columns(2)
            with d1:
                dpd_nombre = st.text_input(
                    "Nombre Completo del Delegado *",
                    value=delegado_actual["nombre_completo"] if delegado_actual else "",
                    placeholder="Ej. María Teresa Edwards",
                )
                dpd_email = st.text_input(
                    "Correo Electrónico de Contacto Público * (Art. 11)",
                    value=delegado_actual["email_contacto_publico"] if delegado_actual else "",
                    placeholder="Ej. dpo@empresa.cl / privacidad@empresa.cl",
                    help="Canal publicado y accesible para titulares de datos y la Agencia (Art. 11).",
                )
                dpd_tel = st.text_input(
                    "Teléfono de Contacto (Opcional)",
                    value=delegado_actual["telefono_contacto"] if delegado_actual and delegado_actual.get("telefono_contacto") else "",
                )
            with d2:
                dpd_rut = st.text_input(
                    "RUT del Delegado [Opcional - Dato interno]",
                    value=delegado_actual["rut_interno"] if delegado_actual and delegado_actual.get("rut_interno") else "",
                    help="Minimización de datos: El RUT es opcional y se almacena solo para efectos de control interno (no público).",
                )
                canal_detalles = st.text_area(
                    "Detalles de Publicación del Canal de Atención (Art. 11)",
                    value=delegado_actual["canal_atencion_detalles"] if delegado_actual and delegado_actual.get("canal_atencion_detalles") else "",
                    placeholder="Ej. Formulario web publicado en https://empresa.cl/privacidad y correo exclusivo.",
                    height=70,
                )

            st.markdown("---")
            st.markdown("#### 2. Calidad, Autonomía y Designación *(Arts. 6, 7 y 8)*")
            d3, d4 = st.columns(2)
            with d3:
                tipo_vinc_idx = 0
                if delegado_actual:
                    val_tv = delegado_actual.get("tipo_vinculo", "dependiente")
                    for i, (k, _) in enumerate(TIPOS_VINCULO_DELEGADO):
                        if k == val_tv:
                            tipo_vinc_idx = i
                tipo_vinc = st.selectbox(
                    "Calidad y Tipo de Vínculo del Delegado (Art. 7)",
                    options=[k for k, _ in TIPOS_VINCULO_DELEGADO],
                    format_func=lambda x: dict(TIPOS_VINCULO_DELEGADO).get(x, x),
                    index=tipo_vinc_idx,
                )
                pj_prestadora = st.text_input(
                    "Persona Jurídica Prestadora (Art. 7)",
                    value=delegado_actual["persona_juridica_prestadora"] if delegado_actual and delegado_actual.get("persona_juridica_prestadora") else "",
                    placeholder="Indicar si el servicio es prestado por persona jurídica externa",
                )
                cargo_int = st.text_input(
                    "Cargo Interno en la Organización",
                    value=delegado_actual["cargo_interno"] if delegado_actual and delegado_actual.get("cargo_interno") else "",
                    placeholder="Ej. Oficial de Privacidad / Compliance Officer",
                )
            with d4:
                aut_desig_idx = 0
                if delegado_actual and delegado_actual.get("autoridad_designacion") in AUTORIDADES_DESIGNACION_DPD:
                    aut_desig_idx = AUTORIDADES_DESIGNACION_DPD.index(delegado_actual["autoridad_designacion"])
                aut_desig = st.selectbox(
                    "Máxima Autoridad que lo Designó (Art. 8)",
                    options=AUTORIDADES_DESIGNACION_DPD,
                    index=aut_desig_idx,
                )
                f_desig = st.date_input(
                    "Fecha Formal de Designación (Art. 3 b)",
                    value=delegado_actual["fecha_designacion"] if delegado_actual and delegado_actual.get("fecha_designacion") else date.today(),
                )
                chk_autonomia = st.checkbox(
                    "Declaración de Autonomía Técnica: El delegado goza de autonomía respecto de la administración y rinde cuentas directamente a la autoridad que lo designó (Art. 8).",
                    value=delegado_actual["declaracion_autonomia"] if delegado_actual else True,
                )

            st.markdown("---")
            st.markdown("#### 3. Idoneidad, Medios y Evidencias *(Arts. 9, 10 y 12)*")
            d5, d6 = st.columns(2)
            with d5:
                decl_idoneidad = st.text_area(
                    "Declaración de Idoneidad y Conocimientos Especializados (Art. 10)",
                    value=delegado_actual["declaracion_idoneidad"] if delegado_actual and delegado_actual.get("declaracion_idoneidad") else "",
                    placeholder="Ej. Abogado especialista en protección de datos / Certificación internacional CIPP/E / Experiencia de 5 años...",
                    height=90,
                )
            with d6:
                medios_facultades = st.text_area(
                    "Medios Materiales, Presupuesto y Facultades Asignadas (Arts. 3 c y 9)",
                    value=delegado_actual["recursos_materiales_facultades"] if delegado_actual and delegado_actual.get("recursos_materiales_facultades") else "",
                    placeholder="Ej. Acceso irrestricto a procesos y bases de datos; presupuesto anual de capacitación; equipo de soporte TI.",
                    height=90,
                )

            ev_id_dpd = st.selectbox(
                "Evidencia Documental del Acto de Designación (Enlace Externo)",
                options=list(evidencias_ops.keys()),
                key="ev_dpd_sel",
            )

            st.caption("🔒 **Nota de Deber de Secreto (Art. 12):** El delegado está sujeto a estricto deber de reserva y secreto profesional respecto de los datos e información conocidos en el ejercicio de sus funciones.")

            sub_dpd = st.form_submit_button("💾 Guardar Delegado de Protección de Datos", type="primary", use_container_width=True)
            if sub_dpd:
                if not dpd_nombre or not dpd_nombre.strip() or not dpd_email or not dpd_email.strip():
                    st.error("El nombre completo y el correo de contacto público del Delegado son obligatorios (Arts. 3 b y 11).")
                else:
                    ok, msg = save_delegado_dpd(
                        empresa_id=empresa_id,
                        nombre_completo=dpd_nombre,
                        email_contacto_publico=dpd_email,
                        rut_interno=dpd_rut,
                        telefono_contacto=dpd_tel,
                        canal_atencion_detalles=canal_detalles,
                        tipo_vinculo=tipo_vinc,
                        persona_juridica_prestadora=pj_prestadora,
                        cargo_interno=cargo_int,
                        autoridad_designacion=aut_desig,
                        fecha_designacion=f_desig,
                        declaracion_autonomia=chk_autonomia,
                        declaracion_idoneidad=decl_idoneidad,
                        recursos_materiales_facultades=medios_facultades,
                        evidencia_designacion_id=evidencias_ops[ev_id_dpd],
                        delegado_id=delegado_actual["id"] if delegado_actual else None,
                    )
                    if ok:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

        # Listado de Delegados (con RUT enmascarado para protección de datos)
        df_delegados = get_delegados_df(empresa_id=empresa_id)
        if not df_delegados.empty:
            st.markdown("---")
            st.subheader("📜 Historial de Delegados de la Empresa")
            st.dataframe(
                df_delegados[[
                    "id", "nombre_completo", "email_contacto_publico",
                    "tipo_vinculo", "autoridad_designacion", "fecha_designacion",
                    "activo", "created_at"
                ]],
                use_container_width=True,
                hide_index=True,
            )

    # ==========================================================================
    # PESTAÑA 3: TRAZABILIDAD NORMATIVA (DECRETO N° 662)
    # ==========================================================================
    with tab_normativa:
        st.subheader("📖 Marco Normativo de Referencia — Decreto N° 662")
        st.markdown(
            "Reglamento que regula requisitos, modalidades y procedimientos para implementación, certificación, "
            "registro y supervisión de los Modelos de Prevención de Infracciones (MPI) a que se refiere el **artículo 49 incorporado por Ley N° 21.719 a la Ley N° 19.628**."
        )

        df_norm = get_referencias_normativas_df()
        if not df_norm.empty:
            st.dataframe(
                df_norm[["articulo", "materia", "descripcion_criterio"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No hay referencias normativas cargadas.")
