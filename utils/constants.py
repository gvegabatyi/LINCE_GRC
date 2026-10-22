"""
Constantes globales de la aplicación Lince GRC.
Centraliza listas de valores, textos de checklist, etiquetas de semáforo
y referencias normativas del Decreto N° 662 (Ministerio de Hacienda).
"""

# ==============================================================================
# CHECKLIST DE SEGURIDAD (15 PREGUNTAS — Mantenidas sin cambios desde Fase 1)
# ==============================================================================
CHECKLIST_PREGUNTAS = [
    "1. ¿Cuenta con política de seguridad de la información documentada?",
    "2. ¿Existe un responsable de seguridad de la información?",
    "3. ¿Se realizan copias de seguridad periódicas?",
    "4. ¿Los sistemas tienen control de acceso con usuario y contraseña?",
    "5. ¿Las contraseñas cumplen con política de complejidad?",
    "6. ¿Existe control de acceso físico a las instalaciones?",
    "7. ¿El personal ha recibido capacitación en seguridad?",
    "8. ¿Existen procedimientos para gestión de incidentes?",
    "9. ¿Se realiza mantenimiento preventivo de equipos?",
    "10. ¿Existe política de uso aceptable de recursos TI?",
    "11. ¿Los datos sensibles están encriptados?",
    "12. ¿Existe control de cambios en sistemas críticos?",
    "13. ¿Se realizan evaluaciones de riesgo periódicas?",
    "14. ¿Existe plan de continuidad del negocio?",
    "15. ¿Se realizan auditorías internas de seguridad?",
]

CHECKLIST_MAX_PUNTAJE = len(CHECKLIST_PREGUNTAS)

# ==============================================================================
# FASE 2A: MODELO DE PREVENCIÓN DE INFRACCIONES (MPI) — DECRETO N° 662
# ==============================================================================

# Estados Internos de Implementación (Declarativos internos)
ESTADOS_MPI_INTERNOS = [
    ("preparacion", "🔵 En Preparación"),
    ("implementado_internamente", "🟡 Implementado Internamente"),
    ("en_revision_interna", "🟠 En Revisión Interna"),
]

ESTADOS_MPI_INTERNOS_MAP = dict(ESTADOS_MPI_INTERNOS)

# Estados Oficiales Registrales (Exigen respaldo documental y de la Agencia)
ESTADOS_MPI_OFICIALES = [
    ("sin_solicitud", "⚪ Sin Solicitud de Certificación"),
    ("solicitud_en_tramite", "⏳ Solicitud en Trámite ante la Agencia"),
    ("certificado_agencia", "🛡️ Certificado por la Agencia (Art. 15)"),
    ("inscrito_registro_agencia", "📋 Inscrito en Registro Nacional (Art. 17)"),
    ("vencido", "⚠️ Certificado Vencido"),
    ("revocado", "❌ Certificado Revocado por la Agencia (Art. 20)"),
]

ESTADOS_MPI_OFICIALES_MAP = dict(ESTADOS_MPI_OFICIALES)

# Tipos de Vínculo del Delegado de Protección de Datos (Art. 7)
TIPOS_VINCULO_DELEGADO = [
    ("dependiente", "Trabajador Dependiente (Contrato de Trabajo)"),
    ("prestacion_servicios_natural", "Prestación de Servicios (Persona Natural)"),
    ("prestacion_servicios_juridica", "Prestación de Servicios (Persona Jurídica)"),
]

# Autoridad que designa al Delegado (Art. 8)
AUTORIDADES_DESIGNACION_DPD = [
    "Directorio",
    "Junta de Accionistas",
    "Gerencia General",
    "Máxima Autoridad Directiva / Administrativa",
    "Administrador Único",
]

# ==============================================================================
# FASE 2A: REGISTRO DE ACTIVIDADES DE TRATAMIENTO (RAT) — ART. 3 LETRA D)
# 11 Numerales Normativos Taxativos (Decreto N° 662)
# ==============================================================================
RAT_NUMERALES_INFO = {
    "i": {
        "numeral": "i",
        "campo_db": "rat_tipo_datos_sensibles",
        "label": "i. Tipo de datos personales y categorías especiales / sensibles",
        "referencia": "Decreto N° 662, Art. 3 letra d) num. i",
        "placeholder": "Ej. Datos identificatorios, de contacto, laborales, remuneraciones, salud, biométricos...",
    },
    "ii": {
        "numeral": "ii",
        "campo_db": "rat_ambito_territorial",
        "label": "ii. Ámbito territorial del tratamiento",
        "referencia": "Decreto N° 662, Art. 3 letra d) num. ii",
        "placeholder": "Ej. Nacional (todo Chile), Regional (Región Metropolitana), Transfronterizo...",
    },
    "iii": {
        "numeral": "iii",
        "campo_db": "rat_bases_datos_administradas",
        "label": "iii. Categorías, clases o tipos de bases de datos administradas",
        "referencia": "Decreto N° 662, Art. 3 letra d) num. iii",
        "placeholder": "Ej. Base de datos de nómina, ERP corporativo, CRM de clientes, repositorio documental...",
    },
    "iv": {
        "numeral": "iv",
        "campo_db": "rat_categorias_titulares",
        "label": "iv. Categorías de titulares de datos",
        "referencia": "Decreto N° 662, Art. 3 letra d) num. iv",
        "placeholder": "Ej. Trabajadores dependientes, postulantes a empleo, clientes personas naturales, proveedores...",
    },
    "v": {
        "numeral": "v",
        "campo_db": "rat_finalidades",
        "label": "v. Fines de las operaciones de tratamiento",
        "referencia": "Decreto N° 662, Art. 3 letra d) num. v",
        "placeholder": "Ej. Pago de remuneraciones y cotizaciones previsionales, gestión de contratos comerciales...",
    },
    "vi": {
        "numeral": "vi",
        "campo_db": "rat_fuente_datos_acceso_publico",
        "label": "vi. Fuente de procedencia y si provienen de fuentes de acceso público",
        "referencia": "Decreto N° 662, Art. 3 letra d) num. vi",
        "placeholder": "Ej. Recolectados directamente del titular; Registro de Comercio (fuente pública)...",
    },
    "vii": {
        "numeral": "vii",
        "campo_db": "rat_base_licitud_interes_legitimo",
        "label": "vii. Base de licitud e interés legítimo cuando corresponda",
        "referencia": "Decreto N° 662, Art. 3 letra d) num. vii",
        "placeholder": "Ej. Ejecución de contrato de trabajo (Ley 19.628 / 21.719); Cumplimiento de obligación legal...",
    },
    "viii": {
        "numeral": "viii",
        "campo_db": "rat_destinatarios_cesiones",
        "label": "viii. Categorías de terceros destinatarios, incluidos terceros países u organizaciones",
        "referencia": "Decreto N° 662, Art. 3 letra d) num. viii",
        "placeholder": "Ej. Instituciones previsionales (AFP, Fonasa), Servicio de Impuestos Internos, bancos...",
    },
    "ix": {
        "numeral": "ix",
        "campo_db": "rat_transferencias_internacionales_art27",
        "label": "ix. Transferencias internacionales: país u organización y medio para cumplir el art. 27",
        "referencia": "Decreto N° 662, Art. 3 letra d) num. ix",
        "placeholder": "Ej. No aplica / Proveedor Cloud en EE.UU. con cláusulas contractuales tipo (Art. 27 Ley 19.628)...",
    },
    "x": {
        "numeral": "x",
        "campo_db": "rat_plazo_condicion_supresion",
        "label": "x. Plazos o condiciones de supresión de los datos",
        "referencia": "Decreto N° 662, Art. 3 letra d) num. x",
        "placeholder": "Ej. 5 años desde el término de la relación laboral (plazo prescripción laboral y tributaria)...",
    },
    "xi": {
        "numeral": "xi",
        "campo_db": "rat_decisiones_automatizadas_perfilamiento",
        "label": "xi. Decisiones automatizadas / perfilamiento: lógica significativa y consecuencias",
        "referencia": "Decreto N° 662, Art. 3 letra d) num. xi",
        "placeholder": "Ej. No se realizan decisiones automatizadas ni perfilamiento / Algoritmo de scoring con supervisión humana...",
    },
}

# Bases Legales Estándar
BASES_LEGALES = [
    "Consentimiento del Titular",
    "Ejecución de Contrato",
    "Obligación Legal",
    "Interés Legítimo del Responsable o Tercero",
    "Interés Público o Ejercicio de Funciones Públicas",
    "Protección de Intereses Vitales",
]

TRANSFERENCIAS_OPCIONES = [
    "No aplica (Tratamiento exclusivamente nacional)",
    "Sí - Servidores Cloud (EE.UU.) con Cláusulas Contractuales",
    "Sí - Proveedores en UE con Nivel Adecuado",
    "Sí - Otros países con Garantías Apropiadas (Art. 27)",
]

# ==============================================================================
# VISITAS / AUDITORÍAS
# ==============================================================================
TIPOS_VISITA = [
    "Sin especificar",
    "Visita Bodega",
    "Visita Farmacia",
    "Entrevista RRHH",
    "Entrevista TI",
    "Entrevista Gerencia",
    "Revisión Documental",
    "Auditoría de Cumplimiento MPI",
    "Otro",
]

# ==============================================================================
# EVALUACIONES GRC
# ==============================================================================
TIPOS_EVALUACION = [
    "Diagnóstico Inicial",
    "Seguimiento MPI",
    "Cierre de Evaluación",
    "Auditoría Interna",
]

ESTADOS_EVALUACION = [
    "borrador",
    "en_progreso",
    "en_revision",
    "cerrada",
]

ESTADO_EVALUACION_DISPLAY = {
    "borrador":    "🔵 Borrador",
    "en_progreso": "🟡 En Progreso",
    "en_revision": "🟠 En Revisión",
    "cerrada":     "✅ Cerrada",
}

ESTADO_EVALUACION_COLOR = {
    "borrador":    "#1565C0",
    "en_progreso": "#F9A825",
    "en_revision": "#E65100",
    "cerrada":     "#2E7D32",
}

# ==============================================================================
# AVISOS LEGALES VISIBLES OBLIGATORIOS
# ==============================================================================
AVISO_ESTADOS_OFICIALES = (
    "⚠️ **Aviso de Responsabilidad:** Los estados oficiales son antecedentes declarativos y documentales. "
    "Lince GRC no certifica, registra, supervisa ni valida oficialmente modelos de prevención de infracciones. "
    "Estas atribuciones corresponden exclusivamente a la Agencia de Protección de Datos Personales."
)

def semaforo_porcentaje(valor: float) -> str:
    """Devuelve estado técnico de terminal según porcentaje (0-100)."""
    if valor is None:
        return "[--] Sin datos"
    if valor >= 80:
        return f"● ALTO ({valor:.0f}%)"
    if valor >= 50:
        return f"▲ MEDIO ({valor:.0f}%)"
    if valor >= 25:
        return f"◆ BAJO ({valor:.0f}%)"
    return f"■ CRÍTICO ({valor:.0f}%)"


# ==============================================================================
# DERECHOS DE LOS TITULARES (Ley 19.628 art. 12/16 · Ley 21.719 arts. 4-11)
# ==============================================================================
DERECHOS_TITULAR = [
    ("acceso", "Acceso (art. 5)"),
    ("rectificacion", "Rectificación (art. 6)"),
    ("supresion", "Supresión (art. 7)"),
    ("oposicion", "Oposición (art. 8)"),
    ("decisiones_automatizadas", "Oposición a decisiones automatizadas (art. 8 bis)"),
    ("bloqueo", "Bloqueo del tratamiento (art. 8 ter)"),
    ("portabilidad", "Portabilidad (art. 9)"),
]
DERECHOS_TITULAR_MAP = dict(DERECHOS_TITULAR)

# Derechos cuya solicitud habilita pedir bloqueo temporal (Ley 21.719 art. 11)
DERECHOS_CON_BLOQUEO_TEMPORAL = {"rectificacion", "supresion", "oposicion"}

CANALES_SOLICITUD = [
    "Correo electrónico",
    "Formulario web",
    "Medio electrónico equivalente",
    "Presencial / carta",
    "Otro",
]

ESTADOS_SOLICITUD = [
    ("recibida", "Recibida"),
    ("en_analisis", "En análisis"),
    ("acogida", "Acogida"),
    ("acogida_parcial", "Acogida parcialmente"),
    ("denegada", "Denegada"),
    ("cerrada", "Cerrada"),
]
ESTADOS_SOLICITUD_MAP = dict(ESTADOS_SOLICITUD)
# Estados en que la solicitud ya fue respondida: el plazo deja de correr
ESTADOS_SOLICITUD_RESPONDIDA = {"acogida", "acogida_parcial", "denegada", "cerrada"}

# Feriados nacionales de Chile para el cómputo de días hábiles.
# Criterio conservador: sólo se incluyen feriados con certeza. Omitir un feriado
# acorta el plazo calculado (lado seguro); incluir uno erróneo lo alargaría.
# MANTENER: validar y agregar cada año contra el calendario oficial.
FERIADOS_CHILE = {
    # 2026
    "2026-01-01", "2026-04-03", "2026-04-04", "2026-05-01", "2026-05-21",
    "2026-06-21", "2026-06-29", "2026-07-16", "2026-08-15", "2026-09-18",
    "2026-09-19", "2026-10-12", "2026-10-31", "2026-11-01", "2026-12-08",
    "2026-12-25",
    # 2027
    "2027-01-01", "2027-03-26", "2027-03-27", "2027-05-01", "2027-05-21",
    "2027-06-21", "2027-06-28", "2027-07-16", "2027-08-15", "2027-09-18",
    "2027-09-19", "2027-10-11", "2027-11-01", "2027-12-08", "2027-12-25",
}
