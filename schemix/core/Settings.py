import json
import os
import sys
import platform
from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QFormLayout, QComboBox, QLabel, QCheckBox, QPushButton
)
from PyQt6.QtCore import Qt

DEFAULT_CONFIG = {
    "theme": "Dark",
    "showGraph": "false",
    "funcH": "true",
    "wikiSentences": "2"
}


def get_appdata_dirs():
    if platform.system() == "Windows":
        local_app_data = os.getenv('LOCALAPPDATA')
    elif platform.system() == "Linux":
        local_app_data = os.path.expanduser("~/.config")
    elif platform.system() == "Darwin":
        local_app_data = os.path.expanduser("~/Library/Application Support")
    else:
        print("Unsupported operating system")
        sys.exit(1)

    local_app_data = os.path.join(local_app_data, "Schemix")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    return local_app_data, script_dir


def get_config_path():
    local_app_data, _ = get_appdata_dirs()
    return os.path.normpath(os.path.join(local_app_data, "..", "Schemix-data", "config.json"))


def load_config():
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                return {**DEFAULT_CONFIG, **config}
        except json.JSONDecodeError:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config):
    config_path = get_config_path()
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)


class SettingsDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Settings", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)

        self.config_path = get_config_path()
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        self.config = load_config()

        container = QWidget()
        layout = QFormLayout()

        # Theme selector
        self.theme_box = QComboBox()
        self.theme_box.addItems(["Light", "Dark"])
        self.theme_box.setCurrentText("Dark")
        layout.addRow(QLabel("Theme:"), self.theme_box)

        self.showGraph = QCheckBox()
        self.showGraph.setText("Show Graph Dock by Default")

        self.funcH = QCheckBox()
        self.funcH.setText("Function Highlighting ")

        self.wiki_box = QComboBox()
        self.wiki_box.addItems(["1", "2", "3", "4", "5", "6", "7"])
        self.wiki_box.setCurrentText(self.config.get("wikiSentences", DEFAULT_CONFIG["wikiSentences"]))

        if self.config.get("showGraph") == "false":
            self.showGraph.setChecked(False)
        else:
            self.showGraph.setChecked(True)

        if self.config.get("funcH") == "false":
            self.funcH.setChecked(False)
        else:
            self.funcH.setChecked(True)

        layout.addRow(self.showGraph)
        layout.addRow(self.funcH)
        layout.addRow(QLabel("Wikipedia Sentences:"), self.wiki_box)

        self.apply_button = QPushButton("Apply Settings")
        self.apply_button.clicked.connect(self.apply_settings)
        layout.addRow(self.apply_button)

        container.setLayout(layout)
        self.setWidget(container)

        self.apply_config()

    def load_config(self):
        return load_config()

    def save_config(self):
        save_config(self.config)

    def apply_config(self):
        self.theme_box.setCurrentText(self.config.get("theme", "Dark"))

    def apply_settings(self):

        self.config["theme"] = self.theme_box.currentText()
        self.config["showGraph"] = "true" if self.showGraph.isChecked() else "false"
        self.config["funcH"] = "true" if self.funcH.isChecked() else "false"
        self.config["wikiSentences"] = self.wiki_box.currentText()
        self.save_config()
