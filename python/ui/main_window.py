
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QColor, QFont, QPainter, QTextFormat
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog,
    QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMenu, QMessageBox, QPlainTextEdit, QPushButton,
    QSplitter, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget
)


STYLE = """
QWidget {
    background: #181818;
    color: #d4d4d4;
    font-family: 'Segoe UI';
    font-size: 13px;
}
QLineEdit, QComboBox, QPlainTextEdit, QTreeWidget {
    background: #1f1f1f;
    border: 1px solid #383838;
    border-radius: 5px;
    padding: 6px;
    selection-background-color: #264f78;
}
QLineEdit:focus, QComboBox:focus {
    border-color: #007acc;
}
QPushButton {
    background: #303030;
    border: 1px solid #454545;
    border-radius: 5px;
    padding: 8px 13px;
}
QPushButton:hover {
    background: #414141;
}
QPushButton:disabled {
    color: #777777;
    background: #252525;
}
QPushButton#compare {
    background: #007acc;
    color: white;
    border: none;
    font-weight: bold;
}
QPushButton#compare:hover {
    background: #1689d1;
}
QCheckBox {
    spacing: 7px;
}
QSplitter::handle {
    background: #454545;
}
QSplitter::handle:hover {
    background: #606060;
}
QTabWidget::pane {
    border: none;
}
QTabBar::tab {
    background: #202020;
    color: #aaaaaa;
    padding: 11px 23px;
    border-bottom: 2px solid transparent;
}
QTabBar::tab:selected {
    color: white;
    background: #292929;
    border-bottom: 2px solid #007acc;
}
QTabBar::tab:hover {
    background: #303030;
}
QMenu {
    background: #252525;
    border: 1px solid #454545;
    padding: 5px;
}
QMenu::item {
    padding: 9px 22px;
}
QMenu::item:selected {
    background: #094771;
}
QMenu::item:disabled {
    color: #777777;
}
QHeaderView::section {
    background: #252525;
    color: #cccccc;
    border: none;
    border-bottom: 1px solid #444444;
    padding: 8px;
}
QStatusBar {
    color: #999999;
}
"""


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()

        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setFont(QFont("Consolas", 11))

        self.line_number_area = QWidget(self)
        self.line_number_area.paintEvent = self.paint_line_numbers

        self.blockCountChanged.connect(self.update_line_number_width)
        self.updateRequest.connect(self.update_line_number_area)

        self.update_line_number_width()

    def line_number_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 15 + self.fontMetrics().horizontalAdvance("9") * digits

    def update_line_number_width(self, *_):
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(), self.line_number_area.width(), rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self.update_line_number_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)

        rect = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(
                rect.left(),
                rect.top(),
                self.line_number_width(),
                rect.height()
            )
        )

    def paint_line_numbers(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#252525"))
        painter.setPen(QColor("#858585"))

        block = self.firstVisibleBlock()
        number = block.blockNumber()
        top = round(
            self.blockBoundingGeometry(block)
            .translated(self.contentOffset()).top()
        )

        while block.isValid() and top <= event.rect().bottom():
            height = round(self.blockBoundingRect(block).height())

            if block.isVisible() and top + height >= event.rect().top():
                painter.drawText(
                    0, top,
                    self.line_number_area.width() - 6,
                    height,
                    Qt.AlignRight | Qt.AlignVCenter,
                    str(number + 1)
                )

            block = block.next()
            number += 1
            top += height


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Diff Tool")
        self.resize(1350, 850)
        self.setMinimumSize(900, 600)

        self.create_interface()
        self.statusBar().showMessage("Ready")

    def create_interface(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(16, 12, 16, 8)
        root.setSpacing(10)

        title = QLabel("Diff Tool")
        title.setStyleSheet(
            "font-size: 23px; font-weight: bold; color: white;"
        )
        root.addWidget(title)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_files_tab(), "Files")
        self.tabs.addTab(self.create_directories_tab(), "Directories")
        self.tabs.currentChanged.connect(self.on_tab_changed)

        root.addWidget(self.tabs, 1)

    def create_files_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 12, 4, 4)
        layout.setSpacing(12)

        paths = QHBoxLayout()

        self.left_path = QLineEdit()
        self.left_path.setPlaceholderText("Original file...")

        self.right_path = QLineEdit()
        self.right_path.setPlaceholderText("Modified file...")

        left_browse = QPushButton("Browse")
        right_browse = QPushButton("Browse")

        left_browse.clicked.connect(
            lambda: self.choose_file(self.left_path, self.left_editor)
        )
        right_browse.clicked.connect(
            lambda: self.choose_file(self.right_path, self.right_editor)
        )

        paths.addWidget(self.left_path, 1)
        paths.addWidget(left_browse)
        paths.addWidget(self.right_path, 1)
        paths.addWidget(right_browse)

        layout.addLayout(paths)

        settings = QHBoxLayout()

        settings.addWidget(QLabel("Algorithm"))

        self.algorithm = QComboBox()
        self.algorithm.addItems(["Myers", "LCS"])
        settings.addWidget(self.algorithm)

        settings.addSpacing(10)
        settings.addWidget(QLabel("Level"))

        self.level = QComboBox()
        self.level.addItems(["Lines", "Words", "Characters"])
        settings.addWidget(self.level)

        settings.addSpacing(10)

        self.ignore_spaces = QCheckBox("Ignore whitespace")
        self.ignore_case = QCheckBox("Ignore case")

        settings.addWidget(self.ignore_spaces)
        settings.addWidget(self.ignore_case)
        settings.addStretch()

        compare = QPushButton("Compare")
        compare.setObjectName("compare")
        compare.clicked.connect(self.compare_files)
        settings.addWidget(compare)

        layout.addLayout(settings)

        self.left_editor = CodeEditor()
        self.right_editor = CodeEditor()

        editors = QSplitter(Qt.Horizontal)
        editors.setHandleWidth(5)

        for label_text, editor in [
            ("ORIGINAL", self.left_editor),
            ("MODIFIED", self.right_editor)
        ]:
            panel = QWidget()
            panel_layout = QVBoxLayout(panel)
            panel_layout.setContentsMargins(0, 0, 0, 0)
            panel_layout.setSpacing(6)

            label = QLabel(label_text)
            label.setStyleSheet(
                "color: #9cdcfe; font-weight: bold;"
            )

            panel_layout.addWidget(label)
            panel_layout.addWidget(editor, 1)
            editors.addWidget(panel)

        editors.setSizes([650, 650])

        self.editor_splitter = editors

        # Comparison statistics and export
        stats = QHBoxLayout()

        self.result_label = QLabel("No comparison performed")
        self.result_label.setStyleSheet("color: #999999;")

        stats.addWidget(self.result_label)
        stats.addStretch()

        self.export_button = QPushButton("Export diff  ▾")
        self.export_button.setEnabled(False)

        export_menu = QMenu(self)
        self.unified_action = export_menu.addAction(
            "Unified diff (.diff)"
        )
        self.json_action = export_menu.addAction(
            "JSON report (.json) — coming later"
        )
        self.json_action.setEnabled(False)

        self.unified_action.triggered.connect(self.export_diff)
        self.export_button.setMenu(export_menu)

        stats.addWidget(self.export_button)

        # Unified diff preview
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(5)

        self.preview_toggle = QPushButton("▾  Unified diff (preview)")
        self.preview_toggle.setCheckable(True)
        self.preview_toggle.setChecked(True)
        self.preview_toggle.clicked.connect(self.toggle_preview)

        self.preview_editor = QPlainTextEdit()
        self.preview_editor.setReadOnly(True)
        self.preview_editor.setFont(QFont("Consolas", 10))
        self.preview_editor.setPlaceholderText(
            "Unified diff preview will appear after "
            "the C++ comparison engine is connected."
        )

        preview_layout.addWidget(self.preview_toggle)
        preview_layout.addWidget(self.preview_editor, 1)

        vertical = QSplitter(Qt.Vertical)
        vertical.setHandleWidth(5)
        vertical.addWidget(editors)
        vertical.addWidget(preview_container)
        vertical.setSizes([560, 180])

        layout.addWidget(vertical, 1)
        layout.addLayout(stats)

        return page

    def create_directories_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 12, 4, 4)
        layout.setSpacing(12)

        paths = QHBoxLayout()

        self.left_directory = QLineEdit()
        self.left_directory.setPlaceholderText("Original directory...")

        self.right_directory = QLineEdit()
        self.right_directory.setPlaceholderText("Modified directory...")

        left_browse = QPushButton("Browse")
        right_browse = QPushButton("Browse")

        left_browse.clicked.connect(
            lambda: self.choose_directory(self.left_directory)
        )
        right_browse.clicked.connect(
            lambda: self.choose_directory(self.right_directory)
        )

        paths.addWidget(self.left_directory, 1)
        paths.addWidget(left_browse)
        paths.addWidget(self.right_directory, 1)
        paths.addWidget(right_browse)

        layout.addLayout(paths)

        options = QHBoxLayout()

        self.recursive = QCheckBox("Include subdirectories")
        self.recursive.setChecked(True)

        options.addWidget(self.recursive)
        options.addStretch()

        compare = QPushButton("Compare directories")
        compare.setObjectName("compare")
        compare.clicked.connect(self.compare_directories)

        options.addWidget(compare)
        layout.addLayout(options)

        self.directory_tree = QTreeWidget()
        self.directory_tree.setHeaderLabels([
            "Relative path", "Status", "Original", "Modified"
        ])

        self.directory_tree.setColumnWidth(0, 400)
        self.directory_tree.setAlternatingRowColors(True)

        layout.addWidget(self.directory_tree, 1)

        self.directory_status = QLabel(
            "Select two directories to begin."
        )
        self.directory_status.setStyleSheet("color: #999999;")
        layout.addWidget(self.directory_status)

        return page

    def choose_file(self, path_field, editor):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select text file",
            "",
            "Text files (*.txt *.py *.cpp *.hpp *.h *.json *.md);;"
            "All files (*)"
        )

        if not filename:
            return

        try:
            content = Path(filename).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            QMessageBox.warning(
                self, "Cannot open file", str(error)
            )
            return

        path_field.setText(filename)
        editor.setPlainText(content)

        self.clear_comparison()
        self.statusBar().showMessage("File loaded")

    def choose_directory(self, field):
        directory = QFileDialog.getExistingDirectory(
            self, "Select directory"
        )

        if directory:
            field.setText(directory)
            self.directory_tree.clear()
            self.directory_status.setText(
                "Directory selected. Comparison not performed."
            )

    def clear_comparison(self):
        self.result_label.setText("No comparison performed")
        self.preview_editor.clear()
        self.export_button.setEnabled(False)

    def compare_files(self):
        left = Path(self.left_path.text())
        right = Path(self.right_path.text())

        if not left.is_file() or not right.is_file():
            QMessageBox.warning(
                self,
                "Missing files",
                "Please select two valid files first."
            )
            return

        self.clear_comparison()

        QMessageBox.information(
            self,
            "C++ engine not connected",
            "Both files are loaded successfully.\n\n"
            "The next development step is to connect "
            "LCS and Myers algorithms through pybind11."
        )

        self.statusBar().showMessage(
            "Files ready — C++ comparison not connected yet"
        )

    def compare_directories(self):
        left = Path(self.left_directory.text())
        right = Path(self.right_directory.text())

        if not left.is_dir() or not right.is_dir():
            QMessageBox.warning(
                self,
                "Missing directories",
                "Please select two valid directories."
            )
            return

        self.directory_tree.clear()
        self.directory_status.setText(
            "Directories selected. Comparison engine not connected."
        )

        QMessageBox.information(
            self,
            "Directory comparison",
            "Directory comparison will be implemented "
            "in the C++ core."
        )

    def toggle_preview(self, checked):
        self.preview_editor.setVisible(checked)
        self.preview_toggle.setText(
            "▾  Unified diff (preview)"
            if checked else
            "▸  Unified diff (preview)"
        )

    def export_diff(self):
        QMessageBox.information(
            self,
            "Export",
            "Unified diff export will become available "
            "after comparison is implemented."
        )

    def on_tab_changed(self, index):
        self.statusBar().showMessage(
            "File comparison" if index == 0
            else "Directory comparison"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
