"""
Servicio de checklist de seguridad.
Centraliza la lógica de cálculo de puntaje y la presentación de respuestas.
El checklist de 15 preguntas se mantiene sin cambios desde la versión anterior.
"""

from utils.constants import CHECKLIST_PREGUNTAS, CHECKLIST_MAX_PUNTAJE


def calcular_puntaje(respuestas: dict) -> int:
    """
    Calcula el puntaje total del checklist.
    Regla: Sí = 1 punto, No = 0 puntos, N/A = 0 puntos.
    Retorna un entero entre 0 y CHECKLIST_MAX_PUNTAJE.
    """
    return sum(1 for v in respuestas.values() if v == "Sí")


def calcular_porcentaje(puntaje: int) -> float:
    """Retorna el porcentaje de cumplimiento (0.0 - 100.0)."""
    if CHECKLIST_MAX_PUNTAJE == 0:
        return 0.0
    return (puntaje / CHECKLIST_MAX_PUNTAJE) * 100


def nivel_cumplimiento(porcentaje: float) -> str:
    """
    Retorna etiqueta de nivel con ícono semafórico.
    Siempre incluye texto y porcentaje (nunca solo color).
    """
    if porcentaje >= 80:
        return f"🟢 Alto ({porcentaje:.1f}%)"
    if porcentaje >= 50:
        return f"🟡 Medio ({porcentaje:.1f}%)"
    if porcentaje >= 25:
        return f"🟠 Bajo ({porcentaje:.1f}%)"
    return f"🔴 Crítico ({porcentaje:.1f}%)"


def opciones_respuesta() -> list:
    """Retorna las opciones válidas de respuesta del checklist."""
    return ["Sí", "No", "N/A"]


def get_preguntas() -> list:
    """Retorna la lista de preguntas del checklist."""
    return CHECKLIST_PREGUNTAS


def icono_respuesta(respuesta: str) -> str:
    """Retorna ícono para cada tipo de respuesta."""
    return {"Sí": "✅", "No": "❌", "N/A": "⚪"}.get(respuesta, "⚪")
