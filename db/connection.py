"""
Módulo de conexión a PostgreSQL (Neon).
Gestiona la URL de conexión y entrega conexiones con transacciones explícitas.
DATABASE_URL nunca se expone en mensajes de error ni logs.
"""

import os
import psycopg2


def get_db_url() -> str | None:
    """
    Obtiene y normaliza la URL de conexión desde la variable de entorno DATABASE_URL.
    Retorna None si la variable no está configurada.
    Normaliza 'postgres://' a 'postgresql://' para compatibilidad con psycopg2.
    """
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return None
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def get_connection() -> psycopg2.extensions.connection:
    """
    Establece y retorna una conexión a PostgreSQL.

    - autocommit=False (comportamiento por defecto de psycopg2):
      cada escritura requiere conn.commit() explícito.
    - Timeout de conexión: 10 segundos.
    - En caso de error, lanza RuntimeError con mensaje genérico
      que NO incluye la URL de conexión ni credenciales.

    Raises:
        RuntimeError: si DATABASE_URL no está configurada o la conexión falla.
    """
    url = get_db_url()
    if not url:
        raise RuntimeError(
            "La variable de entorno DATABASE_URL no está configurada. "
            "Configúrela en Railway → Variables de entorno."
        )
    try:
        conn = psycopg2.connect(dsn=url, connect_timeout=10)
        # psycopg2 inicia transacciones automáticamente (autocommit=False por defecto).
        # Lo establecemos explícitamente para documentar la intención.
        conn.autocommit = False
        return conn
    except psycopg2.OperationalError:
        raise RuntimeError(
            "No se pudo conectar a la base de datos. "
            "Verifique que Neon esté activo y que la URL incluya ?sslmode=require."
        )
    except psycopg2.Error as exc:
        raise RuntimeError(
            f"Error de base de datos al conectar ({type(exc).__name__}). "
            "Contacte al administrador."
        ) from exc
