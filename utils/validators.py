"""
Funciones de validación de campos de formulario.
Devuelven (es_valido: bool, mensaje_error: str).
"""


def validar_nombre(valor: str, campo: str = "Nombre") -> tuple[bool, str]:
    """Valida que un campo de texto no esté vacío."""
    if not valor or not valor.strip():
        return False, f"El campo '{campo}' es obligatorio."
    if len(valor.strip()) > 255:
        return False, f"El campo '{campo}' no puede superar 255 caracteres."
    return True, ""


def validar_rut(rut: str) -> tuple[bool, str]:
    """Valida que el RUT no esté vacío y tenga formato mínimo."""
    if not rut or not rut.strip():
        return False, "El RUT es obligatorio."
    rut_limpio = rut.strip().replace(".", "").replace("-", "")
    if len(rut_limpio) < 7:
        return False, "El RUT parece demasiado corto. Verifique el formato (ej: 76.123.456-7)."
    return True, ""


def validar_email(email: str) -> tuple[bool, str]:
    """Valida formato básico de correo electrónico (campo opcional)."""
    if not email or not email.strip():
        return True, ""   # es opcional
    if "@" not in email or "." not in email.split("@")[-1]:
        return False, "El correo electrónico no parece válido."
    return True, ""


def validar_porcentaje(valor) -> tuple[bool, str]:
    """Valida que un porcentaje esté entre 0 y 100."""
    try:
        v = float(valor)
        if v < 0 or v > 100:
            return False, "El porcentaje debe estar entre 0 y 100."
        return True, ""
    except (TypeError, ValueError):
        return False, "El porcentaje debe ser un número."


def validar_fecha_rango(fecha_inicio, fecha_fin) -> tuple[bool, str]:
    """Valida que fecha_fin sea posterior o igual a fecha_inicio (ambas opcionales)."""
    if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
        return False, "La fecha de cierre no puede ser anterior a la fecha de inicio."
    return True, ""
