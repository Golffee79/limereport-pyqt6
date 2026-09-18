import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from limereport_pyqt6 import ReportEngine

root = Path(__file__).resolve().parent.parent
fixture = root / "tests" / "smoke.lrxml"

app = QApplication(sys.argv)
engine = ReportEngine()
if fixture.exists():
    engine.load_from_file(str(fixture))
engine.design()
result = app.exec()
del engine
sys.exit(result)
