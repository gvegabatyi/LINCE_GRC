# Integración con Lince GRC

Usa esta referencia al desarrollar, auditar o explicar Lince GRC. Traduce requisitos normativos a módulos, tablas y evidencias de la aplicación. No reemplaza el análisis jurídico: lo vuelve trazable dentro del software.

## Mapa requisito → módulo de Lince

| Requisito normativo | Fuente | Módulo / tabla Lince | Observación |
|---|---|---|---|
| Individualización del responsable y representante legal | DS 662 art. 3 a) | `modules/mpi_gobernanza.py` / `mpi_perfiles.representante_legal_*` | Cubierto |
| Designación del delegado por la máxima autoridad | DS 662 arts. 3 b), 8 | `mpi_delegados.autoridad_designacion`, `fecha_designacion`, `evidencia_designacion_id` | Cubierto |
| Delegado dependiente o externo; persona natural individualizada | DS 662 art. 7 | `mpi_delegados.tipo_vinculo`, `persona_juridica_prestadora` | Cubierto |
| Autonomía e idoneidad demostrables | DS 662 arts. 8, 10 | `mpi_delegados.declaracion_autonomia`, `declaracion_idoneidad` | Requiere evidencia, no sólo declaración |
| Medios y facultades del delegado | DS 662 arts. 3 c), 9 | `mpi_delegados.recursos_materiales_facultades` | Cubierto |
| Contacto público del delegado e informe a la Agencia | DS 662 arts. 11, 13 inc. final | `mpi_delegados.email_contacto_publico`, `canal_atencion_detalles` | Falta evidencia de publicación y de comunicación a la Agencia |
| Caracterización de tratamientos (11 ítems) | DS 662 art. 3 d) | `modules/tratamientos.py` / `tratamientos.rat_*` (RAT, Fase 2A) | Cubierto en el esquema; auditar la completitud de cada registro (ver abajo) |
| Matriz de riesgos graduada según sanciones | DS 662 art. 3 e) | `modules/evaluaciones.py` | Verificar que la matriz mapee a los arts. 34 bis, 34 ter y 34 quáter |
| Protocolos proporcionales | DS 662 art. 3 f) | `modules/evidencias.py` | Evidencia documental |
| Reporte interno, reporte a la Agencia/titulares, autodenuncia | DS 662 art. 3 g) | — | No modelado |
| Sanciones internas y procedimiento | DS 662 art. 3 h) | — | No modelado |
| Canal de denuncia con reserva de identidad y sin represalias | DS 662 art. 3 i) | — | No modelado |
| Incorporación a contratos y reglamento interno | DS 662 art. 4 | `modules/evidencias.py` | Evidencia documental |
| Certificación, vigencia de 3 años, registro | DS 662 arts. 15–17 | `mpi_perfiles.estado_certificacion_oficial`, `fecha_certificacion`, `fecha_vencimiento_certificacion`, `nro_registro_agencia` | Cubierto. Alertar 90 días antes del vencimiento |
| Certifica **sólo la Agencia** | DS 662 arts. 14–15; Ley art. 51 | `mpi_perfiles.entidad_certificadora`; etiqueta "Entidad Certificadora Acreditada (Art. 15)" en `modules/mpi_gobernanza.py` | **Inconsistencia:** no existen certificadoras privadas; la Agencia sólo puede contratar a terceros para revisar antecedentes. Ajustar la etiqueta o el uso del campo |
| Autonomía del delegado | DS 662 art. 8 | `mpi_delegados.declaracion_autonomia` (`BOOLEAN DEFAULT TRUE`) | El valor por defecto presume la autonomía: exige evidencia |
| Plan anual del delegado y rendición de cuenta | DS 662 art. 13 i) | — | No modelado |
| Visitas y auditorías internas | Ley 21.719 art. 48; DS 662 art. 13 d) (el delegado supervisa) | `modules/visitas.py` | Evidencia de supervisión interna. La supervisión **de la Agencia** sobre modelos certificados es otra cosa (DS 662 art. 19) |
| Catálogo normativo | — | `normativa_fuentes`, `normativa_referencias` (caché TTL 3600 s) | Las citas deben provenir del corpus verificado |

### RAT ↔ DS 662 art. 3 d)

Cada ítem del art. 3 d) tiene su columna en la tabla `tratamientos` (añadidas en `db/migrations.py`, PASO 5):

| Ítem | Columna |
|---|---|
| i | `rat_tipo_datos_sensibles` |
| ii | `rat_ambito_territorial` |
| iii | `rat_bases_datos_administradas` |
| iv | `rat_categorias_titulares` |
| v | `rat_finalidades` |
| vi | `rat_fuente_datos_acceso_publico` |
| vii | `rat_base_licitud_interes_legitimo` |
| viii | `rat_destinatarios_cesiones` |
| ix | `rat_transferencias_internacionales_art27` |
| x | `rat_plazo_condicion_supresion` |
| xi | `rat_decisiones_automatizadas_perfilamiento` |

En auditoría, verifica la **completitud y calidad** de cada registro, no sólo que la columna exista. Un campo vacío en un ítem aplicable queda `PARCIAL`. En el ítem vii, si la base es interés legítimo, debe identificarse ese interés. En el ítem xi, si hay decisiones automatizadas, debe describirse la lógica y las consecuencias.

## Reglas para el addon de citas normativas

1. Toda cita muestra la **norma + artículo + letra/inciso** y el texto literal recuperado del corpus verificado.
2. Si no se recupera el artículo, se muestra "Sin respaldo en corpus". Nunca se genera un texto legal.
3. Antes de mostrar una obligación de la Ley 21.719 o del DS 662, se aplica el router temporal (exigible desde el 01-DIC-2026).
4. El corpus es de sólo lectura y está versionado. Cambiar una versión de norma requiere volver a verificar esta skill.

## Reglas para el copiloto LLM (opcional)

El copiloto responde consultas en lenguaje natural sobre la normativa. Es un tratamiento con posible proveedor extranjero, así que esta skill se aplica a sí misma:

- **Segregación de datos:** el copiloto **sólo** accede al corpus normativo y a esta skill. **Nunca** lee tablas de Lince (empresas, tratamientos, delegados, evidencias, visitas) ni se le pasa contexto de empresa. Debe implementarse como un servicio sin conexión a `DATABASE_URL`.
- **Entrada del usuario:** advierte que no se ingresen datos personales. Aplica un filtro previo que detecte RUT, correos y teléfonos, y que bloquee o enmascare antes de enviar.
- **Proveedor externo:** si la pregunta sale a una API extranjera, es comunicación a un tercero y posible transferencia internacional (arts. 15 bis, 27 y 28). Por eso hay que cumplir tres condiciones: la segregación anterior, un contrato o términos que excluyan el entrenamiento con los datos y una retención mínima. Para despliegues in-house existe la alternativa de un modelo local.
- **Respuestas:** debe citar los artículos recuperados, aplicar el router temporal, distinguir la obligación legal de la recomendación y terminar con la advertencia de revisión profesional en temas de alto impacto.
- **Registro:** no guardes las preguntas con identificación del usuario salvo que exista una finalidad y una base definidas.
- **Activación:** el copiloto está desactivado por defecto y se habilita por configuración. La credencial de la API va por variable de entorno y nunca en el código ni en la base de datos.
