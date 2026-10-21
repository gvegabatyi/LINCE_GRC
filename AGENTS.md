# GUÍA DE DESARROLLO ASISTIDO POR IA — LINCE GRC

> [!IMPORTANT]
> **Propósito exclusivo de desarrollo:** Este archivo contiene directrices para agentes de IA durante el desarrollo y mantenimiento de **Lince GRC**. **No forma parte del runtime de la aplicación ni de la lógica de negocio del software GRC.**

---

## 1. Identidad y Stack Tecnológico
- **Proyecto:** Lince GRC — Gobierno, Riesgo y Cumplimiento (Serviphar GRC Lite).
- **Enfoque normativo:** Modelo de Prevención de Infracciones (MPI), Decreto Supremo N° 662 (Reglamento Ley N° 21.719 / Ley N° 19.628 Chile).
- **Lenguaje:** Python 3.11 (`runtime.txt`).
- **Framework UI:** Streamlit (ejecución reactiva por reruns).
- **Base de Datos:** PostgreSQL en Neon (Serverless) / Docker Local, conexión vía `psycopg2` y variable `DATABASE_URL`.
- **Despliegue:** Railway / Docker In-House.

---

## 2. Mapa Arquitectónico del Repositorio
```text
/
├── app.py                     # Router principal Streamlit, inicialización de sesión y control de init_db
├── db/
│   ├── connection.py          # Pool/conexión segura a PostgreSQL y context managers de transacción
│   ├── migrations.py          # DDL idempotente y control de versiones del esquema
│   └── repositories/          # Capa pura de acceso a datos (SELECT, INSERT, UPDATE)
│       ├── empresas.py        # Repositorio Empresas (con caché R2.1)
│       ├── importaciones.py   # Repositorio Importaciones Documentales RAT (con caché R2.1)
│       ├── mpi_gobernanza.py  # Repositorio Perfil MPI, Delegado y Normativa (con caché R2.1)
│       ├── tratamientos.py    # Repositorio RAT (con caché R2.1)
│       ├── evaluaciones.py    # Repositorio Evaluaciones
│       ├── visitas.py         # Repositorio Visitas y Auditorías
│       └── evidencias.py      # Repositorio Evidencias
├── modules/                   # Capa de presentación (UI Streamlit). NO debe contener SQL crudo
├── services/                  # Lógica de negocio pesada, parsers (DOCX, Excel) y cálculos
├── utils/                     # Constantes, validadores y componentes visuales
├── requirements.txt           # Dependencias fijadas de producción
└── docs/                      # Documentación funcional y técnica
```

---

## 3. Reglas de Oro para el Desarrollo (Guardrails Críticos)

### A. Base de Datos y Rendimiento (PostgreSQL / Docker / Neon)
1. **`init_db()` NUNCA en cada rerun:** La inicialización de la base de datos se ejecuta una única vez por sesión Streamlit (controlada por `st.session_state.get("db_initialized")` o `@st.cache_resource`). No reintroducir DDL ni inspecciones de tablas en el flujo interactivo regular.
2. **Cero consultas N+1:** Prohibido consultar PostgreSQL fila por fila en bucles. Usar agregaciones, `IN (...)` o joins en lote.
3. **Idempotencia estricta en DDL:** Toda sentencia en `db/migrations.py` debe usar `IF NOT EXISTS` o verificaciones previas seguras para evitar errores de conexión.
4. **No modificar esquema sin aprobación explícita:** Cualquier cambio a tablas de PostgreSQL requiere autorización previa del usuario.

### B. Política de Caché Segura (Microfase R2.1)
1. **Lecturas cacheadas:** Las funciones de lectura esenciales usan `@st.cache_data` con TTL definido:
   - Catálogo normativo (`get_referencias_normativas_df`): TTL 3600s.
   - Empresas activas (`get_empresas_df`): TTL 300s.
   - Tratamientos RAT (`get_tratamientos_df`): TTL 120s, clave obligatoria `empresa_id`.
   - Importaciones (`get_importaciones_documentales_df`): TTL 120s, clave obligatoria `empresa_id`.
2. **Invalidación obligatoria en escrituras:** Toda función que inserte, modifique o elimine datos debe invalidar la función de lectura correspondiente llamando a `.clear()` sobre la función decorada con cache.

### C. Multi-tenancy y Segregación de Empresas
1. **Filtro obligatorio:** Toda consulta y persistencia de evaluaciones, tratamientos, visitas e importaciones DEBE incluir y validar `empresa_id` / `empresa_activa_id`.
2. **Sincronización de UI:** En formularios o módulos con selector de empresa local (ej. `importar_antecedentes.py`), sincronizar siempre con `st.session_state["empresa_activa_id"]` para evitar estados huérfanos o botones invisibles.

### D. Flujo UI en Streamlit
1. **Visibilidad de controles:** Todo botón de acción principal (ej. "💾 Guardar importación RAT") debe ser accesible y visible independientemente de si el archivo fuente es DOCX, XLSX o CSV.
2. **Manejo defensivo de errores:** Utilizar bloques `try/except` con `st.error()` visible y descriptivo, sin exponer trazas crudas ni credenciales al usuario.

---

## 4. Protocolo de Trabajo para el Asistente
1. **Idioma:** Todas las respuestas e interacciones deben ser en **Español**.
2. **Sin cambios no autorizados:** Modificar únicamente los archivos autorizados en cada instrucción del usuario.
3. **Cero comandos Git automáticos:** No realizar commits, pushes ni merges a menos que el usuario lo solicite expresamente.
4. **Verificación antes de concluir:** Validar la sintaxis (`py_compile` o análisis estático) y asegurar que no se hayan introducido regresiones en APIs existentes.
