import json
import os
from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QFormLayout, QComboBox, QLabel, QCheckBox, QPushButton
)
from PyQt6.QtCore import Qt


class SettingsDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Settings", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)

        self.config_path = os.path.join("data", "config.json")
        os.makedirs("data", exist_ok=True)
        self.config = self.load_config()

        container = QWidget()
        layout = QFormLayout()

        # Theme selector
        self.theme_box = QComboBox()
        self.theme_box.addItems(["Light", "Dark"])
        layout.addRow(QLabel("Theme:"), self.theme_box)

        self.showGraph = QCheckBox()
        self.showGraph.setText("Show Graph Dock by Default ")

        if self.config.get("showGraph") == "false":
            self.showGraph.setChecked(False)
        else:
            self.showGraph.setChecked(True)

        layout.addRow(self.showGraph)

        self.apply_button = QPushButton("Apply Settings")
        layout.addRow(self.apply_button)

        container.setLayout(layout)
        self.setWidget(container)

        # Restore saved settings
        self.apply_config()

        # Connect to slots
        self.theme_box.currentIndexChanged.connect(self.on_theme_changed)

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        return {
            "theme": "Dark",
            "showGraph": "false"
        }

    def save_config(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)

    def apply_config(self):
        self.theme_box.setCurrentText(self.config.get("theme", "Dark"))
        self.theme_box.setCurrentText(self.config.get("showGraph", "false"))


    # Slots
    def on_theme_changed(self, index):
        self.config["theme"] = self.theme_box.currentText()
        self.save_config()
        print(f"Theme selected: {self.config['theme']}")
