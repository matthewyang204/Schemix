import json
import os
import re
import sys
import time
from pathlib import Path

import qdarktheme
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QAction, QPixmap, QFont, QTextDocument, QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QTextEdit,
    QListWidget, QDockWidget, QInputDialog, QMenu, QStackedWidget,
    QPushButton, QMessageBox, QToolBar, QComboBox, QFontComboBox, QTabWidget
)
from pint import UnitRegistry

from core import Settings, todo, Graph, PeriodicTable, stylesheets, calc, MiscWidgets
from core.Editor import RichTextEditor, FunctionHighlighter

ureg = UnitRegistry()

UNIT_PATTERN = re.compile(r"\b(\d+(?:\.\d+)?)\s?(km/h|m/s|kg|g|L|ml|N|km|m|cm|mm|ft|in|lb|gal)\b", re.IGNORECASE)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Schemix")
        self.setGeometry(100, 100, 1200, 800)
        self.base_dir = os.path.join(os.getenv("LOCALAPPDATA"), "Schemix")
        os.makedirs(self.base_dir, exist_ok=True)
        self.board_dir = None

        self.setWindowIcon(QIcon("assets/icon.png"))

        self.current_subject = None
        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)
        self.placeholder = QLabel()
        pixmap = QPixmap("assets/placeholder.png")
        self.placeholder.setPixmap(
            pixmap.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setScaledContents(False)
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.central_stack.addWidget(self.placeholder)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabBarDoubleClicked.connect(self.rename_tab)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.central_stack.addWidget(self.tab_widget)

        self.config = self.load_config()
        self.config_path = "data/config.json"

        self.subjects_dock = QDockWidget("Subjects")

        self.subjects_dock.setStyleSheet(stylesheets.qdockwidget_sub_chap)

        subjects_container = QWidget()
        subjects_layout = QVBoxLayout(subjects_container)
        subjects_layout.setContentsMargins(0, 0, 0, 0)
        self.subjects_list = QListWidget()
        add_subject_btn = QPushButton("➕ Add Subject")
        add_subject_btn.clicked.connect(self.add_subject)
        subjects_layout.addWidget(self.subjects_list)
        subjects_layout.addWidget(add_subject_btn)
        self.subjects_dock.setWidget(subjects_container)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.subjects_dock)

        self.wiki_dock = QDockWidget("Wikipedia Summary", self)
        self.wiki_text = QTextEdit()
        self.wiki_text.setReadOnly(True)
        self.wiki_dock.setWidget(self.wiki_text)
        self.wiki_dock.setVisible(False)

        self.chapters_dock = QDockWidget("Chapters")
        self.chapters_dock.setStyleSheet(stylesheets.qdockwidget_sub_chap)
        chapters_container = QWidget()
        chapters_layout = QVBoxLayout(chapters_container)
        chapters_layout.setContentsMargins(0, 0, 0, 0)
        self.chapters_list = QListWidget()
        add_chapter_btn = QPushButton("➕ Add Chapter")
        add_chapter_btn.clicked.connect(self.add_chapter)
        chapters_layout.addWidget(self.chapters_list)
        chapters_layout.addWidget(add_chapter_btn)
        self.chapters_dock.setWidget(chapters_container)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.chapters_dock)

        self.graph_dock = QDockWidget("Function Graph")
        self.graph_dock.setMinimumWidth(200)
        self.graph_dock.setMaximumWidth(500)
        self.graph_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.graph_widget = Graph.GraphWidget()
        self.graph_dock.setWidget(self.graph_widget)

        if self.config.get("showGraph") == "true":
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.graph_dock)
        else:
            pass

        self.graph_widget.add_to_note_requested.connect(self.add_graph_to_current_note)

        self.setup_menu_bar()
        self.setup_toolbar()

        self.subjects_list.currentItemChanged.connect(self.load_chapters)
        self.chapters_list.itemDoubleClicked.connect(self.load_chapter_in_new_tab)
        self.check_or_create_board()

        self.subjects_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.subjects_list.customContextMenuRequested.connect(self.subject_context_menu)

        self.chapters_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chapters_list.customContextMenuRequested.connect(self.chapter_context_menu)

    def add_subject(self):
        subject, ok = QInputDialog.getText(self, "Add Subject", "Enter subject name:")
        if ok and subject:
            os.makedirs(os.path.join(self.board_dir, subject), exist_ok=True)
            self.refresh_subjects()

    def load_config(self):
        if os.path.exists("data/config.json"):
            try:
                with open("data/config.json", "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        return {
            "theme": "Dark",
            "showGraph": "false"
        }

    def add_chapter(self):
        if not self.current_subject:
            QMessageBox.warning(self, "No Subject Selected", "Please select a subject first.")
            return
        chapter, ok = QInputDialog.getText(self, "Add Chapter", "Enter chapter name:")
        if ok and chapter:
            path = Path(self.board_dir) / self.current_subject / f"{chapter}.md"
            path.write_text("", encoding="utf-8")
            self.load_chapters()

    def rename_tab(self, index):
        editor = self.tab_widget.widget(index)
        if not editor:
            return
        old_name = self.tab_widget.tabText(index)
        new_name, ok = QInputDialog.getText(self, "Rename Chapter", "Enter new chapter name:", text=old_name)
        if ok and new_name and new_name != old_name:
            old_path = Path(editor.property("file_path"))
            new_path = old_path.with_name(new_name + ".md")
            if old_path.exists():
                old_path.rename(new_path)
            editor.setProperty("file_path", str(new_path))
            self.tab_widget.setTabText(index, new_name)
            self.load_chapters()

    def triggerSettings(self):
        setting_dock = Settings.SettingsDock()
        self.graph_dock.hide()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, setting_dock)

    def triggerPT(self):
        pt_dock = PeriodicTable.ElementDock()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, pt_dock)

    def triggerSC(self):
        self.calc_dock = calc.ScientificCalculatorDock(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.calc_dock)

    def add_graph_to_current_note(self, pixmap):
        editor = self.get_current_editor()
        if not editor:
            QMessageBox.warning(self, "No Note Open", "Please open a note before adding a graph.")
            return
        note_path_str = editor.property("file_path")
        if not note_path_str:
            QMessageBox.warning(self, "Save Note First", "Please save the note at least once before adding images.")
            return

        note_path = Path(note_path_str)
        save_folder = note_path.parent

        image_name = f"graph_{int(time.time())}.png"
        image_save_path = save_folder / image_name

        if not pixmap.save(str(image_save_path), "PNG"):
            QMessageBox.critical(self, "Save Error", "Could not save the graph image.")
            return
        editor.insert_image_from_path(str(image_save_path))

    def subject_context_menu(self, pos):
        menu = QMenu()
        add_action = menu.addAction("➕ Add Subject")
        delete_action = menu.addAction("🗑️ Delete Subject")
        action = menu.exec(self.subjects_list.mapToGlobal(pos))

        if action == add_action:
            subject, ok = QInputDialog.getText(self, "Add Subject", "Enter subject name:")
            if ok and subject:
                os.makedirs(os.path.join(self.board_dir, subject), exist_ok=True)
                self.refresh_subjects()
        elif action == delete_action:
            item = self.subjects_list.currentItem()
            if item:
                subject_path = os.path.join(self.board_dir, item.text())
                confirm = QMessageBox.question(self, "Delete Subject",
                                               f"Delete '{item.text()}' and all its chapters?",
                                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if confirm == QMessageBox.StandardButton.Yes:
                    import shutil
                    shutil.rmtree(subject_path, ignore_errors=True)
                    self.refresh_subjects()
                    self.chapters_list.clear()

    def chapter_context_menu(self, pos):
        menu = QMenu()
        add_action = menu.addAction("➕ Add Chapter")
        delete_action = menu.addAction("🗑️ Delete Chapter")
        action = menu.exec(self.chapters_list.mapToGlobal(pos))

        if action == add_action:
            chapter, ok = QInputDialog.getText(self, "Add Chapter", "Enter chapter name:")
            if ok and chapter and self.current_subject:
                path = Path(self.board_dir) / self.current_subject / f"{chapter}.md"
                path.write_text("", encoding="utf-8")
                self.load_chapters()
        elif action == delete_action:
            item = self.chapters_list.currentItem()
            if item and self.current_subject:
                chapter_path = Path(self.board_dir) / self.current_subject / f"{item.text()}.md"
                confirm = QMessageBox.question(self, "Delete Chapter",
                                               f"Delete chapter '{item.text()}'?",
                                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if confirm == QMessageBox.StandardButton.Yes and chapter_path.exists():
                    chapter_path.unlink()
                    self.load_chapters()

    def prompt_create_board(self):
        board, ok = QInputDialog.getText(self, "Create Board", "Enter board name:")
        if ok and board:
            self.create_board(board)

    def delete_current_board(self):
        if not self.board_dir:
            return
        board_name = os.path.basename(self.board_dir)
        confirm = QMessageBox.question(self, "Delete Board",
                                       f"Delete the board '{board_name}' and all its contents?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            import shutil
            shutil.rmtree(self.board_dir, ignore_errors=True)
            self.board_dir = None
            self.check_or_create_board()

    def get_current_editor(self):
        return self.tab_widget.currentWidget()

    def handle_graph_request(self, expression):
        self.graph_widget.plot_function(expression)

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
        self.size_combo.addItems([str(s) for s in [8, 9, 10, 11, 12, 14, 16, 18, 24, 36, 48, 72]])
        self.size_combo.setCurrentText("24")
        self.size_combo.textActivated.connect(
            lambda size: self.get_current_editor().setFontPointSize(float(size)) if self.get_current_editor() else None)
        toolbar.addWidget(self.size_combo)
        toolbar.addSeparator()

        bullet_action = QAction("• Bullet List", self)
        bullet_action.triggered.connect(lambda: self.get_current_editor().insert_bullet_list())

        number_action = QAction("1. Numbered List", self)
        number_action.triggered.connect(lambda: self.get_current_editor().insert_numbered_list())

        toolbar.addAction(bullet_action)
        toolbar.addAction(number_action)

        toolbar.addSeparator()

        title_action = QAction("Title", self)
        title_action.triggered.connect(lambda: self.get_current_editor().apply_title_format())

        subheading_action = QAction("Subheading", self)
        subheading_action.triggered.connect(lambda: self.get_current_editor().apply_subheading_format())

        toolbar.addAction(title_action)
        toolbar.addAction(subheading_action)

        toolbar.addSeparator()

        image_action = QAction("🖼️", self)
        image_action.triggered.connect(
            lambda: self.get_current_editor().insert_image() if self.get_current_editor() else None)
        toolbar.addAction(image_action)

        inline_code_action = QAction("</>", self)
        inline_code_action.setIcon(QIcon.fromTheme("code-context"))
        inline_code_action.triggered.connect(
            lambda: self.get_current_editor().insert_inline_code() if self.get_current_editor() else None)
        toolbar.addAction(inline_code_action)

        math_action = QAction("LaTeX", self)
        math_action.triggered.connect(
            lambda: self.get_current_editor().insert_math_equation() if self.get_current_editor() else None)
        toolbar.addAction(math_action)

    def setup_menu_bar(self):
        file_menu = self.menuBar().addMenu("File")
        save_action = QAction("💾 Save Chapter", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_current_chapter)
        file_menu.addAction(save_action)

        add_board_action = QAction("➕ Add Board", self)
        add_board_action.triggered.connect(self.prompt_create_board)
        file_menu.addAction(add_board_action)

        delete_board_action = QAction("🗑️ Delete Board", self)
        delete_board_action.triggered.connect(self.delete_current_board)
        file_menu.addAction(delete_board_action)

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

        view_menu.addSeparator()

        toggle_graph_dock = QAction("Toggle Graph", self)
        toggle_graph_dock.setCheckable(True)
        toggle_graph_dock.setChecked(True)
        toggle_graph_dock.triggered.connect(self.graph_dock.setVisible)
        view_menu.addAction(toggle_graph_dock)

        tools_menu = self.menuBar().addMenu("Tools")
        toggle_todo_action = QAction("To-Do List", self)
        toggle_todo_action.triggered.connect(self.show_todo)
        tools_menu.addAction(toggle_todo_action)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.triggerSettings)
        self.menuBar().addAction(settings_action)

        tools_menu.addSeparator()

        sc_action = QAction("Scientific Calculator", self)
        sc_action.triggered.connect(self.triggerSC)
        tools_menu.addAction(sc_action)

        pt_action = QAction("Periodic Table", self)
        pt_action.triggered.connect(self.triggerPT)
        tools_menu.addAction(pt_action)

    def show_todo(self):
        if not self.board_dir:
            QMessageBox.warning(self, "No Board", "Please select a board first.")
            return
        self.todo_dock = todo.ToDoDock(self.board_dir)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.todo_dock)

    def load_board(self, board_path):
        self.board_dir = board_path
        if hasattr(self, "todo_dock"):
            self.removeDockWidget(self.todo_dock)
            self.todo_dock = todo.ToDoDock(self.board_dir)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.todo_dock)

    def load_chapter_in_new_tab(self, item):
        if not (self.current_subject and item):
            return
        chapter_name = item.text()
        note_path = Path(self.board_dir) / self.current_subject / (chapter_name + ".md")

        for i in range(self.tab_widget.count()):
            editor_widget = self.tab_widget.widget(i)
            if editor_widget and editor_widget.property("file_path") == str(note_path):
                self.tab_widget.setCurrentIndex(i)
                return
        try:
            if not note_path.is_file():
                content = ""  # Create empty content for a new file
            else:
                with open(note_path, "r", encoding="utf-8") as f:
                    content = f.read()

            editor = RichTextEditor(self, graph_callback=self.handle_graph_request)
            editor.setProperty("file_path", str(note_path))

            doc = QTextDocument(editor)
            base_url = QUrl.fromLocalFile(str(note_path.parent) + os.sep)
            doc.setBaseUrl(base_url)
            doc.setHtml(content)
            editor.setDocument(doc)
            editor.highlighter = FunctionHighlighter(editor.document())

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
        path = current_editor.property("file_path")
        if not path:
            QMessageBox.critical(self, "Save Error", "Could not determine the file path.")
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                # Standard markdown is now sufficient
                f.write(current_editor.toHtml())
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
            board_selector = MiscWidgets.BoardSelector(self.create_board)
            self.central_stack.addWidget(board_selector)
            self.central_stack.setCurrentWidget(board_selector)

    def create_board(self, board_name):
        self.board_dir = os.path.join(self.base_dir, board_name)
        os.makedirs(self.board_dir, exist_ok=True)
        self.setWindowTitle(f"{board_name} - Schemix")
        for i in range(self.central_stack.count()):
            widget = self.central_stack.widget(i)
            if isinstance(widget, MiscWidgets.BoardSelector):
                self.central_stack.removeWidget(widget)
                widget.deleteLater()
                break
        self.central_stack.setCurrentWidget(self.placeholder)
        self.refresh_subjects()

    def load_board(self, board_name):
        self.board_dir = os.path.join(self.base_dir, board_name)
        self.setWindowTitle(f"{board_name} - Schemix")
        self.refresh_subjects()

    def refresh_subjects(self):
        self.subjects_list.clear()
        if not self.board_dir or not os.path.exists(self.board_dir):
            return
        for subject in sorted(os.listdir(self.board_dir)):
            if os.path.isdir(os.path.join(self.board_dir, subject)):
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
    qdarktheme.setup_theme("auto")

    splash_label = QLabel()
    splash_pixmap = QPixmap("assets/splash.png")

    splash_label.setPixmap(splash_pixmap)
    splash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    splash_label.setWindowFlags(
        Qt.WindowType.FramelessWindowHint |
        Qt.WindowType.SplashScreen |
        Qt.WindowType.WindowStaysOnTopHint
    )
    splash_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    splash_label.setStyleSheet("background: transparent; border: none;")

    splash_label.resize(splash_pixmap.size())

    screen_geometry = app.primaryScreen().availableGeometry()
    x = (screen_geometry.width() - splash_label.width()) // 2
    y = (screen_geometry.height() - splash_label.height()) // 2
    splash_label.move(x, y)

    splash_label.show()
    app.processEvents()

    time.sleep(2)

    window = MainWindow()
    window.show()
    splash_label.close()

    sys.exit(app.exec())
