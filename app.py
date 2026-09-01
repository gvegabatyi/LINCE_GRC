"""
Serviphar GRC Lite - Plataforma Web de Auditoría y Cumplimiento GRC.
Punto de entrada principal (Streamlit Router).

Configura la página, inicializa/migra la base de datos de forma segura
y enruta la navegación hacia los módulos correspondientes.
"""

import streamlit as st
from db.migrations import init_db

# Importación de módulos UI (rutas absolutas desde la raíz del proyecto)
from modules import (
    dashboard,
    empresas,
    evaluaciones,
    tratamientos,
    visitas,
    evidencias,
    exportar,
)

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Serviphar GRC Lite",
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
# INICIALIZACIÓN Y CONTROL DE BASE DE DATOS
# ==============================================================================
# Ejecuta validaciones y migraciones idempotentes de Fase 1
init_db()

# ==============================================================================
# MENÚ LATERAL Y NAVEGACIÓN
# ==============================================================================
st.sidebar.image("https://img.icons8.com/fluency/96/shield.png", width=70)
st.sidebar.title("Serviphar GRC Lite")
st.sidebar.caption("Plataforma de Auditoría y Cumplimiento Legal")

menu_opcion = st.sidebar.radio(
    "Menú Principal",
    [
        "🏠 Dashboard",
        "🏢 Empresas",
        "📁 Evaluaciones GRC",
        "📋 Tratamientos (ROPA)",
        "🔍 Visitas / Auditorías",
        "📸 Evidencias",
        "📊 Exportar Informe",
    ],
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reparar / Sincronizar Base de Datos"):
    init_db()
    st.sidebar.success("Estructura de base de datos sincronizada.")
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
elif menu_opcion == "📋 Tratamientos (ROPA)":
    tratamientos.render()
elif menu_opcion == "🔍 Visitas / Auditorías":
    visitas.render()
elif menu_opcion == "📸 Evidencias":
    evidencias.render()
elif menu_opcion == "📊 Exportar Informe":
    exportar.render()
