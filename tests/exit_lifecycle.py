"""Catch native Qt/LimeReport crashes on interpreter exit in separate processes."""
import os
import subprocess
import sys
from pathlib import Path

fixture = Path(__file__).with_name('smoke.lrxml')
code = '''
from PyQt6.QtWidgets import QApplication
from limereport_pyqt6 import ReportEngine
app = QApplication([])
for i in range(3):
    report = ReportEngine()
    assert report.load_from_file(%r)
    report.set_variable('title', 'LifetimeTest')
    report.set_data('items', [{'name': 'Test', 'qty': 1}])
    assert report.export_pdf('/tmp/limereport-lifecycle-%%s.pdf' %% i)
    del report
app.quit()
del app
''' % str(fixture)
for attempt in range(5):
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen')
    result = subprocess.run([sys.executable, '-c', code], env=env, capture_output=True, text=True, timeout=90)
    if result.returncode:
        raise RuntimeError(f'lifecycle attempt {attempt + 1} failed ({result.returncode}): {result.stderr}')
print('PASS: 5 independent processes, 3 ReportEngine lifecycles each')
