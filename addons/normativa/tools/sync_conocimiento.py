"""
Sincroniza la base de conocimiento del copiloto con la skill proteccion-datos-chile.

La skill vive en .claude/skills/ (herramienta de desarrollo, fuera del runtime).
El copiloto usa una copia en addons/normativa/conocimiento/. Ejecutar tras
modificar la skill:

    python addons/normativa/tools/sync_conocimiento.py

La prueba tests/test_addon_normativa.py falla si las copias se desfasan.
"""

import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
ORIGEN = RAIZ / ".claude" / "skills" / "proteccion-datos-chile"
DESTINO = Path(__file__).resolve().parent.parent / "conocimiento"

ARCHIVOS = [
    "SKILL.md",
    "LICENSE",
    "references/marco-y-vigencia.md",
    "references/obligaciones-y-derechos.md",
    "references/seguridad-incidentes-dpia-ia.md",
    "references/terceros-transferencias-sanciones.md",
    "references/decreto-662-mpi.md",
    "references/lince-grc-integracion.md",
]


def main() -> None:
    for rel in ARCHIVOS:
        destino = DESTINO / rel
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ORIGEN / rel, destino)
        print(f"copiado {rel}")


if __name__ == "__main__":
    main()
