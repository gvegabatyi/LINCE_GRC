"""
Copiloto normativo (opcional) del addon.

Responde consultas en lenguaje natural sobre la normativa de protección de datos
usando SÓLO:
  - el corpus normativo verificado (addons/normativa/corpus), y
  - la base de conocimiento de la skill proteccion-datos-chile (conocimiento/).

Segregación de datos (regla de diseño, verificada por tests):
  - este módulo no importa db/, psycopg2 ni modules/ y no recibe datos de empresas;
  - las preguntas con identificadores personales (RUT, correo, teléfono) se bloquean
    antes de salir hacia el proveedor;
  - no se registran las preguntas.

Configuración por variables de entorno (desactivado por defecto):
  LINCE_COPILOTO_PROVEEDOR = desactivado | anthropic | ollama
  LINCE_COPILOTO_MODELO    = claude-opus-5-5 (anthropic) | llama3.1 (ollama), u otro
  ANTHROPIC_API_KEY        = credencial de la API de Anthropic (proveedor anthropic)
  OLLAMA_URL               = http://localhost:11434 (proveedor ollama)
"""

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path

from addons.normativa import citas, pii_filter

CONOCIMIENTO_DIR = Path(__file__).resolve().parent / "conocimiento"
PROVEEDORES = ("desactivado", "anthropic", "ollama")
MODELO_POR_DEFECTO = {"anthropic": "claude-opus-5-5", "ollama": "llama3.1"}
MAX_CITAS = 8

REGLAS_BASE = """Eres el copiloto normativo de Lince GRC, plataforma integral de cumplimiento e implementación de protección de datos personales en Chile (Ley 19.628 modificada por la Ley 21.719, Ley 21.663 Marco de Ciberseguridad y Decreto Supremo N° 662 sobre modelos de prevención de infracciones). El MPI es un componente voluntario; el cumplimiento de la ley alcanza a todo responsable.

Reglas obligatorias:
1. Responde en español, de forma clara y operativa.
2. Fundamenta cada afirmación normativa en los artículos entregados dentro de <articulos>. Cita norma y artículo, por ejemplo "(Ley 21.719, art. 14 sexies)".
3. Si los artículos entregados no bastan para responder, dilo expresamente ("sin respaldo en el corpus") y no inventes artículos, plazos ni montos.
4. Aplica el router temporal: hasta el 30-11-2026 rige la Ley 19.628 vigente; la Ley 21.719 y el DS 662 rigen desde el 01-12-2026 y antes de esa fecha son preparación (readiness). La fecha de hoy se indica en la consulta.
5. Distingue obligación legal de recomendación o buena práctica.
6. No asumas un plazo de 72 horas para reportar a la Agencia de Protección de Datos (la Ley 21.719 exige "sin dilaciones indebidas"); los plazos de la Ley 21.663 son ante el CSIRT Nacional y sólo para servicios esenciales u operadores de importancia vital.
7. El delegado de protección de datos no es obligatorio en general; sí lo es para adoptar y certificar un MPI (DS 662 art. 6). Todo responsable debe adoptar acciones de prevención (art. 48).
8. No solicites ni proceses datos personales de terceros. No tienes acceso a los datos de las empresas registradas en Lince.
9. Termina con una advertencia breve de revisión profesional cuando la consulta involucre sanciones, litigios o decisiones de alto impacto."""


@dataclass
class Respuesta:
    texto: str
    citas: list[dict] = field(default_factory=list)
    proveedor: str = "desactivado"
    bloqueada: bool = False


@dataclass
class Configuracion:
    proveedor: str
    modelo: str
    ollama_url: str

    @property
    def activo(self) -> bool:
        return self.proveedor in ("anthropic", "ollama")


def configuracion() -> Configuracion:
    proveedor = os.getenv("LINCE_COPILOTO_PROVEEDOR", "desactivado").strip().lower()
    if proveedor not in PROVEEDORES:
        proveedor = "desactivado"
    modelo = os.getenv("LINCE_COPILOTO_MODELO", "").strip() or MODELO_POR_DEFECTO.get(proveedor, "")
    return Configuracion(proveedor, modelo, os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/"))


@lru_cache(maxsize=1)
def base_conocimiento() -> str:
    """Skill proteccion-datos-chile (copia sincronizada), para el proveedor con contexto amplio."""
    partes = []
    for ruta in [CONOCIMIENTO_DIR / "SKILL.md", *sorted((CONOCIMIENTO_DIR / "references").glob("*.md"))]:
        partes.append(f'<documento nombre="{ruta.name}">\n{ruta.read_text(encoding="utf-8")}\n</documento>')
    return "\n\n".join(partes)


def recuperar_citas(pregunta: str) -> list[dict]:
    """Artículos citados expresamente + los más relevantes por búsqueda, sin duplicados."""
    resultado, vistos = [], set()
    for c in citas.referencias_explicitas(pregunta) + citas.buscar(pregunta, k=MAX_CITAS):
        clave = (c["norma"], c["articulo"])
        if clave not in vistos:
            vistos.add(clave)
            resultado.append(c)
    return resultado[:MAX_CITAS]


def _bloque_articulos(lista: list[dict]) -> str:
    bloques = [
        f'<articulo norma="{c["norma_nombre"]}" referencia="{c["etiqueta"]}" version="{c["version"]}">\n{c["texto"]}\n</articulo>'
        for c in lista
    ]
    return "<articulos>\n" + "\n".join(bloques) + "\n</articulos>"


def construir_consulta(pregunta: str, lista: list[dict], hoy: date | None = None) -> str:
    hoy = hoy or date.today()
    return f"{_bloque_articulos(lista)}\n\nFecha de hoy: {hoy.isoformat()}\n\nConsulta: {pregunta}"


def _llamar_anthropic(cfg: Configuracion, consulta: str, historial: list[dict]) -> str:
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError(
            "Falta el paquete 'anthropic'. Instálalo con: pip install -r addons/normativa/requirements-copiloto.txt"
        ) from exc

    client = anthropic.Anthropic()
    try:
        response = client.beta.messages.create(
            model=cfg.modelo,
            max_tokens=16000,
            # Si el modelo rechaza por sus filtros de seguridad, la API reintenta
            # con un modelo alternativo dentro de la misma llamada.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "high"},
            system=[
                {"type": "text", "text": REGLAS_BASE},
                # Bloque estable y extenso: se cachea entre consultas
                {"type": "text", "text": base_conocimiento(), "cache_control": {"type": "ephemeral"}},
            ],
            messages=historial + [{"role": "user", "content": consulta}],
        )
    except anthropic.AuthenticationError as exc:
        raise RuntimeError("Credencial de Anthropic inválida o ausente (ANTHROPIC_API_KEY).") from exc
    except anthropic.RateLimitError as exc:
        raise RuntimeError("Límite de uso de la API alcanzado. Intenta nuevamente en unos minutos.") from exc
    except anthropic.APIStatusError as exc:
        raise RuntimeError(f"La API de Anthropic respondió con error {exc.status_code}.") from exc
    except anthropic.APIConnectionError as exc:
        raise RuntimeError("No fue posible conectar con la API de Anthropic.") from exc

    if response.stop_reason == "refusal":
        return "El modelo no pudo responder esta consulta. Reformúlala en términos normativos generales."
    texto = "".join(b.text for b in response.content if b.type == "text").strip()
    if response.stop_reason == "max_tokens":
        texto += "\n\n_(Respuesta truncada por longitud.)_"
    return texto


def _llamar_ollama(cfg: Configuracion, consulta: str, historial: list[dict]) -> str:
    # Modelo local: contexto acotado, por eso sólo reglas base + artículos recuperados.
    cuerpo = json.dumps({
        "model": cfg.modelo,
        "stream": False,
        "messages": [{"role": "system", "content": REGLAS_BASE}, *historial, {"role": "user", "content": consulta}],
    }).encode("utf-8")
    req = urllib.request.Request(f"{cfg.ollama_url}/api/chat", data=cuerpo, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"No fue posible conectar con Ollama en {cfg.ollama_url}.") from exc
    return (data.get("message") or {}).get("content", "").strip()


_LLAMADAS = {"anthropic": _llamar_anthropic, "ollama": _llamar_ollama}


def responder(pregunta: str, historial: list[dict] | None = None, cfg: Configuracion | None = None) -> Respuesta:
    """
    Responde una consulta normativa. `historial` contiene sólo turnos previos del
    copiloto ({"role": "user"|"assistant", "content": str}), nunca datos de Lince.
    """
    cfg = cfg or configuracion()
    if not cfg.activo:
        return Respuesta("El copiloto está desactivado. Configura LINCE_COPILOTO_PROVEEDOR para habilitarlo.")

    detectados = pii_filter.detectar(pregunta)
    if detectados:
        return Respuesta(
            "La consulta parece contener datos personales (" + ", ".join(detectados) + "). "
            "El copiloto sólo responde consultas normativas: elimina esos datos y vuelve a preguntar.",
            proveedor=cfg.proveedor,
            bloqueada=True,
        )

    lista = recuperar_citas(pregunta)
    texto = _LLAMADAS[cfg.proveedor](cfg, construir_consulta(pregunta, lista), list(historial or []))
    return Respuesta(texto or "El proveedor no entregó respuesta.", lista, cfg.proveedor)
