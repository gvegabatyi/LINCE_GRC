"""
Análisis de riesgos: diagnóstico a partir de los datos de Lince, niveles y EIPD.

- `diagnosticar()` revisa el RAT, las auditorías y las solicitudes de derechos y
  PROPONE riesgos asociados a infracciones de la Ley 21.719 (arts. 34 bis-34 quáter).
  Las propuestas requieren aceptación humana antes de entrar al registro.
- `nivel_riesgo()` clasifica probabilidad × impacto (escala 1-5). Los umbrales
  son un criterio metodológico interno, no legal, y pueden ajustarse.
- `disparadores_eipd_detectados()` deduce disparadores del art. 15 ter desde el
  RAT; los que no son deducibles (b y c) se marcan manualmente en la EIPD.

Sin dependencias de Streamlit ni de la base de datos.
"""

from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from utils.constants import (
    ESTADOS_SOLICITUD_RESPONDIDA,
    IMPACTO_POR_GRAVEDAD,
    INFRACCIONES_LEY_21719,
)

# Umbrales de nivel sobre puntaje = probabilidad × impacto (1-25)
UMBRAL_MEDIO, UMBRAL_ALTO, UMBRAL_CRITICO = 5, 10, 15

CAMPOS_RAT = [
    "rat_tipo_datos_sensibles", "rat_ambito_territorial", "rat_bases_datos_administradas",
    "rat_categorias_titulares", "rat_finalidades", "rat_fuente_datos_acceso_publico",
    "rat_base_licitud_interes_legitimo", "rat_destinatarios_cesiones",
    "rat_transferencias_internacionales_art27", "rat_plazo_condicion_supresion",
    "rat_decisiones_automatizadas_perfilamiento",
]
_NEGATIVOS = {"", "no", "ninguno", "ninguna", "n/a", "na", "no aplica", "-", "sin", "nada", "no corresponde"}


def nivel_riesgo(probabilidad: int, impacto: int) -> tuple[int, str, str]:
    """(puntaje, código, etiqueta) para probabilidad e impacto entre 1 y 5."""
    if not (1 <= int(probabilidad) <= 5 and 1 <= int(impacto) <= 5):
        raise ValueError("Probabilidad e impacto deben estar entre 1 y 5.")
    p = int(probabilidad) * int(impacto)
    if p >= UMBRAL_CRITICO:
        return p, "critico", "CRÍTICO"
    if p >= UMBRAL_ALTO:
        return p, "alto", "ALTO"
    if p >= UMBRAL_MEDIO:
        return p, "medio", "MEDIO"
    return p, "bajo", "BAJO"


def impacto_sugerido(infraccion: str) -> int:
    gravedad = INFRACCIONES_LEY_21719[infraccion][0]
    return IMPACTO_POR_GRAVEDAD[gravedad]


def _texto(valor) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    return str(valor).strip()


def _afirmativo(valor) -> bool:
    """True si el campo describe algo presente (no vacío ni una negación explícita)."""
    return _texto(valor).lower().rstrip(".") not in _NEGATIVOS


@dataclass
class RiesgoPropuesto:
    codigo_regla: str
    titulo: str
    descripcion: str
    categoria: str
    infraccion: str
    probabilidad: int
    tratamiento_id: int | None = None
    origen: str = ""
    gravedad: str = field(init=False)
    impacto: int = field(init=False)

    def __post_init__(self):
        self.gravedad = INFRACCIONES_LEY_21719[self.infraccion][0]
        self.impacto = IMPACTO_POR_GRAVEDAD[self.gravedad]

    @property
    def clave(self) -> tuple:
        return (self.codigo_regla, self.tratamiento_id or 0)


def _reglas_tratamiento(t: pd.Series) -> list[RiesgoPropuesto]:
    tid, nombre = int(t["id"]), _texto(t.get("nombre_tratamiento")) or f"#{t['id']}"
    origen = f"RAT · {nombre}"
    r: list[RiesgoPropuesto] = []
    if not _texto(t.get("base_legal")) and not _texto(t.get("rat_base_licitud_interes_legitimo")):
        r.append(RiesgoPropuesto(
            "R-LIC", f"Tratamiento sin base de licitud registrada: {nombre}",
            "El RAT no identifica la base de licitud (consentimiento, contrato, obligación legal, interés legítimo u otra).",
            "licitud", "34 ter a", 4, tid, origen))
    if _afirmativo(t.get("rat_tipo_datos_sensibles")):
        r.append(RiesgoPropuesto(
            "R-SEN", f"Tratamiento de datos sensibles: {nombre}",
            "Incluye datos sensibles o de categorías especiales. Verificar consentimiento expreso o excepción legal "
            "(arts. 16 y 16 bis) y evaluar EIPD (art. 15 ter d).",
            "sensibles", "34 quater e", 3, tid, origen))
    if _afirmativo(t.get("rat_decisiones_automatizadas_perfilamiento")):
        r.append(RiesgoPropuesto(
            "R-AUT", f"Decisiones automatizadas o perfilamiento: {nombre}",
            "Si producen efectos jurídicos significativos, la EIPD es obligatoria (art. 15 ter a) y su omisión es "
            "infracción gravísima. Revisar también los derechos del art. 8 bis.",
            "automatizadas", "34 quater k", 3, tid, origen))
    if _afirmativo(t.get("rat_transferencias_internacionales_art27")):
        r.append(RiesgoPropuesto(
            "R-TRI", f"Transferencia internacional de datos: {nombre}",
            "Verificar el mecanismo del art. 27 (país adecuado, cláusulas o garantías, o excepción) y su evidencia.",
            "transferencias", "34 ter m", 3, tid, origen))
    if not _texto(t.get("rat_plazo_condicion_supresion")):
        r.append(RiesgoPropuesto(
            "R-SUP", f"Sin plazo de conservación o supresión definido: {nombre}",
            "Sin plazo de conservación, los datos pueden mantenerse más allá de lo necesario (proporcionalidad, art. 3 c).",
            "proporcionalidad", "34 ter c", 3, tid, origen))
    if _afirmativo(t.get("encargados")):
        r.append(RiesgoPropuesto(
            "R-ENC", f"Tratamiento con encargados o proveedores: {nombre}",
            "Verificar contrato de encargo con el contenido mínimo del art. 15 bis y las medidas de seguridad del encargado.",
            "terceros", "34 ter j", 2, tid, origen))
    vacios = [c for c in CAMPOS_RAT if not _texto(t.get(c))]
    if vacios:
        r.append(RiesgoPropuesto(
            "R-TRA", f"Caracterización incompleta en el RAT: {nombre}",
            f"{len(vacios)} de 11 numerales sin completar (DS 662 art. 3 d). Sin esta información no puede "
            "cumplirse el deber de información y transparencia (art. 14 ter).",
            "transparencia", "34 bis a", 3, tid, origen))
    return r


def _regla_seguridad(visitas: pd.DataFrame) -> list[RiesgoPropuesto]:
    if visitas is None or visitas.empty or "checklist_seguridad" not in visitas.columns:
        return []
    ultima = visitas.sort_values("fecha_visita", ascending=False).iloc[0]
    checklist = ultima["checklist_seguridad"] or {}
    if isinstance(checklist, str):
        import json
        checklist = json.loads(checklist or "{}")
    negativos = [p for p, resp in checklist.items() if resp == "No"]
    if not negativos:
        return []
    prob = 4 if len(negativos) >= len(checklist) / 2 else 3
    return [RiesgoPropuesto(
        "R-SEG", f"Controles de seguridad insuficientes en la última auditoría ({len(negativos)} de {len(checklist)})",
        "Controles con respuesta 'No': " + "; ".join(p.split(". ", 1)[-1] for p in negativos[:6])
        + ("…" if len(negativos) > 6 else "") + ". Medidas de seguridad del art. 14 quinquies.",
        "seguridad", "34 ter j", prob, None, f"Auditoría del {str(ultima['fecha_visita'])[:10]}")]


def _reglas_derechos(solicitudes: pd.DataFrame, hoy: date) -> list[RiesgoPropuesto]:
    if solicitudes is None or solicitudes.empty:
        return []
    abiertas = solicitudes[~solicitudes["estado"].isin(ESTADOS_SOLICITUD_RESPONDIDA)]
    r: list[RiesgoPropuesto] = []
    vencidas = abiertas[pd.to_datetime(abiertas["fecha_vencimiento"]).dt.date < hoy]
    if not vencidas.empty:
        r.append(RiesgoPropuesto(
            "R-DER", f"Solicitudes de derechos con plazo vencido ({len(vencidas)})",
            "Folios: " + ", ".join(vencidas["folio"].astype(str).tolist()[:10]) + ". Responder fuera de plazo es infracción.",
            "derechos", "34 bis c", 4, None, "Derechos de los titulares"))
    bloqueos = solicitudes[(solicitudes["bloqueo_solicitado"]) & (solicitudes["bloqueo_resultado"].fillna("") == "")]
    if not bloqueos.empty:
        venc = pd.to_datetime(bloqueos["bloqueo_vencimiento"]).dt.date
        atrasados = bloqueos[venc < hoy]
        if not atrasados.empty:
            r.append(RiesgoPropuesto(
                "R-BLQ", f"Bloqueos temporales sin responder en plazo ({len(atrasados)})",
                "El bloqueo temporal debe responderse dentro de 2 días hábiles (Ley 21.719 art. 11).",
                "derechos", "34 ter f", 4, None, "Derechos de los titulares"))
    return r


def diagnosticar(tratamientos: pd.DataFrame, visitas: pd.DataFrame | None = None,
                 solicitudes: pd.DataFrame | None = None, hoy: date | None = None) -> list[RiesgoPropuesto]:
    """Riesgos propuestos a partir de los datos de una empresa."""
    hoy = hoy or date.today()
    propuestos: list[RiesgoPropuesto] = []
    if tratamientos is not None and not tratamientos.empty:
        for _, t in tratamientos.iterrows():
            propuestos += _reglas_tratamiento(t)
    propuestos += _regla_seguridad(visitas)
    propuestos += _reglas_derechos(solicitudes, hoy)
    return propuestos


def disparadores_eipd_detectados(tratamiento: pd.Series) -> set[str]:
    """
    Disparadores del art. 15 ter deducibles del RAT (a y d). Son indicios que el
    usuario debe confirmar: el literal d exige además que el tratamiento opere en
    las hipótesis de excepción del consentimiento.
    """
    detectados = set()
    if _afirmativo(tratamiento.get("rat_decisiones_automatizadas_perfilamiento")):
        detectados.add("a")
    if _afirmativo(tratamiento.get("rat_tipo_datos_sensibles")):
        detectados.add("d")
    return detectados
