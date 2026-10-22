"""
Pruebas del addon normativo (citas, filtro de datos personales, copiloto).

Ejecutar desde la raíz del proyecto:
    python -m unittest discover -s tests -t .
No requieren base de datos, red ni el paquete anthropic.
"""

import ast
import filecmp
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from addons.normativa import citas, copiloto, pii_filter

RAIZ = Path(__file__).resolve().parents[1]
ADDON = RAIZ / "addons" / "normativa"


class TestCorpus(unittest.TestCase):
    def test_normas_cargadas(self):
        codigos = {n["codigo"] for n in citas.listar_normas()}
        self.assertEqual(codigos, {"LEY-19628", "LEY-21719", "LEY-21663", "DEC-662-HAC"})

    def test_decreto_completo(self):
        arts = [a["articulo"] for a in citas.cargar_corpus()["DEC-662-HAC"]["articulos"]]
        self.assertEqual(arts, [str(i) for i in range(1, 21)])

    def test_articulo_literal(self):
        (c,) = citas.obtener_articulo("LEY-21719", "14 sexies")
        self.assertIn("sin dilaciones indebidas", c["texto"])

    def test_variantes_de_numeracion(self):
        for entrada in ("Art. 14 Sexies", "artículo 14 sexies", "14 sexies"):
            self.assertTrue(citas.obtener_articulo("LEY-21719", entrada), entrada)
        self.assertTrue(citas.obtener_articulo("LEY-21719", "8° bis"))

    def test_articulo_2_via_modificaciones(self):
        textos = " ".join(c["texto"] for c in citas.obtener_articulo("LEY-21719", "2"))
        self.assertIn("identidad de género", textos)

    def test_transitorios_separados(self):
        (c,) = citas.obtener_articulo("LEY-21719", "sexto transitorio")
        self.assertIn("amonestación por escrito", c["texto"])
        # El artículo "primero" permanente no se confunde con el transitorio
        (p,) = citas.obtener_articulo("LEY-21719", "primero transitorio")
        self.assertIn("vigésimo cuarto", p["texto"])

    def test_sin_respaldo(self):
        self.assertEqual(citas.obtener_articulo("LEY-21719", "999"), [])
        self.assertEqual(citas.obtener_articulo("NO-EXISTE", "1"), [])

    def test_busqueda_relevante(self):
        casos = {
            "plazo para reportar una vulneración de seguridad a la Agencia de Protección de Datos": ("LEY-21719", "14 sexies"),
            "requisitos del delegado de protección de datos": ("DEC-662-HAC", "10"),
            "incidente CSIRT alerta temprana horas": ("LEY-21663", "9"),
            "multa infracción gravísima UTM": ("LEY-21719", "35"),
        }
        for consulta, (norma, art) in casos.items():
            top = [(c["norma"], c["articulo"]) for c in citas.buscar(consulta, k=3)]
            self.assertIn((norma, art), top, consulta)

    def test_referencias_explicitas(self):
        refs = {(c["norma"], c["articulo"]) for c in citas.referencias_explicitas("¿Qué exige el art. 14 sexies de la ley 21.719?")}
        self.assertIn(("LEY-21719", "14 sexies"), refs)
        refs = {(c["norma"], c["articulo"]) for c in citas.referencias_explicitas("artículo 13 del DS 662")}
        self.assertEqual(refs, {("DEC-662-HAC", "13")})

    def test_router_temporal(self):
        self.assertIn("readiness", citas.regimen_temporal("LEY-21719", date(2026, 10, 22)))
        self.assertIn("exigible desde", citas.regimen_temporal("DEC-662-HAC", date(2026, 12, 1)))
        self.assertIn("hasta el 30-11-2026", citas.regimen_temporal("LEY-19628", date(2026, 11, 30)))


class TestFiltroDatosPersonales(unittest.TestCase):
    def test_detecta_identificadores(self):
        self.assertIn("RUT", pii_filter.detectar("El titular 12.345.678-9 pidió acceso"))
        self.assertIn("RUT", pii_filter.detectar("rut 12345678-K"))
        self.assertIn("correo electrónico", pii_filter.detectar("escribió desde ana.perez@empresa.cl"))
        self.assertIn("teléfono", pii_filter.detectar("llamar al +56 9 8765 4321"))

    def test_consulta_normativa_pasa(self):
        for q in ("¿Qué dice el art. 14 sexies?", "multa de 20.000 UTM", "plazo de 30 días corridos", "Ley 21.719"):
            self.assertEqual(pii_filter.detectar(q), [], q)

    def test_enmascarar(self):
        self.assertEqual(pii_filter.enmascarar("RUT 12.345.678-9"), "RUT [RUT]")


class TestCopiloto(unittest.TestCase):
    def test_desactivado_por_defecto(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            cfg = copiloto.configuracion()
            self.assertFalse(cfg.activo)
            self.assertIn("desactivado", copiloto.responder("¿Qué es un dato sensible?").texto)

    def test_proveedor_invalido_queda_desactivado(self):
        with mock.patch.dict("os.environ", {"LINCE_COPILOTO_PROVEEDOR": "openai"}, clear=True):
            self.assertEqual(copiloto.configuracion().proveedor, "desactivado")

    def test_modelo_por_defecto(self):
        with mock.patch.dict("os.environ", {"LINCE_COPILOTO_PROVEEDOR": "anthropic"}, clear=True):
            self.assertEqual(copiloto.configuracion().modelo, "claude-opus-5-5")

    def test_bloquea_datos_personales_sin_llamar_al_proveedor(self):
        cfg = copiloto.Configuracion("anthropic", "claude-opus-5-5", "")
        with mock.patch.dict(copiloto._LLAMADAS, {"anthropic": mock.Mock()}) as llamadas:
            resp = copiloto.responder("¿Puedo tratar los datos de 12.345.678-9?", cfg=cfg)
            llamadas["anthropic"].assert_not_called()
        self.assertTrue(resp.bloqueada)

    def test_consulta_lleva_articulos_y_fecha(self):
        cfg = copiloto.Configuracion("ollama", "llama3.1", "http://localhost:11434")
        falso = mock.Mock(return_value="respuesta")
        with mock.patch.dict(copiloto._LLAMADAS, {"ollama": falso}):
            resp = copiloto.responder("¿Cuándo se reporta una vulneración a la Agencia según el art. 14 sexies?", cfg=cfg)
        consulta = falso.call_args.args[1]
        self.assertIn("<articulos>", consulta)
        self.assertIn("Artículo 14 sexies", consulta)
        self.assertIn("Fecha de hoy:", consulta)
        self.assertEqual(resp.texto, "respuesta")
        self.assertTrue(any(c["articulo"] == "14 sexies" for c in resp.citas))

    def test_base_conocimiento_incluye_ds662(self):
        self.assertIn("decreto-662-mpi.md", copiloto.base_conocimiento())


class TestSegregacion(unittest.TestCase):
    PROHIBIDOS = {"db", "psycopg2", "modules", "services"}

    def test_addon_no_importa_base_de_datos(self):
        for ruta in ADDON.glob("*.py"):
            arbol = ast.parse(ruta.read_text(encoding="utf-8"))
            for nodo in ast.walk(arbol):
                if isinstance(nodo, ast.Import):
                    raices = {a.name.split(".")[0] for a in nodo.names}
                elif isinstance(nodo, ast.ImportFrom) and nodo.module:
                    raices = {nodo.module.split(".")[0]}
                else:
                    continue
                self.assertFalse(raices & self.PROHIBIDOS, f"{ruta.name} importa {raices & self.PROHIBIDOS}")

    def test_conocimiento_sincronizado_con_skill(self):
        skill = RAIZ / ".claude" / "skills" / "proteccion-datos-chile"
        if not skill.exists():
            self.skipTest("Skill no disponible en esta instalación")
        for copia in (ADDON / "conocimiento").rglob("*"):
            if copia.is_file():
                original = skill / copia.relative_to(ADDON / "conocimiento")
                self.assertTrue(filecmp.cmp(copia, original, shallow=False),
                                f"{copia.name} desfasado: ejecutar addons/normativa/tools/sync_conocimiento.py")


if __name__ == "__main__":
    unittest.main()
