from PyQt6.QtWidgets import QApplication, QTextEdit, QMainWindow
from PyQt6.QtCore import Qt
import sys
import re
from pint import UnitRegistry

ureg = UnitRegistry()

UNIT_PATTERN = re.compile(r"\b(\d+(?:\.\d+)?)\s?(km/h|m/s|kg|g|L|ml|N|km|m|cm|mm|ft|in|lb|gal)\b", re.IGNORECASE)

class UnitNoteEditor(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setPlaceholderText("Type something like 'The speed was 72 km/h' and press Ctrl+Shift+U to convert.")

    def keyPressEvent(self, event):
        if event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier) and event.key() == Qt.Key.Key_U:
            self.add_converted_units()
        else:
            super().keyPressEvent(event)

    def add_converted_units(self):
        text = self.toPlainText()
        new_text = text

        matches = list(UNIT_PATTERN.finditer(text))
        offset = 0

        for match in matches:
            value, unit = match.groups()
            converted = self.convert_unit(float(value), unit.lower())

            if converted:
                insert_text = f" ({converted})"
                start = match.end() + offset
                new_text = new_text[:start] + insert_text + new_text[start:]
                offset += len(insert_text)

        self.setPlainText(new_text)

    def convert_unit(self, value, unit):
        try:
            q = None

            if unit == "km/h":
                q = value * ureg.kilometer / ureg.hour
                return f"{q.to('m/s'):.2f~P}"
            elif unit == "m/s":
                q = value * ureg.meter / ureg.second
                return f"{q.to('km/h'):.2f~P}"
            elif unit in ["kg", "g", "lb"]:
                q = value * ureg(unit)
                return f"{q.to('lb'):.2f~P}" if unit != "lb" else f"{q.to('kg'):.2f~P}"
            elif unit in ["L", "ml", "gal"]:
                q = value * ureg(unit)
                return f"{q.to('gallon'):.2f~P}" if unit != "gal" else f"{q.to('liter'):.2f~P}"
            elif unit in ["km", "m", "cm", "mm", "ft", "in"]:
                q = value * ureg(unit)
                return f"{q.to('ft'):.2f~P}" if unit != "ft" else f"{q.to('meter'):.2f~P}"
            elif unit == "n":
                q = value * ureg.newton
                return f"{q.to('kg*m/s^2'):.2f~P}"
        except:
            return None

        return None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unit Converter Demo")
        self.setGeometry(100, 100, 600, 400)
        self.editor = UnitNoteEditor()
        self.setCentralWidget(self.editor)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
