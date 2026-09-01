"""
Migraciones de base de datos — Fase 1.

Orden de ejecución (crítico para dependencias FK):
  a) Validar existencia de tablas requeridas (empresas, tratamientos, visitas, evidencias)
  b) CREATE TABLE IF NOT EXISTS evaluaciones
  c) ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS evaluacion_id (nullable)
  d) ALTER TABLE visitas ADD COLUMN IF NOT EXISTS evaluacion_id (nullable) y tipo_visita
  e) ALTER TABLE evidencias ADD COLUMN IF NOT EXISTS evaluacion_id (nullable)
  f) Migraciones legacy de columnas antiguas en tratamientos y visitas (idempotentes)

REGLAS ABSOLUTAS:
  - No DROP TABLE, TRUNCATE ni DELETE masivo.
  - No modificar tabla empresas (validar existencia y confiar en esquema actual).
  - Toda la migración corre en una sola transacción (commit al final, rollback en error).
  - No poblar evaluacion_id en registros existentes; quedan en NULL.
  - Los mensajes de error no exponen DATABASE_URL ni secretos.
"""

import streamlit as st
from db.connection import get_connection


# ==============================================================================
# HELPERS INTERNOS
# ==============================================================================

def _tabla_existe(cursor, table_name: str) -> bool:
    """Verifica si una tabla existe en el schema 'public'."""
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = %s
        )
        """,
        (table_name,),
    )
    return cursor.fetchone()[0]


def _columna_existe(cursor, table_name: str, column_name: str) -> bool:
    """Verifica si una columna existe en una tabla dada."""
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name   = %s
              AND column_name  = %s
        )
        """,
        (table_name, column_name),
    )
    return cursor.fetchone()[0]


# ==============================================================================
# MIGRACIÓN PRINCIPAL
# ==============================================================================

def init_db() -> None:
    """
    Inicializa y migra la base de datos de forma segura e idempotente.
    Corre dentro de una sola transacción: si algo falla, hace rollback completo.
    Llama a st.error() + st.stop() ante errores irrecuperables.
    """
    conn = None
    try:
        conn = get_connection()

        with conn.cursor() as c:

            # ──────────────────────────────────────────────────────────────────
            # PASO a: Validar que las tablas requeridas existen
            # ──────────────────────────────────────────────────────────────────
            tablas_requeridas = ["empresas", "tratamientos", "visitas", "evidencias"]
            for tabla in tablas_requeridas:
                if not _tabla_existe(c, tabla):
                    raise RuntimeError(
                        f"La tabla '{tabla}' no fue encontrada en la base de datos. "
                        "La base de datos no está inicializada correctamente. "
                        "Contacte al administrador del sistema."
                    )

            # ──────────────────────────────────────────────────────────────────
            # PASO b: CREATE TABLE IF NOT EXISTS evaluaciones
            # ──────────────────────────────────────────────────────────────────
            c.execute("""
                CREATE TABLE IF NOT EXISTS evaluaciones (
                    id                       SERIAL PRIMARY KEY,
                    empresa_id               INTEGER NOT NULL
                                             REFERENCES empresas(id) ON DELETE CASCADE,
                    nombre                   VARCHAR(255) NOT NULL,
                    tipo_evaluacion          VARCHAR(100),
                    periodo                  VARCHAR(100),
                    alcance                  TEXT,
                    objetivo                 TEXT,
                    marco_normativo          TEXT,
                    auditor_responsable      VARCHAR(255),
                    fecha_inicio             DATE DEFAULT CURRENT_DATE,
                    fecha_cierre_planificada DATE,
                    fecha_cierre_real        DATE,
                    estado                   VARCHAR(50) DEFAULT 'borrador',
                    porcentaje_avance        NUMERIC(5,2) DEFAULT 0,
                    puntaje_total            NUMERIC(10,2),
                    max_puntaje              NUMERIC(10,2),
                    observaciones            TEXT,
                    created_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # ──────────────────────────────────────────────────────────────────
            # PASO c: Migraciones legacy de tratamientos (idempotentes)
            #         Estas vienen de versiones anteriores de app.py y
            #         garantizan que la tabla tenga todas las columnas esperadas.
            # ──────────────────────────────────────────────────────────────────
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS nombre_tratamiento VARCHAR(255);")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS descripcion TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS base_legal VARCHAR(100);")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS datos_personales TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS responsables TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS encargados TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS transferencias TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")

            # Migrar datos desde columnas legacy (solo si existían en versiones anteriores)
            c.execute("""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='tratamientos' AND column_name='nombre'
                    ) THEN
                        UPDATE tratamientos
                        SET nombre_tratamiento = nombre
                        WHERE nombre_tratamiento IS NULL AND nombre IS NOT NULL;
                    END IF;

                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='tratamientos' AND column_name='finalidad'
                    ) THEN
                        UPDATE tratamientos
                        SET descripcion = finalidad
                        WHERE descripcion IS NULL AND finalidad IS NOT NULL;
                    END IF;

                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='tratamientos' AND column_name='base_licitud'
                    ) THEN
                        UPDATE tratamientos
                        SET base_legal = base_licitud
                        WHERE base_legal IS NULL AND base_licitud IS NOT NULL;
                    END IF;

                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='tratamientos' AND column_name='datos'
                    ) THEN
                        UPDATE tratamientos
                        SET datos_personales = datos
                        WHERE datos_personales IS NULL AND datos IS NOT NULL;
                    END IF;
                END $$;
            """)

            # Fase 1: columna evaluacion_id en tratamientos (nullable)
            c.execute("""
                ALTER TABLE tratamientos
                ADD COLUMN IF NOT EXISTS evaluacion_id INTEGER
                REFERENCES evaluaciones(id) ON DELETE SET NULL;
            """)

            # ──────────────────────────────────────────────────────────────────
            # PASO d: Migraciones legacy de visitas + nuevas columnas Fase 1
            # ──────────────────────────────────────────────────────────────────
            c.execute("ALTER TABLE visitas ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;")
            c.execute("ALTER TABLE visitas ADD COLUMN IF NOT EXISTS fecha_visita DATE DEFAULT CURRENT_DATE;")
            c.execute("ALTER TABLE visitas ADD COLUMN IF NOT EXISTS auditor VARCHAR(100);")
            c.execute("ALTER TABLE visitas ADD COLUMN IF NOT EXISTS checklist_seguridad JSONB;")
            c.execute("ALTER TABLE visitas ADD COLUMN IF NOT EXISTS puntaje INTEGER DEFAULT 0;")
            c.execute("ALTER TABLE visitas ADD COLUMN IF NOT EXISTS observaciones TEXT;")
            c.execute("ALTER TABLE visitas ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")

            # Migrar datos desde columnas legacy de visitas
            c.execute("""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='visitas' AND column_name='fecha'
                    ) THEN
                        UPDATE visitas
                        SET fecha_visita = fecha
                        WHERE fecha_visita IS NULL AND fecha IS NOT NULL;
                    END IF;

                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='visitas' AND column_name='hallazgos'
                    ) THEN
                        UPDATE visitas
                        SET observaciones = hallazgos
                        WHERE observaciones IS NULL AND hallazgos IS NOT NULL;
                    END IF;

                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='visitas' AND column_name='participantes'
                    ) THEN
                        UPDATE visitas
                        SET auditor = participantes
                        WHERE auditor IS NULL AND participantes IS NOT NULL;
                    END IF;

                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='visitas' AND column_name='empresa'
                    ) THEN
                        UPDATE visitas v
                        SET empresa_id = e.id
                        FROM empresas e
                        WHERE v.empresa_id IS NULL
                          AND (v.empresa = e.nombre OR v.empresa = e.rut);
                    END IF;
                END $$;
            """)

            # Fase 1: columnas nuevas en visitas (nullable)
            c.execute("""
                ALTER TABLE visitas
                ADD COLUMN IF NOT EXISTS evaluacion_id INTEGER
                REFERENCES evaluaciones(id) ON DELETE SET NULL;
            """)
            c.execute("ALTER TABLE visitas ADD COLUMN IF NOT EXISTS tipo_visita VARCHAR(80);")

            # ──────────────────────────────────────────────────────────────────
            # PASO e: Fase 1 — evaluacion_id en evidencias (nullable)
            # ──────────────────────────────────────────────────────────────────
            c.execute("""
                ALTER TABLE evidencias
                ADD COLUMN IF NOT EXISTS evaluacion_id INTEGER
                REFERENCES evaluaciones(id) ON DELETE SET NULL;
            """)

            # ──────────────────────────────────────────────────────────────────
            # PASO f: Verificación de estructura
            # (si llegamos aquí sin excepción, todo OK)
            # ──────────────────────────────────────────────────────────────────
            for tabla, col in [
                ("visitas", "evaluacion_id"),
                ("visitas", "tipo_visita"),
                ("tratamientos", "evaluacion_id"),
                ("evidencias", "evaluacion_id"),
            ]:
                if not _columna_existe(c, tabla, col):
                    raise RuntimeError(
                        f"La columna '{col}' no fue creada correctamente en '{tabla}'. "
                        "Revise los logs de migración."
                    )

        # Confirmar toda la transacción de migración
        conn.commit()

    except RuntimeError as exc:
        if conn:
            conn.rollback()
        st.error(f"⚠️ Error de inicialización de base de datos: {exc}")
        st.stop()

    except Exception as exc:
        if conn:
            conn.rollback()
        # No exponer detalles internos que puedan revelar credenciales
        st.error(
            f"⚠️ Error inesperado durante la migración de base de datos "
            f"({type(exc).__name__}). Contacte al administrador."
        )
        st.stop()

    finally:
        if conn:
            conn.close()
