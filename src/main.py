import sys
import os
import qdarktheme
import numpy as np
import time
import re
from io import BytesIO
from pathlib import Path
from asteval import Interpreter
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QTextEdit,
    QListWidget, QDockWidget, QInputDialog, QMenuBar, QMenu, QStackedWidget,
    QPushButton, QMessageBox, QFileDialog, QToolBar, QComboBox, QFontComboBox, QTabWidget
)
from PyQt6.QtGui import QAction, QTextOption, QTextCharFormat, QPixmap, QFont, QTextDocument, QSyntaxHighlighter
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QRegularExpression


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


class GraphWidget(QWidget):
    add_to_note_requested = pyqtSignal(QPixmap)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(5, 3), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.axes = self.figure.add_subplot(111)
        self.add_button = QPushButton("➕ Add to Note")
        self.add_button.clicked.connect(self.request_add_to_note)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.add_button)
        self.setLayout(layout)
        self.aeval = Interpreter()
        self.show_placeholder_message()

    def show_placeholder_message(self):
        self.axes.clear()
        self.axes.text(0.5, 0.5, 'Select a function in the editor,\nright-click, and choose\n"Graph Function"',
                       horizontalalignment='center', verticalalignment='center',
                       transform=self.axes.transAxes, fontsize=10, color='gray')
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        self.add_button.setEnabled(False)
        self.canvas.draw()

    def plot_function(self, expression):
        self.axes.clear()
        try:
            x = np.linspace(-10, 10, 500)
            self.aeval.symtable['x'] = x
            y = self.aeval.eval(expression)
            self.axes.plot(x, y)
            self.axes.set_title(f"f(x) = {expression}", size=10)
            self.axes.set_xlabel("x")
            self.axes.set_ylabel("f(x)")
            self.axes.grid(True)
            self.add_button.setEnabled(True)
        except Exception as e:
            self.axes.text(0.5, 0.5, 'Invalid Function',
                           horizontalalignment='center', verticalalignment='center',
                           transform=self.axes.transAxes, fontsize=12, color='red')
            self.axes.set_xticks([])
            self.axes.set_yticks([])
            self.add_button.setEnabled(False)
            print(f"Graphing Error: {e}")
        self.figure.tight_layout()
        self.canvas.draw()

    def request_add_to_note(self):
        buf = BytesIO()
        self.figure.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue(), 'PNG')
        if not pixmap.isNull():
            self.add_to_note_requested.emit(pixmap)


class RichTextEditor(QTextEdit):
    def __init__(self, parent=None, graph_callback=None):
        super().__init__(parent)
        self.setPlaceholderText("Write your notes here...")
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.aeval = Interpreter()
        self.graph_callback = graph_callback

        # Attach the syntax highlighter to the editor's document
        self.highlighter = FunctionHighlighter(self.document())

    def insert_image_from_path(self, path):
        image_uri = QUrl.fromLocalFile(path)
        cursor = self.textCursor()
        pixmap = QPixmap(path)
        editor_width = self.viewport().width() - 40
        if pixmap.width() > editor_width:
            pixmap = pixmap.scaledToWidth(editor_width, Qt.TransformationMode.SmoothTransformation)
        cursor.insertBlock()
        cursor.insertImage(pixmap.toImage(), image_uri.toString())
        cursor.insertBlock()

    def request_graph(self):
        if self.graph_callback and self.textCursor().hasSelection():
            expression = self.textCursor().selection().toPlainText()
            self.graph_callback(expression)

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
        context_menu.addSeparator()

        # Engineering tool options
        eval_action = context_menu.addAction("🧮 Evaluate Expression")
        eval_action.setEnabled(self.textCursor().hasSelection())
        eval_action.triggered.connect(self.evaluate_selection)
        graph_action = context_menu.addAction("📈 Graph Function")
        graph_action.setEnabled(self.textCursor().hasSelection())
        graph_action.triggered.connect(self.request_graph)
        context_menu.addSeparator()

        select_all_action = context_menu.addAction("Select All")
        select_all_action.triggered.connect(self.selectAll)

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
        # ... (rest of the __init__ is similar)
        self.setWindowTitle("EngiNote")
        self.setGeometry(100, 100, 1200, 800)
        self.base_dir = os.path.join(os.getenv("LOCALAPPDATA"), "EngiNote")
        os.makedirs(self.base_dir, exist_ok=True)
        self.board_dir = None
        self.current_subject = None
        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)
        self.placeholder = QLabel("📝 Double-click a chapter to start editing.")
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
        self.subjects_dock = QDockWidget("Subjects")
        self.subjects_list = QListWidget()
        self.subjects_dock.setWidget(self.subjects_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.subjects_dock)
        self.chapters_dock = QDockWidget("Chapters")
        self.chapters_list = QListWidget()
        self.chapters_dock.setWidget(self.chapters_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.chapters_dock)
        self.graph_dock = QDockWidget("Function Graph")
        self.graph_widget = GraphWidget()
        self.graph_dock.setWidget(self.graph_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.graph_dock)
        self.graph_widget.add_to_note_requested.connect(self.add_graph_to_current_note)
        self.setup_menu_bar()
        self.setup_toolbar()
        self.subjects_list.currentItemChanged.connect(self.load_chapters)
        self.chapters_list.itemDoubleClicked.connect(self.load_chapter_in_new_tab)
        self.check_or_create_board()

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
            self.load_chapters()  # Refresh list

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
        # --- THIS IS THE FIX ---
        # The save location is now correctly the parent folder of the note,
        # not a non-existent assets_path.
        save_folder = note_path.parent

        image_name = f"graph_{int(time.time())}.png"
        image_save_path = save_folder / image_name

        if not pixmap.save(str(image_save_path), "PNG"):
            QMessageBox.critical(self, "Save Error", "Could not save the graph image.")
            return
        editor.insert_image_from_path(str(image_save_path))

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
        view_menu.addSeparator()
        toggle_graph_dock = QAction("Toggle Graph", self)
        toggle_graph_dock.setCheckable(True)
        toggle_graph_dock.setChecked(True)
        toggle_graph_dock.triggered.connect(self.graph_dock.setVisible)
        view_menu.addAction(toggle_graph_dock)

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

            editor = RichTextEditor(graph_callback=self.handle_graph_request)
            editor.setProperty("file_path", str(note_path))

            # --- THE CORRECTED LOGIC ---
            # 1. Create a new document object.
            doc = QTextDocument(editor)
            # 2. Set its base URL to the folder containing the note.
            base_url = QUrl.fromLocalFile(str(note_path.parent) + os.sep)
            doc.setBaseUrl(base_url)
            # 3. Load the markdown content into our document.
            doc.setMarkdown(content)
            # 4. Give the fully prepared document to the editor.
            editor.setDocument(doc)
            # 5. NOW create the highlighter for the editor's actual document.
            editor.highlighter = FunctionHighlighter(editor.document())
            # --- END OF FIX ---

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
