"""
Lince GRC - Gobierno, Riesgo y Cumplimiento.
Punto de entrada principal (Streamlit Router).

Configura la página, ejecuta la barrera de autenticación temporal de desarrollo,
inicializa la base de datos y enruta la navegación hacia los módulos correspondientes.
"""

import os
import hmac
import streamlit as st
from db.migrations import init_db
from db.repositories.empresas import get_empresas_df

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
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #1E88E5;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stButton>button {
        border-radius: 6px;
        font-weight: 500;
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
st.sidebar.image("https://img.icons8.com/fluency/96/shield.png", width=70)
st.sidebar.title("Lince GRC")
st.sidebar.caption("Gobierno, Riesgo y Cumplimiento")

# ── Bloque persistente: Contexto de Empresa Activa ───────────────────────────
st.sidebar.markdown("---")
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
    st.sidebar.markdown("**🟢 EMPRESA ACTIVA**")
    st.sidebar.markdown(f"**{empresa_activa_data['nombre']}**")
    rut_emp = str(empresa_activa_data.get("rut") or "").strip()
    if rut_emp:
        st.sidebar.caption(f"RUT: {rut_emp}")
    st.sidebar.caption("Estado: **Seleccionada**")
    if st.sidebar.button("Cambiar empresa", key="btn_cambiar_empresa", use_container_width=True):
        st.session_state["nav_menu_principal"] = "🏢 Empresas"
        st.rerun()
else:
    st.sidebar.markdown("**EMPRESA ACTIVA**")
    st.sidebar.markdown("**Sin empresa seleccionada**")
    st.sidebar.caption("Seleccione una empresa antes de gestionar información GRC.")
    if st.sidebar.button("Ir a Empresas", key="btn_ir_a_empresas", use_container_width=True):
        st.session_state["nav_menu_principal"] = "🏢 Empresas"
        st.rerun()

st.sidebar.caption("ℹ️ *Contexto de navegación. Verifique la empresa seleccionada en cada formulario antes de guardar.*")
st.sidebar.markdown("---")

# ── Menú Principal ────────────────────────────────────────────────────────────
OPCIONES_MENU = [
    "🏠 Dashboard",
    "🏢 Empresas",
    "📁 Evaluaciones GRC",
    "🛡️ Perfil MPI y Delegado",
    "📋 Tratamientos (RAT)",
    "📥 Importar Antecedentes RAT",
    "🔍 Visitas / Auditorías",
    "📸 Evidencias",
    "📊 Exportar Informe",
]

nav_actual = st.session_state.get("nav_menu_principal", "🏠 Dashboard")
indice_nav = OPCIONES_MENU.index(nav_actual) if nav_actual in OPCIONES_MENU else 0

menu_opcion = st.sidebar.radio(
    "Menú Principal",
    OPCIONES_MENU,
    index=indice_nav,
    key="nav_menu_radio",
)
st.session_state["nav_menu_principal"] = menu_opcion

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reparar / Sincronizar Base de Datos"):
    init_db()
    st.sidebar.success("Estructura de base de datos sincronizada.")
    st.rerun()

# Botón funcional de cierre de sesión si la autenticación está habilitada
auth_env_actual = os.getenv("LINCE_AUTH_ENABLED", "true").strip().lower()
if auth_env_actual not in ("false", "0"):
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Cerrar sesión", key="btn_cerrar_sesion"):
        st.session_state["lince_authenticated"] = False
        st.rerun()

st.sidebar.info(
    "💡 **Tip Terreno:** Todos los cambios se guardan directamente en PostgreSQL "
    "y quedan sincronizados en tiempo real."
)

# ==============================================================================
# ENRUTAMIENTO DE MÓDULOS
# ==============================================================================
if menu_opcion == "🏠 Dashboard":
    dashboard.render()
elif menu_opcion == "🏢 Empresas":
    empresas.render()
elif menu_opcion == "📁 Evaluaciones GRC":
    evaluaciones.render()
elif menu_opcion == "🛡️ Perfil MPI y Delegado":
    mpi_gobernanza.render()
elif menu_opcion == "📋 Tratamientos (RAT)":
    tratamientos.render()
elif menu_opcion == "📥 Importar Antecedentes RAT":
    importar_antecedentes.render()
elif menu_opcion == "🔍 Visitas / Auditorías":
    visitas.render()
elif menu_opcion == "📸 Evidencias":
    evidencias.render()
elif menu_opcion == "📊 Exportar Informe":
    exportar.render()
