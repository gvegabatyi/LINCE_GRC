# Lince GRC — Auditoría técnica del estado del proyecto

| | |
|---|---|
| **Fecha de corte** | 2026-10-22 |
| **Base auditada** | rama `main`, commit `18a9a04` más la entrega del 2026-10-22: addon normativo, tests, `.env.example`, definición del producto y **correcciones derivadas de esta auditoría** (ver [Registro de correcciones](#registro-de-correcciones-2026-10-22)) |
| **Método** | revisión estática completa del código (≈11.000 líneas), sin conexión a la BD de ningún entorno. Cada hallazgo lleva su referencia `archivo:línea`. Los hallazgos críticos se reverificaron a mano |
| **Destinatario** | ingeniería de infraestructura e IA que se incorpora al proyecto |
| **Severidad** | **ALTA**: bloquea producción o expone datos · **MEDIA**: degrada operación, consistencia o seguridad · **BAJA**: deuda o higiene |

> Este documento describe **lo que el código hace hoy**, no lo que la documentación previa afirma. Cuando ambos difieren, se indica. Los números de línea corresponden a la base auditada y se desplazan con los cambios posteriores. Los hallazgos ya resueltos se marcan **[CORREGIDO]** y se mantienen para trazabilidad.

### Registro de correcciones (2026-10-22)

Cada corrección fue verificada con pruebas automatizadas y con una **simulación de clon desde cero**:
- copia limpia del repositorio, entorno virtual nuevo con `pip install -r requirements.txt` y PostgreSQL desechable;
- recorrido automatizado del `app.py` real con login activado: crear empresa y tratamiento, las 10 páginas, addon y exportación;
- servidor real levantado y sondeado.

La migración se probó además sobre una copia de una base existente y con referencias colgantes.

| ID | Corrección | Verificación |
|---|---|---|
| D-01 | XLSX conserva la primera fila de datos (`fila_inicio=0`), con la misma numeración que CSV | `TestImportacionXlsx` |
| D-02 | **PASO 8** en `db/migrations.py`: crea las 4 FK faltantes, detectadas por columna. Antes de crear cada FK, anula las referencias colgantes | `TestIntegracionBD` (BD nueva, copia de BD existente, caso colgante) |
| D-03 / S-10 | La importación persiste sólo las columnas mapeadas (las demás vacías, salvo opt-in) y trunca las celdas a 4.000 caracteres | `TestPersistenciaImportacion` |
| D-04 | `rat_ambito_territorial` pasa a `TEXT` (PASO 8, sin reescribir la tabla) | `test_ambito_territorial_es_text` |
| D-06 | El selector de empresa queda fuera del `st.form` en Tratamientos y Visitas, preseleccionado con la empresa activa | Simulación de clon |
| D-09 | Las empresas del importador se identifican por "nombre (RUT)" | Revisión de código |
| D-12 | **Dependencias incompatibles:** `pyarrow` sin fijar instalaba la 26.x (exige NumPy ≥ 2) junto a `numpy` 1.26 (exigido por Streamlit 1.32), y `st.dataframe` fallaba en toda la UI. Se fijan `numpy==1.26.4` y `pyarrow==17.0.0` | Instalación limpia + simulación de clon |
| S-01 | `docker-compose.yml`: puerto sólo en `127.0.0.1` (configurable con `POSTGRES_BIND`), modo de desarrollo **sin claves** (`trust`) acotado a loopback, healthcheck | `docker compose config`; conexión sin contraseña verificada sobre un volumen nuevo |
| S-04 / S-07 / S-12 | `.streamlit/config.toml`: `address=127.0.0.1`, `maxUploadSize=10`, `showErrorDetails=false` | Sondeo del servidor real (no responde desde la IP de red) |
| S-08 | Exportación XLSX: neutralización de fórmulas | `TestExportacion` |
| MVP-6 | **Módulo Derechos de los Titulares** (tabla `solicitudes_derechos`, PASO 9): plazos por régimen según la fecha de ingreso (estándar dual Ley 19.628 / Ley 21.719), prórroga única, bloqueo temporal, denegación fundada, respaldo de respuesta, aislamiento por empresa. Integración con Dashboard y exportación (hoja 13, minimizada) | `tests/test_derechos.py` (16) + recorrido en la app real |
| UI | El Dashboard ya no muestra el indicador de "completitud documental MPI", que presentaba el MPI como si fuera el alcance de Lince. Se corrigieron los textos que afirmaban que lo importado no cuenta para ese indicador (era falso, D-05) | Recorrido en la app real |
| Fuentes | Las fuentes legales oficiales (PDF de LeyChile y DOCX del DS 662) quedan versionadas en `addons/normativa/fuentes/` con su SHA-256. El corpus regenerado desde ellas es idéntico al publicado | Regeneración + comparación |
| — | Invalidación de cachés dependientes al editar o borrar una empresa; textos de la UI que afirmaban "Neon" o un estado de BD sin comprobarlo; `pandas` fijado; `.gitignore` ampliado; `AGENTS.md` alineado con el código | Revisión de código + suite de tests |

---

## Índice

1. [Qué es Lince](#1-qué-es-lince)
2. [Resumen ejecutivo del estado](#2-resumen-ejecutivo-del-estado)
3. [Estructura del repositorio](#3-estructura-del-repositorio)
4. [Arquitectura y stack](#4-arquitectura-y-stack)
5. [Montaje del entorno de desarrollo](#5-montaje-del-entorno-de-desarrollo)
6. [Configuración](#6-configuración)
7. [Modelo de datos](#7-modelo-de-datos)
8. [Módulos funcionales y flujos](#8-módulos-funcionales-y-flujos)
9. [Componente de IA](#9-componente-de-ia)
10. [Infraestructura y despliegue](#10-infraestructura-y-despliegue)
11. [Seguridad](#11-seguridad)
12. [Calidad, defectos y deuda técnica](#12-calidad-defectos-y-deuda-técnica)
13. [Cobertura normativa: actual vs objetivo](#13-cobertura-normativa-actual-vs-objetivo)
14. [Hacia dónde va Lince: hoja de ruta](#14-hacia-dónde-va-lince-hoja-de-ruta)
15. [Convenciones de trabajo del repositorio](#15-convenciones-de-trabajo-del-repositorio)
16. [Glosario](#16-glosario)

---

## 1. Qué es Lince

**Lince GRC es una plataforma integral de cumplimiento e implementación de protección de datos personales en Chile.** Integra en una sola herramienta tres cuerpos normativos:

| Norma | Rol en Lince | Vigencia |
|---|---|---|
| **Ley N° 19.628 modificada por la Ley N° 21.719** | Régimen completo: principios, licitud, derechos de los titulares, deberes del responsable, seguridad, vulneraciones, evaluación de impacto, encargados, cesiones, transferencias, sanciones y prevención de infracciones | El régimen reformado rige desde el **01-12-2026**; hasta el 30-11-2026 rige la Ley 19.628 anterior a la reforma |
| **Ley N° 21.663**, Marco de Ciberseguridad | Gestión de incidentes y reporte al CSIRT Nacional para servicios esenciales y operadores de importancia vital. La "producción y/o investigación de productos farmacéuticos" es servicio esencial (art. 4) | Vigente |
| **Decreto Supremo N° 662** (Hacienda) | Reglamento de los **Modelos de Prevención de Infracciones (MPI)** del art. 49: programa de cumplimiento, delegado de protección de datos, certificación y registro ante la Agencia | Tomado de razón el 28-08-2026 |

**El MPI es un componente de Lince, no su alcance.** El MPI es voluntario (art. 49). El cumplimiento de la ley y el deber de prevención (art. 48) alcanzan a todo responsable, adopte o no un MPI.

**Modelo objetivo: plataforma SaaS** multi-cliente (ver §14, "Visión SaaS"). Esta definición condiciona el diseño de datos, identidad e infraestructura desde ahora.

**Modelo de uso actual.** Es una herramienta de **consultoría multiempresa**: un equipo consultor gestiona varias empresas cliente (el piloto es Serviphar, del rubro farmacéutico). La separación por empresa es hoy un **contexto de trabajo**, no un aislamiento de seguridad entre clientes (ver §11 y §12.4).

**Qué no hace Lince.** No certifica, registra ni valida MPI: esas atribuciones son exclusivas de la Agencia de Protección de Datos Personales (DS 662 arts. 14-17). Los estados de certificación que registra la app son declarativos (`utils/constants.py:221-225`).

---

## 2. Resumen ejecutivo del estado

| Dimensión | Estado | Comentario |
|---|---|---|
| Madurez funcional | **Prototipo funcional avanzado (Fase 2A)** | RAT de 11 numerales, importación documental, MPI y delegado, evaluaciones, visitas, evidencias, exportación y addon normativo |
| Cobertura normativa | **Parcial** | 8 de 19 ámbitos legales cubiertos, 7 parciales y 4 no modelados (§13). Faltan vulneraciones, incidentes CSIRT, EIPD y exposición sancionatoria |
| Preparación para producción | **No apto** | Autenticación temporal de contraseña única, sin usuarios ni roles, sin bitácora, sin backups, la app se conecta como superusuario a la BD, sin contenedor de la app (§11) |
| Integridad del esquema | **Mejorada** | FK faltantes y longitud de campo corregidas (PASO 8). Persiste: migraciones sin versionado y DDL en cada arranque (§7.4) |
| Pruebas | **Básicas** | 47 tests: addon normativo, regresión de las correcciones, módulo de derechos e integración contra PostgreSQL efímero. Sin tests de UI ni de la mayoría de los repositorios. Sin CI |
| IA en runtime | **Opcional y desactivada por defecto** | Copiloto RAG con salvaguardas de segregación (§9) |

**Los cinco puntos de mayor riesgo vigentes** (tras las correcciones del 2026-10-22):
1. Autenticación de desarrollo con contraseña compartida y sin usuarios, roles ni auditoría (`app.py:166-216`). En una plataforma que trata datos personales, esto es incompatible con la responsabilidad demostrable que la propia ley exige.
2. No hay backups ni procedimiento de recuperación. Los datos viven en un único volumen Docker o en la BD gestionada sin política definida.
3. La app se conecta como superusuario: no existe un rol de aplicación con mínimo privilegio.
4. Migraciones sin versionado, con DDL en cada arranque de proceso.
5. Escrituras por `id` sin verificar `empresa_id`, más dashboard y exportación globales (S-06). Es aceptable en el modelo de consultor único, pero bloquea el acceso directo de clientes.

---

## 3. Estructura del repositorio

```text
serviphar_grc_lite/
├── app.py                          # Punto de entrada Streamlit: .env, login, init_db, empresa activa, menú y router
├── requirements.txt                # Dependencias de runtime fijadas (incluye numpy/pyarrow: ver D-12)
├── runtime.txt                     # python-3.11 (Railway)
├── railpack-plan.json              # Railpack: sólo fija python 3.11; sin start command
├── docker-compose.yml              # Sólo PostgreSQL 16 local, en 127.0.0.1 (la app no está contenedorizada)
├── .env.example                    # Plantilla de variables (el .env real está en .gitignore)
├── .streamlit/config.toml          # Tema oscuro + server.headless
│
├── db/                             # CAPA DE DATOS: el único lugar donde debería haber SQL
│   ├── connection.py               # Carga de .env, normalización de DATABASE_URL, conexión psycopg2 por llamada
│   ├── migrations.py               # init_db(): DDL idempotente (PASOS 1-7) + seeds del DS 662
│   └── repositories/               # Acceso a datos por agregado (SELECT/INSERT/UPDATE/DELETE parametrizados)
│       ├── empresas.py             # CRUD empresas · cache 60 s
│       ├── evaluaciones.py         # CRUD evaluaciones (contenedor de proyecto) · sin cache
│       ├── tratamientos.py         # RAT · cache 30 s
│       ├── visitas.py              # Visitas + checklist JSONB · sin cache
│       ├── evidencias.py           # Evidencias como URL externa · sin cache
│       ├── mpi_gobernanza.py       # Perfil MPI, delegado (versionados con 'activo'), catálogo normativo · cache 3600 s
│       ├── importaciones.py        # Importaciones documentales y candidatos RAT · cache 15-30 s
│       └── derechos.py             # Solicitudes de derechos de los titulares · cache 30 s · escrituras por id+empresa
│
├── services/                       # LÓGICA DE NEGOCIO sin UI
│   ├── extraccion_service.py       # Extracción determinista (sin IA ni OCR) desde XLSX/CSV/DOCX/PDF/MD/TXT
│   ├── deduplicacion_service.py    # SHA-256, validación estructural de archivos, duplicados (contiene SQL: deuda)
│   ├── plazos_service.py           # Plazos legales de derechos (régimen dual, días hábiles, feriados)
│   ├── mpi_service.py              # Completitud documental MPI (no expuesto en la UI)
│   └── checklist_service.py        # Puntaje del checklist de visitas
│
├── modules/                        # CAPA DE PRESENTACIÓN Streamlit (no debe contener SQL)
│   ├── dashboard.py · empresas.py · evaluaciones.py · mpi_gobernanza.py · tratamientos.py
│   ├── derechos.py                 # Derechos de los titulares: bandeja, alta, gestión y base legal
│   ├── importar_antecedentes.py    # Bandeja de importación RAT (1.746 líneas: candidato a refactor)
│   └── visitas.py · evidencias.py · exportar.py
│
├── utils/
│   ├── constants.py                # Dominio: checklist, estados MPI, numerales RAT, bases legales, avisos
│   └── validators.py               # Validadores (hoy sin uso: código muerto)
│
├── addons/                         # ADDONS OPCIONALES, desacoplados del núcleo
│   └── normativa/                  # Citas normativas verificadas + copiloto LLM (§9)
│       ├── citas.py · copiloto.py · pii_filter.py · ui.py
│       ├── fuentes/                # FUENTE DE VERDAD: PDF LeyChile + DOCX DS 662 oficiales, con SHA-256
│       ├── corpus/*.json           # 4 normas segmentadas por artículo, generadas desde fuentes/ (336 KB)
│       ├── conocimiento/           # Copia sincronizada de la skill de dominio del proyecto
│       ├── tools/                  # build_corpus.py, sync_conocimiento.py (sólo en desarrollo)
│       └── requirements-copiloto.txt  # anthropic==2.1.0 (opcional)
│
├── tests/
│   ├── test_addon_normativa.py     # 21 tests del addon (sin BD, red ni anthropic)
│   ├── test_correcciones.py        # 10 tests: regresión + integración con PostgreSQL (LINCE_TEST_DATABASE_URL)
│   └── test_derechos.py            # 16 tests: plazos y estándar dual + integración del repositorio
│
├── docs/
│   ├── IMPLEMENTACION.md           # Documentación funcional histórica (Fases 1-2A)
│   └── AUDITORIA_ESTADO_PROYECTO.md   # Este documento
│
├── AGENTS.md                       # Reglas para agentes de IA de desarrollo (Claude Code y Google Antigravity)
├── CLAUDE.md                       # Específico de Claude Code; importa AGENTS.md
└── .claude/skills/proteccion-datos-chile/   # Skill de dominio jurídico para el desarrollo asistido (§9.6)
```

**Reglas de dependencia entre capas** (definidas en `AGENTS.md`, con su cumplimiento real):

| Regla | Cumplimiento |
|---|---|
| `modules/` → `services/` → `db/repositories/` → `db/connection.py` | Se respeta en general |
| Sin SQL fuera de `db/` | **Una excepción:** `services/deduplicacion_service.py:245-312` |
| `addons/` no importa `db/`, `modules/` ni `services/` | Se cumple y lo verifica un test (`tests/test_addon_normativa.py`) |

---

## 4. Arquitectura y stack

### 4.1 Stack

| Componente | Versión | Nota |
|---|---|---|
| Python | `runtime.txt`: 3.11 | El `.venv` local usa 3.12.10. Ver deriva en §10.4 |
| Streamlit | 1.32.0 | UI y servidor (Tornado), modelo de *reruns* |
| PostgreSQL | 16 (imagen `postgres:16-alpine`) en local / Neon en el despliegue previsto | Acceso con `psycopg2-binary` 2.9.9 |
| pandas | 2.3.3 | Fijada |
| numpy / pyarrow | 1.26.4 / 17.0.0 | Fijadas: Streamlit 1.32 exige `numpy<2`, y `pyarrow` ≥ 18 sin fijar traía builds incompatibles (D-12) |
| openpyxl, python-docx, pdfplumber | 3.1.2 / 1.1.2 / 0.11.4 | Importación y exportación de documentos |
| anthropic (opcional) | 2.1.0 | Sólo para el copiloto con proveedor Anthropic |

### 4.2 Modelo de ejecución

```text
Navegador ──HTTP/WebSocket──► Streamlit server (1 proceso Python)
                                  │  cada interacción = rerun completo de app.py
                                  ├─ _load_env_file()                       db/connection.py:11
                                  ├─ login temporal (hmac.compare_digest)   app.py:168-216
                                  ├─ init_db()  @st.cache_resource          app.py:226-237  (1 vez por PROCESO)
                                  ├─ empresa activa en st.session_state     app.py:251-261
                                  ├─ menú (11 opciones) → módulo.render()   app.py:285-364
                                  │      └─ repositorio → psycopg2.connect() por llamada (sin pool)
                                  └─ addon normativa (import perezoso, try/except)
```

Consecuencias operativas a tener en cuenta:

- **El estado de la sesión vive en la memoria del proceso** (`st.session_state`). No hay afinidad de sesión externa: un escalado horizontal requiere *sticky sessions* en el balanceador.
- **`st.cache_data` es por proceso y se comparte entre usuarios.** `.clear()` sólo invalida el proceso local, así que con varias réplicas cada una sirve datos obsoletos hasta que vence el TTL.
- **No hay pool de conexiones.** Cada llamada a un repositorio abre y cierra una conexión (`connect_timeout=10`, `db/connection.py:70`). Frente a Neon esto suma un handshake TLS por consulta.
- **`init_db()` corre una vez por proceso** (no por sesión, como dice AGENTS.md §3.A.1) y además desde el botón "⟳ Sincronizar Base de Datos" (`app.py:319-322`).

---

## 5. Montaje del entorno de desarrollo

### 5.1 Requisitos

- Docker Engine con Compose v2.
- Python 3.11 (el valor declarado; 3.12 también funciona en el entorno actual).
- Git. El puerto 5432 debe estar libre (o hay que ajustar `docker-compose.yml` y `DATABASE_URL`).

### 5.2 Pasos

```bash
# 1. Clonar
git clone https://github.com/gvegabatyi/serviphar-grc-lite.git
cd serviphar-grc-lite

# 2. Configuración: un único .env para docker compose y para la app
cp .env.example .env                   # modo desarrollo local SIN CLAVES: no requiere edición
                                       # (PostgreSQL trust + app sin login, todo en 127.0.0.1)

# 3. Base de datos local (contenedor lince-postgres, volumen lince_pgdata, sólo 127.0.0.1)
docker compose up -d
docker compose ps                      # esperar estado "healthy"

# 4. Entorno Python
python3.11 -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Opcional, copiloto con Anthropic:
# pip install -r addons/normativa/requirements-copiloto.txt

# 5. Arrancar desde la raíz del repo (los imports son absolutos y .env se busca en el cwd).
#    .streamlit/config.toml ya fija address=127.0.0.1; el puerto por defecto es 8501.
streamlit run app.py
```

### 5.3 Verificación

| Comprobación | Comando o acción | Resultado esperado |
|---|---|---|
| Servidor vivo | `curl -s localhost:8501/_stcore/health` | `ok` |
| Esquema creado | Abrir la app e iniciar sesión. `init_db()` crea el esquema en el primer rerun | 12 tablas en `lince_grc` (`\dt` en psql) |
| Seeds | `SELECT count(*) FROM normativa_referencias;` | 21 |
| Tests | `python -m unittest discover -s tests -t .` | `Ran 47 tests ... OK (skipped=9)`. Los 9 omitidos son de integración |
| Tests de integración | Con una BD **desechable**: `LINCE_TEST_DATABASE_URL=postgresql://... python -m unittest discover -s tests -t .` (ejemplo de contenedor en `tests/test_correcciones.py`) | `Ran 47 tests ... OK` |
| Addon | Menú **§ Normativa** → Consultar artículo → Ley 21.719, "14 sexies" | Texto literal del artículo |

### 5.4 Problemas frecuentes

- **"La variable de entorno DATABASE_URL no está configurada"** (`db/connection.py:64-68`): falta `DATABASE_URL`, o se lanzó Streamlit fuera de la raíz del repo, porque `.env` se busca primero relativo al cwd (`db/connection.py:13-17`).
- **La app se detiene tras el login con error de inicialización**: `init_db()` falló y hace `st.stop()` (`db/migrations.py:422-435`). Revisar credenciales y conectividad.
- **"Acceso no configurado"**: `LINCE_AUTH_ENABLED=true` sin `LINCE_ACCESS_PASSWORD` (`app.py:196-200`).

---

## 6. Configuración

Todas las variables que lee el código:

| Variable | Leída en | Default | Obligatoria | Propósito |
|---|---|---|---|---|
| `POSTGRES_USER` / `POSTGRES_DB` / `POSTGRES_PORT` | `docker-compose.yml` | `postgres` / `lince_grc` / `5432` | No | Usuario, base y puerto del contenedor local |
| `POSTGRES_HOST_AUTH_METHOD` | `docker-compose.yml` | `trust` | No | `trust` permite desarrollo local **sin contraseña**. Es seguro sólo con `POSTGRES_BIND=127.0.0.1`. En un servidor compartido: `scram-sha-256` + `POSTGRES_PASSWORD`. Se fija al inicializar el volumen por primera vez |
| `POSTGRES_PASSWORD` | `docker-compose.yml` | vacía | Sólo sin `trust` | Contraseña del superusuario cuando no se usa `trust` |
| `POSTGRES_BIND` | `docker-compose.yml` | `127.0.0.1` | No | Interfaz donde se publica PostgreSQL. `127.0.0.1` sólo da acceso al propio equipo. **Nunca** una IP de red con `trust` |
| `DATABASE_URL` | `db/connection.py:42` | — | **Sí** | DSN PostgreSQL. `postgres://` se normaliza a `postgresql://`. No se añade `sslmode`: en Neon debe ir en la URL (`?sslmode=require`) |
| `LINCE_AUTH_ENABLED` | `app.py:174, 325` | `true` | No | Sólo `false` o `0` desactivan el login |
| `LINCE_ACCESS_PASSWORD` | `app.py:186` | — | Si el login está activo | Contraseña única compartida. La plantilla de desarrollo local desactiva el login (`LINCE_AUTH_ENABLED=false`). El código mantiene `true` por defecto como protección si falta el `.env` |
| `LINCE_SABADO_HABIL` | `services/plazos_service.py` | `true` | No | Cómputo de días hábiles de los plazos de derechos. `true` (conservador) cuenta el sábado como hábil y da plazos más cortos. Pendiente de revisión profesional |
| `LINCE_COPILOTO_PROVEEDOR` | `addons/normativa/copiloto.py:72` | `desactivado` | No | `desactivado` · `anthropic` · `ollama`. Un valor inválido se trata como `desactivado` |
| `LINCE_COPILOTO_MODELO` | `copiloto.py:75` | `claude-opus-5-5` / `llama3.1` | No | Modelo del proveedor |
| `ANTHROPIC_API_KEY` | SDK `anthropic` (implícita) | — | Con `anthropic` | Credencial de la API |
| `OLLAMA_URL` | `copiloto.py:76` | `http://localhost:11434` | Con `ollama` | Endpoint de Ollama |

**Cómo se carga `.env`** (`_load_env_file`, `db/connection.py:11-32`):
- Parser mínimo: no admite `export` ni comentarios al final de la línea.
- No sobrescribe variables que ya existan en el entorno, así que en PaaS mandan las variables de la plataforma.
- Falla en silencio.
- Se vuelve a ejecutar en cada `get_db_url()`.

`.streamlit/config.toml` fija:
- `server.address = "127.0.0.1"`: en PaaS, el start command pasa `--server.address 0.0.0.0`, que tiene prioridad;
- `server.maxUploadSize = 10` (MB, igual al límite de la app);
- `server.enableXsrfProtection = true`;
- `client.showErrorDetails = false`, sin trazas al usuario.

`LINCE_TEST_DATABASE_URL` sólo la usan las pruebas de integración y debe apuntar a una BD desechable.

---

## 7. Modelo de datos

### 7.1 Tablas

`init_db()` crea 12 tablas en una sola transacción.

| Tabla | Creada en | Propósito | Claves relevantes |
|---|---|---|---|
| `empresas` | PASO 1 | Cliente gestionado | `rut` UNIQUE |
| `tratamientos` | PASO 1 + PASO 5 | RAT. Incluye 11 columnas `rat_*` = DS 662 art. 3 d) i-xi | `empresa_id` FK CASCADE |
| `visitas` | PASO 1 | Visita o auditoría + `checklist_seguridad` JSONB | `empresa_id` FK CASCADE |
| `evidencias` | PASO 1 | Evidencia como **URL externa** (`foto_url`) | `visita_id` FK CASCADE. **Sin `empresa_id`** |
| `evaluaciones` | PASO 2 | Contenedor de proyecto GRC | `empresa_id` FK CASCADE |
| `normativa_fuentes` | PASO 3 | Catálogo de normas | `codigo` UNIQUE |
| `normativa_referencias` | PASO 3 | Criterios por artículo (seed DS 662: 21 filas) | `fuente_id` FK CASCADE |
| `mpi_perfiles` | PASO 4 | Perfil MPI, versionado con `activo` | UNIQUE parcial `(empresa_id) WHERE activo` |
| `mpi_delegados` | PASO 4 | Delegado de protección de datos, versionado con `activo` | UNIQUE parcial `(empresa_id) WHERE activo` |
| `importaciones_documentales` | PASO 6 + PASO 7 | Importación: metadatos, hash, matriz JSONB | índices `(empresa_id)`, `(empresa_id, hash_sha256)`, **no UNIQUE** |
| `importacion_tratamientos_candidatos` | PASO 6 | Candidatos RAT para revisión humana | índices `(empresa_id, estado_revision)`, `(importacion_id)` |
| `solicitudes_derechos` | PASO 9 | Solicitudes de derechos de los titulares: derecho, régimen, plazos, prórroga, bloqueo, respuesta | `empresa_id` FK CASCADE; UNIQUE `(empresa_id, folio)`; índices `(empresa_id, estado)`, `(fecha_vencimiento)` |

No hay restricciones CHECK: los estados son VARCHAR libres validados sólo en la UI.

### 7.2 Relaciones

```text
empresas (1)
 ├─< evaluaciones ─────────────────────────────────────┐ (referenciada por SET NULL)
 ├─< tratamientos            ··· evaluacion_id, evidencia_id   (FK ausentes en BD nueva: §7.4)
 ├─< visitas                 ··· evaluacion_id                 (ídem)
 │     └─< evidencias        ··· evaluacion_id                 (ídem)
 ├─< mpi_perfiles            → evaluaciones / evidencias (SET NULL)
 ├─< mpi_delegados           → evidencias (SET NULL)
 ├─< importaciones_documentales → evaluaciones / evidencias (SET NULL)
 │     └─< importacion_tratamientos_candidatos → tratamientos (SET NULL)
normativa_fuentes (1) ─< normativa_referencias          (independiente de empresas)
```

`DELETE FROM empresas` borra en cascada todo lo de la empresa. Las evidencias sin `visita_id` quedan huérfanas.

### 7.3 Almacenamiento de archivos (clave para dimensionar)

- **No se guardan binarios**: no hay BYTEA en la BD, no se escribe a disco y no hay `tempfile`. Las evidencias son URLs externas (Drive, SharePoint, etc.).
- **Importaciones**: el archivo se lee entero en la memoria del proceso (`modules/importar_antecedentes.py:407`) y se descarta. Persisten los metadatos (nombre, tamaño, SHA-256) y el contenido extraído en JSONB:
  - `importaciones_documentales.datos_extraidos_json`: hasta **200 filas crudas** sin truncar (`importar_antecedentes.py:1202`). **Puede contener datos personales**, lo que importa para cifrado en reposo y para la retención de backups.
  - Candidatos: hasta 100 por extracción, con campos truncados a 4.000 caracteres.
- **La aplicación no necesita volumen persistente.** Sólo lo necesita PostgreSQL.

### 7.4 Migraciones: mecanismo y defectos

- **No hay control de versiones de esquema**: ni tabla de versión ni Alembic. La idempotencia descansa en `IF NOT EXISTS`, `ON CONFLICT` y un bloque `DO $$`. Los helpers `_tabla_existe` y `_columna_existe` (`migrations.py:22, 36`) no se usan.
- **El DDL se ejecuta en cada arranque de proceso y a demanda desde la UI.** Son unos 25 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, y cada `ALTER TABLE` toma un lock `ACCESS EXCLUSIVE` aunque no cambie nada. Hay riesgo de bloqueos con consultas largas o con varias réplicas arrancando a la vez.
- **[CORREGIDO — PASO 8] Faltaban 4 FK en instalaciones nuevas.** Las columnas `tratamientos.evaluacion_id`, `tratamientos.evidencia_id`, `visitas.evaluacion_id` y `evidencias.evaluacion_id` se creaban en el `CREATE TABLE` sin `REFERENCES`. Los `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ... REFERENCES` posteriores se omitían enteros, porque la columna ya existía. `_aplicar_paso_8()` (`db/migrations.py`):
  - detecta la FK por columna (respeta las FK con nombre automático de BD antiguas);
  - anula los IDs colgantes, el mismo efecto que `ON DELETE SET NULL`;
  - crea `fk_<tabla>_<columna> ... ON DELETE SET NULL`.

  Se verificó sobre una BD nueva, sobre la copia de una BD existente (a la que efectivamente le faltaban las 4 FK) y con referencias colgantes.
- Seed de referencias del DS 662 "todo o nada" (`migrations.py:204`): las ampliaciones futuras del seed no llegarán a BD existentes.
- **[CORREGIDO — PASO 8]** `rat_ambito_territorial` era `VARCHAR(255)` frente a los 4.000 caracteres de la importación. Ahora es `TEXT`; el cambio es binario-compatible y no reescribe la tabla.

### 7.5 Caché (`@st.cache_data`)

| Función | TTL |
|---|---|
| `get_empresas_df` | 60 s |
| `get_tratamientos_df` | 30 s |
| `get_importaciones_df` / reabribles / por id | 30 s |
| `get_candidatos_df` | 15 s |
| `get_referencias_normativas_df` | 3600 s |

`AGENTS.md` quedó alineado con estos valores; antes declaraba 300 / 120 / 120 s.

**[CORREGIDO]** `delete_empresa` y `update_empresa` ahora invalidan las cachés de tratamientos, importaciones y candidatos (`_invalidar_cache_dependiente`, `db/repositories/empresas.py`).

Pendiente: las escrituras de evaluaciones y evidencias no invalidan `get_tratamientos_df`, que hace JOIN con ellas.

El dato obsoleto dura como máximo un TTL.

---

## 8. Módulos funcionales y flujos

### 8.1 Menú y responsabilidades

| Menú | Archivo | Función | ¿Usa la empresa activa de la sesión? |
|---|---|---|---|
| Dashboard | `modules/dashboard.py` | KPIs globales y alertas de plazos de derechos (todas las empresas) | No (lecturas globales) |
| Empresas | `modules/empresas.py` | CRUD; **fija** `empresa_activa_id` | Es la fuente |
| Derechos de los Titulares | `modules/derechos.py` | Bandeja con semáforo de plazos, alta, gestión (acuse, prórroga, bloqueo, respuesta) y base legal | Sí (la lee y la fija) |
| Evaluaciones GRC | `modules/evaluaciones.py` | Contenedor de proyecto (estado, avance, alcance) | No (selector propio) |
| Perfil MPI y Delegado | `modules/mpi_gobernanza.py` | DS 662 art. 3 a)-c) y arts. 6-13; catálogo normativo | No (selector propio) |
| Tratamientos (RAT) | `modules/tratamientos.py` | Alta del RAT con los 11 numerales. **Sin edición** (`update_tratamiento` se importa y no se usa) | No |
| Importar Antecedentes RAT | `modules/importar_antecedentes.py` | Bandeja documental: carga, mapeo, candidatos y conciliación | Sí (la lee y la reescribe) |
| Visitas / Auditorías | `modules/visitas.py` | Visita en terreno con checklist de 15 preguntas | No |
| Evidencias | `modules/evidencias.py` | Evidencia como URL, ligada a una visita | No |
| Exportar Informe | `modules/exportar.py` | XLSX de 13 hojas, en memoria | No (**exporta todas las empresas**) |
| § Normativa | `addons/normativa/ui.py` | Citas, búsqueda y copiloto | No aplica (sin BD) |

La regla de AGENTS.md "sincronizar siempre con `empresa_activa_id`" se cumple en la importación. En Tratamientos y Visitas el selector se preselecciona con la empresa activa, y está **fuera** del `st.form`, de modo que evaluaciones y evidencias se recalculan al cambiarlo **[CORREGIDO D-06]**. Dashboard, Evaluaciones, Perfil MPI, Evidencias y Exportar mantienen selectores propios o lecturas globales.

### 8.2 Pipeline de importación documental del RAT

1. **Contexto**: empresa (sincronizada con la sesión) y, opcionalmente, una evaluación.
2. **Carga**: se aceptan `xlsx, csv, docx, pdf, md, txt` y se rechazan `xls, xlsm, doc` y binarios (`services/deduplicacion_service.py:29-35`). El archivo se lee entero en memoria.
3. **Límites**: 10 MB por archivo y 5 archivos o 30 MB por sesión. Se validan **después** de leer el archivo, y el límite por sesión sólo se contabiliza al "Guardar candidatos".
4. **Validación estructural**: integridad ZIP y `[Content_Types].xml` para XLSX/DOCX, firma `%PDF-` para PDF, decodificación UTF-8 o Latin-1 para texto.
5. **SHA-256 y aviso de duplicado** por `(empresa, hash)`. Sólo advierte, no bloquea.
6. **Extracción determinista** (sin IA ni OCR, `services/extraccion_service.py`):
   - XLSX, CSV y DOCX-tabla: mapeo de columnas hacia 18 campos destino (11 `rat_*` + nombre, descripción y 5 complementarios).
   - PDF, DOCX texto libre y MD/TXT: candidato manual.
   - Máximo 100 candidatos.
7. **Persistencia**:
   - "Guardar importación RAT" hace upsert en `importaciones_documentales` con encabezados, matriz (máximo 200 filas) y mapeo. **[CORREGIDO D-03]** Sin opt-in, las columnas no mapeadas se persisten vacías, conservando la estructura para reabrir el mapeo, y las celdas se truncan a 4.000 caracteres. El botón no aparece en PDF, TXT ni DOCX texto libre.
   - "Guardar candidatos" inserta candidatos con 2 consultas por candidato (N+1).
8. **Conciliación humana**: crear un tratamiento nuevo, conciliar campo a campo con uno existente o ignorar.
9. **Reapertura**: una importación guardada se puede reabrir para continuar el mapeo.

### 8.3 Indicador de completitud MPI (`services/mpi_service.py`, no expuesto en la UI)

**Retirado de la interfaz (2026-10-22):** presentaba el MPI como si fuera el alcance de Lince. El cálculo se conserva en el servicio por si se reincorpora dentro del módulo del MPI.

| Requisito | Peso |
|---|---|
| Perfil activo con nombre y RUT del representante legal | 25 |
| Delegado activo con nombre y correo público | 25 |
| ≥ 1 tratamiento en el RAT | 20 |
| Todos los tratamientos con los 11 numerales completos | 20 |
| Evidencia vinculada al perfil o al delegado | 10 |

El 100% sólo se alcanza si se cumplen todos los requisitos. En cualquier otro caso se aplica `min(puntos, 95)`, un tope que nunca opera porque el máximo posible es 90. Es un **indicador interno de completitud documental**, no una medida de cumplimiento legal.

### 8.4 Exportación

XLSX con openpyxl generado en memoria (`modules/exportar.py`), con 13 hojas: empresas, tratamientos, visitas, evidencias, resumen, evaluaciones, perfil MPI, delegado, RAT DS 662, referencias normativas, importaciones y candidatos y solicitudes de derechos (sin datos del titular).
- Las hojas 6 a 12 están envueltas en `except Exception: pass`: si fallan, se omiten sin aviso.
- **[CORREGIDO S-08]** `_neutralizar_formulas()` fuerza a texto toda celda que openpyxl interpretó como fórmula. El informe no usa fórmulas propias, así que cualquier celda de ese tipo proviene de datos del usuario.

### 8.5 Derechos de los titulares (`modules/derechos.py`)

**Estándar dual.** El régimen exigible se determina por la **fecha de ingreso** de cada solicitud (`services/plazos_service.py`):

| Fecha de ingreso | Régimen | Plazo de respuesta | Prórroga | Si se deniega o no se responde |
|---|---|---|---|---|
| Hasta el 30-11-2026 | Ley 19.628 vigente (art. 16) | 2 días hábiles | No procede | Amparo ante el juez de letras en lo civil |
| Desde el 01-12-2026 | Ley 21.719 (art. 11) | 30 días corridos | Una vez, hasta 30 días corridos | Reclamo ante la Agencia en 30 días hábiles (art. 41); la denegación debe ser fundada |

- **Plazo de referencia:** para solicitudes bajo la ley vigente, la UI muestra también el plazo que regiría con la Ley 21.719, como preparación.
- **Bloqueo temporal** (sólo junto a rectificación, supresión u oposición): respuesta en 2 días hábiles.
- **Días hábiles:** criterio **conservador**, el sábado se cuenta como hábil (configurable con `LINCE_SABADO_HABIL=false`). Domingos y `FERIADOS_CHILE` (`utils/constants.py`, mantenimiento anual) nunca son hábiles. Sólo se listan feriados con certeza: omitir uno acorta el plazo, que es el lado seguro. `PENDIENTE DE REVISIÓN PROFESIONAL`.
- **Flujo:** recibida → en análisis (acuse) → [prórroga] → acogida, acogida parcial, denegada o cerrada. La denegación total o parcial exige fundamento. La respuesta se vincula a una evidencia, porque el art. 11 obliga a guardar respaldo de la remisión.
- **Seguridad:** toda escritura filtra por `id` **y** `empresa_id`, cerrando para este módulo el patrón S-06.
- **Minimización:** del titular sólo se guarda lo necesario para identificarlo y responderle. La hoja 13 del Excel no incluye ni su nombre ni su contacto.

---

## 9. Componente de IA

Lince usa IA en dos planos separados: **en runtime** (el copiloto normativo, opcional) y **en el desarrollo** (agentes de código con una skill jurídica verificada).

### 9.1 Corpus normativo

| Norma | Registros | Detalle |
|---|---|---|
| `LEY-21719` | 104 | Artículos insertos en la Ley 19.628, 14 instrucciones de modificación ("artículo primero, numeral N") y 8 transitorios |
| `LEY-21663` | 61 | 6 transitorios |
| `LEY-19628` | 27 | Texto anterior a la reforma (rige hasta el 30-11-2026); 3 transitorios |
| `DEC-662-HAC` | 20 | Arts. 1-20, completo |

- **Fuente de verdad:** PDF oficiales de LeyChile/BCN y DOCX del DS 662, **versionados en `addons/normativa/fuentes/`** con versión y SHA-256 en su README. El corpus regenerado desde esas fuentes es idéntico al publicado.
- **Construcción:** `addons/normativa/tools/build_corpus.py`, herramienta sólo de desarrollo que requiere PyMuPDF. Hace cuatro cosas:
  1. extrae el texto y limpia el ruido de página y las notas marginales de LeyChile;
  2. reconstruye los párrafos;
  3. segmenta por encabezado de artículo y separa las disposiciones transitorias;
  4. separa en registros propios las **instrucciones de modificación** de la Ley 21.719, con el campo `modifica`. Así el art. 2 (definiciones), que la 21.719 no reemplaza entero sino que modifica letra a letra, se puede recuperar.
- **Formato:** `corpus/<codigo>.json` (`articulo` normalizado, `etiqueta`, `transitorio`, `modifica`, `texto`). Es de sólo lectura en runtime.

### 9.2 Recuperación (`addons/normativa/citas.py`)

- **Recuperación exacta** por norma y artículo, con normalización de la numeración (`8° bis`, `Art. 14 Sexies`, `sexto transitorio`).
- **Recuperación léxica BM25** propia (k1=1.4, b=0.75, `citas.py:131`):
  - sin dependencias externas;
  - normalización NFKD, stopwords en español y stemming mínimo de singular y plural;
  - el índice se construye una vez por proceso con `lru_cache`.
- **Detección de referencias explícitas** en la pregunta, por ejemplo "art. 14 sexies de la 21.719". Se priorizan sobre los resultados de BM25.
- **Router temporal** (`regimen_temporal`): marca la Ley 21.719 y el DS 662 como *readiness* antes del 01-12-2026.

**Límite conocido:** la recuperación es léxica y no semántica. No hay embeddings ni reranking. Con 212 registros y un vocabulario jurídico estable funciona bien en los casos probados (test `test_busqueda_relevante`), pero las consultas parafraseadas pueden perder recall. Las mejoras naturales son una recuperación híbrida (BM25 + embeddings) o un reranker.

### 9.3 Copiloto (`addons/normativa/copiloto.py`)

```text
pregunta ──► pii_filter.detectar() ──(RUT/correo/teléfono)──► BLOQUEO (no sale nada)
    │
    ▼
recuperar_citas(): referencias explícitas + BM25  → máx. 8 artículos  (copiloto.py:88)
    │
    ▼
prompt:  system = [REGLAS_BASE, base_conocimiento (skill, ~68k caracteres, cache_control)]
         user   = <articulos>…</articulos> + fecha de hoy + pregunta
    │
    ├─ proveedor anthropic: SDK oficial, client.beta.messages.create (copiloto.py:112-151)
    │     model claude-opus-5-5 · max_tokens 16000 · output_config.effort "high"
    │     betas ["server-side-fallback-2026-07-01"] + fallbacks "default"
    │     (si el modelo rechaza por sus filtros de seguridad, la API reintenta con otro
    │      modelo dentro de la misma llamada) · se maneja stop_reason refusal / max_tokens
    │
    └─ proveedor ollama: POST {OLLAMA_URL}/api/chat, stream false, timeout 180 s
          sólo REGLAS_BASE + artículos (sin la skill completa, por contexto acotado)
    ▼
Respuesta(texto, citas usadas, proveedor, bloqueada)  → la UI muestra los artículos consultados
```

**Diseño del prompt:**
- El bloque estable (reglas y skill) va primero y lleva `cache_control`.
- El contenido volátil (artículos, fecha y pregunta) va en el turno de usuario, para no invalidar la caché del prefijo.
- Las reglas obligan a citar sólo los artículos entregados, a declarar "sin respaldo en el corpus" cuando no alcanzan, a aplicar el router temporal y a distinguir obligación legal de recomendación.

**Errores:** cadena de excepciones tipadas del SDK (autenticación, rate limit, estado y conexión). La UI muestra un mensaje sin trazas.

### 9.4 Segregación de datos y privacidad

| Control | Implementación | Verificación |
|---|---|---|
| El copiloto no accede a la BD de Lince | El addon no importa `db/`, `psycopg2`, `modules/` ni `services/` | Test AST `TestSegregacion` |
| No recibe contexto de empresa | `responder()` sólo recibe la pregunta y el historial del propio copiloto | Revisión de código |
| Bloqueo de identificadores | Regex de RUT, correo y teléfono chileno **antes** de llamar al proveedor | Tests `TestFiltroDatosPersonales` y `test_bloquea_datos_personales_sin_llamar_al_proveedor` |
| Sin registro de preguntas | No se loguea ni se persiste nada | Revisión de código |
| Desactivado por defecto | `LINCE_COPILOTO_PROVEEDOR=desactivado` | Test |
| Opción sin salida de datos | Proveedor `ollama` local | — |

**Límites honestos:**
- El filtro de PII no detecta nombres ni datos indirectos.
- La segregación es a nivel de código, no de proceso: el copiloto corre en el mismo proceso que tiene `DATABASE_URL` en su entorno.
- Con `anthropic`, la pregunta sale a un proveedor extranjero. Jurídicamente es una comunicación a un tercero y posible transferencia internacional (Ley 21.719, arts. 15 bis, 27 y 28), y la retención depende de los términos del proveedor.
- Para aislamiento fuerte, el siguiente paso es ejecutar el copiloto como **servicio separado**, sin credenciales de BD y con egress restringido.

### 9.5 Estado de evaluación

- Hay tests funcionales de la recuperación (casos con artículo esperado en el top-3) y del ensamblado del prompt.
- La llamada al SDK se probó contra un servidor HTTP local simulado: estructura de la petición, cabecera beta, `fallbacks`, `cache_control` e interpretación de la respuesta.
- **No existe todavía un set de evaluación de calidad de respuestas** (exactitud jurídica, fidelidad a las citas, rechazo ante falta de respaldo) ni telemetría de uso, costo o tasa de caché. Es una tarea prioritaria antes de habilitar el copiloto a usuarios finales (§14).
- No hay streaming de respuesta: la respuesta llega completa.

### 9.6 IA en el ciclo de desarrollo

- **Agentes de código:** el repositorio lo editan en paralelo **Claude Code** y **Google Antigravity**. Las reglas compartidas están en `AGENTS.md`; `CLAUDE.md` agrega las específicas de Claude Code (revisar `git status` al iniciar, no tocar `.env`, BD ni servicios sin autorización, no hacer commits automáticos).
- **Skill de dominio** `.claude/skills/proteccion-datos-chile`:
  - Skill de dominio jurídico del proyecto: guía el análisis normativo de los agentes y alimenta la base de conocimiento del copiloto.
  - **Se verificó contra el corpus oficial** mediante RAG por artículo y verificadores independientes con veredicto por afirmación (verificado / impreciso / incorrecto / sin respaldo).
  - **1ª pasada:** 119 afirmaciones, 85% exactas, 0 incorrectas y cobertura del DS 662 muy baja.
  - Después se corrigió y se completó con el DS 662, la Ley 21.663 y los arts. 16, 16 bis y 48.
  - **2ª pasada:** ~263 afirmaciones, 94% exactas. Todas las desviaciones detectadas se corrigieron. No se ejecutó una tercera pasada sobre esas últimas correcciones.
- **Sincronización skill → runtime:** el copiloto usa una copia en `addons/normativa/conocimiento/`. La regenera `tools/sync_conocimiento.py` y un test falla si las copias se desfasan.

---

## 10. Infraestructura y despliegue

### 10.1 Estado actual

| Elemento | Estado |
|---|---|
| BD local / on-premise | `docker-compose.yml`: un servicio `postgres:16-alpine`, contenedor `lince-postgres`, volumen `lince_pgdata`, `restart: unless-stopped`, puerto publicado en `POSTGRES_BIND` (por defecto `127.0.0.1`), credenciales desde `.env` y healthcheck con `pg_isready`. Sin red dedicada ni backups |
| Modalidades de trabajo | **(a) Local, sin claves (por defecto):** cada desarrollador clona, copia `.env.example` a `.env` y levanta su propio compose. Ni la BD ni la app piden credenciales, y ambas responden sólo en `127.0.0.1`. **(b) Servidor on-premise del proyecto:** el acceso remoto se hace por túnel SSH (`ssh -L 8501:127.0.0.1:8501 -L 5432:127.0.0.1:5432 servidor`) sin publicar puertos en la LAN |
| App | **No contenedorizada.** No existen Dockerfile, `.dockerignore`, Procfile ni `railway.json` |
| PaaS previsto | Railway + Neon (`docs/IMPLEMENTACION.md:156-163`). Start command documentado: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`. Se configura en el panel de Railway; `railpack-plan.json` sólo fija Python 3.11 |
| TLS | Streamlit sirve HTTP plano. En PaaS el TLS lo termina la plataforma. Hacia Neon depende de `sslmode=require` en la URL |
| Observabilidad | Sólo `print()` en las migraciones. Sin logging estructurado, métricas, trazas ni registro de accesos |
| Backups | **Inexistentes** en el repositorio y sin documentación |
| CI/CD | Inexistente |

### 10.2 Perfil de recursos

- **CPU y RAM:** la importación lee el archivo completo en memoria (hasta 200 MB con la configuración actual de Streamlit) y openpyxl y pdfplumber son intensivos. La caché de `get_importacion_por_id` mantiene el JSONB completo por cada importación abierta.
- **Conexiones a la BD:** una por llamada a un repositorio. Una importación con 100 candidatos puede abrir unas 200 conexiones de forma secuencial. Frente a Neon conviene usar pooling (PgBouncer de Neon, o un pool en la app).
- **Almacenamiento:** sólo PostgreSQL. El crecimiento está dominado por los JSONB de importaciones y candidatos, que no tienen política de retención ni purga.

### 10.3 Escalado

Hoy es **mono-instancia**. Para escalar horizontalmente hacen falta tres cosas:
1. sesiones con afinidad (sticky sessions);
2. una caché compartida o TTL conservadores;
3. sacar `init_db()` del arranque de la app y llevarlo a un paso de migración controlado (job de release).

### 10.4 Deriva de versiones

| Elemento | Hallazgo |
|---|---|
| Python | `runtime.txt` declara 3.11, el `.venv` local usa 3.12.10 y hay `.pyc` de 3.14 en el árbol de trabajo |
| Dependencias directas | **[CORREGIDO]** Todas fijadas, incluidas `numpy` y `pyarrow` (D-12) |
| Lockfile | No existe: el resto de dependencias transitivas no está fijado. Se recomienda `pip-tools` o `uv` (Fase 0) |
| `fitz` (PyMuPDF) | La usa `build_corpus.py`, que es sólo de desarrollo, y no figura en ningún requirements |

---

## 11. Seguridad

| ID | Hallazgo | Referencia | Sev. |
|---|---|---|---|
| S-01 | **[CORREGIDO]** PostgreSQL estaba publicado en todas las interfaces con contraseña trivial versionada. Ahora el puerto queda en `127.0.0.1` y el desarrollo local usa `trust`, sin contraseñas en el repositorio. La seguridad descansa en el aislamiento de loopback: si se publica en red debe cambiarse a `scram-sha-256` | `docker-compose.yml` | ~~ALTA~~ BAJA (local) |
| S-02 | La app se conecta como superusuario; no existe un rol de aplicación con mínimo privilegio | `docker-compose.yml:7`, `DATABASE_URL` | **ALTA** |
| S-03 | Autenticación temporal: contraseña única compartida, sin usuarios, roles, bloqueo por intentos, expiración ni bitácora. El logout sólo cambia un flag | `app.py:166-216, 328-330` | **ALTA** (producción) |
| S-04 | **[MITIGADO]** Con `LINCE_AUTH_ENABLED=false` la app quedaba abierta a la LAN. Ahora `server.address=127.0.0.1` por defecto (verificado: no responde desde la IP de red). Desactivar el login sigue siendo riesgoso si se expone con `0.0.0.0` | `app.py:174`, `.streamlit/config.toml` | MEDIA |
| S-05 | Sin backups ni procedimiento de restauración | — | **ALTA** |
| S-06 | Escrituras y borrados por `id` sin verificar `empresa_id` (tratamientos, evaluaciones, visitas, evidencias, importaciones, MPI). Dashboard y exportación son globales | `db/repositories/tratamientos.py:132, 176` y otros | MEDIA (ALTA si hay varios clientes con acceso propio) |
| S-07 | **[MITIGADO]** `showErrorDetails=false` evita trazas, y el PASO 8 no expone la excepción al usuario. Persisten algunos `st.error(str(exc))` puntuales | `migrations.py` (Paso 7), `importar_antecedentes.py:692, 760, 784` | BAJA |
| S-08 | **[CORREGIDO]** Inyección de fórmulas en el XLSX exportado | `modules/exportar.py` | — |
| S-09 | Sin TLS propio. Hacia Neon depende de la URL | `db/connection.py:70` | MEDIA |
| S-10 | **[CORREGIDO]** Contradicción de privacidad en la importación: ver D-03 | `importar_antecedentes.py` | — |
| S-11 | DDL ejecutable desde la UI por cualquier usuario autenticado | `app.py:319-320` | BAJA |
| S-12 | **[MITIGADO]** `server.maxUploadSize=10` acota la subida en el servidor. La validación de la app sigue siendo posterior a la lectura | `importar_antecedentes.py:407, 417` | BAJA |
| S-13 | La URL de evidencias no se valida y se renderiza con `st.image` si termina en una extensión de imagen | `modules/evidencias.py:132-133` | BAJA |

**Controles positivos:**
- todo el SQL va parametrizado (los dos f-strings de SQL usan fragmentos fijos, sin entrada del usuario);
- el login usa `hmac.compare_digest` y `st.stop()` antes de cualquier consulta;
- `.env` nunca se versionó (`git log --all -- .env` vacío);
- la minimización por defecto en candidatos (opt-in para columnas no mapeadas) y el truncado a 4.000 caracteres;
- la segregación del copiloto (§9.4).

---

## 12. Calidad, defectos y deuda técnica

### 12.1 Defectos funcionales confirmados

| ID | Defecto | Referencia | Sev. |
|---|---|---|---|
| D-01 | **[CORREGIDO]** XLSX perdía la primera fila de datos (`fila_inicio=1` sobre filas que ya excluían el encabezado) | `services/extraccion_service.py` | — |
| D-02 | **[CORREGIDO]** Faltaban 4 FK en instalaciones nuevas (ver §7.4, PASO 8) | `db/migrations.py` | — |
| D-03 | **[CORREGIDO]** Se persistían filas crudas pese a la promesa de minimización | `importar_antecedentes.py`, `importaciones.py` | — |
| D-04 | **[CORREGIDO]** `VARCHAR(255)` en `rat_ambito_territorial` (ahora `TEXT`) | `db/migrations.py` | — |
| D-05 | Los tratamientos importados cuentan para la completitud MPI aunque la UI los presenta como borradores: la tabla no tiene estado | `services/mpi_service.py`, `importar_antecedentes.py:9, 90` | MEDIA |
| D-06 | **[CORREGIDO]** Selector de empresa dentro de `st.form` en Tratamientos y Visitas | `modules/tratamientos.py`, `visitas.py` | — |
| D-07 | El RAT no se puede editar desde Tratamientos | `modules/tratamientos.py:14, 282` | MEDIA |
| D-08 | El checklist se guarda con el texto de la pregunta como clave: cambiar la redacción rompe el historial. Un N/A penaliza el puntaje | `modules/visitas.py:92`, `services/checklist_service.py:16-23` | BAJA |
| D-09 | **[CORREGIDO]** Empresas homónimas colisionaban en el importador (ahora la clave es nombre + RUT) | `importar_antecedentes.py` | — |
| D-10 | `st.success()` seguido de `st.rerun()`: el mensaje nunca se ve | p. ej. `modules/empresas.py:42-43` | BAJA |
| D-11 | Borrado con un clic, sin confirmación, en Tratamientos, Visitas y Evidencias | `tratamientos.py:311`, `visitas.py:205`, `evidencias.py:134` | BAJA |
| D-12 | **[CORREGIDO]** Dependencias incompatibles: `pyarrow` 26 (exige NumPy ≥ 2) con `numpy` 1.26 rompía `st.dataframe` en toda la UI tras una instalación limpia | `requirements.txt` | — |

### 12.2 Rendimiento

- N+1 al guardar candidatos: 2 conexiones, 1 SELECT, 1 INSERT, 1 commit y 3 invalidaciones de caché por candidato (`importar_antecedentes.py:635-650`).
- Sin pool de conexiones.
- Faltan índices sobre `empresa_id` en `tratamientos`, `visitas` y `evaluaciones`, y sobre `evidencias.visita_id`. No se nota con el volumen actual.

### 12.3 Mantenibilidad

- `modules/importar_antecedentes.py` tiene 1.746 líneas; `_tab_revisar_candidatos` ocupa unas 350.
- Duplicación:
  - los flujos XLSX, CSV y DOCX-tabla son casi idénticos;
  - `save_perfil_mpi` se invoca 4 veces con los mismos argumentos;
  - los builders de opciones están repetidos en 3 módulos.
- Código muerto:
  - `utils/validators.py`;
  - `ESTADO_EVALUACION_COLOR`;
  - claves de sesión que se escriben y nunca se leen;
  - la acción `proponer_actualizacion`;
  - `detectar_candidato_similar_en_tratamientos`.
- `RAT_NUMERALES_INFO` (constants) no se reutiliza en `mpi_service.py`, que repite la lista de campos.
- **[CORREGIDO]** Textos de la UI que afirmaban "guardados en Neon" en un entorno Docker local, o un estado de la BD "en tiempo real" sin comprobarlo.
- No hay TODO ni FIXME en el código.

### 12.4 Discrepancias entre AGENTS.md y el código

**[CORREGIDO]** `AGENTS.md` ya describe correctamente que `init_db()` corre una vez por proceso, los TTL reales y la conexión por llamada sin pool.

Discrepancias vigentes entre las reglas de `AGENTS.md` (objetivo) y el código:

| Regla | Realidad |
|---|---|
| Filtro obligatorio por `empresa_id` | Lecturas con filtro opcional; escrituras por `id`; dashboard y exportación globales (S-06) |
| Sincronizar siempre con `empresa_activa_id` | En la importación, Tratamientos y Visitas; no en el resto de los módulos |
| Cero consultas N+1 | Persiste el N+1 al guardar candidatos (§12.2) |

### 12.5 Pruebas

- **47 tests** (`python -m unittest discover -s tests -t .`):
  - `tests/test_derechos.py` (16): router temporal, días hábiles con sábado y feriados, prórroga única, estándar dual y estados del plazo; más integración del repositorio (régimen y vencimiento al crear, prórroga, denegación fundada y aislamiento entre empresas);
  - `tests/test_addon_normativa.py` (21): corpus, recuperación, filtro de PII, copiloto y segregación;
  - `tests/test_correcciones.py` (10): regresión de D-01, D-03 y S-08, más **integración de migraciones contra PostgreSQL real**. La integración se activa con `LINCE_TEST_DATABASE_URL`, apuntando siempre a una BD desechable; ejecuta `init_db()` dos veces y verifica tablas, FK, tipos, seed y anulación de colgantes.
- **Sin cobertura:** la UI de `modules/` y la mayoría de los repositorios. Sin CI.
- **Nota sobre `streamlit.testing` (AppTest 1.32):**
  - no reinicia los triggers de botones tras `st.rerun()` (el servidor real sí), lo que reenvía formularios en bucle;
  - falla con `selectbox` que usan `format_func`.

  La simulación de clon de esta entrega replicó el comportamiento real del servidor para evitarlo. Hay que tenerlo en cuenta al escribir tests de UI.

---

## 13. Cobertura normativa: actual vs objetivo

"No modelado" indica una brecha de producto, no un incumplimiento del usuario.

| Ámbito | Fuente | Estado | Implementación |
|---|---|---|---|
| Registro y caracterización de tratamientos (RAT) | Ley 21.719 arts. 3, 12-14 ter; DS 662 art. 3 d) | **Cubierto** | `tratamientos` + 11 `rat_*`, importación y conciliación |
| Base de licitud y consentimiento | arts. 12, 13, 16, 16 bis | Parcial | Campo de texto; sin gestión de la evidencia de consentimiento ni de su revocación |
| Diagnóstico y evaluación | arts. 3, 14 quinquies, 48 | Parcial | 15 preguntas genéricas de seguridad, **no mapeadas a artículos** |
| Seguridad de la información | art. 14 quinquies; Ley 21.663 | Parcial | Checklist y evidencias |
| Evidencias y trazabilidad | art. 3 a) | **Cubierto** | `evidencias` (URL) |
| Visitas y auditorías internas | art. 48; DS 662 art. 13 d) | **Cubierto** | `visitas` |
| Derechos de los titulares | Ley 19.628 arts. 12, 16 · Ley 21.719 arts. 4-11 | **Cubierto** | `modules/derechos.py` (ver §8.5). Pendiente: autenticación de identidad según el procedimiento que fije la Agencia, y gratuidad o cobro (art. 10) |
| Transparencia y política | art. 14 ter | Parcial | Sólo como evidencia |
| Vulneraciones de seguridad | art. 14 sexies | **No modelado** | Registro, reporte a la Agencia y comunicación a titulares |
| Incidentes de ciberseguridad | Ley 21.663 arts. 9, 27 | **No modelado** | Plazos ante el CSIRT: alerta en 3 h, actualización en 72 h (24 h para operador de importancia vital) e informe en 15 días |
| Evaluación de impacto (EIPD) | art. 15 ter | **No modelado** | — |
| Encargados y contratos | art. 15 bis | Parcial | Texto libre en el RAT |
| Cesiones y transferencias internacionales | arts. 15, 27, 28 | Parcial | Campos del RAT |
| Datos sensibles, de salud, biométricos y de NNA | arts. 16-16 quáter | Parcial | Campo `rat_tipo_datos_sensibles` |
| Decisiones automatizadas | art. 8 bis | Parcial | Campo `rat_*` xi |
| Exposición sancionatoria | arts. 34-40 | **No modelado** | Base para la matriz de riesgos del MPI |
| MPI: programa, delegado, certificación y registro | arts. 48-53; DS 662 | **Cubierto parcialmente** | Perfil, delegado y estados declarativos. **Sin** matriz de riesgos (art. 3 e), protocolos, canal de denuncias ni sanciones internas (art. 3 f-i), ni plan anual del delegado (art. 13 i) |
| Consulta normativa | 4 normas | **Cubierto** | `addons/normativa` |
| Usuarios, roles y bitácora | art. 3 a) (responsabilidad demostrable) | **No modelado** | Contraseña compartida |

El detalle por requisito vive en `.claude/skills/proteccion-datos-chile/references/lince-grc-integracion.md` y en `decreto-662-mpi.md`.

---

## 14. Hacia dónde va Lince: hoja de ruta

**Objetivo del producto:** ser la plataforma con la que una organización chilena **implementa, opera y demuestra** su cumplimiento de la Ley 19.628/21.719 y de la Ley 21.663. El MPI del DS 662 es un módulo para quien lo adopte. Toda funcionalidad debe dejar **evidencia trazable**, porque el principio de responsabilidad obliga al responsable a poder acreditar la licitud (art. 3 a).

La secuencia propuesta, derivada de esta auditoría, se valida con la dirección del proyecto. **Las fases 0 y 1 son prerrequisito de producción.** Fecha de referencia: el régimen reformado rige desde el **01-12-2026**.

### Visión SaaS: implicancias de diseño

Lince se diseñará como **plataforma SaaS**: cada organización cliente es un *tenant* aislado. El modelo actual (un consultor con varias empresas en una misma BD, aislamiento sólo de contexto) **no es apto para SaaS tal como está**. Estas son las decisiones que conviene tomar **antes** de ampliar el modelo de datos, porque cambiarlas después es caro:

| Área | Estado actual | Requisito SaaS | Notas |
|---|---|---|---|
| Tenancy | `empresas` global, sin tenant; escrituras por `id` en varios repositorios (S-06) | `tenant_id` en todas las tablas de negocio y aislamiento a nivel BD con **Row-Level Security** de PostgreSQL. Alternativas: *schema-per-tenant* o *BD-per-tenant* para clientes que exijan aislamiento físico | El módulo de derechos ya filtra las escrituras por `empresa_id`: es el patrón a generalizar a `tenant_id` |
| Identidad | Contraseña única compartida | Usuarios por tenant; roles (administrador del cliente, delegado, operador, auditor externo, consultor); OIDC/SSO y MFA; bitácora inmutable | Es el bloque 5 del MVP. En SaaS pasa a ser bloqueante |
| Rol legal del operador | — | El operador de Lince es **encargado de tratamiento** de sus clientes (Ley 21.719 art. 15 bis): contrato de encargo, seguridad (14 quinquies), aviso de vulneraciones al responsable, devolución o supresión al término. Hosting, proveedor LLM y otros son **subencargados** que el cliente debe autorizar por escrito. Hosting fuera de Chile implica **transferencia internacional** (arts. 27-28) | El propio Lince debe tener su RAT, su evaluación de impacto (EIPD) y su política de seguridad: "comer la propia comida" |
| Ley 21.663 | — | El art. 4 incluye entre los servicios esenciales los "servicios digitales y servicios de tecnología de la información gestionados por terceros". **Evaluar si el operador de Lince queda sujeto** al deber de reporte de incidentes al CSIRT (3 h / 72 h / 15 días) y a la gestión de riesgos de ciberseguridad | `PENDIENTE DE VERIFICACIÓN` con asesoría legal y la calificación de la Agencia Nacional de Ciberseguridad |
| Datos por tenant | — | Backups y restauración por tenant; exportación completa (portabilidad del cliente) y borrado verificable al término del contrato; retención configurable | La matriz cruda de las importaciones (JSONB) debe entrar en esa política |
| Caché y estado | `st.cache_data` por proceso, compartida entre usuarios; sesión en memoria | Claves de caché con `tenant_id` (nunca compartir resultados entre tenants); caché compartida (p. ej. Redis) para escalar; sesiones con afinidad o sin estado | Riesgo de fuga entre tenants si una función cacheada no incluye el tenant en sus parámetros |
| Copiloto LLM | Sin acceso a la BD | Aislamiento por tenant, medición de uso y costo por tenant, límites de uso, y opción de proveedor local para clientes que no admitan transferencia internacional | La segregación actual (§9.4) es una buena base |
| Migraciones | DDL en el arranque de cada proceso | Migraciones versionadas como paso de release, compatibles con varias réplicas y con despliegues sin corte | Bloque 4 del MVP |
| Operación | Mono-instancia | Observabilidad por tenant, SLA, *feature flags*, *onboarding* automatizado, medición para facturación | — |

**Decisión de stack a evaluar temprano.** Streamlit permite prototipar rápido, pero tiene límites para un SaaS multi-tenant:
- estado de sesión en la memoria del proceso;
- escalado horizontal que requiere afinidad de sesión;
- autenticación y autorización que no son nativas;
- control fino de la UI y las APIs limitado.

Hay dos caminos:
- **(a)** mantener Streamlit detrás de un gateway de autenticación (OIDC) con RLS en la BD, como solución puente;
- **(b)** separar ya una API (p. ej. FastAPI) con la lógica y los repositorios actuales, y un frontend independiente.

La capa `db/` + `services/` actual se puede reutilizar en ambos casos, porque la UI no contiene SQL. Recomendación: decidirlo junto con el diseño de tenancy, antes de construir los módulos funcionales pendientes.

### Ruta crítica al Producto Mínimo Viable (MVP)

**Definición propuesta de MVP:** una instancia desplegada en la que una organización real (el piloto Serviphar) pueda:
1. levantar y mantener su RAT;
2. gestionar las solicitudes de derechos de los titulares;
3. registrar y gestionar vulneraciones e incidentes (Ley 21.719 art. 14 sexies + Ley 21.663);
4. demostrar quién hizo qué, con usuarios y bitácora;
5. operar con datos respaldados y recuperables.

Todo antes de la exigibilidad del 01-12-2026. El MPI completo y la IA avanzada quedan **después** del MVP. El MVP se valida con el piloto, pero los bloques 2 a 5 deben construirse ya con el diseño multi-tenant de la sección anterior, para no rehacerlos al pasar a SaaS.

| # | Bloque | Contenido | Área | Estado |
|---|---|---|---|---|
| 1 | Base técnica estable | Defectos críticos (D-01 a D-04, D-06, D-09, D-12), configuración segura local, dependencias fijadas, tests de integración de migraciones | App / BD | **Hecho (2026-10-22)** |
| 2 | Despliegue reproducible | Dockerfile de la app, compose completo, entorno de staging en Railway + Neon (`sslmode=require`), CI con tests | Infraestructura | Pendiente |
| 3 | Datos protegidos | Backups con restauración probada, rol de aplicación con mínimo privilegio, rotación de credenciales | Infraestructura | Pendiente |
| 4 | Migraciones versionadas | Alembic (o equivalente) como paso de release; sin DDL en el arranque ni en la UI | Infraestructura / BD | Pendiente |
| 5 | Identidad y bitácora | Usuarios, roles, autenticación robusta y bitácora de auditoría (reemplaza S-03) | App / Infraestructura | Pendiente |
| 6 | Derechos de los titulares | Flujo con plazos legales por régimen (estándar dual) y evidencia | App | **Hecho (2026-10-22)** |
| 7 | Vulneraciones e incidentes | Flujo único que derive las obligaciones de la Ley 21.719 y la Ley 21.663 (Fase 3) | App | Pendiente |

Los bloques 2 a 5 son del área de infraestructura y pueden avanzar en paralelo con los bloques funcionales 6 y 7.

### Fase 0: Endurecimiento de infraestructura (prioridad inmediata, área de infraestructura)

1. Contenedorizar la app: Dockerfile multi-stage, usuario no root y healthcheck en `/_stcore/health`. Agregar el servicio a compose con red interna. *(Postgres local ya publica sólo en `127.0.0.1`, con healthcheck.)*
2. Crear un rol de aplicación con mínimo privilegio, separado del rol propietario del esquema, y rotar credenciales en los entornos. *(Hecho: las credenciales de compose ya se leen desde `.env`.)*
3. Definir la estrategia de backups y restauración: `pg_dump` o PITR, cifrado, retención y restauración probada. Tener en cuenta que los JSONB pueden contener datos personales.
4. TLS de punta a punta y `sslmode=require` hacia la BD gestionada.
5. Logging estructurado, métricas básicas y registro de accesos.
6. Lockfile de dependencias transitivas (`pip-tools`/`uv`) y una misma versión de Python en runtime, venv e imagen. *(Hecho: dependencias directas fijadas, `maxUploadSize` y `showErrorDetails=false` configurados.)*
7. CI: lint, tests y build de la imagen. Los tests de integración contra PostgreSQL efímero ya existen (`LINCE_TEST_DATABASE_URL`) y sólo falta orquestarlos en CI.

### Fase 1: Integridad y corrección (base de datos y aplicación)

1. Migraciones versionadas (Alembic o equivalente), ejecutadas como paso de release y no en el arranque. Eliminar el botón de DDL de la UI.
2. ~~Migración correctiva de las 4 FK (D-02) y del `VARCHAR(255)` (D-04)~~ **Hecho (PASO 8).**
3. ~~Corregir D-01 y D-03~~ **Hecho.** Pendiente: un estado del tratamiento (borrador o vigente) para D-05, y la edición del RAT (D-07).
4. Cerrar la separación por empresa en escrituras y lecturas (S-06). Agregar `empresa_id` a `evidencias`.
5. Pool de conexiones, eliminar el N+1 de candidatos e índices sobre `empresa_id`.
6. ~~Escapar fórmulas en la exportación (S-08)~~ **Hecho.** Pendiente: sanear los `st.error(str(exc))` restantes (S-07).

### Fase 2: Identidad y responsabilidad demostrable

1. Usuarios, roles (consultor, cliente, auditor, administrador) y autenticación robusta (OIDC/SSO o equivalente). Reemplaza S-03.
2. Bitácora de auditoría inmutable: quién hizo qué y cuándo, sobre cada entidad.
3. Si los clientes acceden con cuenta propia: aislamiento multi-tenant a nivel de BD (Row-Level Security por `empresa_id`).

### Fase 3: Cobertura normativa integral (núcleo del producto)

| Módulo | Base legal | Contenido mínimo |
|---|---|---|
| ~~Derechos de los titulares~~ | arts. 4-11 | **Hecho:** ver §8.5 |
| Vulneraciones de seguridad | art. 14 sexies | Registro obligatorio, evaluación de riesgo, reporte a la Agencia "sin dilaciones indebidas", comunicación a titulares (datos sensibles, menores de 14, datos financieros) |
| Incidentes de ciberseguridad | Ley 21.663 arts. 9, 27 | Clasificación de efecto significativo y reloj de reporte al CSIRT (3 h / 72 h o 24 h / 15 días). Conviene un flujo único de incidentes que derive las obligaciones de ambas leyes |
| Evaluación de impacto (EIPD) | art. 15 ter | Disparadores obligatorios, metodología, riesgo inherente y residual, mitigación |
| Encargados y transferencias | arts. 15 bis, 27, 28 | Inventario de proveedores, contrato mínimo, mecanismo de transferencia |
| Matriz de riesgos y exposición sancionatoria | arts. 34-40; DS 662 art. 3 e) | Actividades de riesgo mapeadas a infracciones leves, graves y gravísimas |
| MPI completo | DS 662 arts. 3 f-i, 13 | Protocolos, canal de denuncias con reserva de identidad, sanciones internas, plan anual del delegado, control de vigencia del certificado |
| Hallazgos y planes de acción | — | Entidad propia con responsable, plazo y cierre con evidencia |
| Checklist normativo | — | Preguntas mapeadas a artículos, con ID estable |

### Fase 4: IA aplicada

1. **Set de evaluación del copiloto** (exactitud jurídica, fidelidad a las citas, rechazo sin respaldo, cumplimiento del router temporal) antes de habilitarlo a usuarios finales. Telemetría de costo, latencia y tasa de caché.
2. Recuperación híbrida (BM25 + embeddings) o reranking. Proceso de actualización del corpus con cada modificación legal y re-verificación de la skill.
3. Copiloto como servicio aislado: sin credenciales de BD, con egress restringido, cola de consultas y streaming.
4. Asistencia contextual dentro de los módulos (por ejemplo, la cita normativa de cada numeral del RAT o de cada requisito del MPI) **sin enviar datos de empresas al LLM**, o con el proveedor local cuando se requiera procesar contenido del cliente.
5. Extracción asistida en la importación documental (hoy es determinista), con revisión humana obligatoria y el proveedor local por defecto.

---

## 15. Convenciones de trabajo del repositorio

- **Idioma:** español en el código de dominio, la UI, los commits y la documentación.
- **Commits:** convención `tipo(ámbito): descripción` (`feat`, `fix`, `perf`, `docs`, `chore`). Los agentes de IA no hacen commits ni push sin instrucción expresa.
- **Cambios de esquema:** requieren aprobación explícita (AGENTS.md §3.A.4).
- **Caché:** toda escritura debe invalidar las lecturas cacheadas afectadas con `.clear()`.
- **Errores en la UI:** `try/except` con `st.error()` descriptivo, sin trazas ni credenciales.
- **Edición concurrente con agentes:** antes de editar, revisar `git status` y `git log`; no editar archivos con cambios sin commitear de otro agente sin coordinarlo.
- **Skill y corpus:**
  - tras editar la skill, ejecutar `python addons/normativa/tools/sync_conocimiento.py`;
  - tras actualizar las normas, ejecutar `build_corpus.py` y volver a verificar la skill.
- **Verificación antes de entregar:** `py_compile` o análisis estático, más la suite de tests.

---

## 16. Glosario

| Término | Significado |
|---|---|
| **Agencia** | Agencia de Protección de Datos Personales, autoridad creada por la Ley 21.719 |
| **CSIRT Nacional** | Equipo nacional de respuesta a incidentes de seguridad informática (Ley 21.663) |
| **DPD / Delegado** | Delegado de protección de datos personales. Obligatorio para adoptar y certificar un MPI (DS 662 art. 6) |
| **EIPD / DPIA** | Evaluación de impacto en protección de datos (art. 15 ter) |
| **MPI** | Modelo de prevención de infracciones: programa de cumplimiento voluntario (art. 49; DS 662) |
| **NNA** | Niños, niñas y adolescentes |
| **OIV** | Operador de importancia vital (Ley 21.663) |
| **RAT / RoPA** | Registro de actividades de tratamiento. En Lince implementa la caracterización del DS 662 art. 3 d) |
| **Readiness** | Preparación para una obligación que aún no es exigible (la Ley 21.719 antes del 01-12-2026) |
| **Router temporal** | Regla que determina qué régimen aplica según la fecha del hecho analizado |
| **Responsable** | Quien decide sobre el tratamiento de datos personales |
| **UTM** | Unidad Tributaria Mensual, base de las multas (art. 35: hasta 5.000 / 10.000 / 20.000 UTM) |
