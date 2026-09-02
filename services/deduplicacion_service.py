"""
Servicio de Deduplicación y Validación de Formato — Fase 2A.2 (Lince GRC).

Calcula hash SHA-256 de archivos en memoria, detecta duplicados por empresa
consultando la tabla importaciones_documentales y valida la estructura interna real
de los archivos (ZIP/XLSX/DOCX, PDF, CSV/MD/TXT) sin dependencias nativas del sistema.

No almacena archivos. No usa servicios externos ni IA.
"""

import io
import hashlib
import zipfile


# ==============================================================================
# HASH SHA-256 EN MEMORIA
# ==============================================================================

def calcular_hash_sha256(contenido: bytes) -> str:
    """Retorna el hash SHA-256 hexadecimal del contenido en bytes."""
    return hashlib.sha256(contenido).hexdigest()


# ==============================================================================
# CONSTANTES Y LISTAS DE FORMATO
# ==============================================================================

EXTENSIONES_PERMITIDAS = {"xlsx", "csv", "docx", "pdf", "md", "txt"}

EXTENSIONES_RECHAZADAS_EXPLICITAS = {
    "xls", "xlsm", "doc", "exe", "bat", "cmd", "sh", "py", "js", "vbs",
    "zip", "rar", "7z", "tar", "gz", "bz2", "pptx", "ppt",
    "jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp", "svg",
}

TAMANO_MAXIMO_BYTES = 10 * 1024 * 1024   # 10 MB

MENSAJE_FORMATO_NO_SOPORTADO = (
    "Formato no soportado en esta etapa. "
    "Convierta el archivo a XLSX, CSV, DOCX, PDF con texto, Markdown o TXT; "
    "o regístrelo como evidencia y realice el levantamiento manual."
)


# ==============================================================================
# VALIDACIÓN ESTRUCTURAL POR FORMATO (SIN DEPENDENCIAS NATIVAS)
# ==============================================================================

def validar_estructura_zip_office(contenido: bytes, extension_declarada: str) -> tuple[bool, str, str]:
    """
    Inspecciona la estructura interna de un contenedor ZIP para determinar
    si es un documento XLSX o DOCX válido conforme al estándar OpenXML.

    Retorna (es_valido, tipo_confirmado, mensaje_error).
    No asume que la firma PK diferencie XLSX de DOCX; inspecciona el catálogo XML interno.
    """
    if not zipfile.is_zipfile(io.BytesIO(contenido)):
        return False, "invalido", "El archivo no es un contenedor ZIP/OpenXML válido."

    try:
        with zipfile.ZipFile(io.BytesIO(contenido)) as zf:
            # Validar integridad del archivo ZIP
            corrupt_file = zf.testzip()
            if corrupt_file is not None:
                return False, "corrupto", f"El archivo contiene un archivo interno corrupto: {corrupt_file}."

            nombres = set(zf.namelist())

            # [Content_Types].xml es obligatorio en todo paquete OpenXML
            if "[Content_Types].xml" not in nombres:
                return (
                    False,
                    "zip_generico",
                    "El archivo es un ZIP estándar pero no contiene el manifiesto OpenXML ([Content_Types].xml).",
                )

            # Estructura XLSX: xl/workbook.xml
            es_xlsx = "xl/workbook.xml" in nombres

            # Estructura DOCX: word/document.xml
            es_docx = "word/document.xml" in nombres

            if es_xlsx and not es_docx:
                if extension_declarada != "xlsx":
                    return (
                        False,
                        "xlsx",
                        f"El archivo contiene una estructura interna de planilla XLSX, pero su extensión es '.{extension_declarada}'.",
                    )
                return True, "xlsx", ""

            elif es_docx and not es_xlsx:
                if extension_declarada != "docx":
                    return (
                        False,
                        "docx",
                        f"El archivo contiene una estructura interna de documento DOCX, pero su extensión es '.{extension_declarada}'.",
                    )
                return True, "docx", ""

            else:
                return (
                    False,
                    "openxml_no_soportado",
                    "El archivo OpenXML no corresponde a un documento de texto DOCX ni a una planilla XLSX reconocible.",
                )

    except zipfile.BadZipFile:
        return False, "invalido", "El contenedor ZIP está dañado o incompleto."
    except Exception as exc:
        return False, "error", f"Error al inspeccionar contenedor ZIP: {exc}"


def validar_estructura_pdf(contenido: bytes) -> tuple[bool, str, list[str]]:
    """
    Verifica la firma '%PDF-' y valida si el PDF puede ser parseado y si contiene texto extraíble.
    Retorna (es_valido, mensaje_error, advertencias).
    """
    advertencias = []
    # Firma estándar de encabezado PDF
    if not (contenido.startswith(b"%PDF-") or b"%PDF-" in contenido[:1024]):
        return False, "El archivo no contiene la firma esperada de un documento PDF (%PDF-).", advertencias

    # Intentar parseo seguro con pdfplumber si está disponible
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(contenido)) as pdf:
            if len(pdf.pages) == 0:
                return False, "El archivo PDF no contiene páginas legibles.", advertencias

            # Verificar si al menos una página contiene texto extraíble
            tiene_texto = False
            for page in pdf.pages:
                try:
                    txt = page.extract_text()
                    if txt and txt.strip():
                        tiene_texto = True
                        break
                except Exception:
                    continue

            if not tiene_texto:
                advertencias.append(
                    "PDF sin texto extraíble detectado. Este archivo parece contener solo imágenes o páginas escaneadas. "
                    "El procesamiento automático no podrá extraer campos de texto."
                )

        return True, "", advertencias

    except ImportError:
        # Fallback sin pdfplumber: validar al menos firma de fin de archivo %%EOF
        if b"%%EOF" not in contenido[-2048:]:
            advertencias.append("El archivo PDF no contiene el marcador final estándar (%%EOF), podría estar incompleto.")
        return True, "", advertencias
    except Exception as exc:
        return False, f"El archivo PDF no se pudo abrir o está protegido con contraseña ({type(exc).__name__}).", advertencias


def validar_estructura_texto(contenido: bytes, extension_declarada: str) -> tuple[bool, str, str]:
    """
    Valida decodificación segura de archivos de texto plano (CSV, MD, TXT).
    No afirma identificación MIME inequívoca.
    Retorna (es_valido, tipo_confirmado, mensaje_error).
    """
    try:
        contenido.decode("utf-8")
        return True, extension_declarada, ""
    except UnicodeDecodeError:
        try:
            contenido.decode("latin-1")
            return True, extension_declarada, ""
        except Exception:
            return False, "binario", "El archivo no pudo ser decodificado como texto (ni UTF-8 ni Latin-1)."


# ==============================================================================
# VALIDACIÓN GENERAL DEL ARCHIVO
# ==============================================================================

def validar_archivo(nombre_archivo: str, contenido: bytes) -> tuple[bool, list[str], list[str], str]:
    """
    Valida extensión, estructura interna, tamaño y contenido vacío.
    Retorna (es_valido, lista_de_errores, lista_de_advertencias, tipo_detectado).
    """
    errores = []
    advertencias = []
    ext = nombre_archivo.lower().rsplit(".", 1)[-1] if "." in nombre_archivo else ""

    # Archivo vacío
    if len(contenido) == 0:
        errores.append("El archivo está vacío (0 bytes).")
        return False, errores, advertencias, "vacio"

    # Extensión rechazada explícitamente
    if ext in EXTENSIONES_RECHAZADAS_EXPLICITAS:
        errores.append(MENSAJE_FORMATO_NO_SOPORTADO)
        return False, errores, advertencias, ext

    # Extensión no permitida
    if ext not in EXTENSIONES_PERMITIDAS:
        errores.append(MENSAJE_FORMATO_NO_SOPORTADO)
        return False, errores, advertencias, ext

    # Tamaño máximo
    if len(contenido) > TAMANO_MAXIMO_BYTES:
        errores.append(
            f"El archivo supera el tamaño máximo permitido de 10 MB "
            f"(tamaño actual: {len(contenido) / 1024 / 1024:.2f} MB)."
        )
        return False, errores, advertencias, ext

    tipo_detectado = ext

    # Validación estructural específica
    if ext in ("xlsx", "docx"):
        valido_zip, tipo_zip, msg_zip = validar_estructura_zip_office(contenido, ext)
        if not valido_zip:
            errores.append(msg_zip)
        else:
            tipo_detectado = tipo_zip

    elif ext == "pdf":
        valido_pdf, msg_pdf, adv_pdf = validar_estructura_pdf(contenido)
        if not valido_pdf:
            errores.append(msg_pdf)
        advertencias.extend(adv_pdf)
        tipo_detectado = "pdf"

    elif ext in ("csv", "md", "txt"):
        valido_txt, tipo_txt, msg_txt = validar_estructura_texto(contenido, ext)
        if not valido_txt:
            errores.append(msg_txt)
        else:
            tipo_detectado = tipo_txt

    es_valido = len(errores) == 0
    return es_valido, errores, advertencias, tipo_detectado


# ==============================================================================
# DETECCIÓN DE DUPLICADOS EN BD
# ==============================================================================

def detectar_duplicado_empresa(empresa_id: int, hash_sha256: str) -> dict | None:
    """
    Consulta si ya existe una importación con el mismo hash para esta empresa.
    Retorna el registro anterior como dict, o None si no hay duplicado.
    No bloquea la carga; el resultado se usa solo para mostrar advertencia.
    """
    from db.connection import get_connection
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                SELECT id, nombre_archivo, estado, created_at
                FROM importaciones_documentales
                WHERE empresa_id = %s AND hash_sha256 = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (empresa_id, hash_sha256),
            )
            row = c.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "nombre_archivo": row[1],
                "estado": row[2],
                "created_at": row[3],
            }
    except Exception:
        return None
    finally:
        if conn:
            conn.close()


def detectar_candidato_similar_en_tratamientos(empresa_id: int, nombre_tratamiento: str) -> dict | None:
    """
    Busca un tratamiento existente con nombre idéntico (normalizado) en la misma empresa.
    Retorna dict con id y nombre, o None si no hay coincidencia exacta.
    """
    if not nombre_tratamiento or not nombre_tratamiento.strip():
        return None
    from db.connection import get_connection
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as c:
            c.execute(
                """
                SELECT id, nombre_tratamiento
                FROM tratamientos
                WHERE empresa_id = %s
                  AND LOWER(TRIM(nombre_tratamiento)) = LOWER(TRIM(%s))
                LIMIT 1
                """,
                (empresa_id, nombre_tratamiento.strip()),
            )
            row = c.fetchone()
            if not row:
                return None
            return {"id": row[0], "nombre_tratamiento": row[1]}
    except Exception:
        return None
    finally:
        if conn:
            conn.close()
