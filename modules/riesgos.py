"""
Módulo Análisis de Riesgos.

- Diagnóstico: propone riesgos a partir de los datos de Lince (RAT, auditorías,
  derechos), asociados a infracciones de la Ley 21.719 (arts. 34 bis-34 quáter).
- Registro y evaluación: probabilidad × impacto (1-5), controles, riesgo residual
  y plan de tratamiento.
- Mapa de calor 5×5, matriz de riesgos del MPI (DS 662 art. 3 e: graduada por la
  sanción) y evaluación de impacto por tratamiento (Ley 21.719 art. 15 ter).
"""

from datetime import date

import pandas as pd
import streamlit as st

from db.repositories.derechos import get_solicitudes_df
from db.repositories.empresas import get_empresas_df
from db.repositories.evidencias import get_evidencias_df
from db.repositories.riesgos import (
    actualizar_riesgo,
    crear_riesgo,
    get_eipd_df,
    get_riesgos_df,
    guardar_eipd,
    registrar_propuestos,
)
from db.repositories.tratamientos import get_tratamientos_df
from db.repositories.visitas import get_visitas_df
from services import riesgos_service as rs
from utils.constants import (
    CATEGORIAS_RIESGO,
    CATEGORIAS_RIESGO_MAP,
    DISPARADORES_EIPD,
    ESCALA_IMPACTO,
    ESCALA_PROBABILIDAD,
    ESTADOS_RIESGO,
    ESTADOS_RIESGO_MAP,
    GRAVEDAD_LEGAL_LABEL,
    INFRACCIONES_LEY_21719,
    RESPUESTAS_RIESGO,
    RESPUESTAS_RIESGO_MAP,
)

_CLAVE_AVISO = "riesgos_aviso"
_COLOR_NIVEL = {"bajo": "#1F3B2C", "medio": "#4A4317", "alto": "#5A3412", "critico": "#5E1A1A"}


def _aviso(ok: bool, msg: str) -> None:
    st.session_state[_CLAVE_AVISO] = (ok, msg)


def _mostrar_aviso() -> None:
    r = st.session_state.pop(_CLAVE_AVISO, None)
    if r:
        (st.success if r[0] else st.error)(r[1])


def _nivel_txt(p, i) -> str:
    puntaje, _, etiqueta = rs.nivel_riesgo(int(p), int(i))
    return f"{etiqueta} ({puntaje})"


def _residual_txt(r: pd.Series) -> str:
    if pd.notna(r.get("probabilidad_residual")) and pd.notna(r.get("impacto_residual")):
        return _nivel_txt(r["probabilidad_residual"], r["impacto_residual"])
    return "Sin evaluar"


def _selector_empresa(df_empresas: pd.DataFrame) -> int:
    mapa = {f"{r['nombre']} ({r['rut']})": int(r["id"]) for _, r in df_empresas.iterrows()}
    ids = list(mapa.values())
    activa = st.session_state.get("empresa_activa_id")
    etiqueta = st.selectbox("Empresa", list(mapa.keys()), index=ids.index(activa) if activa in ids else 0,
                            key="rsg_empresa")
    st.session_state["empresa_activa_id"] = mapa[etiqueta]
    return mapa[etiqueta]


def _evidencias(empresa_id: int) -> dict:
    ops = {"Sin evidencia vinculada": None}
    df = get_evidencias_df(empresa_id=empresa_id)
    if not df.empty:
        ops.update({f"ID {r['id']} - {(r['descripcion'] or '')[:40]}": int(r["id"]) for _, r in df.iterrows()})
    return ops


# ------------------------------------------------------------------------------
# Diagnóstico
# ------------------------------------------------------------------------------
def _tab_diagnostico(empresa_id: int, df_riesgos: pd.DataFrame) -> None:
    st.caption(
        "Lince revisa el RAT, la última auditoría y las solicitudes de derechos, y propone riesgos asociados "
        "a infracciones de la Ley 21.719. Las propuestas no se registran hasta que usted las incorpore."
    )
    propuestos = rs.diagnosticar(
        get_tratamientos_df(empresa_id=empresa_id),
        get_visitas_df(empresa_id=empresa_id),
        get_solicitudes_df(empresa_id=empresa_id),
    )
    registrados = set()
    if not df_riesgos.empty:
        reg = df_riesgos[df_riesgos["codigo_regla"].notna()]
        registrados = {(r["codigo_regla"], int(r["tratamiento_id"]) if pd.notna(r["tratamiento_id"]) else 0)
                       for _, r in reg.iterrows()}
    pendientes = [p for p in propuestos if p.clave not in registrados]
    st.markdown(f"**{len(propuestos)}** riesgos detectados · **{len(pendientes)}** pendientes de incorporar")
    if not pendientes:
        st.info("No hay riesgos nuevos por incorporar con los datos actuales.")
        return
    tabla = pd.DataFrame([{
        "Riesgo": p.titulo,
        "Infracción asociada": f"Art. {p.infraccion} ({GRAVEDAD_LEGAL_LABEL[p.gravedad]})",
        "Nivel sugerido": _nivel_txt(p.probabilidad, p.impacto),
        "Origen": p.origen,
    } for p in pendientes])
    st.dataframe(tabla, use_container_width=True, hide_index=True)
    opciones = {f"{i + 1}. {p.titulo}": p for i, p in enumerate(pendientes)}
    elegidos = st.multiselect("Riesgos a incorporar al registro", list(opciones.keys()),
                              default=list(opciones.keys()), key="rsg_elegidos")
    if st.button("Incorporar al registro", type="primary", key="rsg_incorporar"):
        _aviso(*registrar_propuestos(empresa_id, [opciones[e] for e in elegidos]))
        st.rerun()


# ------------------------------------------------------------------------------
# Registro y evaluación
# ------------------------------------------------------------------------------
def _tab_registro(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Aún no hay riesgos registrados. Use la pestaña Diagnóstico o registre uno manualmente.")
        return
    filtro = st.multiselect("Estado", [e[0] for e in ESTADOS_RIESGO], default=["abierto", "en_tratamiento"],
                            format_func=lambda k: ESTADOS_RIESGO_MAP[k], key="rsg_filtro")
    vista = df[df["estado"].isin(filtro)] if filtro else df
    st.dataframe(pd.DataFrame([{
        "ID": r["id"],
        "Riesgo": r["titulo"],
        "Categoría": CATEGORIAS_RIESGO_MAP.get(r["categoria"], r["categoria"] or ""),
        "Infracción": f"Art. {r['infraccion_ref']}" if r["infraccion_ref"] else "",
        "Inherente": _nivel_txt(r["probabilidad"], r["impacto"]),
        "Residual": _residual_txt(r),
        "Respuesta": RESPUESTAS_RIESGO_MAP.get(r["respuesta"], "") if r["respuesta"] else "",
        "Responsable": r["responsable"] or "",
        "Plazo": str(r["plazo"])[:10] if pd.notna(r["plazo"]) else "",
        "Estado": ESTADOS_RIESGO_MAP.get(r["estado"], r["estado"]),
    } for _, r in vista.iterrows()]), use_container_width=True, hide_index=True)


def _tab_evaluar(df: pd.DataFrame, empresa_id: int) -> None:
    df_eipd = get_eipd_df(empresa_id=empresa_id)
    eipd_ops = {"Sin EIPD vinculada": None}
    if not df_eipd.empty:
        eipd_ops.update({f"EIPD {r['id']} - {r['tratamiento'] or 'sin tratamiento'}": int(r["id"])
                         for _, r in df_eipd.iterrows()})
    if not df.empty:
        opciones = {f"{r['id']} - {r['titulo']}": int(r["id"]) for _, r in df.iterrows()}
        sel = st.selectbox("Riesgo a evaluar", list(opciones.keys()), key="rsg_sel")
        r = df[df["id"] == opciones[sel]].iloc[0]
        if r["descripcion"]:
            st.caption(r["descripcion"])
        if r["infraccion_ref"]:
            grav, desc = INFRACCIONES_LEY_21719.get(r["infraccion_ref"], ("", ""))
            st.caption(f"Infracción asociada: Art. {r['infraccion_ref']}, {GRAVEDAD_LEGAL_LABEL.get(grav, '')}: {desc}")
        ev_ops = _evidencias(empresa_id)
        with st.form(f"form_eval_{r['id']}"):
            c1, c2 = st.columns(2)
            p = c1.select_slider("Probabilidad", options=[1, 2, 3, 4, 5], value=int(r["probabilidad"]),
                                 format_func=lambda v: f"{v} - {ESCALA_PROBABILIDAD[v]}")
            i = c2.select_slider("Impacto", options=[1, 2, 3, 4, 5], value=int(r["impacto"]),
                                 format_func=lambda v: f"{v} - {ESCALA_IMPACTO[v]}")
            controles = st.text_area("Controles existentes", value=r["controles"] or "")
            evaluar_res = st.checkbox("Evaluar riesgo residual (con los controles aplicados)",
                                      value=pd.notna(r["probabilidad_residual"]))
            c3, c4 = st.columns(2)
            pr = c3.select_slider("Probabilidad residual", options=[1, 2, 3, 4, 5],
                                  value=int(r["probabilidad_residual"]) if pd.notna(r["probabilidad_residual"]) else int(r["probabilidad"]),
                                  format_func=lambda v: f"{v} - {ESCALA_PROBABILIDAD[v]}")
            ir = c4.select_slider("Impacto residual", options=[1, 2, 3, 4, 5],
                                  value=int(r["impacto_residual"]) if pd.notna(r["impacto_residual"]) else int(r["impacto"]),
                                  format_func=lambda v: f"{v} - {ESCALA_IMPACTO[v]}")
            c5, c6, c7 = st.columns(3)
            claves_resp = [x[0] for x in RESPUESTAS_RIESGO]
            respuesta = c5.selectbox("Respuesta al riesgo", claves_resp,
                                     index=claves_resp.index(r["respuesta"]) if r["respuesta"] in claves_resp else 0,
                                     format_func=lambda k: RESPUESTAS_RIESGO_MAP[k])
            claves_est = [x[0] for x in ESTADOS_RIESGO]
            estado = c6.selectbox("Estado", claves_est, index=claves_est.index(r["estado"]),
                                  format_func=lambda k: ESTADOS_RIESGO_MAP[k])
            responsable = c7.text_input("Responsable", value=r["responsable"] or "")
            plan = st.text_area("Plan de acción", value=r["plan_accion"] or "")
            c8, c9, c10 = st.columns(3)
            con_plazo = c8.checkbox("Definir plazo", value=pd.notna(r["plazo"]))
            plazo = c8.date_input("Plazo", value=pd.to_datetime(r["plazo"]).date() if pd.notna(r["plazo"]) else date.today())
            ev_keys = list(ev_ops.keys())
            ev_actual = next((k for k, v in ev_ops.items() if v == (int(r["evidencia_id"]) if pd.notna(r["evidencia_id"]) else None)), ev_keys[0])
            evidencia = c9.selectbox("Evidencia", ev_keys, index=ev_keys.index(ev_actual))
            eipd_keys = list(eipd_ops.keys())
            eipd_actual = next((k for k, v in eipd_ops.items() if v == (int(r["eipd_id"]) if pd.notna(r["eipd_id"]) else None)), eipd_keys[0])
            eipd_sel = c10.selectbox("EIPD vinculada", eipd_keys, index=eipd_keys.index(eipd_actual))
            st.markdown(f"Nivel inherente: **{_nivel_txt(p, i)}**")
            if st.form_submit_button("Guardar evaluación", type="primary"):
                _aviso(*actualizar_riesgo(
                    int(r["id"]), empresa_id, p, i, controles,
                    pr if evaluar_res else None, ir if evaluar_res else None,
                    respuesta, plan, responsable, plazo if con_plazo else None, estado,
                    ev_ops[evidencia], eipd_ops[eipd_sel],
                ))
                st.rerun()

    st.markdown("#### Registrar riesgo manualmente")
    df_trat = get_tratamientos_df(empresa_id=empresa_id)
    trat_ops = {"Riesgo de la organización (sin tratamiento)": None}
    if not df_trat.empty:
        trat_ops.update({f"{t['id']} - {t['nombre_tratamiento']}": int(t["id"]) for _, t in df_trat.iterrows()})
    infr_ops = {"Sin infracción asociada": ""}
    infr_ops.update({f"Art. {k} ({GRAVEDAD_LEGAL_LABEL[v[0]]}) - {v[1]}": k for k, v in INFRACCIONES_LEY_21719.items()})
    with st.form("form_riesgo_manual", clear_on_submit=True):
        titulo = st.text_input("Riesgo *")
        descripcion = st.text_area("Descripción")
        c1, c2 = st.columns(2)
        categoria = c1.selectbox("Categoría", [c[0] for c in CATEGORIAS_RIESGO], format_func=lambda k: CATEGORIAS_RIESGO_MAP[k])
        tratamiento = c2.selectbox("Tratamiento", list(trat_ops.keys()))
        infraccion = st.selectbox("Infracción asociada (Ley 21.719)", list(infr_ops.keys()))
        c3, c4 = st.columns(2)
        p = c3.select_slider("Probabilidad", options=[1, 2, 3, 4, 5], value=3,
                             format_func=lambda v: f"{v} - {ESCALA_PROBABILIDAD[v]}")
        i = c4.select_slider("Impacto", options=[1, 2, 3, 4, 5], value=3,
                             format_func=lambda v: f"{v} - {ESCALA_IMPACTO[v]}")
        if st.form_submit_button("Registrar riesgo"):
            ref = infr_ops[infraccion]
            _aviso(*crear_riesgo(empresa_id, titulo, p, i, descripcion, categoria, ref,
                                 INFRACCIONES_LEY_21719[ref][0] if ref else "", trat_ops[tratamiento]))
            st.rerun()


# ------------------------------------------------------------------------------
# Mapa de calor y matriz MPI
# ------------------------------------------------------------------------------
def _tab_mapa(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Sin riesgos registrados.")
        return
    tipo = st.radio("Riesgo", ["Inherente", "Residual"], horizontal=True, key="rsg_mapa_tipo")
    activos = df[df["estado"] != "cerrado"]
    if tipo == "Residual":
        activos = activos[activos["probabilidad_residual"].notna() & activos["impacto_residual"].notna()]
        cp, ci = "probabilidad_residual", "impacto_residual"
    else:
        cp, ci = "probabilidad", "impacto"
    matriz = pd.DataFrame(0, index=[5, 4, 3, 2, 1], columns=[1, 2, 3, 4, 5])
    for _, r in activos.iterrows():
        matriz.loc[int(r[ci]), int(r[cp])] += 1
    colores = pd.DataFrame("", index=matriz.index, columns=matriz.columns)
    for imp in matriz.index:
        for prob in matriz.columns:
            colores.loc[imp, prob] = f"background-color: {_COLOR_NIVEL[rs.nivel_riesgo(prob, imp)[1]]}; color: #F1F5F9"
    vista = matriz.copy()
    vista.index = [f"Impacto {v} - {ESCALA_IMPACTO[v]}" for v in vista.index]
    vista.columns = [f"P{v} {ESCALA_PROBABILIDAD[v]}" for v in vista.columns]
    colores.index, colores.columns = vista.index, vista.columns
    st.dataframe(vista.style.apply(lambda _: colores, axis=None), use_container_width=True)
    st.caption(f"Riesgos no cerrados: {len(activos)}. Niveles: BAJO < {rs.UMBRAL_MEDIO} ≤ MEDIO < {rs.UMBRAL_ALTO} "
               f"≤ ALTO < {rs.UMBRAL_CRITICO} ≤ CRÍTICO (probabilidad × impacto). Criterio metodológico interno.")


def _tab_matriz_mpi(df: pd.DataFrame) -> None:
    st.caption(
        "Matriz de riesgos del programa de cumplimiento (DS 662 art. 3 e): actividades que generan o "
        "incrementan el riesgo de las infracciones de los arts. 34 bis, 34 ter y 34 quáter, graduadas "
        "según la sanción prevista en la ley. Aplica a organizaciones que adoptan un MPI."
    )
    if df.empty:
        st.info("Sin riesgos registrados.")
        return
    con_infr = df[df["infraccion_ref"].notna() & (df["infraccion_ref"] != "")]
    orden = {"gravisima": 0, "grave": 1, "leve": 2}
    filas = []
    for ref, grupo in con_infr.groupby("infraccion_ref"):
        grav, desc = INFRACCIONES_LEY_21719.get(ref, ("", ref))
        peor = max(grupo.itertuples(), key=lambda x: x.probabilidad * x.impacto)
        filas.append({
            "_orden": (orden.get(grav, 9), -(peor.probabilidad * peor.impacto)),
            "Gravedad legal": GRAVEDAD_LEGAL_LABEL.get(grav, ""),
            "Infracción": f"Art. {ref} - {desc}",
            "Riesgos": len(grupo),
            "Abiertos": int((grupo["estado"] != "cerrado").sum()),
            "Nivel máximo": _nivel_txt(peor.probabilidad, peor.impacto),
        })
    filas.sort(key=lambda f: f["_orden"])
    st.dataframe(pd.DataFrame(filas).drop(columns="_orden"), use_container_width=True, hide_index=True)
    sin = len(df) - len(con_infr)
    if sin:
        st.caption(f"{sin} riesgo(s) sin infracción asociada no aparecen en la matriz.")


# ------------------------------------------------------------------------------
# EIPD
# ------------------------------------------------------------------------------
def _tab_eipd(empresa_id: int, df_riesgos: pd.DataFrame) -> None:
    st.caption(
        "Ley 21.719 art. 15 ter: la EIPD se realiza antes del inicio del tratamiento cuando sea probable un alto "
        "riesgo, y siempre en los casos a) a d). La Agencia publicará una lista orientativa y orientaciones mínimas "
        "(pendiente de verificación regulatoria)."
    )
    df_trat = get_tratamientos_df(empresa_id=empresa_id)
    if df_trat.empty:
        st.info("Registre tratamientos en el RAT para evaluar su impacto.")
        return
    df_eipd = get_eipd_df(empresa_id=empresa_id)
    aprobadas = set(df_eipd[df_eipd["estado"] == "aprobada"]["tratamiento_id"].dropna().astype(int)) if not df_eipd.empty else set()
    resumen = []
    for _, t in df_trat.iterrows():
        det = rs.disparadores_eipd_detectados(t)
        if det:
            resumen.append({"Tratamiento": t["nombre_tratamiento"], "Disparadores detectados": ", ".join(sorted(det)),
                            "EIPD aprobada": "Sí" if int(t["id"]) in aprobadas else "NO"})
    if resumen:
        st.markdown("**Tratamientos con indicios de EIPD obligatoria**")
        st.dataframe(pd.DataFrame(resumen), use_container_width=True, hide_index=True)

    trat_ops = {f"{t['id']} - {t['nombre_tratamiento']}": int(t["id"]) for _, t in df_trat.iterrows()}
    sel = st.selectbox("Tratamiento", list(trat_ops.keys()), key="rsg_eipd_trat")
    tid = trat_ops[sel]
    t = df_trat[df_trat["id"] == tid].iloc[0]
    detectados = rs.disparadores_eipd_detectados(t)
    previas = df_eipd[df_eipd["tratamiento_id"] == tid] if not df_eipd.empty else pd.DataFrame()
    actual = previas.iloc[0] if not previas.empty else None

    riesgos_t = df_riesgos[df_riesgos["tratamiento_id"] == tid] if not df_riesgos.empty else pd.DataFrame()
    if not riesgos_t.empty:
        st.markdown("**Riesgos del tratamiento** (evaluación de riesgos de la EIPD)")
        st.dataframe(pd.DataFrame([{"Riesgo": r["titulo"], "Inherente": _nivel_txt(r["probabilidad"], r["impacto"]),
                                    "Residual": _residual_txt(r)} for _, r in riesgos_t.iterrows()]),
                     use_container_width=True, hide_index=True)
    else:
        st.caption("Este tratamiento no tiene riesgos registrados: ejecute el Diagnóstico o regístrelos manualmente.")

    ev_ops = _evidencias(empresa_id)

    def _v(campo, defecto=""):
        return actual[campo] if actual is not None and pd.notna(actual[campo]) else defecto

    with st.form(f"form_eipd_{tid}"):
        st.markdown("**Disparadores de EIPD obligatoria (art. 15 ter)**")
        marcados = set()
        for k, texto in DISPARADORES_EIPD.items():
            previo = bool(_v(f"disparador_{k}", False)) if actual is not None else (k in detectados)
            etiqueta = f"{k}) {texto}" + (" [indicio detectado en el RAT: confirmar]" if k in detectados else "")
            if st.checkbox(etiqueta, value=previo, key=f"eipd_{tid}_{k}"):
                marcados.add(k)
        descripcion = st.text_area("Descripción de las operaciones de tratamiento *", value=_v("descripcion_operaciones"))
        finalidad = st.text_area("Finalidad *", value=_v("finalidad") or (t.get("rat_finalidades") or ""))
        necesidad = st.text_area("Evaluación de necesidad y proporcionalidad *", value=_v("necesidad_proporcionalidad"))
        mitigacion = st.text_area("Medidas de mitigación *", value=_v("medidas_mitigacion"))
        c1, c2, c3 = st.columns(3)
        conclusiones = {"riesgo_aceptable": "Riesgo residual aceptable", "alto_riesgo_residual": "Alto riesgo residual"}
        claves_c = list(conclusiones.keys())
        conclusion = c1.selectbox("Conclusión", claves_c, format_func=lambda k: conclusiones[k],
                                  index=claves_c.index(_v("conclusion")) if _v("conclusion") in claves_c else 0)
        estados = {"borrador": "Borrador", "aprobada": "Aprobada"}
        estado = c2.selectbox("Estado", list(estados.keys()), format_func=lambda k: estados[k],
                              index=1 if _v("estado") == "aprobada" else 0)
        responsable = c3.text_input("Responsable", value=_v("responsable"))
        consulta = st.checkbox("Se consultará a la Agencia (procede si el resultado es de alto riesgo)",
                               value=bool(_v("consulta_agencia", False)))
        ev_keys = list(ev_ops.keys())
        evidencia = st.selectbox("Evidencia (documento de la EIPD)", ev_keys)
        if st.form_submit_button("Guardar EIPD", type="primary"):
            ok, msg = guardar_eipd(empresa_id, tid, marcados, descripcion, finalidad, necesidad, mitigacion,
                                   conclusion, consulta, estado, responsable, ev_ops[evidencia],
                                   int(actual["id"]) if actual is not None else None)
            if ok and conclusion == "alto_riesgo_residual" and not consulta:
                msg += " El resultado es de alto riesgo: evalúe consultar a la Agencia (art. 15 ter)."
            _aviso(ok, msg)
            st.rerun()
    if detectados and actual is None:
        st.warning("Este tratamiento tiene indicios de EIPD obligatoria y aún no tiene una evaluación registrada.")


def render() -> None:
    st.header("Análisis de Riesgos")
    st.caption(
        "Diagnóstico de riesgos de protección de datos a partir de la información de la organización, "
        "con matriz de riesgos del MPI (DS 662 art. 3 e) y evaluación de impacto (Ley 21.719 art. 15 ter)."
    )
    df_empresas = get_empresas_df()
    if df_empresas.empty:
        st.warning("Primero debe registrar al menos una empresa.")
        return
    empresa_id = _selector_empresa(df_empresas)
    _mostrar_aviso()
    df = get_riesgos_df(empresa_id=empresa_id)

    abiertos = df[df["estado"] != "cerrado"] if not df.empty else df
    niveles = [rs.nivel_riesgo(r["probabilidad"], r["impacto"])[1] for _, r in abiertos.iterrows()] if not df.empty else []
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Riesgos abiertos", len(abiertos))
    m2.metric("Críticos", niveles.count("critico"))
    m3.metric("Altos", niveles.count("alto"))
    m4.metric("Con plan de acción", int(abiertos["plan_accion"].notna().sum()) if not df.empty else 0)

    t1, t2, t3, t4, t5, t6 = st.tabs(["Diagnóstico", "Registro", "Evaluar", "Mapa de calor", "Matriz MPI", "EIPD"])
    with t1:
        _tab_diagnostico(empresa_id, df)
    with t2:
        _tab_registro(df)
    with t3:
        _tab_evaluar(df, empresa_id)
    with t4:
        _tab_mapa(df)
    with t5:
        _tab_matriz_mpi(df)
    with t6:
        _tab_eipd(empresa_id, df)
