from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QWidget,
)

from constants import (
    BUTTON_TINY_SIZE,
    COLOR_ACCENT_GOLD,
    COLOR_ACCENT_ORANGE,
    COLOR_DARKER_BG,
    COLOR_DARKEST_BG,
    COLOR_DELETE_HOVER,
    COLOR_DELETE_RED,
    COLOR_TEXT_LIGHT,
    COLOR_TEXT_MUTED,
)


class TodoItemWidget(QWidget):
    delete_requested = pyqtSignal()

    def __init__(self, text: str = "", parent: QWidget | None = None, *, completed: bool = False):
        super().__init__(parent)
        self.text: str = text
        self.completed: bool = completed
        self.is_editing: bool = False
        self._widgets_initialized: bool = False  # Флаг инициализации

        self.setStyleSheet("QWidget { background: transparent; }")
        self._setup_ui()
        self._update_appearance()
        self._widgets_initialized = True  # Виджеты инициализированы

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.completed)
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        self.checkbox.setStyleSheet(f"""
            QCheckBox {{ spacing: 8px; background: transparent; }}
            QCheckBox::indicator {{
                width: 16px; height: 16px;
                border: 2px solid {COLOR_ACCENT_GOLD};
                border-radius: 3px;
                background: {COLOR_DARKER_BG};
            }}
            QCheckBox::indicator:checked {{
                background: {COLOR_ACCENT_ORANGE};
                border: 2px solid {COLOR_ACCENT_ORANGE};
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid #F4A460;
            }}
        """)
        layout.addWidget(self.checkbox)

        self.text_label = QLabel(self.text)
        self.text_label.setWordWrap(True)
        self.text_label.setMinimumHeight(30)
        layout.addWidget(self.text_label, 1)

        self.edit_input = QLineEdit(self.text)
        self.edit_input.setVisible(False)
        self.edit_input.setMinimumHeight(30)
        self.edit_input.setStyleSheet(f"""
            QLineEdit {{
                font-family: "Times New Roman"; font-size: 12px;
                color: white; padding: 5px;
                background: #606060;
                border: 2px solid {COLOR_ACCENT_ORANGE};
                border-radius: 3px;
            }}
        """)
        self.edit_input.returnPressed.connect(self._finish_editing)
        self.edit_input.focusOutEvent = self._on_edit_focus_out
        layout.addWidget(self.edit_input, 1)

        self.delete_btn = QPushButton("✕")
        self.delete_btn.setFixedSize(*BUTTON_TINY_SIZE)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_DELETE_RED}; color: white;
                border: none; border-radius: 12px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {COLOR_DELETE_HOVER}; }}
        """)
        self.delete_btn.clicked.connect(self._request_delete)
        layout.addWidget(self.delete_btn)

    def _update_appearance(self) -> None:
        if not self._widgets_initialized:
            return

        if self.completed:
            self.text_label.setStyleSheet(f"""
                QLabel {{
                    font-family: "Times New Roman"; font-size: 12px;
                    color: {COLOR_TEXT_MUTED}; padding: 5px;
                    background: {COLOR_DARKEST_BG};
                    border: 1px solid #505050; border-radius: 3px;
                    text-decoration: line-through;
                }}
            """)
        else:
            self.text_label.setStyleSheet(f"""
                QLabel {{
                    font-family: "Times New Roman"; font-size: 12px;
                    color: {COLOR_TEXT_LIGHT}; padding: 5px;
                    background: #505050;
                    border: 1px solid #696969; border-radius: 3px;
                }}
            """)

    def _on_checkbox_changed(self, state: int) -> None:
        self.completed = state == Qt.CheckState.Checked.value
        self._update_appearance()

    def start_editing(self) -> None:
        if not self._widgets_initialized:
            return

        self.is_editing = True
        self.text_label.setVisible(False)
        self.edit_input.setVisible(True)
        self.edit_input.setText(self.text)
        self.edit_input.setFocus()
        self.edit_input.selectAll()

    def _finish_editing(self) -> None:
        if not self._widgets_initialized:
            return

        new_text = self.edit_input.text().strip()
        if new_text:
            self.text = new_text
            self.text_label.setText(new_text)
        self.is_editing = False
        self.edit_input.setVisible(False)
        self.text_label.setVisible(True)

    def _on_edit_focus_out(self, a0) -> None:
        if self._widgets_initialized:
            self._finish_editing()
        super().focusOutEvent(a0)

    def _request_delete(self) -> None:
        reply = QMessageBox.question(
            self,
            "Удаление задачи",
            f'Вы уверены, что хотите удалить задачу:\n"{self.text}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit()
