import sys
import os
import qdarktheme
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QTextEdit,
    QListWidget, QDockWidget, QInputDialog, QMenuBar, QMenu, QStackedWidget,
    QPushButton, QMessageBox, QFileDialog, QToolBar, QComboBox, QFontComboBox, QTabWidget
)
from PyQt6.QtGui import QAction, QTextOption, QTextCharFormat, QPixmap, QFont
from PyQt6.QtCore import Qt


class RichTextEditor(QTextEdit):
    """
    A custom QTextEdit with added functionality for text formatting and image insertion.
    Each instance of this class will be a separate document in a tab.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Write your notes here...")
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)

    def set_format(self, fmt_type):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            cursor.select(cursor.SelectionType.WordUnderCursor)

        fmt = QTextCharFormat()
        current_fmt = cursor.charFormat()

        if fmt_type == "bold":
            is_bold = current_fmt.fontWeight() == QFont.Weight.Bold
            fmt.setFontWeight(QFont.Weight.Normal if is_bold else QFont.Weight.Bold)
        elif fmt_type == "italic":
            fmt.setFontItalic(not current_fmt.fontItalic())
        elif fmt_type == "underline":
            fmt.setFontUnderline(not current_fmt.fontUnderline())

        cursor.mergeCharFormat(fmt)
        self.mergeCurrentCharFormat(fmt)

    def insert_image(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Insert Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if filename:
            pixmap = QPixmap(filename)
            if pixmap.isNull():
                return

            editor_width = self.viewport().width() - 40
            if pixmap.width() > editor_width:
                pixmap = pixmap.scaledToWidth(editor_width, Qt.TransformationMode.SmoothTransformation)

            cursor = self.textCursor()
            cursor.insertBlock()
            cursor.insertImage(pixmap.toImage())
            cursor.insertBlock()
            self.setTextCursor(cursor)


class BoardSelector(QWidget):
    """
    A widget shown on first launch to prompt the user to create a board.
    """

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
    """
    The main application window, modified to support a tabbed document interface.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("EngiNote")
        self.setGeometry(100, 100, 1200, 800)

        self.base_dir = os.path.join(os.getenv("LOCALAPPDATA"), "EngiNote")
        os.makedirs(self.base_dir, exist_ok=True)

        self.board_dir = None
        self.current_subject = None

        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)

        self.placeholder = QLabel("📝 Double-click a chapter from the list to start editing.")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.central_stack.addWidget(self.placeholder)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.central_stack.addWidget(self.tab_widget)

        self.subjects_dock = QDockWidget("Subjects")
        self.subjects_list = QListWidget()
        self.subjects_dock.setWidget(self.subjects_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.subjects_dock)

        self.chapters_dock = QDockWidget("Chapters")
        self.chapters_list = QListWidget()
        self.chapters_dock.setWidget(self.chapters_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.chapters_dock)

        self.setup_menu_bar()
        self.setup_toolbar()

        self.subjects_list.currentItemChanged.connect(self.load_chapters)
        self.chapters_list.itemDoubleClicked.connect(self.load_chapter_in_new_tab)

        self.check_or_create_board()

    def get_current_editor(self):
        return self.tab_widget.currentWidget()

    def setup_toolbar(self):
        toolbar = QToolBar("Formatting")
        self.addToolBar(toolbar)

        bold_action = QAction("B", self)
        bold_font = QFont();
        bold_font.setBold(True);
        bold_action.setFont(bold_font)
        bold_action.triggered.connect(
            lambda: self.get_current_editor().set_format("bold") if self.get_current_editor() else None)
        toolbar.addAction(bold_action)

        italic_action = QAction("I", self)
        italic_font = QFont();
        italic_font.setItalic(True);
        italic_action.setFont(italic_font)
        italic_action.triggered.connect(
            lambda: self.get_current_editor().set_format("italic") if self.get_current_editor() else None)
        toolbar.addAction(italic_action)

        underline_action = QAction("U", self)
        underline_font = QFont();
        underline_font.setUnderline(True);
        underline_action.setFont(underline_font)
        underline_action.triggered.connect(
            lambda: self.get_current_editor().set_format("underline") if self.get_current_editor() else None)
        toolbar.addAction(underline_action)

        toolbar.addSeparator()

        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(
            lambda font: self.get_current_editor().setCurrentFont(font) if self.get_current_editor() else None)
        toolbar.addWidget(self.font_combo)

        self.size_combo = QComboBox()
        self.size_combo.addItems([str(s) for s in [8, 9, 10, 11, 12, 14, 16, 18, 24, 36]])
        self.size_combo.setCurrentText("12")
        self.size_combo.textActivated.connect(
            lambda size: self.get_current_editor().setFontPointSize(float(size)) if self.get_current_editor() else None)
        toolbar.addWidget(self.size_combo)

        toolbar.addSeparator()

        image_action = QAction("🖼️", self)
        image_action.triggered.connect(
            lambda: self.get_current_editor().insert_image() if self.get_current_editor() else None)
        toolbar.addAction(image_action)

    def setup_menu_bar(self):
        file_menu = self.menuBar().addMenu("File")
        save_action = QAction("💾 Save Chapter", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_current_chapter)
        file_menu.addAction(save_action)

        view_menu = self.menuBar().addMenu("View")
        toggle_subjects_dock = QAction("Toggle Subjects", self)
        toggle_subjects_dock.setCheckable(True)
        toggle_subjects_dock.setChecked(True)
        toggle_subjects_dock.triggered.connect(self.subjects_dock.setVisible)
        view_menu.addAction(toggle_subjects_dock)

        toggle_chapters_dock = QAction("Toggle Chapters", self)
        toggle_chapters_dock.setCheckable(True)
        toggle_chapters_dock.setChecked(True)
        toggle_chapters_dock.triggered.connect(self.chapters_dock.setVisible)
        view_menu.addAction(toggle_chapters_dock)

    def load_chapter_in_new_tab(self, item):
        if not (self.current_subject and item):
            return

        chapter_name = item.text()
        chapter_path = os.path.join(self.board_dir, self.current_subject, chapter_name + ".md")

        # Check if the chapter is already open by checking the widget's property
        for i in range(self.tab_widget.count()):
            editor_widget = self.tab_widget.widget(i)
            if editor_widget and editor_widget.property("file_path") == chapter_path:
                self.tab_widget.setCurrentIndex(i)
                return

        try:
            with open(chapter_path, "r", encoding="utf-8") as f:
                content = f.read()

            editor = RichTextEditor()
            # Set the custom property on the widget itself
            editor.setProperty("file_path", chapter_path)
            editor.setMarkdown(content)

            index = self.tab_widget.addTab(editor, chapter_name)
            self.tab_widget.setCurrentIndex(index)

            if self.tab_widget.count() > 0:
                self.central_stack.setCurrentWidget(self.tab_widget)

        except Exception as e:
            QMessageBox.critical(self, "Error Opening File", str(e))

    def save_current_chapter(self):
        current_editor = self.get_current_editor()
        if not current_editor:
            QMessageBox.warning(self, "Save Error", "No chapter is open to save.")
            return

        # Get the path from the widget's property, not the tab data
        path = current_editor.property("file_path")
        if not path:
            QMessageBox.critical(self, "Save Error", "Could not determine the file path for this tab.")
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(current_editor.toMarkdown())
            self.statusBar().showMessage(f"Saved {os.path.basename(path)}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", str(e))

    def close_tab(self, index):
        widget = self.tab_widget.widget(index)
        if widget:
            widget.deleteLater()
        self.tab_widget.removeTab(index)

        if self.tab_widget.count() == 0:
            self.central_stack.setCurrentWidget(self.placeholder)

    def check_or_create_board(self):
        boards = [d for d in os.listdir(self.base_dir) if os.path.isdir(os.path.join(self.base_dir, d))]
        if boards:
            boards.sort(key=lambda d: os.path.getmtime(os.path.join(self.base_dir, d)), reverse=True)
            self.load_board(boards[0])
        else:
            board_selector = BoardSelector(self.create_board)
            self.central_stack.addWidget(board_selector)
            self.central_stack.setCurrentWidget(board_selector)

    def create_board(self, board_name):
        self.board_dir = os.path.join(self.base_dir, board_name)
        os.makedirs(self.board_dir, exist_ok=True)
        self.setWindowTitle(f"{board_name} - EngiNote")

        for i in range(self.central_stack.count()):
            widget = self.central_stack.widget(i)
            if isinstance(widget, BoardSelector):
                self.central_stack.removeWidget(widget)
                widget.deleteLater()
                break

        self.central_stack.setCurrentWidget(self.placeholder)
        self.refresh_subjects()

    def load_board(self, board_name):
        self.board_dir = os.path.join(self.base_dir, board_name)
        self.setWindowTitle(f"{board_name} - EngiNote")
        self.refresh_subjects()

    def refresh_subjects(self):
        self.subjects_list.clear()
        if not self.board_dir or not os.path.exists(self.board_dir):
            return
        for subject in sorted(os.listdir(self.board_dir)):
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
            for file in sorted(os.listdir(subject_path)):
                if file.endswith(".md"):
                    self.chapters_list.addItem(os.path.splitext(file)[0])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    qdarktheme.setup_theme()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
