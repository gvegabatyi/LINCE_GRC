# Marco jurídico y vigencia

**Última verificación jurídica: 2026-10-21** (corpus oficial del proyecto, ver `SKILL.md`).

## Regla temporal

| Fecha relevante | Régimen que debe tratarse como exigible | Uso de Ley 21.719 / DS 662 |
|---|---|---|
| hasta 30-NOV-2026 | Ley 19.628, versión vigente (fin de vigencia 30-NOV-2026) | preparación, gap analysis y migración |
| desde 01-DIC-2026 | Ley 19.628 modificada por Ley 21.719 y modificaciones vigentes; DS 662 para MPI | régimen aplicable |

La Ley 21.719 fue publicada el 13-DIC-2024. Su vigencia es diferida "el día primero del mes vigésimo cuarto posterior a la publicación" (art. primero transitorio), es decir, el 01-DIC-2026. La versión oficial revisada incorpora las modificaciones de la Ley 21.755 (D.O. 11-JUL-2025, art. segundo transitorio) y de la Ley 21.806 (D.O. 05-FEB-2026). No conviertas la preparación para diciembre de 2026 en una afirmación falsa de exigibilidad actual.

## Fuentes oficiales de referencia

1. Biblioteca del Congreso Nacional / LeyChile: Ley 19.628.
2. Biblioteca del Congreso Nacional / LeyChile: Ley 21.719 y su texto diferido o consolidado.
3. Decreto Supremo N° 662 de Hacienda, reglamento de los Modelos de Prevención de Infracciones (art. 49). Ver `decreto-662-mpi.md`.
4. Ley 21.663, Marco de Ciberseguridad, para incidentes de servicios esenciales y operadores de importancia vital.
5. Diario Oficial, para modificaciones, reglamentos y actos publicados.
6. Agencia de Protección de Datos Personales, cuando sus instrucciones, resoluciones, listas y criterios estén vigentes.
7. Reguladores sectoriales, cuando exista una obligación adicional aplicable.

Antes de responder sobre el estado jurídico **actual**, verifica si hubo modificaciones posteriores a la última verificación. Si la Agencia dicta una instrucción general, lista o criterio que la ley le encarga, aplícala en ese punto dentro de los límites legales. **Nunca prevalece sobre la ley ni sobre el reglamento.** Las instrucciones o normas generales dictadas antes de la entrada en vigencia sólo obligan desde el 01-DIC-2026 (art. cuarto transitorio).

## Ley 19.628 vigente hasta 30-NOV-2026: baseline mínimo

Cuando el hecho analizado ocurre antes de la entrada en vigencia de la reforma, revisa al menos:

- **Art. 4:** el tratamiento requiere autorización legal o consentimiento expreso. El consentimiento debe ser informado y constar por escrito, salvo las excepciones legales. Ojo: el inc. 5° exime de autorización a ciertos datos de fuentes accesibles al público, excepción que **desaparece** con el nuevo art. 2 i).
- **Arts. 6 y 9:** eliminación, modificación o bloqueo según proceda; finalidad y exactitud de los datos.
- **Art. 7:** deber de secreto de quienes trabajan en el tratamiento de datos no provenientes de fuentes accesibles al público.
- **Arts. 10 y 11:** reglas de datos sensibles y deber de diligencia del responsable.
- **Arts. 12 a 16:** derechos del titular y amparo ante el juez civil (art. 16).

No evalúes un incidente de noviembre de 2026 aplicando retroactivamente el régimen sancionatorio de diciembre. Las disposiciones transitorias no regulan infracciones anteriores, y se aplica el principio de irretroactividad en materia sancionatoria (Constitución, art. 19 N° 3, fuera del corpus del proyecto).

## Ley 21.719 / nueva Ley 19.628 desde 01-DIC-2026

La reforma cambia el enfoque hacia la responsabilidad demostrable, los derechos ampliados y una autoridad especializada. El análisis base debe incluir:

- principios del art. 3;
- derechos de los arts. 4 a 11 (incluye 8° bis, decisiones automatizadas, y 8° ter, bloqueo);
- licitud y consentimiento de los arts. 12 y 13;
- obligaciones del responsable de los arts. 14 a 14 septies;
- cesión, encargados y evaluación de impacto de los arts. 15 a 15 ter;
- categorías especiales de los arts. 16 a 16 sexies:
  - sensibles (16);
  - salud y perfil biológico (16 bis);
  - biométricos (16 ter);
  - niños, niñas y adolescentes (16 quáter);
  - fines históricos, estadísticos o científicos (16 quinquies);
  - geolocalización (16 sexies);
- transferencias internacionales de los arts. 27 y 28;
- fiscalización (art. 29), infracciones (arts. 34 a 34 quáter), sanciones (arts. 35 a 40), responsabilidad civil (art. 47) y prevención de infracciones (arts. 48 a 53, más el DS 662).

## Disposiciones transitorias relevantes (Ley 21.719)

| Art. transitorio | Regla |
|---|---|
| primero | Vigencia el 01-DIC-2026 |
| segundo | Los reglamentos se dictan dentro de 6 meses desde la publicación. El reglamento del art. 26 se dicta dentro de 6 meses desde la vigencia (modificado por la Ley 21.755) |
| tercero | El Registro Civil elimina el registro de bancos de datos del actual art. 22 dentro de los 60 días anteriores a la vigencia |
| cuarto | Las instrucciones o normas generales de la Agencia dictadas antes de la vigencia sólo obligan desde el 01-DIC-2026 |
| quinto | Los órganos públicos que designen delegado deben elegir a un funcionario de la dotación vigente |
| sexto | Durante los primeros 12 meses de vigencia, la Agencia puede sancionar con amonestación escrita a las empresas de menor tamaño (Ley 20.416), con deber de registro |

## Alcance territorial desde 01-DIC-2026

El art. 1° bis alcanza, entre otros, los tratamientos en que:

- el responsable o el mandatario/encargado está establecido o constituido en Chile;
- un mandatario/encargado, esté donde esté, trata datos por cuenta de un responsable establecido en Chile;
- un responsable o mandatario extranjero ofrece bienes o servicios a titulares que están en Chile; o
- se monitorea el comportamiento de titulares en Chile, incluido el análisis, rastreo, perfilamiento o predicción.

También quedan sujetos quienes lo están "a causa de un contrato o del derecho internacional" (inciso final).

Por eso, tener la infraestructura o el proveedor fuera de Chile no elimina por sí solo la aplicabilidad.

## Regla de separación temporal en auditorías

Si una organización se prepara antes del 01-DIC-2026, clasifica cada hallazgo en una de estas categorías:

- `VIGENTE-19628`: incumplimiento o riesgo bajo la ley actualmente exigible.
- `READINESS-21719`: brecha que debe cerrarse para la entrada en vigencia.
- `DOBLE`: exigencia relevante hoy y además reforzada por el nuevo régimen.
- `PENDIENTE-REGULATORIO`: la ley remite a un reglamento, instrucción, lista, modelo o criterio que debe verificarse.

Esto evita confundir la urgencia de preparación con la vigencia jurídica.
