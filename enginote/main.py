import json
import os
import time
from io import BytesIO
from pathlib import Path

import numpy as np
import qdarktheme
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QRegularExpression, QEvent
from PyQt6.QtGui import QAction, QTextOption, QTextCharFormat, QPixmap, QFont, QTextDocument, QSyntaxHighlighter, \
    QTextCursor, QIcon, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QTextEdit,
    QListWidget, QDockWidget, QInputDialog, QMenu, QStackedWidget,
    QPushButton, QMessageBox, QFileDialog, QToolBar, QComboBox, QFontComboBox, QTabWidget, QToolTip
)
import wikipedia
from asteval import Interpreter
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core import Settings, todo, Graph


class FunctionHighlighter(QSyntaxHighlighter):
    """A syntax highlighter for recognizing math functions and constants."""

    def __init__(self, parent: QTextDocument):
        super().__init__(parent)
        self.highlighting_rules = []

        # Define the format for keywords (e.g., functions, constants)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(Qt.GlobalColor.cyan)
        keyword_format.setFontItalic(True)

        keywords = [
            'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
            'log', 'log10', 'ln', 'exp', 'sqrt', 'pi', 'e'
        ]

        # Create a regular expression for each keyword
        for word in keywords:
            pattern = QRegularExpression(rf'\b{word}\b')
            rule = (pattern, keyword_format)
            self.highlighting_rules.append(rule)

    def highlightBlock(self, text: str):
        """Applies highlighting rules to the given block of text."""
        for pattern, fmt in self.highlighting_rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)




from pint import UnitRegistry
import re
import sys

ureg = UnitRegistry()

UNIT_PATTERN = re.compile(r"\b(\d+(?:\.\d+)?)\s?(km/h|m/s|kg|g|L|ml|N|km|m|cm|mm|ft|in|lb|gal)\b", re.IGNORECASE)


class RichTextEditor(QTextEdit):
    def __init__(self, parent, graph_callback=None, inline=False):
        super().__init__(parent)
        self.setPlaceholderText("Write your notes here...")
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.aeval = Interpreter()
        self.graph_callback = graph_callback
        self.setFont(QFont("Consolas"))
        self.main_window = parent

        self.setMouseTracking(True)
        self.viewport().installEventFilter(self)
        self.inline_conversion = inline  # Show in brackets inline if True
        self.config = self.load_config()
        self.config_path = "data/config.json"

        if self.config.get("funcH") == "true":
            self.highlighter = FunctionHighlighter(self.document())
        else:
            pass

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

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.MouseMove:
            cursor = self.cursorForPosition(event.position().toPoint())
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            word = cursor.selectedText()

            full_text = self.toPlainText()
            pos = cursor.position()
            matches = list(UNIT_PATTERN.finditer(full_text))

            for match in matches:
                if match.start() <= pos <= match.end():
                    value, unit = match.groups()
                    converted = self.convert_unit(float(value), unit)
                    if converted:
                        QToolTip.showText(event.globalPosition().toPoint(), converted)

                        # Optional inline replacement
                        if self.inline_conversion:
                            self.inline_add_conversion(match, converted)
                    break
            else:
                QToolTip.hideText()

        return super().eventFilter(source, event)

    def insert_inline_code(self):
        cursor = self.textCursor()
        format = QTextCharFormat()
        format.setFontFamily("Courier New")
        format.setFontPointSize(self.fontPointSize() * 0.95)
        format.setBackground(QColor("#121212"))
        format.setForeground(QColor("#d63384"))
        format.setFontFixedPitch(True)
        format.setProperty(QTextCharFormat.Property.FullWidthSelection, True)

        if cursor.hasSelection():
            cursor.mergeCharFormat(format)
        else:
            cursor.insertText("code", format)
            cursor.movePosition(cursor.MoveOperation.Left, cursor.MoveMode.MoveAnchor, 4)
            self.setTextCursor(cursor)

    def convert_unit(self, value, unit):
        try:
            unit = unit.lower()
            q = value * ureg(unit)

            # Convert to a commonly used counterpart
            if unit == "km/h":
                return f"{q.to('m/s'):.2f~P}"
            elif unit == "m/s":
                return f"{q.to('km/h'):.2f~P}"
            elif unit == "kg":
                return f"{q.to('lb'):.2f~P}"
            elif unit == "g":
                return f"{q.to('oz'):.2f~P}"
            elif unit == "lb":
                return f"{q.to('kg'):.2f~P}"
            elif unit in ["L", "ml"]:
                return f"{q.to('gallon'):.2f~P}"
            elif unit == "gal":
                return f"{q.to('liter'):.2f~P}"
            elif unit in ["km", "m", "cm", "mm"]:
                return f"{q.to('ft'):.2f~P}"
            elif unit in ["ft", "in"]:
                return f"{q.to('m'):.2f~P}"
            elif unit == "n":
                return f"{q.to('kg*m/s^2'):.2f~P}"
        except Exception:
            return None

    def inline_add_conversion(self, match, converted):
        """Insert the converted unit in brackets right after the match."""
        cursor = self.textCursor()
        cursor.setPosition(match.end())
        cursor.insertText(f" ({converted})")
        self.inline_conversion = False

    def insert_image_from_path(self, path):
        image_uri = QUrl.fromLocalFile(path)
        cursor = self.textCursor()
        pixmap = QPixmap(path)
        max_width = int(self.viewport().width() * 0.6)
        max_height = int(self.viewport().height() * 0.6)

        if pixmap.width() > max_width or pixmap.height() > max_height:
            pixmap = pixmap.scaled(
                max_width,
                max_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

        cursor.insertBlock()
        cursor.insertImage(pixmap.toImage(), image_uri.toString())
        cursor.insertBlock()

    def request_graph(self):
        if self.graph_callback and self.textCursor().hasSelection():
            expression = self.textCursor().selection().toPlainText()

            # Extract only math function-looking content
            cleaned_expr = self.extract_valid_expression(expression)

            if cleaned_expr:
                self.graph_callback(cleaned_expr)
            else:
                QMessageBox.warning(self, "Invalid Function", "Please select a valid mathematical expression.")

    def extract_valid_expression(self, text):
        # Only allow characters used in math expressions
        allowed = re.sub(r"[^0-9+\-*/^().xeπpialnsqrtgco% ]", "", text)
        allowed = allowed.replace("^", "**")  # Convert ^ to Python-style power

        try:
            # Test-evaluate before passing to graph
            x = np.linspace(-10, 10, 100)
            self.aeval.symtable['x'] = x
            y = self.aeval.eval(allowed)
            if isinstance(y, np.ndarray):
                return allowed
        except:
            pass
        return ""

    def evaluate_selection(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        expression = cursor.selection().toPlainText()
        try:
            result = self.aeval.eval(expression)
            cursor.insertText(f" = {result:g}")
        except Exception as e:
            QMessageBox.warning(self, "Evaluation Error", f"Could not evaluate expression.\n\nError: {e}")

    def wikiTriggered(self):
        cursor = self.textCursor()
        self.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.main_window.wiki_dock)
        if not cursor.hasSelection():
            self.main_window.wiki_text.setText("Please select a word or phrase to search.")
            self.main_window.wiki_dock.setVisible(True)
            return

        expression = cursor.selectedText().strip()
        if not expression:
            self.main_window.wiki_text.setText("Selected text is empty.")
            self.main_window.wiki_dock.setVisible(True)
            return

        wikipedia.set_lang("en")

        sentences = int(self.config.get("wikiSentences"))

        try:
            result = wikipedia.summary(expression, sentences=sentences, auto_suggest=True)
            self.main_window.wiki_text.setText(f"{result}")

            self.main_window.wiki_dock.setVisible(True)

        except wikipedia.exceptions.DisambiguationError as e:
            try:
                suggestion = e.options[0]
                result = wikipedia.summary(suggestion, sentences=2)
                self.main_window.wiki_text.setText(f"**{suggestion}** (suggested from '{expression}')\n\n{result}")
                self.main_window.wiki_dock.setVisible(True)
            except Exception as inner_e:
                self.main_window.wiki_text.setText(f"Couldn't fetch suggestion:\n{str(inner_e)}")
                self.main_window.wiki_dock.setVisible(True)

        except wikipedia.exceptions.PageError:
            self.main_window.wiki_text.setText(f"No page found for '{expression}'.")
            self.main_window.wiki_dock.setVisible(True)

        except Exception as e:
            self.main_window.wiki_text.setText(f"Error: {str(e)}")
            self.main_window.wiki_dock.setVisible(True)

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)

        # Standard editing options
        undo_action = context_menu.addAction("Undo")
        undo_action.setEnabled(self.document().isUndoAvailable())
        undo_action.triggered.connect(self.undo)
        redo_action = context_menu.addAction("Redo")
        redo_action.setEnabled(self.document().isRedoAvailable())
        redo_action.triggered.connect(self.redo)
        context_menu.addSeparator()
        cut_action = context_menu.addAction("Cut")
        cut_action.setEnabled(self.textCursor().hasSelection())
        cut_action.triggered.connect(self.cut)
        copy_action = context_menu.addAction("Copy")
        copy_action.setEnabled(self.textCursor().hasSelection())
        copy_action.triggered.connect(self.copy)
        paste_action = context_menu.addAction("Paste")
        paste_action.setEnabled(self.canPaste())
        paste_action.triggered.connect(self.paste)
        select_all_action = context_menu.addAction("Select All")
        select_all_action.triggered.connect(self.selectAll)
        context_menu.addSeparator()

        # Engineering tool options
        eval_action = context_menu.addAction("🧮 Evaluate Expression")
        eval_action.setEnabled(self.textCursor().hasSelection())
        eval_action.triggered.connect(self.evaluate_selection)

        graph_action = context_menu.addAction("📈 Graph Function")
        graph_action.setEnabled(self.textCursor().hasSelection())
        graph_action.triggered.connect(self.request_graph)

        context_menu.addSeparator()

        wiki_action = context_menu.addAction("📚 Wikipedia")
        wiki_action.triggered.connect(self.wikiTriggered)

        context_menu.exec(event.globalPos())

    def set_format(self, fmt_type):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            cursor.select(cursor.SelectionType.WordUnderCursor)
        fmt = QTextCharFormat()
        current_fmt = cursor.charFormat()
        if fmt_type == "bold":
            fmt.setFontWeight(
                QFont.Weight.Normal if current_fmt.fontWeight() == QFont.Weight.Bold else QFont.Weight.Bold)
        elif fmt_type == "italic":
            fmt.setFontItalic(not current_fmt.fontItalic())
        elif fmt_type == "underline":
            fmt.setFontUnderline(not current_fmt.fontUnderline())
        cursor.mergeCharFormat(fmt)
        self.mergeCurrentCharFormat(fmt)

    def insert_image(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Insert Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if filename:
            self.insert_image_from_path(filename)


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
        self.setWindowTitle("EngiNote")
        self.setGeometry(100, 100, 1200, 800)
        self.base_dir = os.path.join(os.getenv("LOCALAPPDATA"), "EngiNote")
        os.makedirs(self.base_dir, exist_ok=True)
        self.board_dir = None
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

        self.todo_dock = todo.ToDoDockWidget(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.todo_dock)
        self.todo_dock.hide()

        self.chapters_dock = QDockWidget("Chapters")
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

        inline_code_action = QAction("</>", self)
        inline_code_action.setIcon(QIcon.fromTheme("code-context"))
        inline_code_action.triggered.connect(
            lambda: self.get_current_editor().insert_inline_code() if self.get_current_editor() else None)
        toolbar.addAction(inline_code_action)

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

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.triggerSettings)
        self.menuBar().addAction(settings_action)

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
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
