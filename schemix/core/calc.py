from PyQt6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QGridLayout, QPushButton, QLineEdit, QHBoxLayout
from PyQt6.QtCore import Qt
import math
import re


class ScientificCalculatorDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Scientific Calculator", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        self.degrees_mode = True

        self.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: #00ffcc;
                font-size: 18px;
                padding: 8px;
                border: 1px solid #333;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #2e2e2e;
                color: #eee;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)

        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(6, 6, 6, 6)

        self.display = QLineEdit()
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setReadOnly(False)
        self.display.setFixedHeight(40)
        main_layout.addWidget(self.display)

        toggle_layout = QHBoxLayout()
        self.toggle_btn = QPushButton("Mode: DEG")
        self.toggle_btn.clicked.connect(self.toggle_mode)
        toggle_layout.addWidget(self.toggle_btn)
        main_layout.addLayout(toggle_layout)

        grid = QGridLayout()
        buttons = [
            ['7', '8', '9', '/', 'sqrt', 'π'],
            ['4', '5', '6', '*', '^', 'e'],
            ['1', '2', '3', '-', '(', ')'],
            ['0', '.', '=', '+', 'C', '←'],
            ['sin', 'cos', 'tan', 'log', 'ln', 'exp'],
            ['asin', 'acos', 'atan', '!', '', '']
        ]

        for row, row_items in enumerate(buttons):
            for col, text in enumerate(row_items):
                if text:
                    btn = QPushButton(text)
                    btn.clicked.connect(self.on_button_click)
                    grid.addWidget(btn, row, col)

        main_layout.addLayout(grid)
        self.setWidget(widget)

    def toggle_mode(self):
        self.degrees_mode = not self.degrees_mode
        self.toggle_btn.setText("Mode: DEG" if self.degrees_mode else "Mode: RAD")

    def on_button_click(self):
        sender = self.sender()
        text = sender.text()
        current = self.display.text()

        try:
            if text == "=":
                expr = self.prepare_expression(current)

                # The easter eggs
                if expr == "05072025":
                    self.display.setText("I Love You Neeraja 💖")
                    return

                # Required filters
                expr = re.sub(r'\b0+([1-9][0-9]*)\b', r'\1', expr)

                # Some other specific/conditional replacements, leading straight up to results
                # Detect and replace 3.14 or 22/7 with proper π
                print(f"Replacing 3.14 and/or 22/7 with proper π: {expr}")
                expr = re.sub(r'\b(3\.14|22/7)\b', str(math.pi), expr)
                # Detect and replace standalone π or pi, which are invalid characters
                print(f"Replacing invalid characters and interpreting them: {expr}")
                expr = re.sub(r'\b(π|pi)\b', str(math.pi), expr)
                print(f"Resulting expression to evaluate: {expr}")
                result = eval(expr, {"__builtins__": None}, self.get_math_namespace())
                self.display.setText(str(result))
                print(f"Result: {expr} = {result}")
            elif text == "C":
                self.display.clear()
            elif text == "←":
                self.display.setText(current[:-1])
            elif text == "!":
                self.display.setText(current + "!")
            elif text in ['sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'log', 'ln', 'sqrt', 'exp']:
                self.display.insert(f"{text}(")
            else:
                self.display.insert(text)
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)

            self.display.setText(f"Error: {error_type}: {error_msg}")
            print(error_type + ": " + error_msg)

    def prepare_expression(self, expr):
        expr = expr.replace('π', str(math.pi)).replace('e', str(math.e)).replace('^', '**')
        expr = re.sub(r'(\d+)!', r'factorial(\1)', expr)
        expr = expr.replace('ln(', 'log(' + str(math.e) + ',')  # ln(x) → log(e,x)
        return expr

    def get_math_namespace(self):
        ns = math.__dict__.copy()
        ns["factorial"] = math.factorial
        if self.degrees_mode:
            ns.update({
                'sin': lambda x: math.sin(math.radians(x)),
                'cos': lambda x: math.cos(math.radians(x)),
                'tan': lambda x: math.tan(math.radians(x)),
                'asin': lambda x: math.degrees(math.asin(x)),
                'acos': lambda x: math.degrees(math.acos(x)),
                'atan': lambda x: math.degrees(math.atan(x)),
            })
        return ns
