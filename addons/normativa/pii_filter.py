"""
Filtro de datos personales para el copiloto normativo.

Las consultas al copiloto deben ser normativas y no deben contener datos
personales. Antes de enviar una pregunta a un proveedor LLM se detectan
identificadores directos frecuentes en Chile (RUT, correo, teléfono). Si se
encuentran, la consulta se bloquea y se pide reformularla.

Es una salvaguarda, no una garantía: no detecta nombres ni datos indirectos.
"""

import re

_PATRONES = {
    "RUT": re.compile(r"\b\d{1,2}(?:\.\d{3}){2}-[\dkK]\b|\b\d{7,8}-[\dkK]\b"),
    "correo electrónico": re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b"),
    "teléfono": re.compile(r"(?<!\d)(?:\+?56[\s-]?)?(?:9[\s-]?\d{4}[\s-]?\d{4}|2[\s-]?\d{4}[\s-]?\d{4})(?!\d)"),
}


def detectar(texto: str) -> list[str]:
    """Tipos de dato personal detectados en el texto (lista vacía si no hay)."""
    if not texto:
        return []
    return [tipo for tipo, patron in _PATRONES.items() if patron.search(texto)]


def enmascarar(texto: str) -> str:
    """Reemplaza los identificadores detectados por marcadores, p. ej. [RUT]."""
    for tipo, patron in _PATRONES.items():
        texto = patron.sub(f"[{tipo.upper()}]", texto)
    return texto
