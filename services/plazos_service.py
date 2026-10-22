"""
Cálculo de plazos legales de las solicitudes de derechos de los titulares.

Router temporal (según la fecha de ingreso de la solicitud):
  - Hasta el 30-11-2026 rige la Ley 19.628: el responsable debe pronunciarse
    dentro de 2 días hábiles (art. 16). Sin prórroga. Si no responde, amparo
    ante el juez de letras en lo civil.
  - Desde el 01-12-2026 rige la Ley 19.628 reformada por la Ley 21.719 (art. 11):
    acusar recibo y pronunciarse dentro de 30 días corridos, prorrogables por
    una sola vez hasta por 30 días corridos. Bloqueo temporal: 2 días hábiles.
    Denegación: informar el plazo de 30 días hábiles para reclamar ante la Agencia.

Días hábiles: la ley no define si el sábado es hábil. Por defecto se aplica el
criterio CONSERVADOR (sábado hábil → plazo más corto). Configurable con
LINCE_SABADO_HABIL=false. Domingos y feriados (utils.constants.FERIADOS_CHILE)
nunca son hábiles. PENDIENTE DE REVISIÓN PROFESIONAL.

Sin dependencias de Streamlit ni de la base de datos.
"""

import os
from dataclasses import dataclass
from datetime import date, timedelta

from utils.constants import ESTADOS_SOLICITUD_RESPONDIDA, FERIADOS_CHILE

FECHA_REFORMA = date(2026, 12, 1)
REGIMEN_19628 = "LEY-19628"
REGIMEN_21719 = "LEY-21719"

PLAZO_19628_DIAS_HABILES = 2
PLAZO_21719_DIAS_CORRIDOS = 30
PRORROGA_21719_DIAS_CORRIDOS = 30
PLAZO_BLOQUEO_DIAS_HABILES = 2
PLAZO_RECLAMO_AGENCIA_DIAS_HABILES = 30

_FERIADOS = {date.fromisoformat(f) for f in FERIADOS_CHILE}


def sabado_es_habil() -> bool:
    return os.getenv("LINCE_SABADO_HABIL", "true").strip().lower() not in ("false", "0", "no")


def es_dia_habil(dia: date, sabado_habil: bool | None = None) -> bool:
    if sabado_habil is None:
        sabado_habil = sabado_es_habil()
    if dia in _FERIADOS or dia.weekday() == 6:  # domingo
        return False
    if dia.weekday() == 5:  # sábado
        return sabado_habil
    return True


def sumar_dias_habiles(desde: date, dias: int, sabado_habil: bool | None = None) -> date:
    """Fecha en que vence un plazo de `dias` hábiles contados desde el día siguiente a `desde`."""
    actual, contados = desde, 0
    while contados < dias:
        actual += timedelta(days=1)
        if es_dia_habil(actual, sabado_habil):
            contados += 1
    return actual


def regimen_aplicable(fecha_ingreso: date) -> str:
    return REGIMEN_21719 if fecha_ingreso >= FECHA_REFORMA else REGIMEN_19628


def admite_prorroga(regimen: str) -> bool:
    return regimen == REGIMEN_21719


def calcular_vencimiento(fecha_ingreso: date, prorrogada: bool = False,
                         sabado_habil: bool | None = None) -> date:
    """Vencimiento del plazo de respuesta según el régimen de la fecha de ingreso."""
    if regimen_aplicable(fecha_ingreso) == REGIMEN_19628:
        if prorrogada:
            raise ValueError("La Ley 19.628 vigente no contempla prórroga del plazo de respuesta.")
        return sumar_dias_habiles(fecha_ingreso, PLAZO_19628_DIAS_HABILES, sabado_habil)
    dias = PLAZO_21719_DIAS_CORRIDOS + (PRORROGA_21719_DIAS_CORRIDOS if prorrogada else 0)
    return fecha_ingreso + timedelta(days=dias)


def vencimiento_referencia_21719(fecha_ingreso: date) -> date | None:
    """
    Estándar dual: para solicitudes bajo la Ley 19.628 vigente, plazo que aplicaría
    con la Ley 21.719 (referencia de preparación, no exigible). None si ya rige la 21.719.
    """
    if regimen_aplicable(fecha_ingreso) == REGIMEN_21719:
        return None
    return fecha_ingreso + timedelta(days=PLAZO_21719_DIAS_CORRIDOS)


def calcular_vencimiento_bloqueo(fecha_ingreso: date, sabado_habil: bool | None = None) -> date:
    """Plazo para responder la solicitud de bloqueo temporal (Ley 21.719 art. 11)."""
    return sumar_dias_habiles(fecha_ingreso, PLAZO_BLOQUEO_DIAS_HABILES, sabado_habil)


@dataclass
class EstadoPlazo:
    codigo: str          # en_plazo | por_vencer | vencida | respondida
    etiqueta: str
    dias_restantes: int | None


def estado_plazo(estado_solicitud: str, fecha_vencimiento: date, regimen: str,
                 hoy: date | None = None) -> EstadoPlazo:
    """Semáforo del plazo. 'Por vencer': ≤ 5 días (régimen 21.719) o ≤ 1 día (2 días hábiles)."""
    hoy = hoy or date.today()
    if estado_solicitud in ESTADOS_SOLICITUD_RESPONDIDA:
        return EstadoPlazo("respondida", "● Respondida", None)
    restantes = (fecha_vencimiento - hoy).days
    if restantes < 0:
        return EstadoPlazo("vencida", f"■ VENCIDA ({-restantes} d)", restantes)
    umbral = 5 if regimen == REGIMEN_21719 else 1
    if restantes <= umbral:
        return EstadoPlazo("por_vencer", f"▲ Por vencer ({restantes} d)", restantes)
    return EstadoPlazo("en_plazo", f"◆ En plazo ({restantes} d)", restantes)


def descripcion_regimen(regimen: str) -> str:
    if regimen == REGIMEN_19628:
        return ("Ley 19.628 vigente (art. 16): pronunciarse dentro de 2 días hábiles, sin prórroga. "
                "Si no hay respuesta o se deniega, el titular puede recurrir al juez de letras en lo civil.")
    return ("Ley 21.719 (art. 11): acusar recibo y pronunciarse dentro de 30 días corridos, prorrogables "
            "una vez por 30 días corridos. Si se deniega, informar el plazo de 30 días hábiles para "
            "reclamar ante la Agencia (art. 41).")
