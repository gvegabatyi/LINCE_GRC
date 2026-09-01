"""
Constantes globales de la aplicación Serviphar GRC Lite.
Centraliza listas de valores, textos de checklist y etiquetas de semáforo.
"""

# ==============================================================================
# CHECKLIST DE SEGURIDAD (15 PREGUNTAS — Mantenidas sin cambios desde Fase anterior)
# ==============================================================================
CHECKLIST_PREGUNTAS = [
    "1. ¿Cuenta con política de seguridad de la información documentada?",
    "2. ¿Existe un responsable de seguridad de la información?",
    "3. ¿Se realizan copias de seguridad periódicas?",
    "4. ¿Los sistemas tienen control de acceso con usuario y contraseña?",
    "5. ¿Las contraseñas cumplen con política de complejidad?",
    "6. ¿Existe control de acceso físico a las instalaciones?",
    "7. ¿El personal ha recibido capacitación en seguridad?",
    "8. ¿Existen procedimientos para gestión de incidentes?",
    "9. ¿Se realiza mantenimiento preventivo de equipos?",
    "10. ¿Existe política de uso aceptable de recursos TI?",
    "11. ¿Los datos sensibles están encriptados?",
    "12. ¿Existe control de cambios en sistemas críticos?",
    "13. ¿Se realizan evaluaciones de riesgo periódicas?",
    "14. ¿Existe plan de continuidad del negocio?",
    "15. ¿Se realizan auditorías internas de seguridad?",
]

CHECKLIST_MAX_PUNTAJE = len(CHECKLIST_PREGUNTAS)

# ==============================================================================
# TRATAMIENTOS / ROPA
# ==============================================================================
BASES_LEGALES = [
    "Consentimiento",
    "Ejecución de Contrato",
    "Obligación Legal",
    "Interés Legítimo",
    "Interés Público",
    "Protección de Intereses Vitales",
]

TRANSFERENCIAS_OPCIONES = [
    "No aplica",
    "Sí - Servidores Cloud (EE.UU.)",
    "Sí - Proveedores en UE",
    "Sí - Otros países",
]

# ==============================================================================
# VISITAS / AUDITORÍAS
# ==============================================================================
TIPOS_VISITA = [
    "Sin especificar",
    "Visita Bodega",
    "Visita Farmacia",
    "Entrevista RRHH",
    "Entrevista TI",
    "Entrevista Gerencia",
    "Revisión Documental",
    "Otro",
]

# ==============================================================================
# EVALUACIONES GRC
# ==============================================================================
TIPOS_EVALUACION = [
    "Diagnóstico Inicial",
    "Seguimiento",
    "Cierre",
    "Auditoría Interna",
]

ESTADOS_EVALUACION = [
    "borrador",
    "en_progreso",
    "en_revision",
    "cerrada",
]

# Etiquetas para mostrar en UI (estado → label con ícono)
ESTADO_EVALUACION_DISPLAY = {
    "borrador":    "🔵 Borrador",
    "en_progreso": "🟡 En Progreso",
    "en_revision": "🟠 En Revisión",
    "cerrada":     "✅ Cerrada",
}

# Colores semafóricos (CSS hex) por estado
ESTADO_EVALUACION_COLOR = {
    "borrador":    "#1565C0",   # Azul
    "en_progreso": "#F9A825",   # Amarillo
    "en_revision": "#E65100",   # Naranja
    "cerrada":     "#2E7D32",   # Verde
}

# ==============================================================================
# SEMÁFORO GENÉRICO DE PORCENTAJE
# ==============================================================================
def semaforo_porcentaje(valor: float) -> str:
    """Devuelve ícono + texto según porcentaje (0-100)."""
    if valor is None:
        return "⚪ Sin datos"
    if valor >= 80:
        return f"🟢 Alto ({valor:.0f}%)"
    if valor >= 50:
        return f"🟡 Medio ({valor:.0f}%)"
    if valor >= 25:
        return f"🟠 Bajo ({valor:.0f}%)"
    return f"🔴 Crítico ({valor:.0f}%)"
