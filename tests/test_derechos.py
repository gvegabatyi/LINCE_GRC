"""
Pruebas del módulo Derechos de los Titulares.

- Unitarias (sin BD): router temporal, días hábiles, feriados, prórroga, estándar dual.
- Integración (LINCE_TEST_DATABASE_URL, BD desechable): repositorio, reglas de negocio
  y aislamiento entre empresas.
"""

import os
import unittest
from datetime import date
from unittest import mock

from services import plazos_service as plazos


class TestRouterTemporal(unittest.TestCase):
    def test_limite_de_vigencia(self):
        self.assertEqual(plazos.regimen_aplicable(date(2026, 11, 30)), plazos.REGIMEN_19628)
        self.assertEqual(plazos.regimen_aplicable(date(2026, 12, 1)), plazos.REGIMEN_21719)

    def test_prorroga_solo_en_21719(self):
        self.assertFalse(plazos.admite_prorroga(plazos.REGIMEN_19628))
        self.assertTrue(plazos.admite_prorroga(plazos.REGIMEN_21719))
        with self.assertRaises(ValueError):
            plazos.calcular_vencimiento(date(2026, 11, 2), prorrogada=True)


class TestPlazos19628(unittest.TestCase):
    def test_dos_dias_habiles_sabado_habil(self):
        # Jueves 26-11-2026: viernes 27 (1), sábado 28 (2)
        self.assertEqual(plazos.calcular_vencimiento(date(2026, 11, 26), sabado_habil=True), date(2026, 11, 28))

    def test_dos_dias_habiles_sabado_inhabil(self):
        # Jueves 26-11-2026: viernes 27 (1), lunes 30 (2)
        self.assertEqual(plazos.calcular_vencimiento(date(2026, 11, 26), sabado_habil=False), date(2026, 11, 30))

    def test_feriados_patrios(self):
        # Jueves 17-09-2026: 18 y 19 feriados, domingo 20; lunes 21 (1), martes 22 (2)
        self.assertEqual(plazos.calcular_vencimiento(date(2026, 9, 17), sabado_habil=True), date(2026, 9, 22))

    def test_criterio_configurable_por_entorno(self):
        with mock.patch.dict(os.environ, {"LINCE_SABADO_HABIL": "false"}):
            self.assertFalse(plazos.sabado_es_habil())
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertTrue(plazos.sabado_es_habil())  # conservador por defecto


class TestPlazos21719(unittest.TestCase):
    def test_treinta_dias_corridos(self):
        self.assertEqual(plazos.calcular_vencimiento(date(2026, 12, 1)), date(2026, 12, 31))

    def test_prorroga_unica_treinta_dias(self):
        self.assertEqual(plazos.calcular_vencimiento(date(2026, 12, 1), prorrogada=True), date(2027, 1, 30))

    def test_bloqueo_dos_dias_habiles(self):
        # Jueves 03-12-2026: viernes 4 (1), sábado 5 (2)
        self.assertEqual(plazos.calcular_vencimiento_bloqueo(date(2026, 12, 3), sabado_habil=True), date(2026, 12, 5))


class TestEstandarDual(unittest.TestCase):
    def test_referencia_21719_para_solicitudes_actuales(self):
        self.assertEqual(plazos.vencimiento_referencia_21719(date(2026, 10, 22)), date(2026, 11, 21))

    def test_sin_referencia_cuando_ya_rige_21719(self):
        self.assertIsNone(plazos.vencimiento_referencia_21719(date(2026, 12, 2)))


class TestEstadoPlazo(unittest.TestCase):
    def test_estados(self):
        hoy = date(2026, 12, 20)
        r21 = plazos.REGIMEN_21719
        self.assertEqual(plazos.estado_plazo("denegada", date(2026, 12, 1), r21, hoy).codigo, "respondida")
        self.assertEqual(plazos.estado_plazo("recibida", date(2026, 12, 19), r21, hoy).codigo, "vencida")
        self.assertEqual(plazos.estado_plazo("recibida", date(2026, 12, 25), r21, hoy).codigo, "por_vencer")
        self.assertEqual(plazos.estado_plazo("recibida", date(2026, 12, 31), r21, hoy).codigo, "en_plazo")
        r19 = plazos.REGIMEN_19628
        self.assertEqual(plazos.estado_plazo("en_analisis", date(2026, 12, 21), r19, hoy).codigo, "por_vencer")


@unittest.skipUnless(os.getenv("LINCE_TEST_DATABASE_URL"), "Definir LINCE_TEST_DATABASE_URL (BD desechable)")
class TestRepositorioDerechos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env = mock.patch.dict(os.environ, {"DATABASE_URL": os.environ["LINCE_TEST_DATABASE_URL"]})
        cls.env.start()
        from db.migrations import init_db
        init_db()
        from db.connection import get_connection
        conn = get_connection()
        with conn.cursor() as c:
            c.execute("INSERT INTO empresas (nombre, rut) VALUES ('Der A', 'TEST-DER-A') RETURNING id")
            cls.emp_a = c.fetchone()[0]
            c.execute("INSERT INTO empresas (nombre, rut) VALUES ('Der B', 'TEST-DER-B') RETURNING id")
            cls.emp_b = c.fetchone()[0]
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

    def _crear(self, fecha, **extra):
        from db.repositories.derechos import crear_solicitud, get_solicitudes_df
        ok, msg = crear_solicitud(self.emp_a, extra.pop("derecho", "acceso"), fecha, "Titular Prueba",
                                  titular_contacto="titular@ejemplo.cl", **extra)
        self.assertTrue(ok, msg)
        df = get_solicitudes_df(empresa_id=self.emp_a)
        return df[df["folio"] == msg.split()[1]].iloc[0]

    def test_crea_con_regimen_y_vencimiento(self):
        s19 = self._crear(date(2026, 11, 26))
        self.assertEqual(s19["regimen"], plazos.REGIMEN_19628)
        self.assertTrue(s19["folio"].startswith("SD-2026-"))
        s21 = self._crear(date(2026, 12, 1))
        self.assertEqual(s21["regimen"], plazos.REGIMEN_21719)
        self.assertEqual(str(s21["fecha_vencimiento"])[:10], "2026-12-31")

    def test_prorroga(self):
        from db.repositories.derechos import get_solicitudes_df, prorrogar_solicitud
        s19 = self._crear(date(2026, 11, 26))
        ok, _ = prorrogar_solicitud(int(s19["id"]), self.emp_a, date(2026, 11, 26), "motivo")
        self.assertFalse(ok)
        s21 = self._crear(date(2026, 12, 1))
        ok, msg = prorrogar_solicitud(int(s21["id"]), self.emp_a, date(2026, 12, 1), "Complejidad del requerimiento")
        self.assertTrue(ok, msg)
        ok, _ = prorrogar_solicitud(int(s21["id"]), self.emp_a, date(2026, 12, 1), "segunda")
        self.assertFalse(ok, "la prórroga sólo procede una vez")
        df = get_solicitudes_df(empresa_id=self.emp_a)
        self.assertEqual(str(df[df["id"] == s21["id"]].iloc[0]["fecha_vencimiento"])[:10], "2027-01-30")

    def test_denegacion_exige_fundamento(self):
        from db.repositories.derechos import registrar_respuesta
        s = self._crear(date(2026, 12, 2))
        ok, _ = registrar_respuesta(int(s["id"]), self.emp_a, "denegada", date(2026, 12, 5), "correo")
        self.assertFalse(ok)
        ok, msg = registrar_respuesta(int(s["id"]), self.emp_a, "denegada", date(2026, 12, 5), "correo",
                                      "Causal legal y antecedentes")
        self.assertTrue(ok, msg)

    def test_aislamiento_entre_empresas(self):
        from db.repositories.derechos import get_solicitudes_df, registrar_acuse
        s = self._crear(date(2026, 12, 3), derecho="supresion", bloqueo_solicitado=True)
        self.assertEqual(str(s["bloqueo_vencimiento"])[:10], "2026-12-05")
        ok, _ = registrar_acuse(int(s["id"]), self.emp_b, date(2026, 12, 4))
        self.assertFalse(ok, "otra empresa no debe poder modificar la solicitud")
        self.assertTrue(get_solicitudes_df(empresa_id=self.emp_b).empty)
        ok, _ = registrar_acuse(int(s["id"]), self.emp_a, date(2026, 12, 4))
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
