"""
Módulo Derechos de los Titulares.

Registro y gestión de solicitudes de acceso, rectificación, supresión, oposición,
oposición a decisiones automatizadas, bloqueo y portabilidad, con plazos legales
calculados según el régimen de la fecha de ingreso (estándar dual):
  - Ley 19.628 vigente (hasta el 30-11-2026): 2 días hábiles, art. 16.
  - Ley 21.719 (desde el 01-12-2026): 30 días corridos + prórroga única, art. 11.
Para solicitudes bajo la ley vigente se muestra además el plazo de referencia
de la Ley 21.719 (preparación).
"""

from datetime import date

import pandas as pd
import streamlit as st

from db.repositories.derechos import (
    crear_solicitud,
    get_solicitudes_df,
    prorrogar_solicitud,
    registrar_acuse,
    registrar_respuesta,
    resolver_bloqueo,
    resumen_plazos,
)
from db.repositories.empresas import get_empresas_df
from db.repositories.evidencias import get_evidencias_df
from db.repositories.tratamientos import get_tratamientos_df
from services import plazos_service as plazos
from utils.constants import (
    CANALES_SOLICITUD,
    DERECHOS_CON_BLOQUEO_TEMPORAL,
    DERECHOS_TITULAR,
    DERECHOS_TITULAR_MAP,
    ESTADOS_SOLICITUD_MAP,
)

_CLAVE_AVISO = "derechos_aviso"
_ESTADOS_RESPUESTA = [
    ("acogida", "Acogida"),
    ("acogida_parcial", "Acogida parcialmente (requiere fundamento)"),
    ("denegada", "Denegada (requiere fundamento)"),
    ("cerrada", "Cerrada sin pronunciamiento de fondo"),
]


def _aviso(ok: bool, msg: str) -> None:
    """Guarda el resultado para mostrarlo tras el rerun (st.success se perdería)."""
    st.session_state[_CLAVE_AVISO] = (ok, msg)


def _mostrar_aviso() -> None:
    resultado = st.session_state.pop(_CLAVE_AVISO, None)
    if resultado:
        (st.success if resultado[0] else st.error)(resultado[1])


def _fecha(valor) -> date:
    return pd.to_datetime(valor).date()


def _selector_empresa(df_empresas: pd.DataFrame) -> int:
    mapa = {f"{r['nombre']} ({r['rut']})": int(r["id"]) for _, r in df_empresas.iterrows()}
    ids = list(mapa.values())
    activa = st.session_state.get("empresa_activa_id")
    etiqueta = st.selectbox(
        "Empresa (responsable de datos)",
        list(mapa.keys()),
        index=ids.index(activa) if activa in ids else 0,
        key="der_empresa",
    )
    empresa_id = mapa[etiqueta]
    st.session_state["empresa_activa_id"] = empresa_id
    return empresa_id


def _tab_bandeja(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No hay solicitudes registradas para esta empresa.")
        return
    filas = []
    for _, r in df.iterrows():
        ep = plazos.estado_plazo(r["estado"], _fecha(r["fecha_vencimiento"]), r["regimen"])
        filas.append({
            "Folio": r["folio"],
            "Plazo": ep.etiqueta,
            "Derecho": DERECHOS_TITULAR_MAP.get(r["derecho"], r["derecho"]),
            "Ingreso": _fecha(r["fecha_ingreso"]).strftime("%d-%m-%Y"),
            "Vence": _fecha(r["fecha_vencimiento"]).strftime("%d-%m-%Y"),
            "Régimen": "Ley 21.719" if r["regimen"] == plazos.REGIMEN_21719 else "Ley 19.628",
            "Estado": ESTADOS_SOLICITUD_MAP.get(r["estado"], r["estado"]),
            "Titular": r["titular_nombre"],
            "Bloqueo": "Sí" if r["bloqueo_solicitado"] else "",
        })
    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)


def _tab_nueva(empresa_id: int) -> None:
    st.caption(
        "Contenido mínimo de la solicitud (Ley 21.719 art. 11): individualización del titular "
        "(o representante) y autenticación de identidad, medio para comunicar la respuesta y "
        "datos o tratamiento sobre los que se ejerce el derecho."
    )
    df_trat = get_tratamientos_df(empresa_id=empresa_id)
    trat_ops = {"(No vincular)": None}
    if not df_trat.empty:
        trat_ops.update({f"{r['id']} - {r['nombre_tratamiento']}": int(r["id"]) for _, r in df_trat.iterrows()})

    with st.form("form_nueva_solicitud", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        derecho = c1.selectbox("Derecho ejercido *", [d[0] for d in DERECHOS_TITULAR],
                               format_func=lambda k: DERECHOS_TITULAR_MAP[k])
        fecha_ingreso = c2.date_input("Fecha de ingreso *", value=date.today(), max_value=date.today())
        canal = c3.selectbox("Canal", CANALES_SOLICITUD)

        c4, c5 = st.columns(2)
        titular = c4.text_input("Titular (nombre) *")
        contacto = c5.text_input("Correo o domicilio para responder *")
        representante = c4.text_input("Representante o mandatario (si corresponde)")
        verificada = c5.checkbox("Identidad del titular verificada")
        metodo = c5.text_input("Método de verificación", placeholder="Ej.: cédula vigente cotejada")

        tratamiento = st.selectbox("Tratamiento del RAT afectado", list(trat_ops.keys()))
        descripcion = st.text_area(
            "Detalle de la solicitud",
            placeholder="Datos o tratamiento involucrado; en rectificación, los cambios precisos; "
                        "en supresión u oposición, la causal invocada.",
        )
        bloqueo = st.checkbox(
            "El titular solicitó bloqueo temporal (sólo rectificación, supresión u oposición)",
            help="Ley 21.719 art. 11: debe responderse dentro de 2 días hábiles y, mientras tanto, "
                 "no se pueden tratar los datos objeto del requerimiento.",
        )
        enviar = st.form_submit_button("Registrar solicitud", type="primary")

    if enviar:
        if not titular.strip() or not contacto.strip():
            st.error("El nombre del titular y el medio para responder son obligatorios.")
            return
        if bloqueo and derecho not in DERECHOS_CON_BLOQUEO_TEMPORAL:
            st.error("El bloqueo temporal sólo procede junto a una solicitud de rectificación, supresión u oposición.")
            return
        ok, msg = crear_solicitud(
            empresa_id=empresa_id, derecho=derecho, fecha_ingreso=fecha_ingreso,
            titular_nombre=titular, canal=canal, titular_contacto=contacto,
            representante=representante, identidad_verificada=verificada,
            metodo_verificacion=metodo, descripcion=descripcion,
            bloqueo_solicitado=bloqueo, tratamiento_id=trat_ops[tratamiento],
        )
        _aviso(ok, msg)
        st.rerun()


def _detalle_plazos(s: pd.Series) -> None:
    ingreso = _fecha(s["fecha_ingreso"])
    vence = _fecha(s["fecha_vencimiento"])
    ep = plazos.estado_plazo(s["estado"], vence, s["regimen"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Plazo", ep.etiqueta)
    c2.metric("Vence", vence.strftime("%d-%m-%Y"))
    c3.metric("Estado", ESTADOS_SOLICITUD_MAP.get(s["estado"], s["estado"]))
    st.caption(plazos.descripcion_regimen(s["regimen"]))
    referencia = plazos.vencimiento_referencia_21719(ingreso)
    if referencia:
        st.info(
            f"**Estándar Ley 21.719 (referencia de preparación):** con la reforma, esta solicitud "
            f"vencería el {referencia:%d-%m-%Y}. El plazo exigible hoy es el de la Ley 19.628."
        )
    if s["bloqueo_solicitado"]:
        venc_b = _fecha(s["bloqueo_vencimiento"]) if pd.notna(s["bloqueo_vencimiento"]) else None
        estado_b = s["bloqueo_resultado"] or "pendiente"
        st.warning(f"Bloqueo temporal solicitado · responder antes del {venc_b:%d-%m-%Y} · estado: {estado_b}"
                   if venc_b else f"Bloqueo temporal solicitado · estado: {estado_b}")


def _tab_gestionar(df: pd.DataFrame, empresa_id: int) -> None:
    if df.empty:
        st.info("No hay solicitudes para gestionar.")
        return
    opciones = {f"{r['folio']} · {DERECHOS_TITULAR_MAP.get(r['derecho'], r['derecho'])} · {r['titular_nombre']}": int(r["id"])
                for _, r in df.iterrows()}
    sel = st.selectbox("Solicitud", list(opciones.keys()), key="der_sel")
    s = df[df["id"] == opciones[sel]].iloc[0]
    sid, ingreso = int(s["id"]), _fecha(s["fecha_ingreso"])

    _detalle_plazos(s)
    with st.expander("Datos de la solicitud", expanded=False):
        st.write(f"**Titular:** {s['titular_nombre']} · **Responder a:** {s['titular_contacto'] or '—'}")
        st.write(f"**Representante:** {s['representante'] or '—'} · **Identidad verificada:** "
                 f"{'Sí' if s['identidad_verificada'] else 'No'} {('(' + s['metodo_verificacion'] + ')') if s['metodo_verificacion'] else ''}")
        st.write(f"**Canal:** {s['canal'] or '—'} · **Tratamiento:** {s['tratamiento'] or '—'}")
        st.write(f"**Detalle:** {s['descripcion'] or '—'}")
        if s["prorrogada"]:
            st.write(f"**Prórroga:** {s['prorroga_motivo']}")
        if s["fecha_respuesta"] is not None and pd.notna(s["fecha_respuesta"]):
            st.write(f"**Respuesta:** {_fecha(s['fecha_respuesta']):%d-%m-%Y} por {s['medio_respuesta'] or '—'}")
            if s["fundamento_respuesta"]:
                st.write(f"**Fundamento:** {s['fundamento_respuesta']}")

    st.markdown("#### Acciones")
    a1, a2 = st.columns(2)
    with a1:
        with st.form(f"form_acuse_{sid}"):
            f_acuse = st.date_input("Fecha de acuse de recibo", value=date.today(), max_value=date.today())
            if st.form_submit_button("Registrar acuse de recibo"):
                _aviso(*registrar_acuse(sid, empresa_id, f_acuse))
                st.rerun()
    with a2:
        if plazos.admite_prorroga(s["regimen"]) and not s["prorrogada"]:
            with st.form(f"form_prorroga_{sid}"):
                motivo = st.text_input("Motivo de la prórroga (única, hasta 30 días corridos)")
                if st.form_submit_button("Prorrogar plazo"):
                    _aviso(*prorrogar_solicitud(sid, empresa_id, ingreso, motivo))
                    st.rerun()
        elif s["prorrogada"]:
            st.caption("La prórroga ya fue utilizada (sólo procede una vez).")
        else:
            st.caption("La Ley 19.628 vigente no contempla prórroga.")

    if s["bloqueo_solicitado"] and not s["bloqueo_resultado"]:
        with st.form(f"form_bloqueo_{sid}"):
            b1, b2 = st.columns(2)
            resultado_b = b1.selectbox("Resolución del bloqueo temporal", ["acogido", "rechazado"])
            fecha_b = b2.date_input("Fecha de resolución", value=date.today(), max_value=date.today())
            st.caption("Si se rechaza, debe ser fundado (Ley 21.719 art. 11).")
            if st.form_submit_button("Registrar resolución del bloqueo"):
                _aviso(*resolver_bloqueo(sid, empresa_id, resultado_b, fecha_b))
                st.rerun()

    df_ev = get_evidencias_df(empresa_id=empresa_id)
    ev_ops = {"(Sin evidencia vinculada)": None}
    if not df_ev.empty:
        ev_ops.update({f"ID {r['id']} - {(r['descripcion'] or '')[:40]}": int(r["id"]) for _, r in df_ev.iterrows()})

    with st.form(f"form_respuesta_{sid}"):
        st.markdown("**Respuesta al titular**")
        r1, r2 = st.columns(2)
        estado_r = r1.selectbox("Resultado", [e[0] for e in _ESTADOS_RESPUESTA],
                                format_func=lambda k: dict(_ESTADOS_RESPUESTA)[k])
        fecha_r = r2.date_input("Fecha de respuesta", value=date.today(), max_value=date.today())
        medio_r = r1.text_input("Medio de envío", placeholder="Ej.: correo a la dirección indicada por el titular")
        evidencia_r = r2.selectbox("Respaldo del envío (evidencia)", list(ev_ops.keys()),
                                   help="Ley 21.719 art. 11: guardar respaldo de la remisión, su fecha y contenido íntegro.")
        fundamento_r = st.text_area("Fundamento (obligatorio si se deniega total o parcialmente)")
        if st.form_submit_button("Registrar respuesta", type="primary"):
            ok, msg = registrar_respuesta(sid, empresa_id, estado_r, fecha_r, medio_r,
                                          fundamento_r, ev_ops[evidencia_r])
            if ok and estado_r in ("denegada", "acogida_parcial"):
                if s["regimen"] == plazos.REGIMEN_21719:
                    limite = plazos.sumar_dias_habiles(fecha_r, plazos.PLAZO_RECLAMO_AGENCIA_DIAS_HABILES)
                    msg += (f" Recuerde informar al titular que dispone de 30 días hábiles para reclamar "
                            f"ante la Agencia (referencia: hasta el {limite:%d-%m-%Y}).")
                else:
                    msg += " El titular puede recurrir al juez de letras en lo civil (Ley 19.628 art. 16)."
            _aviso(ok, msg)
            st.rerun()


def _tab_base_legal() -> None:
    try:
        from addons.normativa import citas
    except Exception:
        st.info("El addon normativo no está disponible en esta instalación.")
        return
    for norma, art, titulo in [
        ("LEY-19628", "16", "Ley 19.628 vigente — plazo y amparo (hasta el 30-11-2026)"),
        ("LEY-19628", "12", "Ley 19.628 vigente — derechos del titular"),
        ("LEY-21719", "11", "Ley 21.719 — procedimiento ante el responsable (desde el 01-12-2026)"),
        ("LEY-21719", "10", "Ley 21.719 — forma, medios y gratuidad"),
    ]:
        for c in citas.obtener_articulo(norma, art)[:1]:
            with st.expander(titulo):
                st.markdown(c["texto"].replace("\n", "  \n"))
                st.caption(f'{c["norma_nombre"]} · {c["version"]}')
    st.caption(
        "Días hábiles: por criterio conservador el sábado se cuenta como hábil (configurable con "
        "LINCE_SABADO_HABIL=false). Pendiente de revisión profesional."
    )


def render() -> None:
    st.header("Derechos de los Titulares")
    st.caption(
        "Estándar dual: plazo exigible según la Ley 19.628 vigente o la Ley 21.719 (desde el 01-12-2026), "
        "determinado por la fecha de ingreso de cada solicitud."
    )
    df_empresas = get_empresas_df()
    if df_empresas.empty:
        st.warning("Primero debes registrar al menos una empresa.")
        return

    empresa_id = _selector_empresa(df_empresas)
    _mostrar_aviso()
    df = get_solicitudes_df(empresa_id=empresa_id)

    resumen = resumen_plazos(df)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("En plazo", resumen["en_plazo"])
    m2.metric("Por vencer", resumen["por_vencer"])
    m3.metric("Vencidas", resumen["vencida"])
    m4.metric("Respondidas", resumen["respondida"])

    t1, t2, t3, t4 = st.tabs(["Bandeja", "Nueva solicitud", "Gestionar", "§ Base legal"])
    with t1:
        _tab_bandeja(df)
    with t2:
        _tab_nueva(empresa_id)
    with t3:
        _tab_gestionar(df, empresa_id)
    with t4:
        _tab_base_legal()
