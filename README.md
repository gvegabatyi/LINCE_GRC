# Lince GRC

**Gobierno, Riesgo y Cumplimiento**

Plataforma integral para gestionar gobierno, riesgos, cumplimiento, evidencias y acciones de mejora.

La implementación de los requerimientos para el **Modelo de Prevención de Infracciones (MPI)** bajo el **Decreto Supremo N° 662 del Ministerio de Hacienda** (Reglamentario del artículo 49 incorporado por la Ley N° 21.719 a la Ley N° 19.628 sobre Protección de la Vida Privada en Chile) constituye el foco normativo inicial de la plataforma, la cual está diseñada con una arquitectura modular y extensible a diversos dominios y marcos GRC, incluyendo:
- Modelo de Prevención de Infracciones (MPI).
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
6. **🔍 Visitas / Auditorías:** Auditorías en terreno con checklist de seguridad (15 puntos) y tipo de visita.
7. **📸 Evidencias:** Registro de enlaces a evidencias fotográficas y documentales externas vinculables al Perfil, Delegado y RAT.
8. **📊 Exportar Informe:** Descarga de informe consolidado Excel de 10 hojas profesionales (`EMPRESAS`, `TRATAMIENTOS`, `VISITAS`, `EVIDENCIAS`, `RESUMEN`, `EVALUACIONES`, `PERFIL_MPI`, `DELEGADO_DPD`, `RAT_DECRETO_662`, `REFERENCIAS_NORMATIVAS`).

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

1. Asegurar dependencias instaladas:
   ```bash
   pip install -r requirements.txt
   ```
2. Configurar variable de entorno `DATABASE_URL`:
   ```bash
   export DATABASE_URL="postgresql://usuario:contraseña@host:5432/nombre_bd?sslmode=require"
   ```
3. Iniciar Streamlit:
   ```bash
   streamlit run app.py
   ```
