"""
Página Streamlit del addon normativo: citas, búsqueda y copiloto.

No usa la base de datos ni la empresa activa: el contenido es normativo y común
a todas las empresas, por lo que no aplica el filtro empresa_id.
"""

import streamlit as st

from addons.normativa import citas, copiloto

_CLAVE_HISTORIAL = "normativa_copiloto_historial"


def _mostrar_cita(c: dict, expandido: bool = True) -> None:
    titulo = f'{c["norma_nombre"]} — {c["etiqueta"]}'
    with st.expander(titulo, expanded=expandido):
        st.markdown(c["texto"].replace("\n", "  \n"))
        st.caption(f'Versión: {c["version"]} · {citas.regimen_temporal(c["norma"])}')


def _tab_articulo(normas: list[dict]) -> None:
    nombres = {n["nombre"]: n["codigo"] for n in normas}
    col1, col2 = st.columns([3, 1])
    nombre = col1.selectbox("Norma", list(nombres), key="normativa_sel_norma")
    articulo = col2.text_input("Artículo", placeholder="14 sexies", key="normativa_art")
    if st.button("Ver artículo", key="normativa_btn_art", type="primary"):
        if not articulo.strip():
            st.warning("Indica el número de artículo (por ejemplo: 3, 14 sexies, sexto transitorio).")
            return
        resultado = citas.obtener_articulo(nombres[nombre], articulo)
        if not resultado:
            st.info("Sin respaldo en el corpus para ese artículo.")
        for c in resultado:
            _mostrar_cita(c)


def _tab_buscar(normas: list[dict]) -> None:
    consulta = st.text_input("Consulta", placeholder="plazo para reportar una vulneración de seguridad", key="normativa_q")
    col1, col2 = st.columns([3, 1])
    filtro = col1.multiselect("Limitar a", [n["codigo"] for n in normas], key="normativa_filtro")
    k = col2.number_input("Resultados", min_value=1, max_value=15, value=5, key="normativa_k")
    if st.button("Buscar", key="normativa_btn_buscar", type="primary") and consulta.strip():
        resultados = citas.buscar(consulta, k=int(k), normas=filtro or None)
        if not resultados:
            st.info("Sin resultados en el corpus.")
        for i, c in enumerate(resultados):
            _mostrar_cita(c, expandido=(i == 0))


def _tab_copiloto() -> None:
    cfg = copiloto.configuracion()
    st.caption(
        "El copiloto responde sólo con el corpus normativo verificado. **No accede a los datos de Lince** "
        "(empresas, tratamientos, delegados, evidencias). No ingreses datos personales."
    )
    if not cfg.activo:
        st.info(
            "Copiloto desactivado. Para habilitarlo define `LINCE_COPILOTO_PROVEEDOR` = `anthropic` "
            "(con `ANTHROPIC_API_KEY`) u `ollama` (modelo local, `OLLAMA_URL`). Ver `addons/normativa/README.md`."
        )
        return
    st.caption(f"Proveedor: **{cfg.proveedor}** · Modelo: `{cfg.modelo}`")

    historial = st.session_state.setdefault(_CLAVE_HISTORIAL, [])
    for turno in historial:
        with st.chat_message(turno["role"]):
            st.markdown(turno["content"])

    with st.form("normativa_form_copiloto", clear_on_submit=True):
        pregunta = st.text_area("Consulta normativa", placeholder="¿Cuándo debo informar una brecha a los titulares?")
        enviar = st.form_submit_button("Consultar", type="primary")
    if st.button("Limpiar conversación", key="normativa_btn_limpiar"):
        st.session_state[_CLAVE_HISTORIAL] = []
        st.rerun()

    if enviar and pregunta.strip():
        try:
            with st.spinner("Consultando el corpus normativo..."):
                resp = copiloto.responder(pregunta, historial)
        except Exception as exc:  # error del proveedor: se muestra sin trazas
            st.error(f"No fue posible obtener respuesta del copiloto: {exc}")
            return
        if resp.bloqueada:
            st.warning(resp.texto)
            return
        historial += [{"role": "user", "content": pregunta}, {"role": "assistant", "content": resp.texto}]
        with st.chat_message("assistant"):
            st.markdown(resp.texto)
        if resp.citas:
            st.markdown("**Artículos consultados**")
            for c in resp.citas:
                _mostrar_cita(c, expandido=False)


def render() -> None:
    st.header("Normativa")
    st.caption(
        "Citas literales de la Ley 19.628, Ley 21.719, Ley 21.663 y Decreto Supremo N° 662, "
        "desde el corpus oficial verificado del proyecto."
    )
    try:
        normas = citas.listar_normas()
    except Exception:
        st.error("No fue posible cargar el corpus normativo (addons/normativa/corpus).")
        return

    tab1, tab2, tab3 = st.tabs(["Consultar artículo", "Buscar", "Copiloto"])
    with tab1:
        _tab_articulo(normas)
    with tab2:
        _tab_buscar(normas)
    with tab3:
        _tab_copiloto()
