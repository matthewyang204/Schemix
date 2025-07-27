import json
import os
from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QFormLayout, QComboBox, QLabel
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

        # Distance unit preference
        self.distance_box = QComboBox()
        self.distance_box.addItems(["km", "m", "cm", "mm", "mile", "ft"])
        layout.addRow(QLabel("Preferred Distance Unit:"), self.distance_box)

        # Speed unit preference
        self.speed_box = QComboBox()
        self.speed_box.addItems(["km/h", "m/s", "mph"])
        layout.addRow(QLabel("Preferred Speed Unit:"), self.speed_box)

        # Volume unit preference
        self.volume_box = QComboBox()
        self.volume_box.addItems(["L", "ml", "gallon"])
        layout.addRow(QLabel("Preferred Volume Unit:"), self.volume_box)

        # Mass unit preference
        self.mass_box = QComboBox()
        self.mass_box.addItems(["kg", "g", "lb"])
        layout.addRow(QLabel("Preferred Mass Unit:"), self.mass_box)

        # Time unit preference
        self.time_box = QComboBox()
        self.time_box.addItems(["s", "min", "hr"])
        layout.addRow(QLabel("Preferred Time Unit:"), self.time_box)

        container.setLayout(layout)
        self.setWidget(container)

        # Restore saved settings
        self.apply_config()

        # Connect to slots
        self.theme_box.currentIndexChanged.connect(self.on_theme_changed)
        self.distance_box.currentIndexChanged.connect(self.on_distance_changed)
        self.speed_box.currentIndexChanged.connect(self.on_speed_changed)
        self.volume_box.currentIndexChanged.connect(self.on_volume_changed)
        self.mass_box.currentIndexChanged.connect(self.on_mass_changed)
        self.time_box.currentIndexChanged.connect(self.on_time_changed)

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        # Defaults if no config
        return {
            "theme": "Light",
            "distance": "km",
            "speed": "km/h",
            "volume": "L",
            "mass": "kg",
            "time": "s"
        }

    def save_config(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)

    def apply_config(self):
        self.theme_box.setCurrentText(self.config.get("theme", "Light"))
        self.distance_box.setCurrentText(self.config.get("distance", "km"))
        self.speed_box.setCurrentText(self.config.get("speed", "km/h"))
        self.volume_box.setCurrentText(self.config.get("volume", "L"))
        self.mass_box.setCurrentText(self.config.get("mass", "kg"))
        self.time_box.setCurrentText(self.config.get("time", "s"))

    # Slots
    def on_theme_changed(self, index):
        self.config["theme"] = self.theme_box.currentText()
        self.save_config()
        print(f"Theme selected: {self.config['theme']}")

    def on_distance_changed(self, index):
        self.config["distance"] = self.distance_box.currentText()
        self.save_config()
        print(f"Distance unit: {self.config['distance']}")

    def on_speed_changed(self, index):
        self.config["speed"] = self.speed_box.currentText()
        self.save_config()
        print(f"Speed unit: {self.config['speed']}")

    def on_volume_changed(self, index):
        self.config["volume"] = self.volume_box.currentText()
        self.save_config()
        print(f"Volume unit: {self.config['volume']}")

    def on_mass_changed(self, index):
        self.config["mass"] = self.mass_box.currentText()
        self.save_config()
        print(f"Mass unit: {self.config['mass']}")

    def on_time_changed(self, index):
        self.config["time"] = self.time_box.currentText()
        self.save_config()
        print(f"Time unit: {self.config['time']}")
