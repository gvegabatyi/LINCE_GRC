"""
Pruebas del módulo Análisis de Riesgos.

- Unitarias (sin BD): niveles, reglas de diagnóstico sobre datos sintéticos, disparadores de EIPD.
- Integración (LINCE_TEST_DATABASE_URL, BD desechable): registro en lote sin duplicados,
  restricción de escala 1-5, aislamiento entre empresas y validación de la EIPD.
"""

import os
import unittest
from datetime import date
from unittest import mock

import pandas as pd

from services import riesgos_service as rs

TRATAMIENTO_COMPLETO = {
    "id": 1, "nombre_tratamiento": "Nómina", "base_legal": "Obligación legal", "encargados": "",
    "rat_tipo_datos_sensibles": "No", "rat_ambito_territorial": "Chile", "rat_bases_datos_administradas": "ERP",
    "rat_categorias_titulares": "Trabajadores", "rat_finalidades": "Remuneraciones",
    "rat_fuente_datos_acceso_publico": "El titular", "rat_base_licitud_interes_legitimo": "Art. 13 b",
    "rat_destinatarios_cesiones": "Previred", "rat_transferencias_internacionales_art27": "Ninguna",
    "rat_plazo_condicion_supresion": "5 años", "rat_decisiones_automatizadas_perfilamiento": "No",
}


def _df(**cambios) -> pd.DataFrame:
    return pd.DataFrame([{**TRATAMIENTO_COMPLETO, **cambios}])


def _codigos(propuestos) -> set:
    return {p.codigo_regla for p in propuestos}


class TestNiveles(unittest.TestCase):
    def test_umbrales(self):
        self.assertEqual(rs.nivel_riesgo(1, 4)[1], "bajo")
        self.assertEqual(rs.nivel_riesgo(1, 5)[1], "medio")
        self.assertEqual(rs.nivel_riesgo(2, 5)[1], "alto")
        self.assertEqual(rs.nivel_riesgo(3, 5)[1], "critico")
        self.assertEqual(rs.nivel_riesgo(5, 5), (25, "critico", "CRÍTICO"))

    def test_fuera_de_escala(self):
        with self.assertRaises(ValueError):
            rs.nivel_riesgo(0, 3)

    def test_impacto_por_gravedad_legal(self):
        self.assertEqual(rs.impacto_sugerido("34 bis a"), 2)
        self.assertEqual(rs.impacto_sugerido("34 ter j"), 4)
        self.assertEqual(rs.impacto_sugerido("34 quater k"), 5)


class TestDiagnostico(unittest.TestCase):
    def test_tratamiento_completo_sin_riesgos(self):
        self.assertEqual(rs.diagnosticar(_df()), [])

    def test_reglas_del_rat(self):
        p = rs.diagnosticar(_df(base_legal="", rat_base_licitud_interes_legitimo="",
                                rat_tipo_datos_sensibles="Datos de salud", rat_plazo_condicion_supresion="",
                                rat_decisiones_automatizadas_perfilamiento="Scoring crediticio",
                                rat_transferencias_internacionales_art27="AWS EE.UU.", encargados="Proveedor TI"))
        self.assertEqual(_codigos(p), {"R-LIC", "R-SEN", "R-AUT", "R-TRI", "R-SUP", "R-ENC", "R-TRA"})
        por = {x.codigo_regla: x for x in p}
        self.assertEqual(por["R-AUT"].infraccion, "34 quater k")
        self.assertEqual(por["R-AUT"].impacto, 5)
        self.assertEqual(por["R-LIC"].gravedad, "grave")
        self.assertEqual(por["R-LIC"].tratamiento_id, 1)

    def test_negaciones_no_generan_riesgo(self):
        for valor in ("no", "Ninguno", "N/A", "no aplica", ""):
            self.assertNotIn("R-SEN", _codigos(rs.diagnosticar(_df(rat_tipo_datos_sensibles=valor))), valor)

    def test_seguridad_desde_auditoria(self):
        visitas = pd.DataFrame([
            {"fecha_visita": date(2026, 9, 1), "checklist_seguridad": {"1. A?": "Sí", "2. B?": "Sí"}},
            {"fecha_visita": date(2026, 10, 1), "checklist_seguridad": {"1. A?": "No", "2. B?": "No", "3. C?": "Sí"}},
        ])
        (p,) = rs.diagnosticar(_df(), visitas=visitas)
        self.assertEqual((p.codigo_regla, p.infraccion, p.probabilidad), ("R-SEG", "34 ter j", 4))
        self.assertIn("2 de 3", p.titulo)

    def test_derechos_vencidos_y_bloqueo(self):
        sol = pd.DataFrame([
            {"folio": "SD-1", "estado": "recibida", "fecha_vencimiento": date(2026, 10, 1),
             "bloqueo_solicitado": True, "bloqueo_resultado": None, "bloqueo_vencimiento": date(2026, 9, 28)},
            {"folio": "SD-2", "estado": "acogida", "fecha_vencimiento": date(2026, 10, 1),
             "bloqueo_solicitado": False, "bloqueo_resultado": None, "bloqueo_vencimiento": None},
        ])
        p = rs.diagnosticar(_df(), solicitudes=sol, hoy=date(2026, 10, 22))
        self.assertEqual(_codigos(p), {"R-DER", "R-BLQ"})
        self.assertIn("(1)", next(x for x in p if x.codigo_regla == "R-DER").titulo)


class TestDisparadoresEIPD(unittest.TestCase):
    def test_detecta_a_y_d(self):
        t = pd.Series({**TRATAMIENTO_COMPLETO, "rat_tipo_datos_sensibles": "Salud",
                       "rat_decisiones_automatizadas_perfilamiento": "Perfilamiento"})
        self.assertEqual(rs.disparadores_eipd_detectados(t), {"a", "d"})
        self.assertEqual(rs.disparadores_eipd_detectados(pd.Series(TRATAMIENTO_COMPLETO)), set())


@unittest.skipUnless(os.getenv("LINCE_TEST_DATABASE_URL"), "Definir LINCE_TEST_DATABASE_URL (BD desechable)")
class TestRepositorioRiesgos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env = mock.patch.dict(os.environ, {"DATABASE_URL": os.environ["LINCE_TEST_DATABASE_URL"]})
        cls.env.start()
        from db.connection import get_connection
        from db.migrations import init_db
        init_db()
        conn = get_connection()
        with conn.cursor() as c:
            c.execute("INSERT INTO empresas (nombre, rut) VALUES ('Rsg A', 'TEST-RSG-A') RETURNING id")
            cls.emp_a = c.fetchone()[0]
            c.execute("INSERT INTO empresas (nombre, rut) VALUES ('Rsg B', 'TEST-RSG-B') RETURNING id")
            cls.emp_b = c.fetchone()[0]
            c.execute("INSERT INTO tratamientos (empresa_id, nombre_tratamiento) VALUES (%s, 'Clientes') RETURNING id",
                      (cls.emp_a,))
            cls.trat = c.fetchone()[0]
        conn.commit()
        conn.close()

    @classmethod
    def tearDownClass(cls):
        from db.connection import get_connection
        conn = get_connection()
        with conn.cursor() as c:
            c.execute("DELETE FROM empresas WHERE id IN (%s, %s)", (cls.emp_a, cls.emp_b))
        conn.commit()
        conn.close()
        cls.env.stop()

    def test_registro_en_lote_sin_duplicados(self):
        from db.repositories.riesgos import get_riesgos_df, registrar_propuestos
        from db.repositories.tratamientos import get_tratamientos_df
        propuestos = rs.diagnosticar(get_tratamientos_df(empresa_id=self.emp_a))
        self.assertTrue(propuestos)
        ok, msg = registrar_propuestos(self.emp_a, propuestos)
        self.assertTrue(ok, msg)
        n = len(get_riesgos_df(empresa_id=self.emp_a))
        ok, msg = registrar_propuestos(self.emp_a, propuestos)
        self.assertIn("ya estaban registrados", msg)
        self.assertEqual(len(get_riesgos_df(empresa_id=self.emp_a)), n)

    def test_escala_restringida_en_bd(self):
        from db.repositories.riesgos import crear_riesgo
        ok, _ = crear_riesgo(self.emp_a, "Fuera de escala", 6, 3)
        self.assertFalse(ok, "CHECK debe rechazar probabilidad 6")

    def test_aislamiento_entre_empresas(self):
        from db.repositories.riesgos import actualizar_riesgo, crear_riesgo, get_riesgos_df
        crear_riesgo(self.emp_a, "Riesgo de A", 3, 3)
        rid = int(get_riesgos_df(empresa_id=self.emp_a).query("titulo == 'Riesgo de A'").iloc[0]["id"])
        ok, _ = actualizar_riesgo(rid, self.emp_b, 1, 1, "", None, None, "aceptar", "", "", None, "cerrado", None)
        self.assertFalse(ok)
        ok, _ = actualizar_riesgo(rid, self.emp_a, 2, 3, "Control X", 1, 3, "mitigar", "Plan", "DPO",
                                  date(2026, 12, 15), "en_tratamiento", None)
        self.assertTrue(ok)

    def test_eipd_aprobada_exige_contenido_minimo(self):
        from db.repositories.riesgos import get_eipd_df, guardar_eipd
        ok, _ = guardar_eipd(self.emp_a, self.trat, {"d"}, "", "", "", "", "riesgo_aceptable", False,
                             "aprobada", "", None)
        self.assertFalse(ok)
        ok, msg = guardar_eipd(self.emp_a, self.trat, {"d"}, "Operaciones", "Finalidad", "Necesaria",
                               "Cifrado y control de acceso", "riesgo_aceptable", False, "aprobada", "DPO", None)
        self.assertTrue(ok, msg)
        e = get_eipd_df(empresa_id=self.emp_a).iloc[0]
        self.assertTrue(e["disparador_d"])
        self.assertFalse(e["disparador_a"])


if __name__ == "__main__":
    unittest.main()
