from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QTextEdit,
    QListWidget, QDockWidget, QInputDialog, QMenuBar, QMenu, QStackedWidget,
    QPushButton, QMessageBox
)
from PyQt6.QtGui import QIcon, QAction
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


class EngiNote(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Board - EngiNote")
        self.setGeometry(100, 100, 1000, 600)
        self.setWindowIcon(QIcon("icon.png"))

        self.base_dir = os.path.join(os.getenv("LOCALAPPDATA"), "EngiNote")
        os.makedirs(self.base_dir, exist_ok=True)

        self.board_dir = None
        self.current_subject = None
        self.current_chapter = None

        self.subject_list = QListWidget()
        self.chapter_list = QListWidget()
        self.text_edit = QTextEdit()

        self.subjects_dock = None
        self.chapters_dock = None

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        self.init_menu()

        self.check_or_create_board()

    def check_or_create_board(self):
        boards = [d for d in os.listdir(self.base_dir) if os.path.isdir(os.path.join(self.base_dir, d))]
        if boards:
            self.load_board(boards[0])
        else:
            self.stacked_widget.addWidget(BoardSelector(self.create_board))

    def create_board(self, board_name):
        self.board_dir = os.path.join(self.base_dir, board_name)
        os.makedirs(self.board_dir, exist_ok=True)
        self.setWindowTitle(f"{board_name} - EngiNote")
        self.init_main_ui()

    def load_board(self, board_name):
        self.board_dir = os.path.join(self.base_dir, board_name)
        self.setWindowTitle(f"{board_name} - EngiNote")
        self.init_main_ui()

    def init_main_ui(self):
        self.subject_list.clear()
        self.subject_list.currentItemChanged.connect(self.load_chapters_for_subject)

        self.chapter_list.clear()
        self.chapter_list.currentItemChanged.connect(self.load_chapter)

        self.subjects_dock = QDockWidget("Subjects", self)
        self.subjects_dock.setWidget(self.subject_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.subjects_dock)

        self.chapters_dock = QDockWidget("Chapters", self)
        self.chapters_dock.setWidget(self.chapter_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.chapters_dock)

        self.text_edit.setPlaceholderText("Write your notes here...")

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Editor:"))
        right_layout.addWidget(self.text_edit)

        container = QWidget()
        container.setLayout(right_layout)
        self.stacked_widget.addWidget(container)
        self.stacked_widget.setCurrentWidget(container)

        self.refresh_subjects()

    def refresh_subjects(self):
        self.subject_list.clear()
        for subject in os.listdir(self.board_dir):
            subject_path = os.path.join(self.board_dir, subject)
            if os.path.isdir(subject_path):
                self.subject_list.addItem(subject)

    def init_menu(self):
        file_menu = QMenu("File", self)
        self.menu_bar.addMenu(file_menu)

        save_action = QAction("💾 Save Chapter", self)
        save_action.triggered.connect(self.manual_save_chapter)
        file_menu.addAction(save_action)

        subject_menu = QMenu("Subject", self)
        self.menu_bar.addMenu(subject_menu)

        add_subject_action = QAction("➕ Add Subject", self)
        add_subject_action.triggered.connect(self.add_subject)
        subject_menu.addAction(add_subject_action)

        add_chapter_action = QAction("➕ Add Chapter", self)
        add_chapter_action.triggered.connect(self.add_chapter)
        subject_menu.addAction(add_chapter_action)

        view_menu = QMenu("View", self)
        self.menu_bar.addMenu(view_menu)

        self.toggle_subjects_action = QAction("📁 Subjects", self, checkable=True, checked=True)
        self.toggle_subjects_action.triggered.connect(
            lambda checked: self.subjects_dock.setVisible(checked)
        )
        view_menu.addAction(self.toggle_subjects_action)

        self.toggle_chapters_action = QAction("📄 Chapters", self, checkable=True, checked=True)
        self.toggle_chapters_action.triggered.connect(
            lambda checked: self.chapters_dock.setVisible(checked)
        )
        view_menu.addAction(self.toggle_chapters_action)

        # Keep menu checkmarks in sync with actual dock visibility
        if self.subjects_dock:
            self.subjects_dock.visibilityChanged.connect(
                lambda visible: self.toggle_subjects_action.setChecked(visible)
            )
        if self.chapters_dock:
            self.chapters_dock.visibilityChanged.connect(
                lambda visible: self.toggle_chapters_action.setChecked(visible)
            )

    def add_subject(self):
        subject, ok = QInputDialog.getText(self, "Add Subject", "Enter subject name:")
        if ok and subject:
            subject_path = os.path.join(self.board_dir, subject)
            if not os.path.exists(subject_path):
                os.makedirs(subject_path)
                self.subject_list.addItem(subject)

    def load_chapters_for_subject(self):
        current_item = self.subject_list.currentItem()
        self.chapter_list.clear()
        self.current_subject = None
        if current_item:
            self.current_subject = current_item.text()
            subject_path = os.path.join(self.board_dir, self.current_subject)
            for file in os.listdir(subject_path):
                if file.endswith(".md"):
                    self.chapter_list.addItem(file)

    def add_chapter(self):
        if not self.current_subject:
            QMessageBox.warning(self, "No Subject Selected", "Please select a subject before adding a chapter.")
            return

        chapter_name, ok = QInputDialog.getText(self, "Add Chapter", "Enter chapter name:")
        if ok and chapter_name:
            filename = chapter_name.replace(" ", "_") + ".md"
            chapter_path = os.path.join(self.board_dir, self.current_subject, filename)

            if not os.path.exists(chapter_path):
                with open(chapter_path, "w", encoding="utf-8") as f:
                    f.write(f"# {chapter_name}\n\n")
            self.chapter_list.addItem(filename)
            self.chapter_list.setCurrentRow(self.chapter_list.count() - 1)

    def load_chapter(self):
        current_item = self.chapter_list.currentItem()
        if current_item:
            self.current_chapter = current_item.text()
            chapter_path = os.path.join(self.board_dir, self.current_subject, self.current_chapter)
            try:
                with open(chapter_path, "r", encoding="utf-8") as f:
                    self.text_edit.setPlainText(f.read())
            except Exception as e:
                QMessageBox.critical(self, "Load Failed", f"Failed to load chapter:\n{str(e)}")

    def manual_save_chapter(self):
        if not (self.current_subject and self.current_chapter):
            QMessageBox.warning(self, "No Chapter", "No chapter is currently loaded.")
            return

        chapter_path = os.path.join(self.board_dir, self.current_subject, self.current_chapter)
        try:
            with open(chapter_path, "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())
            self.statusBar().showMessage("Chapter saved!", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", f"Failed to save chapter:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EngiNote()
    window.show()
    sys.exit(app.exec())
