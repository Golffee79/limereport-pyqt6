# LimeReport PyQt6

Python bindings for [LimeReport](https://github.com/fralx/LimeReport) using
PyQt6 and Qt 6.

This project uses PyQt6. It does not require PySide6 or Shiboken6.

## Install

```bash
pip install limereport-pyqt6
```

Requirements: Python 3.10–3.13 and PyQt6 (installed automatically).

Binary wheels are provided for Windows (64-bit) and macOS (Apple
Silicon). On Linux, install from source until manylinux wheels are
available — this needs a C++ compiler, CMake, and Qt 6 development
headers:

```bash
pip install limereport-pyqt6 --no-binary limereport-pyqt6
```

## Usage

```python
from PyQt6.QtWidgets import QApplication
from limereport_pyqt6 import ReportEngine

app = QApplication([])
engine = ReportEngine()
if not engine.load_from_file("invoice.lrxml"):
    raise RuntimeError(engine.last_error())

engine.set_variable("invoice_no", "INV-001")
engine.set_data("items", [
    {"name": "Gold Ring", "qty": 1},
    {"name": "Silver Chain", "qty": 2},
])
engine.export_pdf("invoice.pdf")
```

`set_data()` accepts a list of dictionaries, or a list of lists/tuples with
explicit column names:

```python
engine.set_data("items", [["Gold Ring", 1]], ["name", "qty"])
```

Available methods: `load_from_file()`, `save_to_file()`, `set_variable()`,
`set_data()`, `export_pdf()`, `preview()`, `design()`, and `last_error()`.

Create a `QApplication` before creating `ReportEngine`. `preview()` is modal;
`design()` opens the report designer.

## Development

Building from source requires a Qt 6 SDK with development headers. Published
wheels will only require PyQt6.

## License

This project is licensed under GPL-3.0-or-later. LimeReport is distributed
under LGPL-3.0-or-later. PyQt6 is available under GPL-3.0-only or a commercial
license.
