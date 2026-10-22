---
name: proteccion-datos-chile
description: Analiza, diseña, implementa o audita cumplimiento de protección de datos personales en Chile bajo la Ley 19.628, su reforma por Ley 21.719, el Decreto Supremo N° 662 (Modelos de Prevención de Infracciones) y su interacción con la Ley 21.663 (Marco de Ciberseguridad). Úsala para privacidad, datos personales, datos de salud, consentimiento, derechos de titulares, DPIA, incidentes, encargados, transferencias internacionales, biometría, niños y adolescentes, decisiones automatizadas, IA, modelo de prevención de infracciones (MPI), delegado de protección de datos, RAT, políticas, contratos, código, APIs, bases de datos o arquitectura, incluido el desarrollo de Lince GRC.
---

# Protección de Datos Chile

**Última verificación jurídica: 2026-10-21** — contrastada artículo por artículo contra el corpus oficial del proyecto (ver [Disciplina de fuentes](#disciplina-de-fuentes)).

Convierte la normativa chilena de protección de datos en decisiones, controles y evidencia verificable. No declares cumplimiento por la existencia de una política: exige evidencia de diseño y operación. La base legal de esta exigencia es la responsabilidad demostrable: el responsable "deberá ser capaz de acreditar la licitud" (Ley 21.719, art. 3 a) y "deberá acreditar la licitud del tratamiento" (art. 13 inc. final).

> Esta skill apoya análisis y cumplimiento. Para decisiones jurídicas de alto impacto, litigios, sanciones o interpretaciones dudosas, identifica la incertidumbre y solicita revisión profesional; no inventes una conclusión para cerrar el análisis.

## 0. Router temporal obligatorio

Antes de aplicar una obligación, fija la fecha relevante del tratamiento, incidente, contrato o auditoría.

- **Hasta 30-NOV-2026:** la Ley 19.628 vigente sigue siendo el régimen exigible. La Ley 21.719 y el DS 662 se usan como **readiness / transición**, no como si todas sus obligaciones ya fueran exigibles.
- **Desde 01-DIC-2026:** aplica la Ley 19.628 modificada por la Ley 21.719 y sus modificaciones vigentes, y el DS 662 para los modelos de prevención de infracciones.
- Si el caso cruza ambas fechas, separa el análisis en periodos.
- Si la consulta depende de normativa posterior a la última verificación, revisa primero fuentes oficiales. Lee [`references/marco-y-vigencia.md`](references/marco-y-vigencia.md).

## Flujo de trabajo

1. **Define alcance y rol.** Identifica responsable, tercero mandatario/encargado, cesionario, órgano público, proveedor extranjero y titulares afectados. Determina si hay alcance territorial chileno (art. 1° bis).
2. **Modela el tratamiento.** Recorre: **qué datos**, **por qué**, **dónde**, **quién accede/recibe**, **cuánto tiempo**, **cómo se protegen**. Añade origen, base de licitud, transferencias, automatización y categorías especiales. Si existe MPI, usa los 11 ítems de caracterización del DS 662 art. 3 d) como checklist.
3. **Aplica norma artículo-primero.** Para cada hallazgo: artículo/regla → aplicabilidad → excepción → evidencia → brecha → acción. Nunca empieces por un control extranjero y luego fuerces la ley chilena a encajar.
4. **Exige evidencia.** Distingue `obligación legal`, `control recomendado` y `evidencia observada`. Una afirmación sin evidencia queda como `NO VERIFICADO`.
5. **Prioriza riesgo.** Usa `CRÍTICO / ALTO / MEDIO / BAJO`, justificando impacto en titulares, sensibilidad, escala, automatización, exposición y sanción potencial; no calcules una multa cierta sin procedimiento y hechos suficientes.
6. **Remedia con dueño y prueba.** Cada acción debe indicar responsable, plazo, evidencia de cierre y prueba de efectividad.
7. **Verifica vigencia.** En asuntos regulatorios actuales, confirma LeyChile/BCN, Diario Oficial y, cuando corresponda, instrucciones de la Agencia antes de cerrar.

## Salidas soportadas

### Respuesta jurídica-operativa

Entrega, en este orden:

1. régimen temporal aplicable;
2. regla y artículo;
3. por qué aplica o no aplica;
4. excepciones/condiciones;
5. evidencia que falta revisar;
6. acción práctica;
7. incertidumbres o normas complementarias pendientes.

### Gap analysis / auditoría

Usa esta matriz mínima:

| Requisito | Artículo | Aplica | Estado | Evidencia | Riesgo | Brecha | Acción | Owner | Plazo |
|---|---|---|---|---|---|---|---|---|---|

Estados: `CUMPLE`, `PARCIAL`, `NO CUMPLE`, `NO APLICA`, `NO VERIFICADO`.

Para obligaciones y derechos, lee [`references/obligaciones-y-derechos.md`](references/obligaciones-y-derechos.md).

### Revisión de software, arquitectura o IA

No revises sólo la política de privacidad. Inspecciona al menos:

- puntos de recolección y campos;
- base de licitud por finalidad;
- minimización y retención;
- permisos, secretos, logs, backups y ambientes;
- APIs, exportaciones, analítica, trackers y terceros (incluidos proveedores de LLM);
- ubicación y transferencias internacionales;
- mecanismos para derechos del titular;
- perfilamiento y decisiones automatizadas;
- datos sensibles, de salud, biométricos y de niños, niñas o adolescentes;
- trazabilidad de incidentes y evidencia de controles.

Para seguridad, incidentes, DPIA, IA y Ley 21.663, lee [`references/seguridad-incidentes-dpia-ia.md`](references/seguridad-incidentes-dpia-ia.md).

### Terceros y gobernanza

Para contratos de encargados, cesiones, transferencias internacionales y sanciones, lee [`references/terceros-transferencias-sanciones.md`](references/terceros-transferencias-sanciones.md).

### Modelo de prevención de infracciones (MPI) y delegado

Para el programa de cumplimiento, delegado, certificación, Registro Nacional de Sanciones y Cumplimiento y supervisión, lee [`references/decreto-662-mpi.md`](references/decreto-662-mpi.md). **En este proyecto el detalle del DS 662 prevalece** sobre resúmenes secundarios.

### Integración con Lince GRC

Lince GRC es una plataforma integral de cumplimiento e implementación de protección de datos en Chile (Ley 19.628 modificada por la Ley 21.719, Ley 21.663 y DS 662). El MPI es uno de sus componentes, no su alcance. Para mapear requisitos a módulos de Lince, conocer la cobertura por ámbito legal y las reglas del copiloto normativo, lee [`references/lince-grc-integracion.md`](references/lince-grc-integracion.md).

## Guardrails Chile-específicos

- **Brechas (Ley 21.719):** no asumas un plazo general de **72 horas** por analogía con GDPR; el art. 14 sexies exige reportar a la Agencia por los medios más expeditos y **sin dilaciones indebidas** cuando exista riesgo razonable para los titulares. Si la vulneración afecta datos sensibles, de menores de 14 años u obligaciones económicas/financieras/bancarias/comerciales, comunica también a los titulares.
- **Brechas (Ley 21.663):** si la entidad es servicio esencial u operador de importancia vital (ojo: el art. 4 incluye expresamente la **producción y/o investigación de productos farmacéuticos**), **sí existen plazos horarios** ante el CSIRT Nacional para incidentes con efectos significativos (art. 27, que incluye los que afectan sistemas con datos personales): alerta temprana en 3 h, actualización en 72 h (24 h para operador de importancia vital con servicio esencial afectado) e informe final en 15 días corridos desde la alerta temprana (art. 9). Ambos deberes son independientes y acumulables (Ley 21.719 art. 14 sexies inc. final).
- **RoPA:** un **RoPA / inventario de tratamientos no es obligación legal universal de la Ley 21.719**. Pero si se adopta un MPI, la **caracterización del DS 662 art. 3 d) es obligatoria** y "podrá realizarse a través de un registro de actividades de tratamiento".
- **DPO:** el **delegado no es obligación universal**: la ley dice "podrá designar" (art. 50). Es **obligatorio para adoptar y certificar un MPI** (DS 662 art. 6). Aunque el MPI sea voluntario, **todo responsable debe adoptar acciones de prevención de infracciones** (art. 48).
- **Datos de salud:** salud y perfil biológico sólo para los fines de las leyes sanitarias (art. 16 bis); sin consentimiento, sólo en los casos taxativos de ese artículo. Crítico en contexto farmacéutico.
- **GDPR/ISO:** GDPR, ISO/IEC 27001, ISO/IEC 27701, NIST u otros marcos pueden mejorar controles o servir de crosswalk, pero no sustituyen el texto chileno ni crean por sí solos una obligación legal local.
- **Fuentes públicas:** bajo el nuevo régimen, que un dato provenga de una fuente de acceso público no lo deja fuera de la ley (art. 2 i).
- **Datos reales:** para ejemplos, pruebas y documentación, minimiza o anonimiza datos personales. No copies RUT, salud, biometría, credenciales u otros datos reales si no son imprescindibles.
- **Norma pendiente:** si la ley remite a reglamento, instrucción general, lista o criterio de la Agencia y no has verificado su versión vigente, marca `PENDIENTE DE VERIFICACIÓN REGULATORIA`.

## Disciplina de fuentes

Prioridad: (1) LeyChile/BCN y Diario Oficial; (2) Agencia de Protección de Datos Personales cuando sus actos sean vigentes; (3) regulador sectorial competente; (4) jurisprudencia/Contraloría según materia; (5) fuentes secundarias sólo como contexto.

**Corpus verificado del proyecto** (fuente de verdad para Lince GRC):

| Norma | Versión del texto |
|---|---|
| Ley 19.628 | LeyChile, última modificación Ley 21.504 (10-NOV-2022), fin de vigencia 30-NOV-2026 |
| Ley 21.719 | LeyChile, generado 07-ABR-2026, vigencia diferida 01-DIC-2026, última modificación Ley 21.806 (05-FEB-2026) |
| Ley 21.663 | LeyChile, versión 01-MAR-2025 |
| Decreto Supremo N° 662 (Hacienda) | Reglamento MPI, 13-JUN-2025, tomado de razón 28-AGO-2026 |

No cites de memoria un número de artículo, plazo o sanción cuando la precisión pueda cambiar el resultado. Reabre la fuente oficial y verifica.

## Mantenimiento

Skill de dominio del equipo de desarrollo de Lince GRC, verificada artículo por artículo contra el corpus oficial del proyecto. Licencia: ver `LICENSE`. Tras modificarla, sincronizar la copia del copiloto con `python addons/normativa/tools/sync_conocimiento.py`.
