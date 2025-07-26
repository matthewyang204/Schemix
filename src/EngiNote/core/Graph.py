from io import BytesIO

import numpy as np
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QVBoxLayout, QWidget, QPushButton
)
from asteval import Interpreter
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class GraphWidget(QWidget):
    add_to_note_requested = pyqtSignal(QPixmap)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(5, 3), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.axes = self.figure.add_subplot(111)
        self.add_button = QPushButton("➕ Add to Note")
        self.add_button.clicked.connect(self.request_add_to_note)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.add_button)
        self.setLayout(layout)
        self.aeval = Interpreter()
        self.show_placeholder_message()

    def show_placeholder_message(self):
        self.axes.clear()
        self.axes.text(0.5, 0.5, 'Select a function in the editor,\nright-click, and choose\n"Graph Function"',
                       horizontalalignment='center', verticalalignment='center',
                       transform=self.axes.transAxes, fontsize=10, color='gray')
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        self.add_button.setEnabled(False)
        self.canvas.draw()

    def plot_function(self, expression):
        self.axes.clear()
        try:
            x = np.linspace(-10, 10, 500)
            self.aeval.symtable['x'] = x
            y = self.aeval.eval(expression)
            self.axes.plot(x, y)
            self.axes.set_title(f"f(x) = {expression}", size=10)
            self.axes.set_xlabel("x")
            self.axes.set_ylabel("f(x)")
            self.axes.grid(True)
            self.add_button.setEnabled(True)
        except Exception as e:
            self.axes.text(0.5, 0.5, 'Invalid Function',
                           horizontalalignment='center', verticalalignment='center',
                           transform=self.axes.transAxes, fontsize=12, color='red')
            self.axes.set_xticks([])
            self.axes.set_yticks([])
            self.add_button.setEnabled(False)
            print(f"Graphing Error: {e}")
        self.figure.tight_layout()
        self.canvas.draw()

    def request_add_to_note(self):
        buf = BytesIO()
        self.figure.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue(), 'PNG')
        if not pixmap.isNull():
            self.add_to_note_requested.emit(pixmap)
