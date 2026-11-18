import os as _os
import sys as _sys

import PyQt6 as _PyQt6

if _sys.platform == "win32":
    _os.add_dll_directory(_os.path.join(_os.path.dirname(_PyQt6.__file__), "Qt6", "bin"))

from PyQt6 import QtCore as _QtCore
from PyQt6 import QtGui as _QtGui
from PyQt6 import QtNetwork as _QtNetwork
from PyQt6 import QtPrintSupport as _QtPrintSupport
from PyQt6 import QtQml as _QtQml
from PyQt6 import QtSql as _QtSql
from PyQt6 import QtSvg as _QtSvg
from PyQt6 import QtWidgets as _QtWidgets
from PyQt6 import QtXml as _QtXml

# A Qt minor-version mismatch can corrupt memory at native extension teardown.
from ._build_qt import BUILT_QT_VERSION as _BUILT_QT_VERSION
if _QtCore.QT_VERSION_STR.split(".")[:2] != _BUILT_QT_VERSION.split(".")[:2]:
    raise RuntimeError(
        f"limereport-pyqt6 was built against Qt {_BUILT_QT_VERSION}, "
        f"but PyQt6 is running Qt {_QtCore.QT_VERSION_STR}. "
        "Use matching Qt major/minor versions or rebuild the wheel."
    )

from ._core import ReportEngine

__all__ = ["ReportEngine"]
