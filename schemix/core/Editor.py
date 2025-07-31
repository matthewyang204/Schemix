import json
import os
import re

import numpy as np
import wikipedia
from PyQt6.QtCore import Qt, QUrl, QRegularExpression, QEvent
from PyQt6.QtGui import QTextOption, QTextCharFormat, QPixmap, QFont, QTextDocument, QSyntaxHighlighter, \
    QTextCursor, QColor, QTextListFormat
from PyQt6.QtWidgets import (
    QTextEdit,
    QMenu, QMessageBox, QFileDialog, QToolTip
)
from asteval import Interpreter
from matplotlib import pyplot as plt
from pint import UnitRegistry


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


ureg = UnitRegistry()

UNIT_PATTERN = re.compile(r"\b(\d+(?:\.\d+)?)\s?(km/h|m/s|kg|g|L|ml|N|km|m|cm|mm|ft|in|lb|gal)\b", re.IGNORECASE)


class RichTextEditor(QTextEdit):
    def __init__(self, parent, graph_callback=None, inline=False):
        super().__init__(parent)
        self.setPlaceholderText("Write your notes here...")
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.aeval = Interpreter()
        self.graph_callback = graph_callback
        font = QFont("Consolas")
        font.setPointSize(24)
        self.setFont(font)

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

    def apply_title_format(self):
        cursor = self.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontPointSize(20)  # Big font
        fmt.setFontWeight(QFont.Weight.Bold)
        cursor.mergeCharFormat(fmt)

    def apply_subheading_format(self):
        cursor = self.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontPointSize(14)
        fmt.setFontWeight(QFont.Weight.DemiBold)
        fmt.setFontItalic(True)
        cursor.mergeCharFormat(fmt)

    def insert_bullet_list(self):
        cursor = self.textCursor()
        list_format = QTextListFormat()
        list_format.setStyle(QTextListFormat.Style.ListDisc)
        cursor.createList(list_format)

    def insert_numbered_list(self):
        cursor = self.textCursor()
        list_format = QTextListFormat()
        list_format.setStyle(QTextListFormat.Style.ListDecimal)
        cursor.createList(list_format)

    def insert_math_equation(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            QMessageBox.information(self, "No Selection", "Please select a LaTeX equation to render.")
            return

        latex_code = cursor.selection().toPlainText().strip()
        if not latex_code:
            return

        fig = plt.figure(figsize=(0.01, 0.01), dpi=300)
        fig.text(0.1, 0.5, f"${latex_code}$", fontsize=16)
        fig.patch.set_facecolor('white')

        # Save to correct path: Schemix/BoardName/SubjectName
        board_path = os.path.join("Schemix", self.main_window.board_dir)  # board_dir is just the board name
        subject_path = os.path.join(board_path, self.main_window.current_subject)
        os.makedirs(subject_path, exist_ok=True)

        # Auto-numbered filename like 1.png, 2.png...
        existing = [f for f in os.listdir(subject_path) if f.endswith(".png")]
        numbers = [int(re.search(r"(\d+)\.png", f).group(1)) for f in existing if re.search(r"(\d+)\.png", f)]
        next_num = max(numbers, default=0) + 1
        image_name = f"{next_num}.png"
        image_path = os.path.join(subject_path, image_name)

        try:
            fig.savefig(image_path, bbox_inches='tight', pad_inches=0.1)
            plt.close(fig)
            self.insert_image_from_path(image_path)
        except Exception as e:
            QMessageBox.warning(self, "Render Error", f"Failed to render LaTeX:\n{e}")

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