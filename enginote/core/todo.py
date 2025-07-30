from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QVBoxLayout, QWidget, QListWidget, QDockWidget, QLineEdit, QListWidgetItem
)


class ToDoDockWidget(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("To-Do List", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)

        self.main_widget = QWidget()
        self.setWidget(self.main_widget)

        self.layout = QVBoxLayout(self.main_widget)

        self.todo_input = QLineEdit()
        self.todo_input.setPlaceholderText("Add a new task and press Enter")
        self.layout.addWidget(self.todo_input)

        self.todo_list = QListWidget()
        self.layout.addWidget(self.todo_list)

        self.todo_input.returnPressed.connect(self.add_task)
        self.todo_list.itemChanged.connect(self.task_toggled)

    def add_task(self):
        text = self.todo_input.text().strip()
        if text:
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.todo_list.addItem(item)
            self.todo_input.clear()

    def task_toggled(self, item):
        # You can add persistence or strike-through here
        pass
