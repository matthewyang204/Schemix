import json
import os

import requests
from PyQt6.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QListWidget, QListWidgetItem, QComboBox, QTextEdit, QScrollArea)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class ElementDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Periodic Table", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetClosable)

        self.main_widget = QWidget()
        self.setWidget(self.main_widget)

        self.layout = QVBoxLayout(self.main_widget)

        self.setStyleSheet("""
            QDockWidget {
                font-family: "Segoe UI", sans-serif;
                font-size: 14px;
            }

            QLineEdit, QComboBox {
                padding: 4px 6px;
                font-size: 14px;
            }

            QListWidget {
                border: 1px solid #ccc;
                padding: 4px;
                font-size: 13px;
                border-radius: 10px;
            }

            QTextEdit {
                background-color: #121212;
                border: 1px solid #ccc;
                padding: 10px;
                font-size: 13px;
                border-radius: 10px;
            }

            QTextEdit h2 {
                color: #004d99;
                margin-bottom: 8px;
            }

            QTextEdit p {
                margin: 4px 0;
            }

            QTextEdit b {
                color: #333;
            }

            QTextEdit i {
                color: #666;
            }

            QComboBox, QLineEdit {
                border: 1px solid #bbb;
                border-radius: 4px;
            }
        """)

        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search by name or symbol")
        self.search_bar.textChanged.connect(self.update_list)
        self.layout.addWidget(self.search_bar)

        # Filter by Category
        self.category_filter = QComboBox()
        self.category_filter.addItem("All")
        self.layout.addWidget(self.category_filter)
        self.category_filter.currentTextChanged.connect(self.update_list)

        # Element List
        self.element_list = QListWidget()
        self.element_list.currentItemChanged.connect(self.display_element_info)
        self.layout.addWidget(self.element_list)

        # Element Detail Viewer
        self.detail_area = QScrollArea()
        self.detail_widget = QTextEdit()
        self.detail_widget.setReadOnly(True)
        self.detail_area.setWidget(self.detail_widget)
        self.detail_area.setWidgetResizable(True)
        self.layout.addWidget(self.detail_area)

        self.elements = {}
        self.load_elements()

    def load_elements(self):
        try:
            path = os.path.join(os.path.dirname(__file__), "..", "data", "periodictable.json")
            with open(path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            element_list = raw_data["elements"]
            self.elements = {e["symbol"]: e for e in element_list}

            # Populate filter categories
            categories = set()
            for elem in element_list:
                categories.add(elem.get("category", "Unknown"))
            self.category_filter.addItems(sorted(categories))

            self.update_list()
        except Exception as e:
            self.detail_widget.setText(f"Error loading element data: {e}")

    def update_list(self):
        self.element_list.clear()
        search = self.search_bar.text().lower()
        category = self.category_filter.currentText()

        for symbol, elem in sorted(self.elements.items(), key=lambda x: x[1]['number']):
            name = elem['name'].lower()
            symbol_lower = symbol.lower()
            match = search in name or search in symbol_lower
            category_match = category == "All" or elem.get("category") == category

            if match and category_match:
                item = QListWidgetItem(f"{symbol} - {elem['name']}")
                item.setData(Qt.ItemDataRole.UserRole, symbol)
                self.element_list.addItem(item)

    def display_element_info(self, current, previous):
        if not current:
            self.detail_widget.clear()
            return

        symbol = current.data(Qt.ItemDataRole.UserRole)
        elem = self.elements.get(symbol, {})

        def format_field(key, value):
            if isinstance(value, list):
                return f"<p><b>{key}:</b> {', '.join(map(str, value))}</p>"
            elif isinstance(value, dict):
                subfields = "<br>".join([f"&nbsp;&nbsp;<i>{k}:</i> {v}" for k, v in value.items()])
                return f"<p><b>{key}:</b><br>{subfields}</p>"
            else:
                return f"<p><b>{key}:</b> {value}</p>"

        html = f"""
        <h2>{elem.get('name')} ({symbol})</h2>
        """

        for key, value in elem.items():
            if key not in ["bohr_model_image", "bohr_model_3d"]:
                html += format_field(key.replace('_', ' ').capitalize(), value)

        self.detail_widget.setHtml(html)
