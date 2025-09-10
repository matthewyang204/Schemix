import tkinter as tk
from tkinter import simpledialog
import os
from pathlib import Path

def prompt_create_board(base_dir, queue):
        boardList = "\n".join(os.path.basename(str(p)) for p in Path(base_dir).iterdir())
        # board, ok = QInputDialog.getText(self, "Create Board", f"{boardList}\n\nEnter board name:")
        board = simpledialog.askstring("Create or Load Board", f"Existing Boards:\n{boardList}\n\nTo load an existing board, simply enter its exact name. To create a blank/new board, simply enter the name of the new board.\n\nEnter board name:")
        queue.put(board)