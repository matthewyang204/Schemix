from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QTextEdit,
    QListWidget, QDockWidget, QInputDialog, QMenuBar, QMenu, QStackedWidget,
    QPushButton, QMessageBox
)
from PyQt6.QtGui import QAction, QTextOption
from PyQt6.QtCore import Qt
import sys
import os


class BoardSelector(QWidget):
    def __init__(self, create_board_callback):
        super().__init__()
        self.create_board_callback = create_board_callback
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(QLabel("No board found. Create a board to continue."))

        create_button = QPushButton("➕ Create Board")
        create_button.clicked.connect(self.create_board)
        self.layout().addWidget(create_button)

    def create_board(self):
        board, ok = QInputDialog.getText(self, "Create Board", "Enter board name:")
        if ok and board:
            self.create_board_callback(board)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Board - EngiNote")
        self.setGeometry(100, 100, 1200, 800)

        self.base_dir = os.path.join(os.getenv("LOCALAPPDATA"), "EngiNote")
        os.makedirs(self.base_dir, exist_ok=True)

        self.board_dir = None
        self.current_subject = None
        self.current_chapter = None

        # Central stacked widget
        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)

        # Placeholder widget when no chapter is open
        self.placeholder = QLabel("📝 Open any chapter to begin editing.")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Editor widget
        self.editor = QTextEdit()
        self.editor.setWordWrapMode(QTextOption.WrapMode.WordWrap)

        # Add both to stack
        self.central_stack.addWidget(self.placeholder)  # index 0
        self.central_stack.addWidget(self.editor)       # index 1

        # Dock widgets
        self.subjects_dock = QDockWidget("Subjects")
        self.subjects_list = QListWidget()
        self.subjects_dock.setWidget(self.subjects_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.subjects_dock)

        self.chapters_dock = QDockWidget("Chapters")
        self.chapters_list = QListWidget()
        self.chapters_dock.setWidget(self.chapters_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.chapters_dock)

        # Menubar
        self.menu_bar = self.menuBar()

        # File menu
        file_menu = self.menu_bar.addMenu("File")

        save_action = QAction("💾 Save Chapter", self)
        save_action.triggered.connect(self.save_current_chapter)
        file_menu.addAction(save_action)

        # View menu
        view_menu = self.menu_bar.addMenu("View")

        toggle_subjects_dock = QAction("Toggle Subjects", self)
        toggle_subjects_dock.setCheckable(True)
        toggle_subjects_dock.setChecked(True)
        toggle_subjects_dock.triggered.connect(
            lambda checked: self.subjects_dock.setVisible(checked)
        )
        view_menu.addAction(toggle_subjects_dock)

        toggle_chapters_dock = QAction("Toggle Chapters", self)
        toggle_chapters_dock.setCheckable(True)
        toggle_chapters_dock.setChecked(True)
        toggle_chapters_dock.triggered.connect(
            lambda checked: self.chapters_dock.setVisible(checked)
        )
        view_menu.addAction(toggle_chapters_dock)

        self.subjects_list.currentItemChanged.connect(self.load_chapters)
        self.chapters_list.currentItemChanged.connect(self.load_chapter)

        self.check_or_create_board()

    def check_or_create_board(self):
        boards = [d for d in os.listdir(self.base_dir) if os.path.isdir(os.path.join(self.base_dir, d))]
        if boards:
            self.load_board(boards[0])
        else:
            self.central_stack.addWidget(BoardSelector(self.create_board))

    def create_board(self, board_name):
        self.board_dir = os.path.join(self.base_dir, board_name)
        os.makedirs(self.board_dir, exist_ok=True)
        self.setWindowTitle(f"{board_name} - EngiNote")
        self.refresh_subjects()

    def load_board(self, board_name):
        self.board_dir = os.path.join(self.base_dir, board_name)
        self.setWindowTitle(f"{board_name} - EngiNote")
        self.refresh_subjects()

    def refresh_subjects(self):
        self.subjects_list.clear()
        for subject in os.listdir(self.board_dir):
            subject_path = os.path.join(self.board_dir, subject)
            if os.path.isdir(subject_path):
                self.subjects_list.addItem(subject)

    def load_chapters(self):
        item = self.subjects_list.currentItem()
        self.chapters_list.clear()
        self.current_subject = None
        if item:
            self.current_subject = item.text()
            subject_path = os.path.join(self.board_dir, self.current_subject)
            for file in os.listdir(subject_path):
                if file.endswith(".md"):
                    self.chapters_list.addItem(file)

    def load_chapter(self):
        item = self.chapters_list.currentItem()
        if item and self.current_subject:
            self.current_chapter = item.text()
            path = os.path.join(self.board_dir, self.current_subject, self.current_chapter)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.editor.setPlainText(content)
                    self.central_stack.setCurrentWidget(self.editor)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def save_current_chapter(self):
        if not (self.current_subject and self.current_chapter):
            QMessageBox.warning(self, "No Chapter", "No chapter is currently loaded.")
            return

        path = os.path.join(self.board_dir, self.current_subject, self.current_chapter)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            self.statusBar().showMessage("Chapter saved", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", str(e))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())