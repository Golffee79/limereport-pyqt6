import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from limereport_pyqt6 import ReportEngine

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "smoke.lrxml"
ORIGINAL = HERE.parent / "vendor" / "LimeReport" / "demo_r1" / "demo_reports" / "change_alignment.lrxml"
TITLE = "SmokeTitleXy9"
ITEMS = [{"name": "AppleQz8", "qty": 3}, {"name": "PearWv7", "qty": 11}]


def current_error(engine):
    value = engine.last_error
    return value() if callable(value) else value


def pdf_text(path):
    from PyQt6.QtPdf import QPdfDocument
    document = QPdfDocument(None)
    document.load(str(path))
    parts = []
    for page in range(document.pageCount()):
        selection = document.getAllText(page)
        parts.append(selection.text() if hasattr(selection, "text") else str(selection))
    return "".join("".join(parts).split())


def export_text(engine, tmp):
    target = Path(tmp) / "out.pdf"
    assert engine.export_pdf(str(target)) is True
    return pdf_text(str(target))


class Smoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtGui import QFontDatabase
        cls.app = QApplication.instance() or QApplication([])
        font_id = QFontDatabase.addApplicationFont(str(HERE / "fonts" / "DejaVuSans.ttf"))
        assert font_id >= 0, "bundled test font failed to load"

    def make_engine(self):
        engine = ReportEngine()
        self.assertIsInstance(current_error(engine), str)
        return engine

    def test_original_snippet(self):
        engine = self.make_engine()
        self.assertIs(engine.load_from_file(str(ORIGINAL)), True)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "smoke.pdf"
            self.assertIs(engine.export_pdf(str(target)), True)
            self.assertTrue(target.read_bytes().startswith(b"%PDF"))

    def test_title_and_items_appear_in_pdf(self):
        engine = self.make_engine()
        self.assertIs(engine.load_from_file(str(FIXTURE)), True)
        engine.set_variable("title", TITLE)
        engine.set_data("items", [dict(row) for row in ITEMS])
        with tempfile.TemporaryDirectory() as tmp:
            text = export_text(engine, tmp)
        self.assertIn(TITLE, text)
        for row in ITEMS:
            self.assertIn(row["name"], text)
            self.assertIn(str(row["qty"]), text)

    def test_replacement_data_changes_pdf(self):
        engine = self.make_engine()
        self.assertIs(engine.load_from_file(str(FIXTURE)), True)
        engine.set_variable("title", "FirstTitleA1")
        engine.set_data("items", [{"name": "FirstItemB2", "qty": 1}])
        with tempfile.TemporaryDirectory() as tmp:
            first = export_text(engine, tmp)
            engine.set_variable("title", "SecondTitleC3")
            engine.set_data("items", [{"name": "SecondItemD4", "qty": 2}])
            second = export_text(engine, tmp)
        self.assertIn("FirstTitleA1", first)
        self.assertIn("SecondTitleC3", second)
        self.assertNotIn("SecondTitleC3", first)
        self.assertNotIn("FirstItemB2", second)

    def test_set_variable_values(self):
        engine = self.make_engine()
        self.assertIs(engine.load_from_file(str(FIXTURE)), True)
        for value in (None, True, False, 0, -5, 2**63 - 1, -2**63, 0.0, -1.5, "", "hello"):
            engine.set_variable("title", value)
        engine.set_variable("title", TITLE)
        engine.set_data("items", [dict(row) for row in ITEMS])
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIn(TITLE, export_text(engine, tmp))

    def test_set_variable_rejects(self):
        engine = self.make_engine()
        for bad in (["x"], {"x": 1}, ("x",), {"x"}, object(), b"x"):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    engine.set_variable("title", bad)
        for bad in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(bad=bad):
                with self.assertRaises((TypeError, ValueError)):
                    engine.set_variable("title", bad)
        for bad in (2**63, -2**63 - 1):
            with self.subTest(bad=bad):
                with self.assertRaises((TypeError, ValueError, OverflowError)):
                    engine.set_variable("title", bad)
        with self.assertRaises(ValueError):
            engine.set_variable("", "x")
        for bad in (None, 123, b"x", ["x"]):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    engine.set_variable(bad, "x")

    def test_set_data_shapes(self):
        engine = self.make_engine()
        self.assertIs(engine.load_from_file(str(FIXTURE)), True)
        engine.set_data("items", [dict(row) for row in ITEMS])
        engine.set_data("items", [["AppleQz8", 3], ["PearWv7", 11]], ["name", "qty"])
        engine.set_data("items", [("AppleQz8", 3)], ("name", "qty"))
        engine.set_data("items", [], ["name", "qty"])
        engine.set_variable("title", TITLE)
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIs(engine.export_pdf(str(Path(tmp) / "o.pdf")), True)

    def test_export_pdf_progress_callback(self):
        engine = self.make_engine()
        self.assertIs(engine.load_from_file(str(FIXTURE)), True)
        engine.set_variable("title", TITLE)
        engine.set_data("items", [dict(row) for row in ITEMS])
        seen = []
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIs(
                engine.export_pdf(str(Path(tmp) / "o.pdf"), seen.append), True)
        self.assertTrue(seen)
        self.assertTrue(all(isinstance(page, int) for page in seen))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(TypeError):
                engine.export_pdf(str(Path(tmp) / "o.pdf"), 123)

    def test_set_data_rejects(self):
        engine = self.make_engine()
        good = [dict(row) for row in ITEMS]
        with self.assertRaises(ValueError):
            engine.set_data("items", [{"name": "a"}, {"name": "b", "qty": 1}])
        with self.assertRaises((TypeError, ValueError)):
            engine.set_data("items", [["a", 1]])
        with self.assertRaises((TypeError, ValueError)):
            engine.set_data("items", [])
        with self.assertRaises(ValueError):
            engine.set_data("items", [], [])
        with self.assertRaises(ValueError):
            engine.set_data("items", [], ["name", "name"])
        with self.assertRaises(ValueError):
            engine.set_data("items", [], ["", "qty"])
        with self.assertRaises(TypeError):
            engine.set_data("items", [], ["name", 1])
        with self.assertRaises(ValueError):
            engine.set_data("items", [["a", 1, 2]], ["name", "qty"])
        with self.assertRaises(ValueError):
            engine.set_data("", good)
        for bad in (None, 123, b"items"):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    engine.set_data(bad, good)
        for bad in (None, "x", {"name": "a"}, {"rows": good}):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    engine.set_data("items", bad)
        with self.assertRaises(TypeError):
            engine.set_data("items", good, "name")
        self.assertIs(engine.load_from_file(str(FIXTURE)), True)
        engine.set_variable("title", TITLE)
        engine.set_data("items", good)
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIs(engine.export_pdf(str(Path(tmp) / "o.pdf")), True)

    def test_failed_calls_keep_previous_data(self):
        engine = self.make_engine()
        self.assertIs(engine.load_from_file(str(FIXTURE)), True)
        engine.set_variable("title", TITLE)
        engine.set_data("items", [dict(row) for row in ITEMS])
        with tempfile.TemporaryDirectory() as tmp:
            before = export_text(engine, tmp)
            with self.assertRaises(TypeError):
                engine.set_variable("title", {"bad": True})
            with self.assertRaises((TypeError, ValueError)):
                engine.set_data("items", [])
            with self.assertRaises(ValueError):
                engine.set_data("items", [{"name": "a"}, {"other": 1}])
            after = export_text(engine, tmp)
        self.assertIn(TITLE, before)
        self.assertIn(TITLE, after)
        for row in ITEMS:
            self.assertIn(row["name"], after)

    def test_path_validation(self):
        engine = self.make_engine()
        for method in ("load_from_file", "save_to_file", "export_pdf"):
            with self.subTest(method=method):
                with self.assertRaises(ValueError):
                    getattr(engine, method)("")
                for bad in (None, 123, b"x", Path("x")):
                    with self.assertRaises(TypeError):
                        getattr(engine, method)(bad)

    def test_missing_file_and_unloaded_export(self):
        engine = self.make_engine()
        try:
            result = engine.load_from_file(str(HERE / "does-not-exist.lrxml"))
            self.assertIs(result, False)
        except RuntimeError:
            pass
        fresh = self.make_engine()
        with tempfile.TemporaryDirectory() as tmp:
            try:
                result = fresh.export_pdf(str(Path(tmp) / "o.pdf"))
                self.assertIs(result, False)
            except RuntimeError:
                pass

    def test_save_roundtrip(self):
        engine = self.make_engine()
        self.assertIs(engine.load_from_file(str(FIXTURE)), True)
        with tempfile.TemporaryDirectory() as tmp:
            saved = str(Path(tmp) / "saved.lrxml")
            self.assertIs(engine.save_to_file(saved), True)
            other = self.make_engine()
            self.assertIs(other.load_from_file(saved), True)
            other.set_variable("title", TITLE)
            other.set_data("items", [dict(row) for row in ITEMS])
            text = export_text(other, tmp)
        self.assertIn(TITLE, text)

if __name__ == "__main__":
    unittest.main(verbosity=2)
