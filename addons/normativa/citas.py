"""
Motor de citas normativas del addon.

Lee el corpus verificado (addons/normativa/corpus/*.json) y permite:
- recuperar el texto literal de un artículo (norma + número);
- buscar artículos por relevancia (BM25, sin dependencias externas);
- indicar el régimen temporal aplicable a una norma en una fecha.

Segregación: este módulo NO accede a la base de datos de Lince ni a datos de
empresas. Sólo lee archivos de sólo lectura del corpus.
"""

import json
import math
import re
import unicodedata
from collections import Counter
from datetime import date
from functools import lru_cache
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent / "corpus"
FECHA_REFORMA = date(2026, 12, 1)

# Alias de entrada para el usuario -> código de norma del corpus
ALIAS_NORMAS = {
    "19628": "LEY-19628", "19.628": "LEY-19628",
    "21719": "LEY-21719", "21.719": "LEY-21719",
    "21663": "LEY-21663", "21.663": "LEY-21663",
    "662": "DEC-662-HAC", "ds662": "DEC-662-HAC", "decreto": "DEC-662-HAC", "reglamento": "DEC-662-HAC",
}

_STOPWORDS = set(
    "a al algo ante antes como con contra cual cuando de del desde donde e el ella ellas ellos en entre era es esa "
    "ese eso esta este esto estos fue ha han hasta la las le les lo los mas me mi muy no nos o otra otro para pero "
    "por que quien se sea segun ser si sin sobre son su sus tambien te tiene todo tu un una uno unos y ya "
    "articulo articulos ley inciso letra".split()
)


def normalizar(texto: str) -> str:
    s = unicodedata.normalize("NFKD", texto.lower().replace("°", "").replace("º", ""))
    return s.encode("ascii", "ignore").decode()


def _raiz(t: str) -> str:
    """Stemming mínimo singular/plural: vulneraciones -> vulneracion, datos -> dato."""
    if len(t) > 5 and t.endswith("iones"):
        return t[:-2]
    if len(t) > 4 and t.endswith("es") and t[-3] not in "aeiou":
        return t[:-2]
    if len(t) > 3 and t.endswith("s"):
        return t[:-1]
    return t


def _tokens(texto: str) -> list[str]:
    return [_raiz(t) for t in re.findall(r"[a-z0-9]+", normalizar(texto)) if t not in _STOPWORDS and len(t) > 1]


def normalizar_articulo(etiqueta: str) -> str:
    s = normalizar(etiqueta)
    s = re.sub(r"\b(art(iculo)?\.?)\s*", "", s)
    return re.sub(r"\s+", " ", s).strip()


@lru_cache(maxsize=1)
def cargar_corpus() -> dict:
    """Devuelve {codigo: datos_norma}. Cacheado: el corpus es de sólo lectura."""
    normas = {}
    for ruta in sorted(CORPUS_DIR.glob("*.json")):
        data = json.loads(ruta.read_text(encoding="utf-8"))
        normas[data["codigo"]] = data
    return normas


ORDEN_NORMAS = ["LEY-21719", "DEC-662-HAC", "LEY-19628", "LEY-21663"]


def listar_normas() -> list[dict]:
    """Metadatos de las normas, en orden de uso habitual (Ley 21.719 primero)."""
    corpus = cargar_corpus()
    orden = [c for c in ORDEN_NORMAS if c in corpus] + [c for c in corpus if c not in ORDEN_NORMAS]
    return [{k: v for k, v in corpus[c].items() if k != "articulos"} | {"n_articulos": len(corpus[c]["articulos"])}
            for c in orden]


def resolver_norma(texto: str) -> str | None:
    """Código de norma a partir de un código exacto o de una mención ('ley 21.719', 'DS 662')."""
    if texto in cargar_corpus():
        return texto
    t = normalizar(texto).replace(" ", "")
    for alias, codigo in ALIAS_NORMAS.items():
        if alias in t:
            return codigo
    return None


def _cita(codigo: str, art: dict, score: float | None = None) -> dict:
    norma = cargar_corpus()[codigo]
    cita = {
        "norma": codigo,
        "norma_nombre": norma["nombre"],
        "version": norma["version"],
        "articulo": art["articulo"],
        "etiqueta": art["etiqueta"],
        "texto": art["texto"],
        "modifica": art.get("modifica"),
    }
    if score is not None:
        cita["score"] = round(score, 3)
    return cita


def obtener_articulo(codigo: str, articulo: str) -> list[dict]:
    """
    Texto literal de un artículo. En la Ley 21.719 también devuelve las
    instrucciones de modificación que recaen sobre ese artículo (p. ej. el art. 2,
    cuyas letras se reemplazan mediante el artículo primero, numeral 5).
    Lista vacía = sin respaldo en el corpus.
    """
    norma = cargar_corpus().get(codigo)
    if not norma:
        return []
    buscado = normalizar_articulo(articulo)
    directos = [a for a in norma["articulos"] if a["articulo"] == buscado]
    modificaciones = [a for a in norma["articulos"] if a.get("modifica") == buscado]
    return [_cita(codigo, a) for a in directos + modificaciones]


class _IndiceBM25:
    def __init__(self, docs: list[tuple[str, dict]], k1: float = 1.4, b: float = 0.75):
        self.docs = docs
        self.k1, self.b = k1, b
        self.tf = [Counter(_tokens(f'{a["etiqueta"]} {a["texto"]}')) for _, a in docs]
        self.largos = [sum(c.values()) for c in self.tf]
        self.promedio = sum(self.largos) / max(len(self.largos), 1)
        df = Counter(t for c in self.tf for t in c)
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def buscar(self, consulta: str, k: int, normas: set[str] | None) -> list[tuple[float, int]]:
        q = _tokens(consulta)
        puntajes = []
        for i, tf in enumerate(self.tf):
            if normas and self.docs[i][0] not in normas:
                continue
            s = 0.0
            for t in q:
                f = tf.get(t)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.largos[i] / self.promedio))
            if s > 0:
                puntajes.append((s, i))
        return sorted(puntajes, reverse=True)[:k]


@lru_cache(maxsize=1)
def _indice() -> _IndiceBM25:
    return _IndiceBM25([(codigo, a) for codigo, d in cargar_corpus().items() for a in d["articulos"]])


def buscar(consulta: str, k: int = 5, normas: list[str] | None = None) -> list[dict]:
    """Artículos más relevantes para una consulta en lenguaje natural."""
    if not consulta or not consulta.strip():
        return []
    idx = _indice()
    return [_cita(idx.docs[i][0], idx.docs[i][1], s) for s, i in idx.buscar(consulta, k, set(normas) if normas else None)]


_REF_ARTICULO = re.compile(
    r"art(?:[ií]culo|\.)?\s*(\d+(?:\s*[°º])?(?:\s+(?:bis|ter|qu[aá]ter|quinquies|sexies|septies|octies|nonies))?)",
    re.I,
)


def referencias_explicitas(texto: str) -> list[dict]:
    """Detecta citas del tipo 'art. 14 sexies de la 21.719' o 'artículo 3 del DS 662'."""
    codigo_ctx = resolver_norma(texto)
    citas = []
    for m in _REF_ARTICULO.finditer(texto):
        codigos = [codigo_ctx] if codigo_ctx else ["LEY-21719", "DEC-662-HAC"]
        for codigo in codigos:
            citas += obtener_articulo(codigo, m.group(1))
    vistos, unicas = set(), []
    for c in citas:
        clave = (c["norma"], c["articulo"])
        if clave not in vistos:
            vistos.add(clave)
            unicas.append(c)
    return unicas


def regimen_temporal(codigo: str, fecha: date | None = None) -> str:
    """Nota de vigencia según el router temporal de la skill proteccion-datos-chile."""
    fecha = fecha or date.today()
    if codigo in ("LEY-21719", "DEC-662-HAC"):
        if fecha < FECHA_REFORMA:
            return ("Vigencia diferida al 01-12-2026: úsese como preparación (readiness). "
                    "Hasta el 30-11-2026 el régimen exigible es la Ley 19.628 vigente.")
        return "Régimen exigible desde el 01-12-2026."
    if codigo == "LEY-19628":
        if fecha < FECHA_REFORMA:
            return "Régimen exigible hasta el 30-11-2026."
        return "Texto anterior a la reforma: desde el 01-12-2026 rige la Ley 19.628 modificada por la Ley 21.719."
    return "Vigente."
