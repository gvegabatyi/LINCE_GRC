"""
Lince GRC - Gobierno, Riesgo y Cumplimiento.
Punto de entrada principal (Streamlit Router).

Configura la página, ejecuta la barrera de autenticación temporal de desarrollo,
inicializa la base de datos y enruta la navegación hacia los módulos correspondientes.
"""

import os
import hmac
import streamlit as st
from db.connection import _load_env_file
from db.migrations import init_db
from db.repositories.empresas import get_empresas_df

# Cargar configuración desde .env si existe antes de verificar accesos
_load_env_file()

# Importación de módulos UI (rutas absolutas desde la raíz del proyecto)
from modules import (
    dashboard,
    empresas,
    evaluaciones,
    mpi_gobernanza,
    tratamientos,
    visitas,
    evidencias,
    exportar,
    importar_antecedentes,
)

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Lince GRC",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS profesionales (Paleta Terminal Técnico de Alto Contraste)
st.markdown("""
<style>
    /* Ocultar barra decorativa superior nativa de Streamlit */
    [data-testid="stDecoration"] {
        display: none !important;
    }

    /* Eliminar barra superior y bordes nativos */
    header[data-testid="stHeader"] {
        background: transparent !important;
        border: none !important;
        border-bottom: none !important;
        box-shadow: none !important;
    }
    [data-testid="stToolbar"], .stDeployButton, [data-testid="stDeployButton"] {
        display: none !important;
    }
    #MainMenu, footer {
        visibility: hidden !important;
    }

    /* Ajustar espaciado superior */
    .block-container {
        padding-top: 1.5rem !important;
    }

    /* Fondo general */
    .stApp {
        background-color: #0B0F19 !important;
    }

    /* Tipografía nítida de alto contraste */
    .stApp, .stApp p, .stApp span, .stApp label, .stMarkdown p {
        color: #E2E8F0 !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
    }
    .stCaption, [data-testid="stCaptionContainer"] p {
        color: #94A3B8 !important;
    }

    /* Tarjetas de métricas del Dashboard (Contenedor Terminal) */
    [data-testid="stMetric"] {
        background-color: #161F30 !important;
        border: 1px solid #1E293B !important;
        border-left: 3px solid #0EA5E9 !important;
        border-radius: 8px !important;
        padding: 14px 18px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4) !important;
    }
    [data-testid="stMetricValue"] div {
        color: #38BDF8 !important; /* Azul eléctrico legible */
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        font-family: monospace, sans-serif !important;
    }
    [data-testid="stMetricLabel"] p {
        color: #CBD5E1 !important; /* Gris claro de alto contraste */
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    [data-testid="stMetricDelta"] div {
        color: #94A3B8 !important;
    }

    /* Cajas de alerta e informativas (st.info, st.warning) */
    [data-testid="stAlert"] {
        background-color: #161F30 !important;
        border: 1px solid #1E293B !important;
        border-left: 4px solid #0EA5E9 !important;
        border-radius: 6px !important;
    }
    [data-testid="stAlert"] * {
        color: #CBD5E1 !important;
    }

    /* Barra lateral */
    [data-testid="stSidebar"] {
        background-color: #0D1524 !important;
        border-right: 1px solid #1E293B !important;
    }
    [data-testid="stSidebar"] * {
        color: #CBD5E1 !important;
    }
    [data-testid="stSidebar"] strong {
        color: #FFFFFF !important;
    }

    /* Botones oscuros elegantes estilo terminal */
    .stButton > button {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover {
        background-color: #0EA5E9 !important;
        color: #FFFFFF !important;
        border-color: #38BDF8 !important;
    }

    /* Radio buttons del menú lateral */
    div[data-testid="stRadio"] label {
        color: #CBD5E1 !important;
        font-size: 0.95rem !important;
        padding: 4px 0 !important;
    }
    div[data-testid="stRadio"] label:hover {
        color: #38BDF8 !important;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# BARRERA DE ACCESO TEMPORAL (ENTORNO DE DESARROLLO)
# ==============================================================================
def _verificar_acceso_temporal() -> None:
    """
    Controla el acceso al despliegue público en desarrollo mediante contraseña única.
    Activo por defecto salvo que LINCE_AUTH_ENABLED sea explícitamente 'false' o '0'.
    Detiene la ejecución antes de cualquier consulta a base de datos o módulo.
    """
    auth_env = os.getenv("LINCE_AUTH_ENABLED", "true").strip().lower()
    auth_activo = auth_env not in ("false", "0")

    if not auth_activo:
        return

    if "lince_authenticated" not in st.session_state:
        st.session_state["lince_authenticated"] = False

    if st.session_state["lince_authenticated"]:
        return

    clave_servidor = os.getenv("LINCE_ACCESS_PASSWORD")

    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.title("🛡️ Lince GRC")
        st.caption("Gobierno, Riesgo y Cumplimiento")
        st.markdown("---")
        st.subheader("Acceso restringido")
        st.write("Ingrese la contraseña de desarrollo para continuar.")

        if not clave_servidor:
            st.error(
                "Acceso no configurado. Configure la variable LINCE_ACCESS_PASSWORD en el entorno de despliegue."
            )
            st.stop()

        with st.form("form_lince_login", clear_on_submit=True):
            clave_ingresada = st.text_input("Contraseña de desarrollo", type="password")
            btn_ingresar = st.form_submit_button("Ingresar", type="primary")

            if btn_ingresar:
                if clave_ingresada and hmac.compare_digest(
                    clave_ingresada.encode("utf-8"),
                    clave_servidor.encode("utf-8"),
                ):
                    st.session_state["lince_authenticated"] = True
                    st.rerun()
                else:
                    st.error("Credenciales de acceso no válidas.")

    st.stop()


# Ejecutar verificación de acceso de forma temprana
_verificar_acceso_temporal()


# ==============================================================================
# INICIALIZACIÓN Y CONTROL DE BASE DE DATOS (UNA VEZ POR INSTANCIA)
# ==============================================================================
@st.cache_resource(show_spinner=False)
def _inicializar_base_una_vez() -> bool:
    """
    Ejecuta validaciones y migraciones idempotentes de Fase 1 y Fase 2A
    exactamente una vez por ciclo de vida de la instancia de Streamlit.
    """
    init_db()
    return True


# Ejecutar inicialización de base de datos solo después de confirmar autenticación
_inicializar_base_una_vez()


# ==============================================================================
# MENÚ LATERAL Y NAVEGACIÓN
# ==============================================================================
st.sidebar.markdown("""
<div style="padding: 6px 0 14px 0; border-bottom: 1px solid #1E293B; margin-bottom: 12px;">
    <div style="font-size: 1.35rem; font-weight: 800; color: #38BDF8; letter-spacing: 0.05em;">◈ LINCE GRC</div>
    <div style="font-size: 0.72rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.1em; font-family: monospace;">Terminal Control // v2.0</div>
</div>
""", unsafe_allow_html=True)

# ── Bloque persistente: Contexto de Empresa Activa ───────────────────────────
empresa_activa_id = st.session_state.get("empresa_activa_id")
df_todas_empresas = get_empresas_df()
empresa_activa_data = None

if empresa_activa_id and not df_todas_empresas.empty:
    filtro_emp = df_todas_empresas[df_todas_empresas["id"] == empresa_activa_id]
    if not filtro_emp.empty:
        empresa_activa_data = filtro_emp.iloc[0]
    else:
        st.session_state.pop("empresa_activa_id", None)
        empresa_activa_id = None

if empresa_activa_data is not None:
    st.sidebar.markdown("**◈ EMPRESA ACTIVA**")
    st.sidebar.markdown(f"**{empresa_activa_data['nombre']}**")
    rut_emp = str(empresa_activa_data.get("rut") or "").strip()
    if rut_emp:
        st.sidebar.caption(f"RUT: {rut_emp}")
    st.sidebar.caption("Estado: **Seleccionada**")
    if st.sidebar.button("Cambiar empresa", key="btn_cambiar_empresa", use_container_width=True):
        st.session_state["nav_menu_principal"] = "▣ Empresas"
        st.rerun()
else:
    st.sidebar.markdown("**◈ EMPRESA ACTIVA**")
    st.sidebar.markdown("**Sin empresa seleccionada**")
    st.sidebar.caption("Seleccione una empresa antes de gestionar información GRC.")
    if st.sidebar.button("Ir a Empresas", key="btn_ir_a_empresas", use_container_width=True):
        st.session_state["nav_menu_principal"] = "▣ Empresas"
        st.rerun()

st.sidebar.caption("ℹ️ *Contexto de navegación. Verifique la empresa seleccionada antes de guardar.*")
st.sidebar.markdown("---")

# ── Menú Principal ────────────────────────────────────────────────────────────
OPCIONES_MENU = [
    "◈ Dashboard",
    "▣ Empresas",
    "◬ Evaluaciones GRC",
    "◆ Perfil MPI y Delegado",
    "☷ Tratamientos (RAT)",
    "⤓ Importar Antecedentes RAT",
    "⌖ Visitas / Auditorías",
    "◫ Evidencias",
    "⇲ Exportar Informe",
]

def _normalizar_opcion_menu(opcion: str) -> str:
    if not opcion:
        return "◈ Dashboard"
    for opt in OPCIONES_MENU:
        clave = opt.split(" ", 1)[-1].strip()
        if clave in opcion:
            return opt
    return "◈ Dashboard"

nav_actual = _normalizar_opcion_menu(st.session_state.get("nav_menu_principal", "◈ Dashboard"))
indice_nav = OPCIONES_MENU.index(nav_actual) if nav_actual in OPCIONES_MENU else 0

menu_opcion = st.sidebar.radio(
    "Menú Principal",
    OPCIONES_MENU,
    index=indice_nav,
    key="nav_menu_radio",
)
st.session_state["nav_menu_principal"] = menu_opcion

st.sidebar.markdown("---")
if st.sidebar.button("⟳ Sincronizar Base de Datos"):
    init_db()
    st.sidebar.success("Estructura de base de datos sincronizada.")
    st.rerun()

# Botón funcional de cierre de sesión si la autenticación está habilitada
auth_env_actual = os.getenv("LINCE_AUTH_ENABLED", "true").strip().lower()
if auth_env_actual not in ("false", "0"):
    st.sidebar.markdown("---")
    if st.sidebar.button("⏻ Cerrar sesión", key="btn_cerrar_sesion"):
        st.session_state["lince_authenticated"] = False
        st.rerun()

st.sidebar.caption(
    "◈ **Control Local:** Base de datos PostgreSQL en Docker activa y sincronizada en tiempo real."
)

# ==============================================================================
# ENRUTAMIENTO DE MÓDULOS
# ==============================================================================
if "Dashboard" in menu_opcion:
    dashboard.render()
elif "Empresas" in menu_opcion:
    empresas.render()
elif "Evaluaciones" in menu_opcion:
    evaluaciones.render()
elif "Perfil MPI" in menu_opcion:
    mpi_gobernanza.render()
elif "Tratamientos" in menu_opcion:
    tratamientos.render()
elif "Importar" in menu_opcion:
    importar_antecedentes.render()
elif "Visitas" in menu_opcion:
    visitas.render()
elif "Evidencias" in menu_opcion:
    evidencias.render()
elif "Exportar" in menu_opcion:
    exportar.render()
