# CLAUDE.md — Lince GRC

> Archivo exclusivo para Claude Code. No forma parte del runtime de la aplicación.

Las reglas del proyecto son las de `AGENTS.md` (compartidas con Google Antigravity):

@AGENTS.md

## Trabajo en paralelo con Antigravity
- Esta misma carpeta (`D:\FARMASOFT\serviphar_grc_lite`) también la edita Antigravity.
- Al iniciar cada sesión: revisar `git status` y `git log --oneline -10` para conocer los cambios hechos desde Antigravity antes de proponer o editar nada.
- No editar un archivo que tenga cambios sin commitear de Antigravity sin avisar primero al usuario.
- La app puede estar corriendo (Streamlit / Docker): no reiniciar servicios, no tocar `.env`, la base de datos ni `docker-compose.yml` sin autorización.

## Skills del proyecto (`.claude/skills/`)
- `proteccion-datos-chile`: análisis normativo de la Ley 19.628 modificada por la Ley 21.719, la Ley 21.663 (Marco de Ciberseguridad) y el Decreto Supremo N° 662 (MPI). Skill de dominio propia del proyecto, verificada contra el corpus oficial el 2026-10-21. Usarla para criterios legales, matrices de brechas y revisión de privacidad del código.
  - Lince es una plataforma integral de cumplimiento; el MPI es sólo uno de sus componentes.
  - Tras editar la skill, ejecutar `python addons/normativa/tools/sync_conocimiento.py`.
