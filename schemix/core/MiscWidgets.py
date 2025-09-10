import re
from PyQt6.QtWidgets import (
    QVBoxLayout, QWidget, QLabel, QPushButton
)
from pint import UnitRegistry

ureg = UnitRegistry()

UNIT_PATTERN = re.compile(r"\b(\d+(?:\.\d+)?)\s?(km/h|m/s|kg|g|L|ml|N|km|m|cm|mm|ft|in|lb|gal)\b", re.IGNORECASE)


class BoardSelector(QWidget):
    def __init__(self, create_board_callback, main_window):
        super().__init__()
        self.main_window = main_window
        self.create_board_callback = create_board_callback
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(QLabel("No board found. Create a board to continue."))
        create_button = QPushButton("➕ Create/Select Board")
        create_button.clicked.connect(self.create_board)
        self.layout().addWidget(create_button)

    def create_board(self):
        self.main_window.prompt_create_board_wrapper()