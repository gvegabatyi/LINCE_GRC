# Fuentes legales oficiales (fuente de verdad)

Documentos oficiales a partir de los cuales se genera `../corpus/*.json`, el texto por artículo que usan las citas, el buscador y el copiloto. Los textos legales oficiales no están protegidos por derecho de autor en Chile.

| Archivo | Norma | Origen y versión | SHA-256 |
|---|---|---|---|
| `LEY-19628_28-AGO-1999.pdf` | Ley N° 19.628 (texto vigente hasta el 30-11-2026) | LeyChile/BCN, última modificación Ley 21.504 (10-NOV-2022) | `3b0004082abf25a7527bedbd2ff04f040e89db3a01888ba432d0a8cafacaf8f0` |
| `Ley-21719_13-DIC-2024.pdf` | Ley N° 21.719 (vigencia diferida 01-12-2026) | LeyChile/BCN, generado 07-ABR-2026, última modificación Ley 21.806 (05-FEB-2026) | `c2fa5e836c3a9bd731accc92d790146fc785762997df9ae9191dbd6c38275be3` |
| `Ley-21663_08-ABR-2024.pdf` | Ley N° 21.663, Marco de Ciberseguridad | LeyChile/BCN, versión 01-MAR-2025 | `cc995e609f2d0675d8d71b07929f192767d5fcdc5fb43565eb75c32246b6b4a5` |
| `DS-662-Hacienda_13-JUN-2025.docx` | Decreto Supremo N° 662 (Hacienda), reglamento de MPI | 13-JUN-2025, tomado de razón 28-AGO-2026 | `27a648394f2e331cde1d8fa1dffdea639c64a63eeeb9633ca6fd51c2a0efdf5a` |

Los PDF de LeyChile incluyen un código de validación verificable en https://www.leychile.cl/validar.

## Actualizar una norma

1. Reemplazar el archivo por la nueva versión oficial y actualizar esta tabla (versión y SHA-256).
2. Regenerar el corpus, que requiere PyMuPDF sólo en desarrollo: `python addons/normativa/tools/build_corpus.py`.
3. Ejecutar las pruebas y volver a verificar la skill de dominio contra el texto nuevo.
