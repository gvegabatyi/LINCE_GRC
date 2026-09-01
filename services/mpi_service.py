"""
Servicio de Gobernanza MPI y Cálculo de Completitud Documental (Fase 2A).
Implementa la lógica del indicador interno según el Decreto N° 662.
"""

import pandas as pd
from db.repositories.mpi_gobernanza import get_perfil_activo, get_delegado_activo
from db.repositories.tratamientos import get_tratamientos_df


def calcular_completitud_mpi(empresa_id: int) -> dict:
    """
    Calcula el porcentaje y desglose de completitud documental interna para una empresa (Fase 2A).

    Reglas para alcanzar 100%:
      1. Perfil MPI activo registrado con representante legal y fecha de adopción.
      2. Delegado de Protección de Datos (DPD) activo registrado con canal de contacto e idoneidad.
      3. Al menos 1 tratamiento RAT registrado para la empresa.
      4. Todos los campos obligatorios del RAT (11 numerales) completados en los tratamientos.
      5. Al menos una evidencia documental vinculada al perfil o al delegado.

    Retorna dict con:
      - porcentaje: float (0.0 a 100.0)
      - requisitos: dict {nombre_requisito: bool}
      - detalles: list[str] de observaciones
      - perfil: dict o None
      - delegado: dict o None
      - cant_tratamientos: int
    """
    resultado = {
        "porcentaje": 0.0,
        "requisitos": {
            "perfil_activo": False,
            "delegado_activo": False,
            "rat_registrado": False,
            "rat_11_numerales_completos": False,
            "evidencia_vinculada": False,
        },
        "detalles": [],
        "perfil": None,
        "delegado": None,
        "cant_tratamientos": 0,
    }

    if not empresa_id:
        return resultado

    # 1. Perfil MPI Activo
    perfil = get_perfil_activo(empresa_id)
    resultado["perfil"] = perfil
    if perfil and perfil.get("representante_legal_nombre") and perfil.get("representante_legal_rut"):
        resultado["requisitos"]["perfil_activo"] = True
    else:
        resultado["detalles"].append("Falta registrar el Perfil MPI activo con representante legal (Art. 3 a).")

    # 2. Delegado DPD Activo
    delegado = get_delegado_activo(empresa_id)
    resultado["delegado"] = delegado
    if delegado and delegado.get("nombre_completo") and delegado.get("email_contacto_publico"):
        resultado["requisitos"]["delegado_activo"] = True
    else:
        resultado["detalles"].append("Falta designar un Delegado DPD activo con canal de contacto público (Arts. 3 b, 6 y 11).")

    # 3. Tratamientos RAT y 11 numerales
    df_trat = get_tratamientos_df(empresa_id=empresa_id)
    cant_trat = len(df_trat)
    resultado["cant_tratamientos"] = cant_trat

    if cant_trat > 0:
        resultado["requisitos"]["rat_registrado"] = True

        # Verificar si los 11 numerales están completos en todos los tratamientos
        campos_11 = [
            "rat_tipo_datos_sensibles",
            "rat_ambito_territorial",
            "rat_bases_datos_administradas",
            "rat_categorias_titulares",
            "rat_finalidades",
            "rat_fuente_datos_acceso_publico",
            "rat_base_licitud_interes_legitimo",
            "rat_destinatarios_cesiones",
            "rat_transferencias_internacionales_art27",
            "rat_plazo_condicion_supresion",
            "rat_decisiones_automatizadas_perfilamiento",
        ]

        tratamientos_incompletos = 0
        for _, row in df_trat.iterrows():
            for c in campos_11:
                val = str(row.get(c) or "").strip()
                if not val:
                    tratamientos_incompletos += 1
                    break

        if tratamientos_incompletos == 0:
            resultado["requisitos"]["rat_11_numerales_completos"] = True
        else:
            resultado["detalles"].append(
                f"Existen {tratamientos_incompletos} de {cant_trat} tratamientos con numerales obligatorios del Art. 3 d) pendientes."
            )
    else:
        resultado["detalles"].append("Falta registrar al menos una actividad de tratamiento en el RAT (Art. 3 d).")

    # 4. Evidencias vinculadas
    tiene_evidencia_perfil = bool(perfil and perfil.get("evidencia_aprobacion_id"))
    tiene_evidencia_dpd = bool(delegado and delegado.get("evidencia_designacion_id"))

    if tiene_evidencia_perfil or tiene_evidencia_dpd:
        resultado["requisitos"]["evidencia_vinculada"] = True
    else:
        resultado["detalles"].append("Falta adjuntar al menos una evidencia documental de respaldo al Perfil o al Delegado.")

    # Cálculo ponderado
    puntos = 0.0
    if resultado["requisitos"]["perfil_activo"]:
        puntos += 25.0
    if resultado["requisitos"]["delegado_activo"]:
        puntos += 25.0
    if resultado["requisitos"]["rat_registrado"]:
        puntos += 20.0
    if resultado["requisitos"]["rat_11_numerales_completos"]:
        puntos += 20.0
    if resultado["requisitos"]["evidencia_vinculada"]:
        puntos += 10.0

    # Condición estricta: para 100%, todos los 5 requisitos deben cumplirse
    if all(resultado["requisitos"].values()):
        resultado["porcentaje"] = 100.0
    else:
        resultado["porcentaje"] = min(puntos, 95.0)  # Nunca 100% si falta algún requisito

    return resultado
