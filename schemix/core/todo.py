from PyQt6.QtWidgets import (
    QDockWidget, QListWidget, QListWidgetItem,
    QVBoxLayout, QPushButton, QWidget, QLineEdit
)
from PyQt6.QtCore import Qt
import json
import os

class ToDoDock(QDockWidget):
    def __init__(self, board_dir):
        super().__init__("To-Do List")
        self.board_dir = board_dir
        self.todo_file = os.path.join(self.board_dir, "todo.json")

        self.setStyleSheet("""
            QDockWidget {
                font-family: "Segoe UI", sans-serif;
                font-size: 14px;
                color: #f0f0f0;
                background-color: #1e1e1e;
            }

            QListWidget {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 10px;
                padding: 6px;
            }

            QListWidget::item {
                padding: 8px;
                margin: 4px;
                border-radius: 6px;
            }

            QListWidget::item:hover {
                background-color: #3a3a3a;
            }

            QListWidget::item:selected {
                background-color: #0078d7;
                color: white;
            }

            QLineEdit {
                background-color: #2c2c2c;
                color: #ffffff;
                padding: 6px 8px;
                border: 1px solid #555;
                border-radius: 6px;
                margin-top: 6px;
            }

            QPushButton {
                background-color: #0078d7;
                color: white;
                padding: 6px;
                border-radius: 6px;
                margin-top: 6px;
            }

            QPushButton:hover {
                background-color: #005fa3;
            }

            QPushButton:pressed {
                background-color: #00457c;
            }
        """)

        self.todo_list = QListWidget()
        self.input_box = QLineEdit()
        self.add_button = QPushButton("Add")

        layout = QVBoxLayout()
        layout.addWidget(self.todo_list)
        layout.addWidget(self.input_box)
        layout.addWidget(self.add_button)

        container = QWidget()
        container.setLayout(layout)
        self.setWidget(container)

        # Event bindings
        self.add_button.clicked.connect(self.add_item)
        self.input_box.returnPressed.connect(self.add_item)
        self.todo_list.itemChanged.connect(self.save_todo)

        self.load_todo()

    def add_item(self):
        text = self.input_box.text().strip()
        if text:
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEditable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.todo_list.addItem(item)
            self.input_box.clear()
            self.save_todo()

    def save_todo(self):
        items = []
        for i in range(self.todo_list.count()):
            item = self.todo_list.item(i)
            items.append({
                "text": item.text(),
                "checked": item.checkState() == Qt.CheckState.Checked
            })
        with open(self.todo_file, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)

    def load_todo(self):
        self.todo_list.clear()
        if os.path.exists(self.todo_file):
            try:
                with open(self.todo_file, "r", encoding="utf-8") as f:
                    items = json.load(f)
                    for entry in items:
                        item = QListWidgetItem(entry["text"])
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEditable)
                        state = Qt.CheckState.Checked if entry.get("checked") else Qt.CheckState.Unchecked
                        item.setCheckState(state)
                        self.todo_list.addItem(item)
            except Exception as e:
                print(f"Failed to load todo: {e}")
