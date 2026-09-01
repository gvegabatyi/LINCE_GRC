"""
Módulo Exportar Informe — Generación de libro Excel consolidado.
Fase 1: mantiene las 5 hojas originales sin regresiones y añade la hoja
EVALUACIONES como sexta hoja en un bloque try/except independiente para
que un error en esa hoja no impida generar las 5 existentes.
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from db.repositories.empresas import get_empresas_df
from db.repositories.evaluaciones import get_evaluaciones_df
from db.repositories.tratamientos import get_tratamientos_df
from db.repositories.visitas import get_visitas_df
from db.repositories.evidencias import get_evidencias_df
from utils.constants import CHECKLIST_PREGUNTAS, ESTADO_EVALUACION_DISPLAY
from services.checklist_service import calcular_porcentaje, nivel_cumplimiento
import json


# ==============================================================================
# ESTILOS EXCEL COMPARTIDOS
# ==============================================================================
def _estilos():
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font  = Font(name="Calibri", size=14, bold=True, color="1F4E79")
    bold_font   = Font(name="Calibri", size=11, bold=True)
    regular_font = Font(name="Calibri", size=10)
    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )
    return header_fill, header_font, title_font, bold_font, regular_font, thin_border


def _format_sheet(ws, header_fill, header_font, thin_border, is_summary=False):
    """Aplica estilos a la primera fila de encabezados y ajusta anchos."""
    if not is_summary:
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.row_dimensions[1].height = 28

    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            cell.border = thin_border
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)


# ==============================================================================
# GENERACIÓN DEL LIBRO EXCEL
# ==============================================================================
def generar_excel_completo() -> bytes:
    """
    Genera un archivo Excel en memoria con hasta 6 hojas.
    Las 5 hojas originales siempre se generan.
    La hoja EVALUACIONES se añade en un bloque try/except independiente.
    Retorna bytes del archivo .xlsx.
    """
    header_fill, header_font, title_font, bold_font, regular_font, thin_border = _estilos()

    wb = openpyxl.Workbook()
    default_sheet = wb.active
    wb.remove(default_sheet)

    # ── Hoja 1: EMPRESAS ──────────────────────────────────────────────────────
    ws1 = wb.create_sheet(title="EMPRESAS")
    df_emp = get_empresas_df()
    ws1.append(["ID", "Nombre Empresa", "RUT", "Dirección", "Contacto", "Email", "Teléfono", "Fecha Registro"])
    for _, r in df_emp.iterrows():
        ws1.append([
            r["id"], r["nombre"], r["rut"],
            r.get("direccion") or "", r.get("contacto") or "",
            r.get("email") or "", r.get("telefono") or "",
            str(r["created_at"])[:19] if pd.notnull(r.get("created_at")) else "",
        ])
    _format_sheet(ws1, header_fill, header_font, thin_border)

    # ── Hoja 2: TRATAMIENTOS ──────────────────────────────────────────────────
    ws2 = wb.create_sheet(title="TRATAMIENTOS")
    df_trat = get_tratamientos_df()
    ws2.append([
        "ID", "Empresa", "RUT Empresa", "Tratamiento", "Descripción",
        "Base Legal", "Datos Personales", "Responsables", "Encargados",
        "Transferencias", "Evaluación", "Fecha Registro",
    ])
    for _, r in df_trat.iterrows():
        ws2.append([
            r["id"], r["empresa"], r["rut_empresa"], r["nombre_tratamiento"],
            r.get("descripcion") or "", r.get("base_legal") or "",
            r.get("datos_personales") or "", r.get("responsables") or "",
            r.get("encargados") or "", r.get("transferencias") or "",
            r.get("evaluacion_nombre") or "",
            str(r["created_at"])[:19] if pd.notnull(r.get("created_at")) else "",
        ])
    _format_sheet(ws2, header_fill, header_font, thin_border)

    # ── Hoja 3: VISITAS ───────────────────────────────────────────────────────
    ws3 = wb.create_sheet(title="VISITAS")
    df_vis = get_visitas_df()
    headers_vis = [
        "ID", "Empresa", "RUT Empresa", "Fecha Visita", "Tipo Visita",
        "Auditor", "Puntaje (/15)", "% Cumplimiento", "Evaluación", "Observaciones",
    ]
    for q in CHECKLIST_PREGUNTAS:
        headers_vis.append(q[:30] + "…")
    ws3.append(headers_vis)

    for _, r in df_vis.iterrows():
        puntaje = int(r["puntaje"]) if pd.notnull(r.get("puntaje")) else 0
        porcentaje = f"{calcular_porcentaje(puntaje):.1f}%"
        row_data = [
            r["id"], r["empresa"], r["rut_empresa"], str(r["fecha_visita"]),
            r.get("tipo_visita") or "", r.get("auditor") or "",
            puntaje, porcentaje,
            r.get("evaluacion_nombre") or "", r.get("observaciones") or "",
        ]
        chk = r["checklist_seguridad"]
        if isinstance(chk, str):
            try:
                chk = json.loads(chk)
            except Exception:
                chk = {}
        elif not isinstance(chk, dict):
            chk = {}
        for q in CHECKLIST_PREGUNTAS:
            row_data.append(chk.get(q, "N/A"))
        ws3.append(row_data)
    _format_sheet(ws3, header_fill, header_font, thin_border)

    # ── Hoja 4: EVIDENCIAS ────────────────────────────────────────────────────
    ws4 = wb.create_sheet(title="EVIDENCIAS")
    df_ev = get_evidencias_df()
    ws4.append(["ID", "ID Visita", "Empresa", "Fecha Visita",
                "Descripción", "URL Foto / Archivo", "Evaluación", "Fecha Registro"])
    for _, r in df_ev.iterrows():
        ws4.append([
            r["id"], r["visita_id"], r["empresa"], str(r["fecha_visita"]),
            r.get("descripcion") or "", r.get("foto_url") or "",
            r.get("evaluacion_nombre") or "",
            str(r["created_at"])[:19] if pd.notnull(r.get("created_at")) else "",
        ])
    _format_sheet(ws4, header_fill, header_font, thin_border)

    # ── Hoja 5: RESUMEN ───────────────────────────────────────────────────────
    ws5 = wb.create_sheet(title="RESUMEN")
    ws5.append(["INFORME CONSOLIDADO DE CUMPLIMIENTO Y AUDITORÍA GRC"])
    ws5.append([f"Fecha de Generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
    ws5.append([])
    ws5.append(["Métrica General", "Valor"])
    ws5.append(["Total de Empresas Registradas", len(df_emp)])
    ws5.append(["Total de Tratamientos (ROPA)", len(df_trat)])
    ws5.append(["Total de Visitas de Auditoría", len(df_vis)])
    ws5.append(["Total de Evidencias Adjuntas", len(df_ev)])

    promedio = df_vis["puntaje"].mean() if not df_vis.empty and "puntaje" in df_vis.columns else 0
    ws5.append(["Promedio Puntaje Seguridad (/15)", f"{promedio:.2f}"])
    ws5.append(["% Promedio Cumplimiento", f"{calcular_porcentaje(promedio):.1f}%"])

    # Estilos hoja resumen
    ws5["A1"].font = title_font
    ws5["A2"].font = regular_font
    for cell in [ws5["A4"], ws5["B4"]]:
        cell.fill = header_fill
        cell.font = header_font
    for col in ws5.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max((len(str(cell.value or "")) for cell in col), default=10)
        ws5.column_dimensions[col_letter].width = min(max(max_len + 3, 14), 45)
        for cell in col:
            cell.border = thin_border

    # ── Hoja 6: EVALUACIONES (protegida con try/except) ───────────────────────
    try:
        df_eval = get_evaluaciones_df()
        ws6 = wb.create_sheet(title="EVALUACIONES")
        ws6.append([
            "ID", "Empresa", "RUT Empresa", "Nombre Evaluación", "Tipo",
            "Período", "Estado", "Auditor", "Fecha Inicio",
            "Cierre Planificado", "Cierre Real", "% Avance",
            "Alcance", "Objetivo", "Marco Normativo", "Observaciones", "Fecha Registro",
        ])
        for _, r in df_eval.iterrows():
            ws6.append([
                r["id"], r["empresa"], r["rut_empresa"], r["nombre"],
                r.get("tipo_evaluacion") or "",
                r.get("periodo") or "",
                ESTADO_EVALUACION_DISPLAY.get(r.get("estado", ""), r.get("estado", "")),
                r.get("auditor_responsable") or "",
                str(r["fecha_inicio"]) if pd.notnull(r.get("fecha_inicio")) else "",
                str(r["fecha_cierre_planificada"]) if pd.notnull(r.get("fecha_cierre_planificada")) else "",
                str(r["fecha_cierre_real"]) if pd.notnull(r.get("fecha_cierre_real")) else "",
                f"{float(r.get('porcentaje_avance') or 0):.1f}%",
                r.get("alcance") or "",
                r.get("objetivo") or "",
                r.get("marco_normativo") or "",
                r.get("observaciones") or "",
                str(r["created_at"])[:19] if pd.notnull(r.get("created_at")) else "",
            ])
        _format_sheet(ws6, header_fill, header_font, thin_border)
    except Exception:
        # Si la hoja de evaluaciones falla, el resto del Excel ya está generado.
        pass

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


# ==============================================================================
# MÓDULO UI
# ==============================================================================
def render() -> None:
    st.header("📊 Generación y Descarga de Informe Completo")
    st.write("Genera un libro Excel consolidado (`.xlsx`) con hojas formateadas profesionalmente:")

    st.markdown("""
    - **Hoja 1 — EMPRESAS:** Catálogo completo de empresas del grupo.
    - **Hoja 2 — TRATAMIENTOS:** Registro de Actividades de Tratamiento (ROPA).
    - **Hoja 3 — VISITAS:** Auditorías con puntaje, tipo y desglose del checklist.
    - **Hoja 4 — EVIDENCIAS:** Registro y enlaces de evidencias levantadas en terreno.
    - **Hoja 5 — RESUMEN:** Métricas ejecutivas, porcentajes de cumplimiento y fecha de emisión.
    - **Hoja 6 — EVALUACIONES:** Proyectos GRC registrados por empresa *(nueva en Fase 1)*.
    """)

    st.markdown("---")

    col_exp1, col_exp2 = st.columns([1, 2])
    with col_exp1:
        if st.button("🔄 Generar Informe Excel", type="primary", use_container_width=True):
            with st.spinner("Generando libro Excel…"):
                try:
                    excel_bytes = generar_excel_completo()
                    st.session_state["excel_informe"] = excel_bytes
                    st.success("✅ ¡Informe generado con éxito!")
                except Exception as exc:
                    st.error(f"Error al generar el informe ({type(exc).__name__}). Intente nuevamente.")

    with col_exp2:
        if "excel_informe" in st.session_state:
            nombre_archivo = f"Serviphar_GRC_Informe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            st.download_button(
                label="📥 Descargar Informe Completo Excel (.xlsx)",
                data=st.session_state["excel_informe"],
                file_name=nombre_archivo,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
