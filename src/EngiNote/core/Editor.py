from PyQt6.QtCore import Qt, QUrl, QRegularExpression
from PyQt6.QtGui import QTextOption, QTextCharFormat, QPixmap, QFont, QTextDocument, QSyntaxHighlighter
from PyQt6.QtWidgets import (
    QTextEdit,
    QMenu, QMessageBox, QFileDialog
)
from asteval import Interpreter


class FunctionHighlighter(QSyntaxHighlighter):
    """A syntax highlighter for recognizing math functions and constants."""

    def __init__(self, parent: QTextDocument):
        super().__init__(parent)
        self.highlighting_rules = []

        # Define the format for keywords (e.g., functions, constants)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(Qt.GlobalColor.cyan)
        keyword_format.setFontItalic(True)

        # Define the keywords to highlight
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