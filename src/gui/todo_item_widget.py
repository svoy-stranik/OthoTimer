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
)


class TodoItemWidget(QWidget):
    delete_requested = pyqtSignal()

    def __init__(self, text: str = "", parent: QWidget | None = None, *, completed: bool = False):
        super().__init__(parent)
        self.text: str = text
        self.completed: bool = completed
        self.is_editing: bool = False
        self._widgets_initialized: bool = False

        self._setup_ui()
        self._update_appearance()
        self._widgets_initialized = True

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 10, 5)
        layout.setSpacing(8)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.completed)
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        self.checkbox.setStyleSheet("margin-left: 10px;")
        layout.addWidget(self.checkbox)

        self.text_label = QLabel(self.text)
        self.text_label.setWordWrap(True)
        self.text_label.setMinimumHeight(30)
        layout.addWidget(self.text_label, 1)

        self.edit_input = QLineEdit(self.text)
        self.edit_input.setVisible(False)
        self.edit_input.setMinimumHeight(30)
        self.edit_input.returnPressed.connect(self._finish_editing)
        self.edit_input.focusOutEvent = self._on_edit_focus_out
        layout.addWidget(self.edit_input, 1)

        self.delete_btn = QPushButton("✕")
        self.delete_btn.setFixedSize(*BUTTON_TINY_SIZE)
        self.delete_btn.setStyleSheet("border: none; border-radius: 12px; font-weight: bold;")
        self.delete_btn.clicked.connect(self._request_delete)
        layout.addWidget(self.delete_btn)

    def _update_appearance(self) -> None:
        if not self._widgets_initialized:
            return

        if self.completed:
            self.text_label.setStyleSheet("text-decoration: line-through; color: gray;")
        else:
            self.text_label.setStyleSheet("")

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
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Удаление задачи")
        msg_box.setText(f'Вы уверены, что хотите удалить задачу:\n"{self.text}"?')
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        reply = msg_box.exec()
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit()
