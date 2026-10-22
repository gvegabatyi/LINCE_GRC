# Seguridad, incidentes, DPIA y decisiones automatizadas

## Seguridad — artículos 3 f) y 14 quinquies

La seguridad debe ser **adecuada al riesgo**, no una lista fija de productos. Evalúa estado de la técnica, costos de aplicación, naturaleza, alcance, contexto, finalidades y probabilidad/gravedad del impacto sobre titulares.

Medidas que el art. 14 quinquies menciona expresamente, "entre otras":

- seudonimización y cifrado;
- confidencialidad, integridad, disponibilidad y resiliencia permanentes;
- capacidad de restaurar la disponibilidad y el acceso a los datos **de forma rápida** tras un incidente físico o técnico;
- verificación, evaluación y valoración regulares de la eficacia de las medidas.

Controles de buena práctica para evidenciar esas medidas (no enumerados literalmente por la ley):

- control de acceso y privilegio mínimo;
- backups y restauraciones probadas;
- gestión de vulnerabilidades y cambios;
- logging y detección sin exponer datos innecesarios;
- seguridad de terceros o encargados (el encargado debe cumplir directamente los arts. 14 bis y 14 quinquies, según el art. 15 bis);
- confidencialidad del personal (arts. 3 h y 14 bis);
- formación del personal (función del delegado: Ley art. 50 d; DS 662 art. 13 f).

Los estándares de seguridad e información **serán determinados** por instrucción general de la Agencia, diferenciados según el tipo de dato, la actividad del responsable, el volumen, la naturaleza y las finalidades de los datos, si se trata de una persona natural o jurídica y el tamaño de la empresa (Ley 20.416) (art. 14 septies). `PENDIENTE DE VERIFICACIÓN REGULATORIA`.

**Regla de evidencia:** ante un incidente y en controversia judicial o administrativa, el responsable debe poder acreditar que las medidas existían y funcionaban en relación con el riesgo y la tecnología disponible. “Tenemos una política” no basta.

## Vulneraciones de seguridad — artículo 14 sexies

### Paso 1: clasificar el evento

Determina si hubo destrucción, filtración, pérdida, alteración accidental o ilícita, comunicación o acceso no autorizado a datos personales.

### Paso 2: evaluar el umbral legal

Si existe **riesgo razonable para los derechos y libertades de los titulares**, el responsable debe reportar la vulneración a la Agencia por los medios más expeditos posibles y **sin dilaciones indebidas**.

**Guardrail:** la Ley 21.719 no fija un plazo de 72 horas para reportar a la Agencia de Protección de Datos; el estándar es "sin dilaciones indebidas". No lo confundas con la Ley 21.663 (ver el paso 2 bis). Los deberes de información de otras leyes se suman (art. 14 sexies inc. final).

Si el incidente ocurre en un encargado, éste debe reportarlo al responsable (art. 15 bis). Pacta plazos internos en el contrato.

### Paso 2 bis: Ley 21.663, Marco de Ciberseguridad

Aplica a las instituciones del art. 4° de la Ley 21.663: **servicios esenciales** (entre otros, prestación institucional de salud, **producción y/o investigación de productos farmacéuticos**, banca, infraestructura digital y servicios TI gestionados por terceros) y **operadores de importancia vital**. Determina primero si la entidad está calificada.

- Un incidente es de **efecto significativo**, entre otros casos, si afecta sistemas informáticos que contienen datos personales (art. 27). Otros criterios son el número de afectados, la duración y la extensión geográfica.
- Plazos de reporte al **CSIRT Nacional** (art. 9):
  - alerta temprana: **3 horas** desde que se tiene conocimiento;
  - actualización con evaluación inicial e indicadores de compromiso: **72 horas** (**24 horas** si es operador de importancia vital con servicio esencial afectado);
  - informe final: **15 días corridos** desde la alerta temprana;
  - plan de acción del operador de importancia vital: **7 días corridos** como máximo.
- En los reportes al CSIRT **se omiten los datos personales** (art. 27). Sólo para efectos de esa ley, la dirección IP no se considera dato personal.
- Los **operadores de importancia vital** deben informar a los potenciales afectados cuando lo requiera la Agencia Nacional de Ciberseguridad, especialmente si hay datos personales y no existe otra disposición legal que exija la notificación (art. 8 g).
- La Ley 21.663 también recoge el principio de seguridad y privacidad desde el diseño y por defecto (art. 3 N° 8), que se conecta con el art. 14 quáter.

El reporte al CSIRT y el reporte a la Agencia de Protección de Datos son **independientes y acumulables**: uno no reemplaza al otro.

### Paso 3: registrar el incidente

La ley exige registrar las comunicaciones de vulneraciones con su naturaleza, efectos, categorías de datos, número aproximado de titulares y medidas adoptadas para gestionarlas y prevenir incidentes futuros (art. 14 sexies inc. 2). Omitir las comunicaciones o los registros es infracción grave (art. 34 ter k; el texto legal remite al "14 quinquies", aparentemente por error de referencia). Omitir deliberadamente la comunicación es gravísima (art. 34 quáter f).

Como buena práctica, mantén un registro que permita reconstruir:

- naturaleza de la vulneración;
- cronología y detección;
- sistemas/activos afectados;
- categorías de datos;
- número aproximado de titulares;
- efectos o consecuencias posibles;
- medidas de contención, solución y mitigación;
- medidas para prevenir recurrencia;
- decisión y fundamento sobre notificación.

### Paso 4: evaluar comunicación a titulares

Además de la comunicación a la Agencia, la ley exige comunicación a titulares —por sus representantes cuando corresponda— cuando la vulneración se refiere a:

- datos personales sensibles;
- datos de niños y niñas **menores de 14 años**;
- datos relativos a obligaciones económicas, financieras, bancarias o comerciales.

La comunicación debe ser clara y sencilla, identificar los datos afectados, posibles consecuencias y medidas de solución/resguardo. Debe dirigirse a cada titular afectado. Si no es posible, se hace mediante la difusión o publicación de un aviso en un medio de comunicación social masivo y de alcance nacional.

### Salida de incidente

Produce siempre:

1. hecho confirmado vs supuesto;
2. datos/titulares/sistemas afectados;
3. régimen temporal aplicable;
4. umbral de notificación y fundamento;
5. obligaciones ante la Agencia, los titulares, el CSIRT Nacional (Ley 21.663) y otros reguladores;
6. medidas inmediatas;
7. evidencia preservada;
8. causa raíz y acciones preventivas;
9. decisiones aún pendientes.

No expongas datos personales del incidente en el informe más allá de lo necesario.

## Protección de datos desde el diseño y por defecto — artículo 14 quáter

Integra privacidad en requisitos, no al final del proyecto. Antes de producción verifica:

- campos estrictamente necesarios;
- defaults restrictivos;
- finalidades explícitas;
- retención y purga/anonimización;
- segregación de datos y ambientes;
- accesibilidad limitada;
- canal de derechos y capacidad real de ejecutar supresión/rectificación/bloqueo/portabilidad;
- terceros y transferencias conocidos;
- telemetría/logs minimizados;
- evaluación de automatización/perfilamiento.

## Evaluación de impacto en protección de datos — artículo 15 ter

Realiza una DPIA **antes del inicio** cuando, por naturaleza, alcance, contexto, tecnología o fines, el tratamiento pueda producir un alto riesgo para derechos de los titulares.

La ley exige DPIA siempre en los siguientes casos (art. 15 ter inc. 2):

1. evaluación sistemática y exhaustiva basada en tratamiento o decisiones automatizadas/perfilamiento con efectos jurídicos significativos;
2. tratamiento masivo o a gran escala;
3. observación o monitoreo sistemático de una zona de acceso público;
4. tratamiento de datos sensibles y especialmente protegidos en las hipótesis de excepción del consentimiento.

La Agencia debe publicar una lista orientativa de operaciones que requieren o no DPIA y orientaciones mínimas. **Antes de usar esa lista, verifica su versión vigente; si no está verificada, marca `PENDIENTE DE VERIFICACIÓN REGULATORIA`.**

### Contenido mínimo operativo de una DPIA

La ley exige que las orientaciones consideren al menos:

- descripción de las operaciones;
- finalidad;
- necesidad y proporcionalidad;
- evaluación de riesgos;
- medidas de mitigación.

Para hacerla útil añade: titulares afectados, datos, escala, ciclo de vida, actores, sistemas/ubicaciones, transferencias, amenazas, controles existentes, riesgo inherente, riesgo residual, owner, plazo y evidencia de cierre.

Si el resultado sigue mostrando alto riesgo, la ley permite consultar a la Agencia para obtener recomendaciones. No presentes esa consulta como aprobación automática del tratamiento.

Incumplir la DPIA cuando corresponde es infracción **gravísima** (art. 34 quáter k). Si existe MPI, el delegado debe asesorar en la DPIA (DS 662 art. 13 h).

## Decisiones automatizadas y perfilamiento — artículo 8 bis

El titular tiene derecho a oponerse y a no ser objeto de decisiones basadas en tratamiento automatizado —incluido perfilamiento— que produzcan efectos jurídicos o le afecten significativamente, sujeto a las excepciones legales.

Las excepciones incluyen, bajo sus condiciones:

- necesidad para celebrar o ejecutar un contrato **entre el titular y el responsable**;
- consentimiento previo y expreso **en la forma del art. 12**;
- autorización legal con salvaguardas.

En todos los casos, incluso bajo esas excepciones, el responsable **debe por ley** adoptar medidas que aseguren (art. 8° bis inc. final):

- información y transparencia;
- explicación significativa;
- intervención humana;
- posibilidad de expresar el punto de vista;
- revisión de la decisión.

### Checklist para sistemas de IA

Antes de aprobar un uso con datos personales pregunta:

- ¿la IA toma o sólo recomienda una decisión?
- ¿hay efecto jurídico o impacto significativo?
- ¿qué datos y variables derivadas usa?
- ¿se generan perfiles, scores, embeddings o inferencias personales?
- ¿cuál es la base de licitud por finalidad?
- ¿hay datos sensibles, biométricos o de NNA?
- ¿el proveedor recibe datos como encargado o como responsable independiente?
- ¿dónde se procesan y transfieren los datos?
- ¿puede explicarse la lógica relevante sin revelar secretos innecesarios?
- ¿existe intervención humana real, con autoridad para cambiar el resultado?
- ¿hay mecanismo de revisión y trazabilidad?
- ¿se activa una DPIA por alto riesgo o por un supuesto obligatorio?

No uses “human in the loop” como etiqueta vacía: verifica tiempo, competencia, información disponible y autoridad real de la persona revisora.
