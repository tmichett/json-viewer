from __future__ import annotations

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QSyntaxHighlighter, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget
from pygments import lex
from pygments.lexers import JsonLexer, XmlLexer, YamlLexer
from pygments.token import Token

from json_viewer.adapters.types import DataFormat, ParseError
from json_viewer.ui.theme import ThemeManager

BRACE_CHARS = "{}[]"
ExtraSelection = QTextEdit.ExtraSelection


class LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor") -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return self._editor.line_number_area_width(), 0

    def paintEvent(self, event) -> None:
        self._editor.paint_line_numbers(event)


class PygmentsHighlighter(QSyntaxHighlighter):
    def __init__(self, document, theme_manager: ThemeManager) -> None:
        super().__init__(document)
        self._theme_manager = theme_manager
        self._format = DataFormat.JSON

    def set_format(self, fmt: DataFormat) -> None:
        self._format = fmt
        self.rehighlight()

    def _fmt(self, color: str, *, bold: bool = False) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        return fmt

    def _color_for_token(self, token, value: str, colors) -> QTextCharFormat:
        token_str = str(token)

        if token_str.startswith("Token.Punctuation"):
            if all(ch in BRACE_CHARS for ch in value):
                return self._fmt(colors.brace, bold=True)
            if value in ":,":
                return self._fmt(colors.null_color)
            return self._fmt(colors.brace)

        if token in Token.Name.Tag or token_str.endswith("Name.Tag"):
            return self._fmt(colors.node_key, bold=True)

        if token in Token.Name.Attribute or token_str.endswith("Name.Attribute"):
            return self._fmt(colors.integer)

        if "String" in token_str or "Literal.String" in token_str:
            return self._fmt(colors.node_value)

        if "Number" in token_str or "Literal.Number" in token_str:
            return self._fmt(colors.integer)

        if token in Token.Keyword or "Keyword" in token_str:
            return self._fmt(colors.node_key)

        if token in Token.Comment:
            return self._fmt(colors.null_color)

        if "Literal" in token_str:
            if value in ("true", "false"):
                return self._fmt(colors.bool_true if value == "true" else colors.bool_false)
            if value in ("null", "None", "~"):
                return self._fmt(colors.null_color)
            return self._fmt(colors.node_value)

        return self._fmt(colors.editor_fg)

    def highlightBlock(self, text: str) -> None:
        colors = self._theme_manager.colors
        lexer_map = {
            DataFormat.JSON: JsonLexer,
            DataFormat.YAML: YamlLexer,
            DataFormat.XML: XmlLexer,
        }
        lexer_cls = lexer_map.get(self._format, JsonLexer)

        offset = 0
        for token, value in lex(text, lexer_cls()):
            fmt = self._color_for_token(token, value, colors)
            token_str = str(token)
            if len(value) == 1 and value in BRACE_CHARS:
                self.setFormat(offset, 1, fmt)
            elif "Punctuation" in token_str and any(ch in BRACE_CHARS for ch in value):
                for index, ch in enumerate(value):
                    ch_fmt = self._fmt(colors.brace, bold=True) if ch in BRACE_CHARS else fmt
                    self.setFormat(offset + index, 1, ch_fmt)
            else:
                self.setFormat(offset, len(value), fmt)
            offset += len(value)


class CodeEditor(QPlainTextEdit):
    def __init__(self, theme_manager: ThemeManager, parent=None) -> None:
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._line_number_area = LineNumberArea(self)
        self._lint_errors: list[ParseError] = []
        self._brace_match_positions: list[tuple[int, int]] = []

        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTabStopDistance(20)

        font = QFont("Menlo, Monaco, Consolas, monospace")
        font.setPointSize(12)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        self.blockCountChanged.connect(self._update_line_number_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._update_brace_matching)
        self._update_line_number_width()

        self._highlighter = PygmentsHighlighter(self.document(), theme_manager)
        self.apply_theme()

    def line_number_area_width(self) -> int:
        digits = max(1, len(str(self.blockCount())))
        extra = 10 if self._lint_errors else 0
        return 12 + self.fontMetrics().horizontalAdvance("9") * digits + extra

    def _update_line_number_width(self) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_width()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def _error_lines(self) -> set[int]:
        return {err.line for err in self._lint_errors if err.line is not None}

    def paint_line_numbers(self, event) -> None:
        painter = QPainter(self._line_number_area)
        colors = self._theme_manager.colors
        painter.fillRect(event.rect(), QColor(colors.editor_bg))

        error_lines = self._error_lines()
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                line_no = block_number + 1
                number = str(line_no)
                if line_no in error_lines:
                    painter.setPen(QColor(colors.status_error))
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
                else:
                    painter.setPen(QColor(colors.null_color))
                painter.drawText(
                    0,
                    top,
                    self._line_number_area.width() - 4,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number,
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def set_lint_errors(self, errors: list[ParseError]) -> None:
        self._lint_errors = errors
        self._sync_extra_selections()
        self._update_line_number_width()
        self._line_number_area.update()

    def clear_lint_errors(self) -> None:
        self.set_lint_errors([])

    def _lint_selections(self) -> list[ExtraSelection]:
        if not self._lint_errors:
            return []

        colors = self._theme_manager.colors
        selections: list[ExtraSelection] = []

        for err in self._lint_errors[:8]:
            if err.line is None:
                continue
            block = self.document().findBlockByLineNumber(err.line - 1)
            if not block.isValid():
                continue

            selection = ExtraSelection()
            line_fill = QColor(colors.status_error)
            line_fill.setAlpha(35)
            selection.format.setBackground(line_fill)

            cursor = QTextCursor(block)
            if err.column is not None and err.column > 0:
                start = block.position() + min(err.column - 1, max(0, block.length() - 1))
                cursor.setPosition(start)
                cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
            else:
                cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)

            selection.format.setUnderlineColor(QColor(colors.status_error))
            selection.format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
            selection.cursor = cursor
            selections.append(selection)

        return selections

    def _brace_selections(self) -> list[ExtraSelection]:
        if not self._brace_match_positions:
            return []

        colors = self._theme_manager.colors
        selections: list[ExtraSelection] = []
        bg = QColor(colors.brace)
        bg.setAlpha(70)

        for start, end in self._brace_match_positions:
            selection = ExtraSelection()
            selection.format.setBackground(bg)
            selection.format.setForeground(QColor(colors.brace))
            selection.format.setFontWeight(QFont.Weight.Bold)

            cursor = QTextCursor(self.document())
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            selection.cursor = cursor
            selections.append(selection)

        return selections

    def _sync_extra_selections(self) -> None:
        self.setExtraSelections(self._lint_selections() + self._brace_selections())

    def _find_matching_brace(self, text: str, index: int) -> int | None:
        if index < 0 or index >= len(text):
            return None

        ch = text[index]
        pairs = {"{": "}", "[": "]", "}": "{", "]": "["}
        if ch not in pairs:
            return None

        forward = ch in "{["
        partner = pairs[ch]
        step = 1 if forward else -1
        depth = 0
        position = index + step

        while 0 <= position < len(text):
            current = text[position]
            if current == ch and forward:
                depth += 1
            elif current == partner:
                if depth == 0:
                    return position
                depth -= 1
            position += step

        return None

    def _update_brace_matching(self) -> None:
        cursor = self.textCursor()
        position = cursor.position()
        text = self.toPlainText()

        self._brace_match_positions = []
        for offset in (0, -1):
            index = position + offset
            if index < 0 or index >= len(text):
                continue
            if text[index] not in BRACE_CHARS:
                continue
            match = self._find_matching_brace(text, index)
            if match is not None:
                self._brace_match_positions = [(index, index + 1), (match, match + 1)]
                break

        self._sync_extra_selections()

    def go_to_error(self, error: ParseError | None = None) -> bool:
        target = error or (self._lint_errors[0] if self._lint_errors else None)
        if target is None or target.line is None:
            return False

        block = self.document().findBlockByLineNumber(target.line - 1)
        if not block.isValid():
            return False

        cursor = QTextCursor(block)
        if target.column is not None and target.column > 0:
            cursor.setPosition(block.position() + min(target.column - 1, max(0, block.length() - 1)))
        self.setTextCursor(cursor)
        self.centerCursor()
        return True

    def set_data_format(self, fmt: DataFormat) -> None:
        self._highlighter.set_format(fmt)

    def apply_theme(self) -> None:
        colors = self._theme_manager.colors
        self.setStyleSheet(
            f"""
            QPlainTextEdit {{
                background-color: {colors.editor_bg};
                color: {colors.editor_fg};
                border: none;
            }}
            """
        )
        self._highlighter.rehighlight()
        self._sync_extra_selections()
