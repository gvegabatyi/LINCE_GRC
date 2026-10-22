# Lince GRC

**Gobierno, Riesgo y Cumplimiento**

**Plataforma integral de cumplimiento e implementación de protección de datos personales en Chile.**

> **¿Te incorporas al proyecto?** Empieza por [`docs/AUDITORIA_ESTADO_PROYECTO.md`](docs/AUDITORIA_ESTADO_PROYECTO.md): estructura, arquitectura, montaje del entorno, modelo de datos, IA, seguridad, estado real y hoja de ruta.

Lince GRC integra en una sola plataforma el cumplimiento de:
- la **Ley N° 19.628 modificada por la Ley N° 21.719** (régimen completo: principios, licitud, derechos de los titulares, deberes del responsable, seguridad, vulneraciones, evaluación de impacto, encargados, transferencias, sanciones y prevención de infracciones);
- la **Ley N° 21.663, Marco de Ciberseguridad** (incidentes y reporte al CSIRT Nacional);
- el **Decreto Supremo N° 662 del Ministerio de Hacienda**, que reglamenta los **Modelos de Prevención de Infracciones (MPI)** del artículo 49.

El MPI es uno de los componentes de Lince, no su alcance: la plataforma acompaña la implementación y la gestión del cumplimiento de la ley completa, adopte o no la organización un MPI. Su arquitectura modular abarca:
- Registro de actividades de tratamiento (RAT) y caracterización de datos.
- Diagnóstico, evaluaciones y auditorías de cumplimiento.
- Modelo de Prevención de Infracciones (MPI) y Delegado de Protección de Datos.
- Privacidad y protección de datos personales.
- Gestión de riesgos y controles.
- Auditoría, hallazgos y planes de acción.
- Ciberseguridad.
- Continuidad operacional.
- Gestión de terceros.
- Otros estándares, normas y obligaciones aplicables.

---

## Módulos Disponibles en Fase 2A

1. **🏠 Dashboard:** Métricas consolidadas e **Indicador Interno de Completitud Documental del MPI** (Decreto N° 662).
2. **🏢 Empresas:** Catálogo y gestión de organizaciones del grupo.
3. **📁 Evaluaciones GRC:** Contenedor principal de proyectos de evaluación por empresa y período.
4. **🛡️ Perfil MPI y Delegado (Nuevo Fase 2A):**
   - Individualización del responsable y representante legal *(Art. 3 letra a)*.
   - Designación y canal de contacto público accesible del Delegado DPD *(Arts. 3 b, 7, 8 y 11)*.
   - Declaración de idoneidad, recursos y facultades suficientes *(Arts. 3 c, 9 y 10)*.
   - Separación estricta entre estados internos de implementación y estados registrales oficiales *(Arts. 15 y 17)*.
   - Catálogo interactivo de Trazabilidad Normativa del Decreto N° 662.
5. **📋 Tratamientos (RAT Ampliado - Fase 2A):**
   - Registro con los **11 numerales taxativos del Art. 3 letra d)** (tipos de datos/sensibles, ámbito territorial, bases administradas, titulares, fines, procedencia, base licitud, destinatarios, transferencias internacionales, plazos y perfilamiento).
   - Sección separada de campos complementarios GRC.
6. **📥 Importar Antecedentes RAT (Fase 2A.2):**
   - Bandeja documental para ingesta temporal en memoria de antecedentes (.xlsx, .csv, .docx, .pdf con texto, .md, .txt).
   - Validación estructural ZIP/OpenXML y verificación de texto en PDF sin OCR.
   - Mapeo manual de columnas a los 11 numerales RAT con límite de 4.000 caracteres por campo.
   - Conciliación campo a campo contra tratamientos existentes con confirmación humana explícita.
   - Política de minimización: los datos extraídos no se exportan ni se usan en completitud hasta su validación manual.
7. **🔍 Visitas / Auditorías:** Auditorías en terreno con checklist de seguridad (15 puntos) y tipo de visita.
8. **📸 Evidencias:** Registro de enlaces a evidencias fotográficas y documentales externas vinculables al Perfil, Delegado y RAT.
9. **📊 Exportar Informe:** Descarga de informe consolidado Excel de 12 hojas profesionales (incluye `IMPORTACIONES_DOCUMENTALES` y `CANDIDATOS_RAT` en modo solo metadatos).

---

## ⚠️ Advertencia de Seguridad, Alcance y Uso Operativo

> [!CAUTION]
> - **Aviso de Estados Oficiales:** Los estados oficiales son antecedentes declarativos y documentales. Lince GRC **no certifica, registra, supervisa ni valida oficialmente modelos de prevención de infracciones**. Estas atribuciones corresponden exclusivamente a la Agencia de Protección de Datos Personales.
> - **Indicador Interno:** El porcentaje de completitud documental es un indicador interno de Fase 2A y no acredita por sí solo el cumplimiento material de la ley.
> - **Uso Interno:** La plataforma está destinada exclusivamente al consultor/auditor para trabajo en terreno.
> - **Acceso Remoto y Centralizado:** Se accede mediante navegador web con conexión a Internet desde notebook, PC o tablet hacia Neon PostgreSQL.
> - **Sin Acceso Externo:** La plataforma **no debe ser abierta a clientes ni terceros externos** en esta etapa.
> - **Minimización de Datos:** El RUT del delegado es opcional y no se expone públicamente ni en reportes generales.

---

## Estructura del Código

```text
serviphar_grc_lite/
  ├── app.py                     # Router principal Streamlit
  ├── db/
  │   ├── connection.py          # Conexión y transacciones seguras
  │   ├── migrations.py          # Migraciones seguras e idempotentes (Fase 1 y 2A)
  │   └── repositories/
  │       ├── empresas.py        # Repositorio Empresas
  │       ├── evaluaciones.py    # Repositorio Evaluaciones
  │       ├── mpi_gobernanza.py  # Repositorio Perfil MPI, Delegado y Normativa (Fase 2A)
  │       ├── tratamientos.py    # Repositorio RAT con 11 numerales (Fase 2A)
  │       ├── visitas.py         # Repositorio Visitas y Auditorías
  │       └── evidencias.py      # Repositorio Evidencias
  ├── modules/                   # Módulos UI interactivos Streamlit
  ├── services/                  # Lógica de negocio y cálculo de completitud MPI
  ├── utils/                     # Constantes, validadores y semáforos
  ├── requirements.txt           # Dependencias fijadas
  ├── runtime.txt                # python-3.11
  └── docs/
      └── IMPLEMENTACION.md      # Documentación técnica completa
```

---

## Ejecución Local

Guía completa y verificada (requisitos, verificación y problemas frecuentes): [`docs/AUDITORIA_ESTADO_PROYECTO.md` §5](docs/AUDITORIA_ESTADO_PROYECTO.md#5-montaje-del-entorno-de-desarrollo).

```bash
cp .env.example .env              # desarrollo local sin claves: no hay que editar nada
docker compose up -d              # PostgreSQL 16 local (sólo 127.0.0.1)
python3.11 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py              # http://localhost:8501 (el esquema se crea al iniciar)
python -m unittest discover -s tests -t .   # pruebas
```

Para una BD gestionada (Neon), usar su URL en `DATABASE_URL` con `?sslmode=require`.
