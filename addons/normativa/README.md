# Addon normativo — Lince GRC

Lince GRC es una plataforma integral de cumplimiento e implementación de protección de datos
personales en Chile: Ley 19.628 modificada por la Ley 21.719, Ley 21.663 (Marco de Ciberseguridad)
y Decreto Supremo N° 662 (modelos de prevención de infracciones). Este addon le da a todos sus
módulos un respaldo normativo común: citas literales verificadas de esas cuatro normas y un copiloto
opcional en lenguaje natural, **segregado de los datos capturados por Lince**.

Menú: **§ Normativa** (pestañas *Consultar artículo*, *Buscar*, *Copiloto*).

## Contenido

| Ruta | Función |
|---|---|
| `corpus/*.json` | Textos oficiales separados por artículo: Ley 19.628, Ley 21.719, Ley 21.663 y DS 662 |
| `citas.py` | Artículo literal por norma y número, búsqueda BM25, referencias explícitas y router temporal |
| `copiloto.py` | Copiloto opcional (Anthropic o modelo local con Ollama) |
| `pii_filter.py` | Bloquea las consultas con RUT, correos o teléfonos antes de enviarlas al proveedor |
| `ui.py` | Página Streamlit |
| `conocimiento/` | Copia sincronizada de la skill de dominio `proteccion-datos-chile` (licencia en `conocimiento/LICENSE`) |
| `tools/build_corpus.py` | Regenera el corpus desde los PDF y el DOCX oficiales (sólo en desarrollo) |
| `tools/sync_conocimiento.py` | Sincroniza `conocimiento/` con `.claude/skills/proteccion-datos-chile` |

Las citas no requieren dependencias adicionales ni base de datos.

## Copiloto (opcional, desactivado por defecto)

| Variable | Valores |
|---|---|
| `LINCE_COPILOTO_PROVEEDOR` | `desactivado` (por defecto), `anthropic` u `ollama` |
| `LINCE_COPILOTO_MODELO` | Por defecto `claude-opus-5-5` (anthropic) o `llama3.1` (ollama) |
| `ANTHROPIC_API_KEY` | Credencial de la API de Anthropic (sólo para `anthropic`) |
| `OLLAMA_URL` | Por defecto `http://localhost:11434` (sólo para `ollama`) |

- **anthropic:** `pip install -r addons/normativa/requirements-copiloto.txt`. Envía al modelo las reglas, la base de conocimiento (cacheada) y los artículos recuperados. Tiene activado el respaldo automático del lado del servidor (`fallbacks: "default"`): si el modelo rechaza una consulta por sus filtros de seguridad, la API la reintenta con otro modelo en la misma llamada.
- **ollama:** modelo local, sin dependencias adicionales. Ningún dato sale del servidor. Por su contexto acotado, sólo recibe las reglas y los artículos recuperados.

Las suscripciones de chat de consumo no habilitan el uso programático: se necesita una clave de API o un modelo local.

### Segregación de datos (regla de diseño)

1. El addon **no importa** `db/`, `psycopg2`, `modules/` ni `services/`. Lo verifica `tests/test_addon_normativa.py`.
2. El copiloto sólo recibe la pregunta del usuario, el historial de la conversación del copiloto y el corpus. Nunca recibe empresa activa, tratamientos, delegados ni evidencias.
3. Las preguntas con identificadores personales se bloquean y no se envían.
4. Las preguntas no se registran.
5. Con `anthropic` la consulta sale a un proveedor extranjero: por eso se aplican la segregación y el filtro anteriores, en línea con los arts. 15 bis, 27 y 28 de la Ley 21.719. Si se requiere que nada salga del servidor, usa `ollama`.

## Mantenimiento

```bash
# Tras actualizar los textos oficiales
python addons/normativa/tools/build_corpus.py --leyes "<carpeta PDF LeyChile>" --decreto "<DOCX DS 662>"
# Tras modificar la skill
python addons/normativa/tools/sync_conocimiento.py
# Pruebas (sin BD, red ni anthropic)
python -m unittest discover -s tests -t .
```

Cambiar el corpus exige volver a verificar la skill contra las nuevas versiones.
