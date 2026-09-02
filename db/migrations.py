"""
Migraciones de base de datos — Fase 1 y Fase 2A (Lince GRC).

Fase 2A (Decreto N° 662 del Ministerio de Hacienda):
  1. Tablas de trazabilidad normativa: normativa_fuentes y normativa_referencias.
  2. Tablas de gobernanza MPI: mpi_perfiles y mpi_delegados (con unicidad de activos).
  3. Ampliación de la tabla tratamientos con los 11 numerales taxativos del Art. 3 letra d).
  4. Carga inicial idempotente (seed) de las referencias del Decreto N° 662.

REGLAS ABSOLUTAS:
  - No DROP TABLE, DROP COLUMN, TRUNCATE ni DELETE masivo.
  - No modificar tabla empresas.
  - Toda la migración corre en una sola transacción atómica.
  - Preservación de datos históricos (columnas nuevas son nullable).
  - Los mensajes de error no exponen DATABASE_URL ni secretos.
"""

import streamlit as st
from db.connection import get_connection


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


def init_db() -> None:
    """
    Inicializa y migra la base de datos de forma segura e idempotente (Fase 1 y Fase 2A).
    Corre dentro de una sola transacción: si algo falla, hace rollback completo.
    """
    conn = None
    try:
        conn = get_connection()

        with conn.cursor() as c:

            # ==================================================================
            # PASO 1: Validar que las tablas base existen
            # ==================================================================
            tablas_requeridas = ["empresas", "tratamientos", "visitas", "evidencias"]
            for tabla in tablas_requeridas:
                if not _tabla_existe(c, tabla):
                    raise RuntimeError(
                        f"La tabla '{tabla}' no fue encontrada en la base de datos. "
                        "Contacte al administrador del sistema."
                    )

            # ==================================================================
            # PASO 2: Tabla evaluaciones (Fase 1)
            # ==================================================================
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

            # Columnas nullable de Fase 1
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS evaluacion_id INTEGER REFERENCES evaluaciones(id) ON DELETE SET NULL;")
            c.execute("ALTER TABLE visitas ADD COLUMN IF NOT EXISTS evaluacion_id INTEGER REFERENCES evaluaciones(id) ON DELETE SET NULL;")
            c.execute("ALTER TABLE visitas ADD COLUMN IF NOT EXISTS tipo_visita VARCHAR(80);")
            c.execute("ALTER TABLE evidencias ADD COLUMN IF NOT EXISTS evaluacion_id INTEGER REFERENCES evaluaciones(id) ON DELETE SET NULL;")

            # ==================================================================
            # PASO 3 (FASE 2A): Capa de Trazabilidad Normativa
            # ==================================================================
            c.execute("""
                CREATE TABLE IF NOT EXISTS normativa_fuentes (
                    id SERIAL PRIMARY KEY,
                    codigo VARCHAR(50) NOT NULL UNIQUE,
                    nombre VARCHAR(255) NOT NULL,
                    organismo VARCHAR(255),
                    fecha_publicacion DATE,
                    version VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS normativa_referencias (
                    id SERIAL PRIMARY KEY,
                    fuente_id INTEGER NOT NULL REFERENCES normativa_fuentes(id) ON DELETE CASCADE,
                    articulo VARCHAR(100) NOT NULL,
                    numeral_letra VARCHAR(50),
                    materia VARCHAR(255) NOT NULL,
                    descripcion_criterio TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Carga inicial (seed) de fuentes normativas del Decreto N° 662
            c.execute("""
                INSERT INTO normativa_fuentes (codigo, nombre, organismo, fecha_publicacion, version)
                VALUES (
                    'DEC-662-HAC',
                    'Decreto Supremo N° 662 (Reglamento Modelo Prevención Infracciones Art. 49 Ley 19.628)',
                    'Ministerio de Hacienda',
                    '2025-06-13',
                    'Oficial (Tomado de Razón 2026-08-28)'
                )
                ON CONFLICT (codigo) DO NOTHING;
            """)

            # Seed de referencias normativas clave del Decreto N° 662
            c.execute("""
                DO $$
                DECLARE
                    f_id INTEGER;
                BEGIN
                    SELECT id INTO f_id FROM normativa_fuentes WHERE codigo = 'DEC-662-HAC';
                    IF f_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM normativa_referencias WHERE fuente_id = f_id) THEN
                        INSERT INTO normativa_referencias (fuente_id, articulo, numeral_letra, materia, descripcion_criterio) VALUES
                        (f_id, 'Art. 3 letra a)', 'a', 'Individualización del responsable', 'Individualización completa del responsable y de su representante legal.'),
                        (f_id, 'Art. 3 letra b)', 'b', 'Designación del delegado', 'Designación de un delegado de protección de datos personales.'),
                        (f_id, 'Art. 3 letra c)', 'c', 'Medios y facultades del delegado', 'Definición precisa de medios materiales, tecnológicos y facultades asignadas al delegado.'),
                        (f_id, 'Art. 3 letra d)', 'd', 'Caracterización de datos y RAT (numerales i al xi)', 'Registro estructurado con los 11 numerales taxativos de actividades de tratamiento.'),
                        (f_id, 'Art. 3 letra e)', 'e', 'Actividades y matriz de riesgos', 'Identificación y priorización de procesos de tratamiento y riesgos de infracción.'),
                        (f_id, 'Art. 3 letra f)', 'f', 'Protocolos, reglas y procedimientos', 'Mecanismos y protocolos de control para prevenir infracciones.'),
                        (f_id, 'Art. 3 letra g)', 'g', 'Reporte interno y comunicaciones', 'Mecanismos de reporte interno y comunicaciones que correspondan.'),
                        (f_id, 'Art. 3 letra h)', 'h', 'Sanciones administrativas internas', 'Sistema de sanciones disciplinarias internas conforme a reglamentos.'),
                        (f_id, 'Art. 3 letra i)', 'i', 'Denuncia interna ante el delegado', 'Canal de denuncia interna con reserva de identidad y protección.'),
                        (f_id, 'Art. 3 letra j)', 'j', 'Disposiciones adicionales útiles', 'Mecanismos complementarios para la eficacia del modelo.'),
                        (f_id, 'Art. 6', '6', 'Obligatoriedad del Delegado', 'El delegado es obligatorio en el marco de adopción y certificación de un MPI.'),
                        (f_id, 'Art. 7', '7', 'Calidad del Delegado', 'El delegado puede ser trabajador dependiente o prestador de servicios externo.'),
                        (f_id, 'Art. 8', '8', 'Designación y Autonomía', 'Designado por máxima autoridad directiva; goza de autonomía respecto de la administración.'),
                        (f_id, 'Art. 9', '9', 'Medios y Facultades del Delegado', 'Recursos suficientes, independencia funcional y prevención de conflictos de interés.'),
                        (f_id, 'Art. 10', '10', 'Idoneidad del Delegado', 'Conocimientos especializados, experiencia, habilidades e idoneidad profesional.'),
                        (f_id, 'Art. 11', '11', 'Canal de Contacto del Delegado', 'Publicación y disponibilidad de datos de contacto para titulares y la Agencia.'),
                        (f_id, 'Art. 12', '12', 'Deber de Secreto y Confidencialidad', 'Obligación estricta de confidencialidad en el ejercicio de sus funciones.'),
                        (f_id, 'Art. 13', '13', 'Funciones del Delegado', 'Supervisión del cumplimiento, asesoría, capacitación y cooperación.'),
                        (f_id, 'Art. 13 letra i)', '13.i', 'Plan Anual y Rendición de Cuentas', 'Plan anual de trabajo y rendición de cuentas al menos anual.'),
                        (f_id, 'Art. 15', '15', 'Certificación Oficial y Vigencia', 'La Agencia certifica el modelo con vigencia de 3 años.'),
                        (f_id, 'Art. 17', '17', 'Registro Nacional de la Agencia', 'Inscripción de modelos certificados en el Registro Nacional de Sanciones y Cumplimiento.');
                    END IF;
                END $$;
            """)

            # ==================================================================
            # PASO 4 (FASE 2A): Tablas de Gobernanza MPI (Perfil y Delegado)
            # ==================================================================
            c.execute("""
                CREATE TABLE IF NOT EXISTS mpi_perfiles (
                    id                             SERIAL PRIMARY KEY,
                    empresa_id                     INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
                    evaluacion_id                  INTEGER REFERENCES evaluaciones(id) ON DELETE SET NULL,
                    representante_legal_nombre     VARCHAR(255) NOT NULL,
                    representante_legal_rut        VARCHAR(20) NOT NULL,
                    representante_legal_email      VARCHAR(255),
                    representante_legal_telefono   VARCHAR(50),
                    fecha_adopcion_modelo          DATE DEFAULT CURRENT_DATE,
                    version_modelo                 VARCHAR(50) DEFAULT '1.0',
                    alcance_organizacional         TEXT,
                    estado_implementacion          VARCHAR(50) DEFAULT 'preparacion',
                    estado_certificacion_oficial   VARCHAR(50) DEFAULT 'sin_solicitud',
                    entidad_certificadora          VARCHAR(255),
                    nro_certificado                VARCHAR(100),
                    fecha_certificacion            DATE,
                    fecha_vencimiento_certificacion DATE,
                    nro_registro_agencia           VARCHAR(100),
                    evidencia_aprobacion_id        INTEGER REFERENCES evidencias(id) ON DELETE SET NULL,
                    activo                         BOOLEAN DEFAULT TRUE,
                    created_at                     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at                     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Restricción: un solo perfil MPI activo por empresa
            c.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_mpi_perfil_activo
                ON mpi_perfiles (empresa_id)
                WHERE activo = TRUE;
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS mpi_delegados (
                    id                             SERIAL PRIMARY KEY,
                    empresa_id                     INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
                    nombre_completo                VARCHAR(255) NOT NULL,
                    rut_interno                    VARCHAR(20),
                    email_contacto_publico         VARCHAR(255) NOT NULL,
                    telefono_contacto              VARCHAR(50),
                    canal_atencion_detalles        TEXT,
                    tipo_vinculo                   VARCHAR(50) DEFAULT 'dependiente',
                    persona_juridica_prestadora    VARCHAR(255),
                    cargo_interno                  VARCHAR(255),
                    autoridad_designacion          VARCHAR(255) DEFAULT 'Directorio',
                    fecha_designacion              DATE NOT NULL DEFAULT CURRENT_DATE,
                    declaracion_autonomia          BOOLEAN DEFAULT TRUE,
                    declaracion_idoneidad          TEXT,
                    recursos_materiales_facultades TEXT,
                    evidencia_designacion_id       INTEGER REFERENCES evidencias(id) ON DELETE SET NULL,
                    activo                         BOOLEAN DEFAULT TRUE,
                    created_at                     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at                     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Restricción: un solo delegado activo por empresa
            c.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_mpi_delegado_activo
                ON mpi_delegados (empresa_id)
                WHERE activo = TRUE;
            """)

            # ==================================================================
            # PASO 5 (FASE 2A): Ampliación del RAT con los 11 Numerales Art. 3 d)
            # ==================================================================
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS rat_tipo_datos_sensibles TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS rat_ambito_territorial VARCHAR(255);")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS rat_bases_datos_administradas TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS rat_categorias_titulares TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS rat_finalidades TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS rat_fuente_datos_acceso_publico TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS rat_base_licitud_interes_legitimo TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS rat_destinatarios_cesiones TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS rat_transferencias_internacionales_art27 TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS rat_plazo_condicion_supresion TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS rat_decisiones_automatizadas_perfilamiento TEXT;")
            c.execute("ALTER TABLE tratamientos ADD COLUMN IF NOT EXISTS evidencia_id INTEGER REFERENCES evidencias(id) ON DELETE SET NULL;")

            # ==================================================================
            # PASO 6 (FASE 2A.2): Bandeja Documental de Importación RAT
            # Tablas idempotentes — no destructivas — sin alterar datos existentes
            # ==================================================================
            c.execute("""
                CREATE TABLE IF NOT EXISTS importaciones_documentales (
                    id                   SERIAL PRIMARY KEY,
                    empresa_id           INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
                    evaluacion_id        INTEGER REFERENCES evaluaciones(id) ON DELETE SET NULL,
                    nombre_archivo       VARCHAR(255) NOT NULL,
                    tipo_archivo         VARCHAR(20) NOT NULL,
                    mime_detectado       VARCHAR(100),
                    tamano_bytes         INTEGER NOT NULL,
                    hash_sha256          VARCHAR(64) NOT NULL,
                    estado               VARCHAR(50) NOT NULL DEFAULT 'recibido',
                    evidencia_id         INTEGER REFERENCES evidencias(id) ON DELETE SET NULL,
                    tiene_evidencia_url  BOOLEAN DEFAULT FALSE,
                    descripcion_origen   TEXT,
                    advertencias         TEXT,
                    resumen_extraccion   TEXT,
                    total_candidatos     INTEGER DEFAULT 0,
                    candidatos_creados   INTEGER DEFAULT 0,
                    candidatos_ignorados INTEGER DEFAULT 0,
                    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            c.execute("""
                CREATE INDEX IF NOT EXISTS idx_imp_doc_empresa
                ON importaciones_documentales (empresa_id);
            """)
            c.execute("""
                CREATE INDEX IF NOT EXISTS idx_imp_doc_hash
                ON importaciones_documentales (empresa_id, hash_sha256);
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS importacion_tratamientos_candidatos (
                    id                       SERIAL PRIMARY KEY,
                    importacion_id           INTEGER NOT NULL
                                             REFERENCES importaciones_documentales(id) ON DELETE CASCADE,
                    empresa_id               INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
                    nro_hoja                 VARCHAR(100),
                    nro_fila                 INTEGER,
                    nro_pagina               INTEGER,
                    seccion_origen           TEXT,
                    datos_extraidos_json     JSONB NOT NULL,
                    estado_revision          VARCHAR(50) NOT NULL DEFAULT 'pendiente',
                    accion_humana            VARCHAR(50),
                    tratamiento_existente_id INTEGER REFERENCES tratamientos(id) ON DELETE SET NULL,
                    tratamiento_creado_id    INTEGER REFERENCES tratamientos(id) ON DELETE SET NULL,
                    observacion_revision     TEXT,
                    revisado_en              TIMESTAMP,
                    created_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            c.execute("""
                CREATE INDEX IF NOT EXISTS idx_candidato_empresa_estado
                ON importacion_tratamientos_candidatos (empresa_id, estado_revision);
            """)
            c.execute("""
                CREATE INDEX IF NOT EXISTS idx_candidato_importacion
                ON importacion_tratamientos_candidatos (importacion_id);
            """)

        # Confirmar toda la transacción de migración (Fase 1, 2A y 2A.2)
        conn.commit()

    except RuntimeError as exc:
        if conn:
            conn.rollback()
        st.error(f"⚠️ Error de inicialización de base de datos: {exc}")
        st.stop()

    except Exception as exc:
        if conn:
            conn.rollback()
        st.error(
            f"⚠️ Error inesperado durante la migración de base de datos "
            f"({type(exc).__name__}). Contacte al administrador."
        )
        st.stop()

    finally:
        if conn:
            conn.close()
