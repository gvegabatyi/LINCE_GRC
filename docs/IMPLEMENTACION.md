# Serviphar GRC Lite - Documentación de Implementación

## Índice
1. [Resumen del Proyecto](#resumen-del-proyecto)
2. [Alcance y Estado Actual (Fase 1)](#alcance-y-estado-actual-fase-1)
3. [Arquitectura del Sistema](#arquitectura-del-sistema)
4. [Estructura del Código Fuente](#estructura-del-código-fuente)
5. [Modelo de Datos y Relaciones](#modelo-de-datos-y-relaciones)
6. [Seguridad, Aislamiento y Limitaciones Operativas](#seguridad-aislamiento-y-limitaciones-operativas)
7. [Configuración del Entorno y Despliegue en Railway](#configuración-del-entorno-y-despliegue-en-railway)
8. [Pruebas Realizadas — Fase 1](#pruebas-realizadas--fase-1)

---

## Resumen del Proyecto
Serviphar GRC Lite es una plataforma web modular de Gobernanza, Riesgo y Cumplimiento (GRC), diseñada para el levantamiento en terreno y la gestión de evaluaciones de privacidad, seguridad y cumplimiento.

La plataforma incorpora campos configurables que pueden apoyar proyectos relacionados con protección de datos personales y marcos de referencia. La determinación de cumplimiento normativo requiere validación jurídica y técnica específica para cada organización.

- **Repositorio:** [https://github.com/gvegabatyi/serviphar-grc-lite](https://github.com/gvegabatyi/serviphar-grc-lite)
- **Despliegue PaaS:** Railway
- **Base de Datos:** Neon PostgreSQL

---

## Alcance y Estado Actual (Fase 1)

En la **Fase 1** se ha implementado:
1. **Refactoring modular por capas:** Separación del router principal (`app.py`), capa de base de datos (`db/`), módulos de interfaz (`modules/`), servicios de negocio (`services/`) y utilidades (`utils/`).
2. **Módulo central de Evaluaciones GRC:** Gestión completa (Alta, Listado, Detalle con dependencias, Edición y Baja controlada) de proyectos de evaluación por empresa y período.
3. **Esquema relacional unificado:** Creación de la tabla `evaluaciones` y ampliación de tablas históricas (`tratamientos`, `visitas`, `evidencias`) con la clave foránea `evaluacion_id` (*nullable*), permitiendo la coexistencia de registros históricos y nuevos registros vinculados.
4. **Dashboard y Exportación compatibles:** Incorporación de métricas de evaluaciones y adición de la hoja `EVALUACIONES` en el libro consolidado Excel de 6 hojas.

> [!NOTE]
> Módulos no incluidos en esta fase (reservados para fases posteriores): RAT ampliado, Catálogo dinámico de checklist, Hallazgos, Matriz de Riesgos 5×5, Diagrama Bow Tie, Catálogo de Controles, Plan de Acción, Autenticación y Control de Roles (RBAC).

---

## Arquitectura del Sistema

```text
┌─────────────────┐
│   Usuario       │  (Navegador en PC / Tablet con conexión a Internet)
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│   Railway       │  Hosting PaaS
│   Start Command │  streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Serviphar GRC Lite                       │
│                                                             │
│   app.py (Router)                                           │
│     ├── db/ (connection.py, migrations.py, repositories/)   │
│     ├── modules/ (dashboard, empresas, evaluaciones, ...)   │
│     ├── services/ (checklist_service.py)                    │
│     └── utils/ (constants.py, validators.py)                │
└────────┬────────────────────────────────────────────────────┘
         │ Transacciones explícitas (psycopg2)
         ▼
┌─────────────────┐
│ Neon PostgreSQL │  Serverless Database
└─────────────────┘
```

---

## Estructura del Código Fuente

```text
serviphar_grc_lite/
├── app.py                      # Router principal y configuración Streamlit
├── requirements.txt            # Dependencias fijadas (Streamlit, Pandas, etc.)
├── runtime.txt                 # python-3.11
├── railpack-plan.json          # Configuración Railway
├── README.md                   # Guía de uso rápido y advertencias operativas
├── docs/
│   └── IMPLEMENTACION.md       # Documentación técnica completa
├── db/
│   ├── __init__.py             # Exporta get_connection, init_db
│   ├── connection.py           # Conexión transaccional y protección de secretos
│   ├── migrations.py           # Migraciones seguras e idempotentes
│   └── repositories/
│       ├── __init__.py
│       ├── empresas.py         # CRUD Empresas
│       ├── evaluaciones.py     # CRUD Evaluaciones GRC
│       ├── tratamientos.py     # CRUD Tratamientos ROPA (soporta evaluacion_id)
│       ├── visitas.py          # CRUD Visitas (soporta evaluacion_id y tipo_visita)
│       └── evidencias.py       # CRUD Evidencias (soporta evaluacion_id)
├── modules/
│   ├── __init__.py
│   ├── dashboard.py            # Panel de control con métricas de evaluaciones y empresas
│   ├── empresas.py             # Gestión de organizaciones
│   ├── evaluaciones.py         # Gestión del contenedor central de evaluaciones GRC
│   ├── tratamientos.py         # Registro de actividades de tratamiento (ROPA)
│   ├── visitas.py              # Auditorías en terreno y checklist de seguridad
│   ├── evidencias.py           # Registro de enlaces a evidencias
│   └── exportar.py             # Generación de reporte Excel consolidado (6 hojas)
├── services/
│   ├── __init__.py
│   └── checklist_service.py    # Lógica de cálculo de puntajes y cumplimiento
└── utils/
    ├── __init__.py
    ├── constants.py            # Constantes, estados, semáforos y preguntas
    └── validators.py           # Validaciones de entradas de formularios
```

---

## Modelo de Datos y Relaciones

El modelo organiza los registros tomando la **Evaluación GRC** como contenedor del proyecto:

```text
Empresa (empresas)
  └── Evaluación GRC (evaluaciones)
        ├── Visitas / Auditorías (visitas)
        │     └── Evidencias (evidencias)
        └── Tratamientos / ROPA (tratamientos)
```

### Tablas y Columnas en Fase 1:

1. **`empresas`**: `id, nombre, rut, direccion, contacto, email, telefono, created_at` (tabla preservada sin modificaciones en su estructura).
2. **`evaluaciones`** (Nueva): `id, empresa_id, nombre, tipo_evaluacion, periodo, alcance, objetivo, marco_normativo, auditor_responsable, fecha_inicio, fecha_cierre_planificada, fecha_cierre_real, estado, porcentaje_avance, puntaje_total, max_puntaje, observaciones, created_at, updated_at`.
3. **`tratamientos`**: `id, empresa_id, evaluacion_id (nullable), nombre_tratamiento, descripcion, base_legal, datos_personales, responsables, encargados, transferencias, created_at`.
4. **`visitas`**: `id, empresa_id, evaluacion_id (nullable), tipo_visita (nullable), fecha_visita, auditor, checklist_seguridad (JSONB), puntaje, observaciones, created_at`.
5. **`evidencias`**: `id, visita_id, evaluacion_id (nullable), descripcion, foto_url, created_at`.

---

## Seguridad, Aislamiento y Limitaciones Operativas

> [!CAUTION]
> **Condiciones de Uso en Fase 1:**
> - **Uso Interno:** La plataforma está destinada exclusivamente al consultor/auditor para trabajo en terreno.
> - **Acceso Remoto:** Se accede mediante navegador web con conexión a Internet desde notebook, PC o tablet.
> - **Almacenamiento Centralizado:** No existe modo *offline*; cada operación se persiste en tiempo real en Neon PostgreSQL.
> - **Sin Acceso Externo:** La plataforma **no debe ser abierta a clientes ni terceros externos** en esta etapa.
> - **Seguridad Pendiente:** No existe sistema de login, autenticación de usuarios, roles (RBAC) ni aislamiento multiempresa validado a nivel de base de datos.
> - **Evidencias:** No se permite almacenar archivos binarios en el servidor ni usar URLs públicas para documentos confidenciales.

---

## Configuración del Entorno y Despliegue en Railway

### Variables de Entorno Requeridas:
* `DATABASE_URL`: String de conexión PostgreSQL con SSL (`postgresql://usuario:contraseña@host:5432/nombre_bd?sslmode=require`). **Nunca debe incluirse en código, documentación ni repositorios.**

### Start Command Verificado en Railway:
```bash
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

---

## Pruebas Realizadas — Fase 1

### 1. Validación de Estructura y Sintaxis:
- Revisión completa de imports absolutos (`from db.repositories...`, `from modules...`, `from services...`, `from utils...`).
- Ausencia de dependencias no declaradas o módulos faltantes.
- Verificación de que `app.py` mantiene su rol como punto de entrada de Streamlit.

### 2. Validación de Migraciones Seguras (`db/migrations.py`):
- Validación de existencia de tablas históricas (`empresas`, `tratamientos`, `visitas`, `evidencias`).
- Creación de tabla `evaluaciones` mediante `CREATE TABLE IF NOT EXISTS`.
- Incorporación de columnas `evaluacion_id` y `tipo_visita` como *nullable* con `ALTER TABLE ADD COLUMN IF NOT EXISTS`.
- Confirmación de que `empresas` no fue alterada ni reconstruida.
- Confirmación de que no se crearon tablas de fases posteriores (`hallazgos`, `riesgos`, etc.).
- Confirmación de ausencia de sentencias `DROP TABLE`, `TRUNCATE` o `DELETE` masivo.

### 3. Validación de Funcionalidades CRUD y Regresión:
- **Empresas:** Listado, búsqueda y creación operando sobre la tabla existente.
- **Evaluaciones:** Creación de evaluación con estados (`borrador`, `en_progreso`, `en_revision`, `cerrada`), edición de campos, listado filtrable por empresa y eliminación segura (con `ON DELETE SET NULL` para no afectar dependencias).
- **Tratamientos:** Creación vinculada opcionalmente a evaluación, listado con filtro y visualización de registros históricos sin evaluación.
- **Visitas:** Formulario en terreno con checklist de 15 puntos, selector de evaluación y tipo de visita, cálculo de puntaje y persistencia en formato JSONB.
- **Evidencias:** Registro de URL externa y vinculación a visita/evaluación sin almacenamiento binario local.
- **Dashboard:** Métricas consolidadas de empresas, tratamientos y auditorías, junto con visualización de evaluaciones activas y manejo de estado vacío.
- **Exportación Excel:** Generación en memoria de libro `.xlsx` con 6 hojas (`EMPRESAS`, `TRATAMIENTOS`, `VISITAS`, `EVIDENCIAS`, `RESUMEN`, `EVALUACIONES`), manteniendo las 5 originales idénticas y la hoja de evaluaciones protegida ante excepciones.
