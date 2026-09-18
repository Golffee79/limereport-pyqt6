import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from limereport_pyqt6 import ReportEngine

root = Path(__file__).resolve().parent.parent
fixture = root / "tests" / "smoke.lrxml"
target = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "basic.pdf"

app = QApplication(sys.argv)
engine = ReportEngine()
if not engine.load_from_file(str(fixture)):
    error = engine.last_error
    raise RuntimeError(error() if callable(error) else error)
engine.set_variable("title", "BasicReport")
engine.set_data("items", [{"name": "Apple", "qty": 3}, {"name": "Pear", "qty": 11}])
if not engine.export_pdf(str(target)):
    error = engine.last_error
    raise RuntimeError(error() if callable(error) else error)
print(str(target))
del engine
app.quit()
