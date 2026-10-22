# Lince GRC - Documentación de Implementación

> **Documento histórico (Fases 1 y 2A).** Describe el diseño funcional original. El **estado vigente** está en [`AUDITORIA_ESTADO_PROYECTO.md`](AUDITORIA_ESTADO_PROYECTO.md): arquitectura real, montaje local sin claves, defectos corregidos y ruta al MVP. Si ambos documentos difieren, prevalece la auditoría.

**Gobierno, Riesgo y Cumplimiento**

## Índice
1. [Resumen del Proyecto](#resumen-del-proyecto)
2. [Alcance y Estado Actual (Fase 1 y Fase 2A)](#alcance-y-estado-actual-fase-1-y-fase-2a)
3. [Arquitectura del Sistema](#arquitectura-del-sistema)
4. [Estructura del Código Fuente](#estructura-del-código-fuente)
5. [Modelo de Datos y Trazabilidad Normativa](#modelo-de-datos-y-trazabilidad-normativa)
6. [Registro de Actividades de Tratamiento (RAT — 11 Numerales)](#registro-de-actividades-de-tratamiento-rat--11-numerales)
7. [Gobernanza MPI, Delegado DPD y Separación de Estados](#gobernanza-mpi-delegado-dpd-y-separación-de-estados)
8. [Seguridad, Aislamiento y Limitaciones Operativas](#seguridad-aislamiento-y-limitaciones-operativas)
9. [Configuración del Entorno y Despliegue en Railway](#configuración-del-entorno-y-despliegue-en-railway)
10. [Pruebas Realizadas — Fase 2A](#pruebas-realizadas--fase-2a)

---

## Resumen del Proyecto
**Lince GRC** es una **plataforma integral de cumplimiento e implementación de protección de datos personales en Chile**. Cubre:
- la Ley N° 19.628 modificada por la Ley N° 21.719, en su régimen completo;
- la Ley N° 21.663, Marco de Ciberseguridad;
- el Decreto Supremo N° 662 del Ministerio de Hacienda, que reglamenta los Modelos de Prevención de Infracciones (MPI) del artículo 49 de la Ley N° 19.628, incorporado por la Ley N° 21.719.

El MPI es un componente de la plataforma, no su alcance. La cobertura por ámbito legal y las brechas de producto están en `.claude/skills/proteccion-datos-chile/references/lince-grc-integracion.md`.

- **Repositorio:** [https://github.com/gvegabatyi/serviphar-grc-lite](https://github.com/gvegabatyi/serviphar-grc-lite)
- **Despliegue PaaS:** Railway
- **Base de Datos:** Neon PostgreSQL

---

## Alcance y Estado Actual (Fase 1 y Fase 2A)

### Implementado en Fase 1:
1. Arquitectura modular por capas (`db/`, `modules/`, `services/`, `utils/`).
2. Contenedor central de Evaluaciones GRC por empresa y período.
3. Repositorios y vistas de Empresas, Visitas (Checklist de 15 puntos), Evidencias y Exportación consolidada.

### Implementado en Fase 2A (Decreto N° 662 / Ley N° 21.719):
1. **Perfil MPI del Responsable:** Individualización del responsable y representante legal *(Art. 3 letra a)*, fecha de adopción y alcance.
2. **Delegado de Protección de Datos (DPD):** Designación formal *(Arts. 3 b y 6)*, canal de contacto accesible a titulares y Agencia *(Art. 11)*, autonomía técnica *(Art. 8)*, idoneidad profesional *(Art. 10)* y recursos/facultades asignadas *(Arts. 3 c y 9)*, con minimización de datos (RUT opcional y no expuesto públicamente).
3. **Separación Estricta de Estados:** Diferenciación entre el *Estado Interno de Implementación* (`preparacion`, `implementado_internamente`, `en_revision_interna`) y el *Estado Registral Oficial* (`sin_solicitud`, `solicitud_en_tramite`, `certificado_agencia`, `inscrito_registro_agencia`, `vencido`, `revocado`) *(Arts. 15 y 17)*.
4. **RAT con los 11 Numerales Taxativos:** Estructuración estricta del Art. 3 letra d) (numerales i al xi) en la tabla `tratamientos` con separación clara de campos complementarios GRC.
5. **Capa de Trazabilidad Normativa:** Tablas `normativa_fuentes` y `normativa_referencias` con el catálogo de artículos y criterios del Decreto N° 662.
6. **Indicador Interno de Completitud Documental:** Medición ponderada en el Dashboard (perfil, DPD, RAT, 11 numerales y evidencias) con aviso explícito de que no constituye certificación oficial.
7. **Exportación Consolidada de 10 Hojas:** Generación en memoria de libro `.xlsx` con las 6 hojas históricas + 4 hojas nuevas (`PERFIL_MPI`, `DELEGADO_DPD`, `RAT_DECRETO_662`, `REFERENCIAS_NORMATIVAS`).

### Implementado en Fase 2A.2 (Importación y Conciliación Documental RAT):
1. **Bandeja Documental Segura:** Módulo `📥 Importar Antecedentes RAT` para ingesta temporal en memoria de antecedentes históricos (.xlsx, .csv, .docx, .pdf con texto, .md, .txt).
2. **Validación Estructural Rigurosa:** Inspección de contenedores ZIP de Office OpenXML (detección de `[Content_Types].xml` y `xl/workbook.xml` o `word/document.xml`), comprobación de encabezado PDF `%PDF-` con `pdfplumber` y decodificación controlada de texto plano.
3. **Privacidad y Minimización:** Aviso previo de legitimidad; exclusión de datos de filas en el resumen técnico; límite de 4.000 caracteres por campo con truncamiento advertido; control opt-in (desactivado por defecto) para columnas adicionales no mapeadas; y exclusión estricta de contenidos extraídos en la exportación Excel (hojas 11 `IMPORTACIONES_DOCUMENTALES` y 12 `CANDIDATOS_RAT`).
4. **Conciliación Campo a Campo con Tratamientos Existentes:** Comparación lado a lado entre valor actual en base de datos y valor extraído, con checkboxes individuales y confirmación humana explícita. No existe actualización automática.
5. **Ausencia de Estado Persistente en Tratamientos:** La tabla `tratamientos` no posee columna de estado. Los tratamientos creados desde importación se catalogan explícitamente como *"Creado desde importación; pendiente de caracterización y validación en Tratamientos (RAT)"*, manteniéndose el estado `aprobado_borrador` exclusivamente en el candidato de importación.

> [!NOTE]
> Elementos diferidos expresamente para fases posteriores: Matriz de riesgos 5×5, catálogo de controles, diagnóstico completo con hallazgos y planes de acción, canal de denuncias operado por terceros, notificaciones a la Agencia, y perfiles de usuario / RBAC.

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
│                         Lince GRC                           │
│                                                             │
│   app.py (Router)                                           │
│     ├── db/ (connection.py, migrations.py, repositories/)   │
│     ├── modules/ (dashboard, empresas, evaluaciones,        │
│     │             mpi_gobernanza, tratamientos, visitas,    │
│     │             evidencias, exportar)                     │
│     ├── services/ (checklist_service.py, mpi_service.py)    │
│     └── utils/ (constants.py, validators.py)                │
└────────┬────────────────────────────────────────────────────┘
         │ Transacciones explícitas (psycopg2)
         ▼
┌─────────────────┐
│ Neon PostgreSQL │  Serverless Database
└─────────────────┘
```

---

## Modelo de Datos y Trazabilidad Normativa

```text
Empresa (empresas)
  ├── Perfil MPI (mpi_perfiles) [1 activo por empresa]
  ├── Delegado DPD (mpi_delegados) [1 activo por empresa]
  ├── Evaluaciones GRC (evaluaciones)
  │     ├── Visitas / Auditorías (visitas) ──< Evidencias (evidencias)
  │     └── Tratamientos (tratamientos) [11 Numerales Art. 3 d]
  └── Evidencias Generales (evidencias)

Normativa (normativa_fuentes) ──< Referencias (normativa_referencias) [Decreto 662]
```

---

## Registro de Actividades de Tratamiento (RAT — 11 Numerales)

Estructurado conforme al **Art. 3 letra d) del Decreto N° 662**:

1. `rat_tipo_datos_sensibles` (num. i: tipos de datos personales y categorías especiales/sensibles).
2. `rat_ambito_territorial` (num. ii: nacional, regional, transfronterizo).
3. `rat_bases_datos_administradas` (num. iii: categorías de bases de datos o sistemas).
4. `rat_categorias_titulares` (num. iv: trabajadores, clientes, proveedores, etc.).
5. `rat_finalidades` (num. v: fines específicos de las operaciones).
6. `rat_fuente_datos_acceso_publico` (num. vi: procedencia y fuentes de acceso público).
7. `rat_base_licitud_interes_legitimo` (num. vii: base de licitud e interés legítimo).
8. `rat_destinatarios_cesiones` (num. viii: categorías de terceros destinatarios).
9. `rat_transferencias_internacionales_art27` (num. ix: país/organización y medio de cumplimiento art. 27).
10. `rat_plazo_condicion_supresion` (num. x: plazos de conservación o condiciones de supresión).
11. `rat_decisiones_automatizadas_perfilamiento` (num. xi: perfilamiento, lógica y consecuencias).

---

## Gobernanza MPI, Delegado DPD y Separación de Estados

1. **Perfil del Responsable (Art. 3 a):** Individualización del responsable y representante legal. Restricción única de 1 perfil activo por empresa mediante índice parcial:
   ```sql
   CREATE UNIQUE INDEX idx_mpi_perfil_activo ON mpi_perfiles(empresa_id) WHERE activo = TRUE;
   ```
2. **Delegado DPD (Arts. 3 b, c; Arts. 6-13):** Calidad de vínculo (Art. 7), canal de contacto accesible (Art. 11), autonomía técnica (Art. 8), idoneidad (Art. 10) y medios/recursos (Art. 9). Restricción única de 1 delegado activo por empresa:
   ```sql
   CREATE UNIQUE INDEX idx_mpi_delegado_activo ON mpi_delegados(empresa_id) WHERE activo = TRUE;
   ```
3. **Separación de Estados:**
   - **Estado Interno:** `preparacion`, `implementado_internamente`, `en_revision_interna`.
   - **Estado Oficial:** `sin_solicitud`, `solicitud_en_tramite`, `certificado_agencia`, `inscrito_registro_agencia`, `vencido`, `revocado` (requiere entidad certificadora, N° de certificado y evidencia).

---

## Seguridad, Aislamiento y Limitaciones Operativas

> [!CAUTION]
> **Condiciones de Uso en Fase 2A:**
> - **Aviso de Estados Oficiales:** Los estados oficiales son antecedentes declarativos. Lince GRC **no certifica, registra, supervisa ni valida oficialmente modelos de prevención de infracciones**. Estas atribuciones corresponden a la Agencia de Protección de Datos Personales.
> - **Uso Interno:** Plataforma destinada exclusivamente al consultor/auditor para trabajo en terreno.
> - **Sin Acceso Externo:** La plataforma **no debe ser abierta a clientes ni terceros externos** en esta etapa.
> - **Minimización de Datos:** El RUT del delegado es opcional y no se expone públicamente ni en reportes generales.

---

## Configuración del Entorno y Despliegue en Railway

### Variables de Entorno Requeridas:
* `DATABASE_URL`: String de conexión PostgreSQL con SSL (`postgresql://usuario:contraseña@host:5432/nombre_bd?sslmode=require`).

### Start Command Verificado en Railway:
```bash
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

---

## Pruebas Realizadas — Fase 2A

### 1. Validación de Estructura e Imports:
- Árbol de imports absolutos verificado en los nuevos repositorios (`mpi_gobernanza.py`), módulos (`mpi_gobernanza.py`) y servicios (`mpi_service.py`).
- Cero dependencias circulares ni errores de sintaxis.

### 2. Validación de Migraciones Seguras (`db/migrations.py`):
- Validación de tablas históricas previas.
- Creación de tablas `normativa_fuentes`, `normativa_referencias`, `mpi_perfiles` y `mpi_delegados` mediante `CREATE TABLE IF NOT EXISTS`.
- Creación de índices parciales únicos para garantizar 1 solo perfil y 1 solo delegado activo por empresa.
- Inserción idempotente de las 11 columnas del RAT con `ALTER TABLE ADD COLUMN IF NOT EXISTS`.
- Carga transaccional (*seed*) de las referencias del Decreto N° 662.

### 3. Validación de Funcionalidades:
- **Perfil MPI:** Registro de representante legal, estados interno y oficial, y vinculación de evidencia.
- **Delegado DPD:** Registro con canal de contacto público, autonomía, idoneidad y recursos; minimización de RUT interno.
- **RAT Ampliado:** Registro y visualización completa de los 11 numerales taxativos del Art. 3 letra d) y campos complementarios.
- **Completitud Documental:** Cálculo estricto que no permite 100% si falta perfil, delegado, RAT, numerales o evidencia.
- **Exportación Excel:** Generación consolidada de 10 hojas profesionales sin fallos ante tablas vacías.
