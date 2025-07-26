from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QFormLayout, QComboBox, QLabel, QVBoxLayout
)
from PyQt6.QtCore import Qt


class SettingsDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Settings", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)

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

        # Optional: Connect to slots if needed
        self.theme_box.currentIndexChanged.connect(self.on_theme_changed)
        self.distance_box.currentIndexChanged.connect(self.on_distance_changed)
        self.speed_box.currentIndexChanged.connect(self.on_speed_changed)
        self.volume_box.currentIndexChanged.connect(self.on_volume_changed)
        self.mass_box.currentIndexChanged.connect(self.on_mass_changed)
        self.time_box.currentIndexChanged.connect(self.on_time_changed)

    # Placeholder methods
    def on_theme_changed(self, index):
        selected = self.theme_box.currentText()
        print(f"Theme selected: {selected}")

    def on_distance_changed(self, index):
        print(f"Distance unit: {self.distance_box.currentText()}")

    def on_speed_changed(self, index):
        print(f"Speed unit: {self.speed_box.currentText()}")

    def on_volume_changed(self, index):
        print(f"Volume unit: {self.volume_box.currentText()}")

    def on_mass_changed(self, index):
        print(f"Mass unit: {self.mass_box.currentText()}")

    def on_time_changed(self, index):
        print(f"Time unit: {self.time_box.currentText()}")
