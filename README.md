# LimeReport PyQt6

Python bindings for [LimeReport](https://github.com/fralx/LimeReport) using
PyQt6 and Qt 6.

> This project is in early development and is not ready for installation yet.

Planned usage:

```python
from limereport_pyqt6 import ReportEngine

engine = ReportEngine()
engine.load_from_file("invoice.lrxml")
engine.export_pdf("invoice.pdf")
```

## License

This project is licensed under GPL-3.0-or-later. LimeReport is distributed
under LGPL-3.0-or-later. PyQt6 is available under GPL-3.0-only or a commercial
license.
