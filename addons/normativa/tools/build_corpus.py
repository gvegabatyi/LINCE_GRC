"""
Genera el corpus normativo del addon a partir de los textos oficiales.

Herramienta de desarrollo, NO forma parte del runtime de Lince. Requiere
PyMuPDF (`fitz`) y python-docx, que sólo se usan aquí:

    python addons/normativa/tools/build_corpus.py --leyes "D:/PROYECTO FARMA/leyes" \
        --decreto "D:/FARMASOFT/decreto 662/Decreto_662_Hacienda_Completo_Editable.docx"

Salida: addons/normativa/corpus/<codigo>.json, un registro por artículo.
Cambiar el corpus exige volver a verificar la skill proteccion-datos-chile.
"""

import argparse
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent.parent / "corpus"

FUENTES_PDF = {
    "LEY-19628": {
        "archivo": "LEY-19628_28-AGO-1999.pdf",
        "nombre": "Ley N° 19.628, sobre protección de la vida privada",
        "version": "LeyChile, última modificación Ley 21.504 (10-NOV-2022)",
        "vigencia_desde": None,
        "vigencia_hasta": "2026-11-30",
    },
    "LEY-21719": {
        "archivo": "Ley-21719_13-DIC-2024.pdf",
        "nombre": "Ley N° 21.719, regula la protección y el tratamiento de los datos personales",
        "version": "LeyChile generado 07-ABR-2026, última modificación Ley 21.806 (05-FEB-2026)",
        "vigencia_desde": "2026-12-01",
        "vigencia_hasta": None,
    },
    "LEY-21663": {
        "archivo": "Ley-21663_08-ABR-2024.pdf",
        "nombre": "Ley N° 21.663, Ley Marco de Ciberseguridad",
        "version": "LeyChile, versión 01-MAR-2025",
        "vigencia_desde": None,
        "vigencia_hasta": None,
    },
}
FUENTE_DECRETO = {
    "codigo": "DEC-662-HAC",
    "nombre": "Decreto Supremo N° 662 (Hacienda), Reglamento de Modelos de Prevención de Infracciones",
    "version": "13-JUN-2025, tomado de razón 28-AGO-2026",
    "vigencia_desde": "2026-12-01",
    "vigencia_hasta": None,
}

# Ruido de página de LeyChile
_RUIDO = re.compile(
    r"^\s*(Ley \d+|Documento firmado.*|Para validar.*|Documento generado.*|"
    r"página \d+ de \d+|Biblioteca del Congreso.*)\s*$",
    re.M,
)
# Notas marginales de LeyChile ("Ley 21806", "Art. 54 N° 1 a)", "D.O. 05.02.2026")
_NOTA_MARGEN = re.compile(r"\s{4,}(Ley \d+|Art\. [^\n]*|D\.O\. [\d.]+|LEY \d+|Decreto \d+[^\n]*)\s*$", re.M)
_SOLO_NOTA = re.compile(r"^\s*(Ley \d+|Art\. \d+[^\n]{0,40}|D\.O\. [\d.]+|LEY \d+)\s*$", re.M)

_SUF = r"(?:\s+(?:bis|ter|qu[aá]ter|quinquies|sexies|septies|octies|nonies|novies|decies))?"
_HDR = re.compile(
    r'^\s*["“]?\s*(?:Art[ií]culo|ART[IÍ]CULO)\s+((?:\d+\s*[°º]?|[a-záéíóú]+)' + _SUF + r")\s*[.\-–:]",
    re.M,
)
# Instrucciones de modificación de una ley modificatoria ("4) Agrégase, en ... del artículo 2°, ...")
_INSTRUCCION = re.compile(
    r"^\s+(\d+)\)\s+(?=(?:Sustit|Reempl|Agr[eé]g|Interc|Introd|Incorp|Supr[ií]m|Elim|Der[oó]g|Modif|Traslad))",
    re.M,
)
_OBJETIVO = re.compile(r"art[ií]culo\s+(\d+(?:\s*[°º])?" + _SUF + r")", re.I)
_TRANSITORIAS = re.compile(r"^\s*(DISPOSICIONES TRANSITORIAS|Disposiciones transitorias|ARTÍCULOS TRANSITORIOS)\s*$", re.M)


def normalizar_articulo(etiqueta: str) -> str:
    """'14 Quáter' / '1° bis' / '4º' -> '14 quater' / '1 bis' / '4'."""
    s = etiqueta.lower().replace("°", "").replace("º", "")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip()


def _reflow(texto: str) -> str:
    """Une las líneas cortadas del PDF; los párrafos de LeyChile empiezan con sangría."""
    lineas = texto.splitlines()
    parrafos, actual = [], []
    for ln in lineas:
        if not ln.strip():
            continue
        if re.match(r"^\s{3,}\S", ln) and actual:
            parrafos.append(" ".join(actual))
            actual = []
        actual.append(ln.strip())
    if actual:
        parrafos.append(" ".join(actual))
    return "\n".join(re.sub(r"\s{2,}", " ", p) for p in parrafos)


def _segmentar(texto: str, modificatoria: bool = False) -> list[dict]:
    m_trans = _TRANSITORIAS.search(texto)
    inicio_trans = m_trans.start() if m_trans else None
    cortes = [("art", h) for h in _HDR.finditer(texto)]
    if modificatoria:
        # Sólo las instrucciones del cuerpo permanente, antes de las transitorias
        cortes += [("mod", m) for m in _INSTRUCCION.finditer(texto)
                   if inicio_trans is None or m.start() < inicio_trans]
    cortes.sort(key=lambda c: c[1].start())

    articulos = []
    for i, (tipo, h) in enumerate(cortes):
        fin = cortes[i + 1][1].start() if i + 1 < len(cortes) else len(texto)
        cuerpo = _reflow(texto[h.start():fin]).strip().lstrip('"“')
        if tipo == "mod":
            objetivo = _OBJETIVO.search(cuerpo[:250])
            articulos.append({
                "articulo": f"primero n{h.group(1)}",
                "etiqueta": f"Artículo primero, numeral {h.group(1)} (modificación)",
                "transitorio": False,
                "modifica": normalizar_articulo(objetivo.group(1)) if objetivo else None,
                "texto": cuerpo,
            })
            continue
        etiqueta = re.sub(r"\s+", " ", h.group(1).replace(" °", "°")).strip()
        transitorio = inicio_trans is not None and h.start() > inicio_trans
        articulos.append({
            "articulo": normalizar_articulo(etiqueta) + (" transitorio" if transitorio else ""),
            "etiqueta": f"Artículo {etiqueta}" + (" transitorio" if transitorio else ""),
            "transitorio": transitorio,
            "texto": cuerpo,
        })
    return articulos


def _extraer_pdf(ruta: Path) -> str:
    import fitz  # PyMuPDF, sólo en desarrollo
    texto = "\n".join(p.get_text() for p in fitz.open(ruta))
    texto = _RUIDO.sub("", texto)
    texto = _NOTA_MARGEN.sub("", texto)
    return _SOLO_NOTA.sub("", texto)


def _extraer_docx(ruta: Path) -> str:
    import docx  # python-docx
    lineas = []
    for p in docx.Document(ruta).paragraphs:
        # Un párrafo DOCX puede traer saltos de línea internos (literales a), b)...)
        lineas += ["     " + ln.strip() for ln in p.text.splitlines() if ln.strip()]
    return "\n".join(lineas)


def _guardar(codigo: str, meta: dict, articulos: list[dict]) -> None:
    # Si un número se repite (p. ej. el "Artículo primero" que envuelve las
    # modificaciones de la Ley 21.719), se conserva la primera aparición con
    # sufijo para no perder texto.
    vistos: dict[str, int] = {}
    for a in articulos:
        n = vistos.get(a["articulo"], 0)
        vistos[a["articulo"]] = n + 1
        if n:
            a["articulo"] = f'{a["articulo"]} ({n + 1})'
    data = {"codigo": codigo, **meta, "generado": date.today().isoformat(), "articulos": articulos}
    (CORPUS_DIR / f"{codigo}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{codigo}: {len(articulos)} artículos")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--leyes", required=True, help="Carpeta con los PDF oficiales de LeyChile")
    ap.add_argument("--decreto", required=True, help="DOCX del Decreto 662")
    args = ap.parse_args()
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    for codigo, meta in FUENTES_PDF.items():
        texto = _extraer_pdf(Path(args.leyes) / meta["archivo"])
        meta = {k: v for k, v in meta.items() if k != "archivo"}
        _guardar(codigo, meta, _segmentar(texto, modificatoria=(codigo == "LEY-21719")))

    texto = _extraer_docx(Path(args.decreto))
    meta = {k: v for k, v in FUENTE_DECRETO.items() if k != "codigo"}
    _guardar(FUENTE_DECRETO["codigo"], meta, _segmentar(texto))


if __name__ == "__main__":
    main()
