# Lince GRC

**Plataforma integral de cumplimiento e implementación de protección de datos personales en Chile.**

> **¿Te incorporas al proyecto?** Empieza por [`docs/AUDITORIA_ESTADO_PROYECTO.md`](docs/AUDITORIA_ESTADO_PROYECTO.md): estructura, arquitectura, montaje del entorno, modelo de datos, IA, seguridad, estado real y ruta al MVP.

Lince GRC integra en una sola plataforma el cumplimiento de:
- la **Ley N° 19.628 modificada por la Ley N° 21.719**: régimen completo de protección de datos, exigible desde el 01-12-2026;
- la **Ley N° 21.663, Marco de Ciberseguridad**: incidentes y reporte al CSIRT Nacional;
- el **Decreto Supremo N° 662 de Hacienda**: Modelos de Prevención de Infracciones (MPI).

El MPI es uno de los componentes de Lince, no su alcance. La plataforma acompaña la implementación y la gestión del cumplimiento de la ley completa, adopte o no la organización un MPI.

**Modelo objetivo:** plataforma **SaaS** multi-cliente. Las implicancias de diseño (tenancy, identidad, rol legal del operador, stack) están en [`docs/AUDITORIA_ESTADO_PROYECTO.md` §14](docs/AUDITORIA_ESTADO_PROYECTO.md#14-hacia-dónde-va-lince-hoja-de-ruta).

---

## Estado actual (prototipo funcional, Fase 2A)

| Menú | Función |
|---|---|
| ◈ Dashboard | Métricas consolidadas, alertas de plazos de derechos, riesgos críticos y EIPD pendientes |
| ▣ Empresas | Gestión de empresas cliente y selección de la empresa activa |
| ◬ Evaluaciones GRC | Contenedor de proyectos de evaluación por empresa y período |
| ◆ Perfil MPI y Delegado | Responsable y representante legal, delegado de protección de datos y estados declarativos de certificación (DS 662) |
| ☷ Tratamientos (RAT) | Registro de actividades de tratamiento con los 11 numerales del DS 662 art. 3 d) |
| ◇ Derechos de los Titulares | Solicitudes de acceso, rectificación, supresión, oposición, bloqueo y portabilidad, con plazos legales según la fecha de ingreso (Ley 19.628 vigente / Ley 21.719 desde el 01-12-2026), prórroga, bloqueo temporal, respuesta fundada y respaldo |
| △ Análisis de Riesgos | Diagnóstico automático desde los datos de Lince, evaluación probabilidad × impacto con residual y plan de acción, mapa de calor, matriz de riesgos del MPI (DS 662 art. 3 e) y EIPD por tratamiento (Ley 21.719 art. 15 ter) |
| ⤓ Importar Antecedentes RAT | Importación documental (XLSX, CSV, DOCX, PDF con texto, MD, TXT), mapeo de columnas y conciliación con revisión humana |
| ⌖ Visitas / Auditorías | Auditorías en terreno con checklist de seguridad de 15 puntos |
| ◫ Evidencias | Enlaces a evidencias externas (no almacena archivos) |
| ⇲ Exportar Informe | Informe Excel consolidado de 15 hojas |
| § Normativa | Citas literales verificadas de las 4 normas, búsqueda y copiloto LLM opcional segregado de los datos |

**Todavía no implementado** (ver la ruta al MVP en el documento de auditoría, §13-§14):
- registro de vulneraciones (art. 14 sexies) e incidentes de ciberseguridad (Ley 21.663);
- usuarios, roles y bitácora;
- protocolos, canal de denuncias y sanciones internas del MPI;
- hallazgos y planes de acción.

> [!CAUTION]
> - Lince **no certifica, registra ni valida** modelos de prevención de infracciones: eso corresponde exclusivamente a la Agencia de Protección de Datos Personales. Los estados oficiales que registra la app son declarativos.
> - **No apto aún para producción ni para acceso de clientes:** el login es una barrera temporal de desarrollo y no hay usuarios, roles ni bitácora.

---

## Estructura del repositorio

```text
app.py              Punto de entrada Streamlit: configuración, login, init_db, menú y router
db/                 Capa de datos: conexión, migraciones idempotentes (init_db) y repositorios
modules/            Interfaz Streamlit por módulo (sin SQL)
services/           Lógica de negocio: extracción documental, deduplicación, completitud MPI
utils/              Constantes de dominio y validadores
addons/normativa/   Addon: fuentes legales oficiales (fuente de verdad), corpus, citas y copiloto LLM (sin acceso a la BD)
tests/              Pruebas unittest (incluye integración de migraciones con PostgreSQL)
docs/               Auditoría del estado del proyecto y documentación funcional histórica
.claude/skills/     Skill de dominio jurídico para el desarrollo asistido por IA
docker-compose.yml  PostgreSQL 16 local (sólo 127.0.0.1, sin claves en desarrollo)
.env.example        Plantilla de configuración de desarrollo local
AGENTS.md           Reglas para agentes de IA de desarrollo (CLAUDE.md las importa)
```

Detalle archivo por archivo: [`docs/AUDITORIA_ESTADO_PROYECTO.md` §3](docs/AUDITORIA_ESTADO_PROYECTO.md#3-estructura-del-repositorio).

---

## Ejecución local (sin claves)

Requisitos: Docker con Compose v2, Python 3.11 y Git. Guía completa y verificada: [`docs/AUDITORIA_ESTADO_PROYECTO.md` §5](docs/AUDITORIA_ESTADO_PROYECTO.md#5-montaje-del-entorno-de-desarrollo).

```bash
git clone https://github.com/gvegabatyi/serviphar-grc-lite.git && cd serviphar-grc-lite
cp .env.example .env              # desarrollo local sin claves: no hay que editar nada
docker compose up -d              # PostgreSQL 16 local (sólo 127.0.0.1)
python3.11 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py              # http://localhost:8501 (el esquema se crea al iniciar)
python -m unittest discover -s tests -t .   # pruebas
```

Despliegue en una BD gestionada (Neon): usar su URL en `DATABASE_URL` con `?sslmode=require` y activar el login (`LINCE_AUTH_ENABLED=true`).
