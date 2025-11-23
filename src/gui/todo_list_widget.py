from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from constants import (
    COLOR_ACCENT_BROWN,
    COLOR_ACCENT_GOLD,
    TASK_ITEM_HEIGHT,
)
from gui.todo_item_widget import TodoItemWidget


class TodoListWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.tasks: list = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        title = QLabel("Задачи")
        title.setFont(QFont("Times New Roman", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLOR_ACCENT_GOLD}; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.add_task_input = QLineEdit()
        self.add_task_input.setPlaceholderText("Добавить новую задачу...")
        self.add_task_input.setStyleSheet(
            f"border: 2px solid {COLOR_ACCENT_BROWN}; border-radius: 5px; margin: 0px 10px;"
        )
        self.add_task_input.returnPressed.connect(self._add_new_task)
        layout.addWidget(self.add_task_input)

        self.tasks_list = QListWidget()
        self.tasks_list.setAlternatingRowColors(True)
        self.tasks_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(self.tasks_list)

    def _add_new_task(self) -> None:
        text = self.add_task_input.text().strip()
        if text:
            self._create_task_item(text)
            self.add_task_input.clear()

    def _create_task_item(self, text: str) -> None:
        item = QListWidgetItem()
        item.setSizeHint(QSize(0, TASK_ITEM_HEIGHT))
        item_widget = TodoItemWidget(text, completed=False)
        item_widget.delete_requested.connect(lambda: self._delete_task_item(item))

        def start_edit():
            if item_widget._widgets_initialized and not item_widget.completed:
                item_widget.start_editing()

        self.tasks_list.addItem(item)
        self.tasks_list.setItemWidget(item, item_widget)

        def handle_double_click(clicked_item):
            if clicked_item == item:
                start_edit()

        self.tasks_list.itemDoubleClicked.connect(handle_double_click)

    def _delete_task_item(self, item: QListWidgetItem) -> None:
        row = self.tasks_list.row(item)
        self.tasks_list.takeItem(row)
