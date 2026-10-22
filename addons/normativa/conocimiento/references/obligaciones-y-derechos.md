# Obligaciones, licitud y derechos — Ley 21.719

Usa esta referencia para el régimen que comienza el **01-DIC-2026**. Para hechos anteriores, vuelve a `marco-y-vigencia.md`.

## Principios — artículo 3

Convierte cada principio en una pregunta de evidencia:

| Principio | Pregunta de auditoría | Evidencia útil |
|---|---|---|
| licitud y lealtad | ¿puede acreditarse por qué cada tratamiento es lícito? | matriz finalidad/base de licitud, contratos, consentimiento |
| finalidad | ¿la finalidad es específica, explícita y lícita? | aviso, especificación funcional, registro de cambios |
| proporcionalidad | ¿se recolecta sólo lo necesario y se conserva sólo el tiempo necesario, para luego suprimir o anonimizar? (un plazo mayor exige ley o consentimiento) | esquema de datos, retención, purgas, anonimización |
| calidad | ¿los datos son exactos, completos, actuales y pertinentes? | validaciones, rectificación, reconciliación |
| responsabilidad | ¿quienes tratan datos responden del cumplimiento de principios y deberes (art. 3 e)? La capacidad de **acreditar** la licitud viene del art. 3 a) y del art. 13 inc. final | controles, owners, evidencias, revisiones |
| seguridad | ¿el nivel de protección corresponde al riesgo? | IAM, cifrado, backups, pruebas, incidentes |
| transparencia e información | ¿el titular entiende qué ocurre y puede ejercer derechos? | política, avisos, canales, trazabilidad |
| confidencialidad | ¿acceso y uso están limitados y sujetos a secreto, incluso después de terminada la relación con el titular? | NDA/cláusulas, RBAC, logs, formación |

**Compatibilidad de fines (art. 3 b):** un tratamiento para un fin distinto del original sólo procede si es compatible, existe una relación contractual o precontractual entre el titular y el responsable y el tratamiento se enmarca en los fines del contrato o es coherente con las tratativas, hay un nuevo consentimiento o lo dispone la ley.

## Consentimiento — artículo 12

Cuando sea la base de licitud, verifica que el consentimiento sea:

- libre;
- informado;
- específico respecto de su finalidad o finalidades;
- previo;
- inequívoco, mediante declaración o acción afirmativa clara.

Puede revocarse **en cualquier momento y sin expresión de causa**, sin efecto retroactivo, por medios similares o equivalentes a los usados para otorgarlo. Esos medios deben ser expeditos, fidedignos, gratuitos y permanentemente disponibles. El responsable debe poder probar que contó con consentimiento y que el tratamiento fue lícito, leal y transparente. El mandatario sólo puede consentir si tiene una facultad expresa para hacerlo.

**Anti-pattern:** no fuerces el consentimiento dentro de un contrato o servicio cuando el tratamiento no es necesario para esa prestación. La ley **presume** que ese consentimiento no fue libre, salvo que el consentimiento sea la única contraprestación del servicio (art. 12).

## Otras bases de licitud — artículo 13

No preguntes siempre “¿hay consentimiento?”. Evalúa la base correcta por finalidad. La ley contempla, entre otros supuestos:

- tratamiento de obligaciones económicas, financieras, bancarias o comerciales, o de la situación socioeconómica, sujeto al Título III;
- obligación legal o disposición de la ley;
- celebración o ejecución de un contrato, o medidas precontractuales solicitadas por el titular;
- interés legítimo del responsable o de un tercero, **siempre que no se afecten los derechos y libertades del titular** (art. 13 d). La ley no usa la ponderación del RGPD. El titular puede exigir siempre que se le informe del tratamiento y del interés legítimo invocado;
- formulación, ejercicio o defensa de derechos ante tribunales u órganos públicos.

El responsable debe **acreditar la licitud**. En un gap analysis, una base escrita sin justificación ni evidencia queda `NO VERIFICADO`.

## Derechos — artículos 4 a 10

El titular dispone, según condiciones legales, de:

- acceso (art. 5): datos y su origen, finalidades, destinatarios (o su identidad, si la pide), período de conservación, interés legítimo invocado y lógica de las decisiones automatizadas;
- rectificación (art. 6), que debe comunicarse a quienes se hayan comunicado o cedido los datos, salvo que sea imposible o exija un esfuerzo desproporcionado;
- supresión (art. 7), con causales y excepciones legales;
- oposición (art. 8), con supuestos especiales para marketing directo y fuentes públicas;
- oposición a decisiones automatizadas y perfilamiento (art. 8° bis, ver `seguridad-incidentes-dpia-ia.md`);
- bloqueo temporal del tratamiento (art. 8° ter), que también puede pedirse en lugar de la supresión;
- portabilidad (art. 9).

Los derechos son personales, intransferibles e irrenunciables, y no pueden limitarse por ningún acto o convención. Los herederos pueden ejercerlos respecto del titular fallecido en los términos legales. La portabilidad exige revisar los requisitos específicos del artículo 9 y no implica la supresión, salvo que el titular la pida conjuntamente.

**Gratuidad (art. 10):** rectificación, supresión y oposición son siempre gratuitas. El acceso es gratuito al menos una vez por trimestre; sólo pueden cobrarse costos directos si el acceso o la portabilidad se piden más de una vez en el trimestre. Las herramientas deben ser expeditas, ágiles y eficaces.

## Procedimiento y plazos — artículo 11

### Solicitud ordinaria

El canal puede ser correo electrónico, formulario de contacto o medio electrónico equivalente. Debe existir autenticación conforme al marco que establezca la Agencia.

**Plazo del responsable:** debe acusar recibo y pronunciarse **a más tardar dentro de 30 días corridos** desde el ingreso. El plazo puede ser **prorrogado una sola vez hasta por otros 30 días corridos**.

La ley exige conservar respaldo de la remisión, su fecha y el contenido íntegro de la respuesta, además de fundar la denegación. Como buena práctica, conserva también:

- recepción;
- identidad o autenticación aplicada;
- destinatario.

Si se deniega total o parcialmente, la respuesta debe ser fundada e informar que el titular tiene **30 días hábiles** para reclamar ante la Agencia (art. 41). Si no hay respuesta dentro del plazo, el titular puede reclamar directamente en los mismos términos.

### Bloqueo temporal asociado a rectificación, supresión u oposición

Cuando se solicita fundadamente bloqueo temporal, el responsable debe responder **dentro de 2 días hábiles** desde la recepción. Mientras resuelve esa solicitud, no debe tratar los datos comprendidos en el requerimiento; el bloqueo no impide su almacenamiento. Si rechaza el bloqueo, debe fundar el rechazo y comunicarlo electrónicamente a la Agencia, y el titular puede reclamar (art. 41).

**No mezcles** este plazo especial de 2 días hábiles con el plazo ordinario de 30 días corridos.

## Transparencia — artículo 14 ter

El responsable debe mantener permanentemente disponible, en web o medio equivalente, información que permita entender y ejercer derechos. El inventario de transparencia debe cubrir, como mínimo legalmente pertinente:

- política de tratamiento, fecha y versión;
- identidad del responsable y representante legal;
- identificación del encargado de prevención si existe;
- domicilio/correo/formulario u otro canal accesible para solicitudes;
- categorías de datos y universo de titulares;
- destinatarios previstos;
- finalidades y bases de legitimidad, incluidos intereses legítimos cuando corresponda;
- política y medidas de seguridad adoptadas (art. 14 ter e). *Recomendación interpretativa, no textual:* descríbelas sin revelar detalles que creen vulnerabilidades;
- derechos del titular y posibilidad de recurrir a la Agencia;
- transferencias internacionales, adecuación o garantías cuando proceda;
- periodo de conservación;
- origen de los datos y si provienen de fuentes de acceso público;
- posibilidad de retirar consentimiento cuando ésa sea la base;
- existencia de decisiones automatizadas/perfilamiento y la información exigible sobre su lógica y consecuencias.

No publiques secretos de seguridad para “cumplir transparencia”. Describe controles al nivel necesario sin crear una vulnerabilidad.

## Privacidad desde el diseño y por defecto — artículo 14 quáter

Antes y durante el tratamiento, exige medidas técnicas y organizativas considerando estado de la técnica, costos, naturaleza, ámbito, contexto, finalidades y riesgo. Por defecto deben tratarse sólo los datos específicos y estrictamente necesarios, considerando cantidad, extensión, retención y accesibilidad.

En software, esto se traduce en requisitos verificables: campos mínimos, defaults restrictivos, retención explícita, permisos mínimos y diseño de derechos antes de producción.

## Categorías especiales

### Datos sensibles

No trates "dato sensible" como sinónimo informal de "dato confidencial". Usa la definición legal (art. 2° g) y las reglas especiales aplicables. Requieren análisis reforzado, entre otros: salud, perfil biológico, biometría, origen étnico o racial, afiliación política, sindical o gremial, situación socioeconómica, convicciones ideológicas o filosóficas, creencias religiosas, y vida sexual, orientación sexual e identidad de género.

### Regla general para datos sensibles — artículo 16

Sólo pueden tratarse con **consentimiento expreso** del titular, otorgado por escrito, verbalmente o por un medio tecnológico equivalente. Sin consentimiento, sólo en estos casos:

- a) datos que el titular hizo manifiestamente públicos, si el tratamiento se relaciona con los fines de esa publicación;
- b) interés legítimo de una persona jurídica sin fines de lucro con finalidad política, filosófica, religiosa, cultural, sindical o gremial, respecto de sus miembros, con garantías y sin cesión;
- c) cuando es indispensable para salvaguardar la vida, salud o integridad del titular o de otro, o cuando el titular está impedido de consentir (después hay que informarle);
- d) formulación, ejercicio o defensa de derechos ante tribunales u órganos administrativos;
- e) ejercicio de derechos y obligaciones en el ámbito laboral o de seguridad social, en el marco de la ley;
- f) cuando la ley lo autorice o mande expresamente.

### Salud y perfil biológico — artículo 16 bis

**Crítico en contexto farmacéutico (Serviphar).**

- Los datos de salud y de perfil biológico (genéticos, proteómicos, metabólicos) sólo pueden tratarse **para los fines previstos por las leyes especiales en materia sanitaria**, aunque exista consentimiento.
- Sin consentimiento, sólo en estos casos:
  - a) vida o integridad, o titular impedido de consentir;
  - b) alerta sanitaria legalmente decretada;
  - c) fines históricos, estadísticos o científicos, estudios de interés público o en beneficio de la salud humana, o **desarrollo de productos o insumos médicos que no podrían desarrollarse de otra manera**. Los resultados publicados deben anonimizarse antes;
  - d) defensa de derechos;
  - e) medicina preventiva o laboral, evaluación de capacidad laboral, diagnóstico, asistencia sanitaria o social, o gestión de esos servicios;
  - f) cuando la ley lo permita e indique expresamente la finalidad.
- **Prohibición:** no pueden tratarse ni cederse datos de salud o de perfil biológico, ni muestras biológicas (incluido su almacenamiento), recolectados en el ámbito laboral, educativo, deportivo, social, de seguros, de seguridad o de identificación. La excepción exige dos condiciones acumulativas: que la ley lo autorice expresamente en casos calificados **y** que el caso sea alguno de los de este artículo.

### Biometría — artículo 16 ter

Los datos biométricos son sensibles. Sólo pueden tratarse con consentimiento expreso (art. 16 inc. 1); sin consentimiento, sólo en los casos del inc. 2° del art. 16 bis. Además, el responsable debe informar sobre:

- sistema biométrico utilizado;
- finalidad específica;
- periodo de utilización;
- forma de ejercer derechos.

No almacenes plantillas o imágenes biométricas “por si acaso”. La minimización y la necesidad deben poder demostrarse.

### Niños, niñas y adolescentes — artículo 16 quáter

- Todo tratamiento debe atender al interés superior y autonomía progresiva.
- Para **niños y niñas menores de 14 años**, el consentimiento corresponde a padres, representantes legales o quien tenga su cuidado personal, salvo autorización o mandato legal.
- Los datos de adolescentes se rigen en general por las reglas de autorización de adultos.
- Para **datos sensibles de adolescentes menores de 16 años**, se requiere el consentimiento de padres, representantes legales o quien tenga el cuidado personal, salvo autorización o mandato legal.
- A efectos de esta ley, adolescente es la persona mayor de 14 y menor de 18 años.

Los establecimientos educacionales y quienes traten datos de NNA tienen un deber especial de resguardo (art. 16 quáter, inciso final).

En productos digitales, verifica edad, experiencia de consentimiento, lenguaje, perfilamiento, publicidad, defaults, compartición con terceros y seguridad. No inventes métodos de verificación de edad si la Agencia o norma sectorial debe definirlos.
