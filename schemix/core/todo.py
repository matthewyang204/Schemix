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
