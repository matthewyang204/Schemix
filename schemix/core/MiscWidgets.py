import re
import tkinter as tk
from PyQt6.QtWidgets import (
    QVBoxLayout, QWidget, QLabel, QInputDialog, QPushButton
)
from pint import UnitRegistry

ureg = UnitRegistry()

UNIT_PATTERN = re.compile(r"\b(\d+(?:\.\d+)?)\s?(km/h|m/s|kg|g|L|ml|N|km|m|cm|mm|ft|in|lb|gal)\b", re.IGNORECASE)


class BoardSelector(QWidget):
    def __init__(self, create_board_callback):
        super().__init__()
        self.create_board_callback = create_board_callback
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(QLabel("No board found. Create a board to continue."))
        create_button = QPushButton("➕ Create/Select Board")
        create_button.clicked.connect(self.create_board)
        self.layout().addWidget(create_button)

    def create_board(self):
        boardList = "\n".join(os.path.basename(str(p)) for p in Path(self.base_dir).iterdir())
        # board, ok = QInputDialog.getText(self, "Create Board", f"{boardList}\n\nEnter board name:")
        board = simpledialog.askstring("Create or Load Board", f"Existing Boards:\n{boardList}\n\nTo load an existing board, simply enter its exact name. To create a blank/new board, simply enter the name of the new board.\n\nEnter board name:")
        if board:
            self.create_board(board)