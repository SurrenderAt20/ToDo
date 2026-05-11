from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QPoint, QThread, Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from claude_client import ClaudeClient
from models import Task
from storage import TaskStorage
from ui.chat_input import ChatInput
from ui.settings_dialog import SettingsDialog
from ui.styles import (
    ACCENT_BG_GREEN,
    ACCENT_GREEN,
    BG_CARD,
    BG_MAIN,
    BG_TITLEBAR,
    BORDER,
    SCROLLBAR_QSS,
    TEXT_MUTED,
    TEXT_PRIMARY,
)
from ui.task_item import TaskItem


class _ClaudeWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, client: ClaudeClient, message: str, summary: str) -> None:
        super().__init__()
        self._client = client
        self._message = message
        self._summary = summary

    def run(self) -> None:
        try:
            result = self._client.parse_intent(self._message, self._summary)
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))


class _Toast(QLabel):
    def __init__(self, text: str, parent: QWidget) -> None:
        super().__init__(text, parent)
        self.setStyleSheet(
            f"QLabel {{ background: {ACCENT_BG_GREEN}; color: {ACCENT_GREEN}; "
            f"border: 1px solid {ACCENT_GREEN}; border-radius: 8px; padding: 6px 14px; font-size: 12px; }}"
        )
        self.adjustSize()
        self._reposition(parent)
        self.show()
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2500, self.deleteLater)

    def _reposition(self, parent: QWidget) -> None:
        x = (parent.width() - self.width()) // 2
        y = parent.height() - self.height() - 70
        self.move(x, y)


class TodoWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._storage = TaskStorage()
        self._claude = ClaudeClient()
        self._tasks: list[Task] = []
        self._task_items: dict[str, TaskItem] = {}
        self._active_project: str | None = None
        self._drag_pos: QPoint | None = None
        self._worker: _ClaudeWorker | None = None
        self._setup_window()
        self._setup_ui()
        self._load_tasks()
        self._check_api_key()

    # ── Window setup ────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setFixedSize(320, 580)
        self.setObjectName("MainWidget")
        self.setStyleSheet(
            f"QWidget#MainWidget {{ background: {BG_MAIN}; border-radius: 12px; border: 1px solid {BORDER}; }}"
        )

    # ── UI construction ──────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_titlebar())

        self._tab_container = self._build_tab_bar()
        root.addWidget(self._tab_container)

        separator = QFrame(self)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"color: {BORDER};")
        root.addWidget(separator)

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background: {BG_MAIN}; border: none; }}"
            f"QWidget {{ background: {BG_MAIN}; }}"
            + SCROLLBAR_QSS
        )
        self._list_widget = QWidget()
        self._list_widget.setStyleSheet(f"background: {BG_MAIN};")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(8, 8, 8, 8)
        self._list_layout.setSpacing(0)
        self._list_layout.addStretch()
        self._scroll.setWidget(self._list_widget)
        root.addWidget(self._scroll, 1)

        self._chat = ChatInput(self)
        self._chat.message_submitted.connect(self._on_message)
        root.addWidget(self._chat)

    def _build_titlebar(self) -> QWidget:
        bar = QWidget(self)
        bar.setFixedHeight(44)
        bar.setStyleSheet(
            f"QWidget {{ background: {BG_TITLEBAR}; border-top-left-radius: 12px; border-top-right-radius: 12px; }}"
        )
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(6)

        self._status_dot = QLabel("●", bar)
        self._status_dot.setStyleSheet(f"color: {ACCENT_GREEN}; font-size: 10px;")
        layout.addWidget(self._status_dot)

        title = QLabel("todo", bar)
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        layout.addStretch()

        add_btn = QPushButton("+", bar)
        add_btn.setFixedSize(28, 28)
        add_btn.setStyleSheet(
            f"QPushButton {{ background: {ACCENT_BG_GREEN}; color: {ACCENT_GREEN}; "
            f"border: none; border-radius: 6px; font-size: 18px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {ACCENT_GREEN}; color: #000; }}"
        )
        add_btn.clicked.connect(self._quick_add)
        layout.addWidget(add_btn)

        settings_btn = QPushButton("⚙", bar)
        settings_btn.setFixedSize(28, 28)
        settings_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {TEXT_MUTED}; border: none; font-size: 16px; }}"
            f"QPushButton:hover {{ color: {TEXT_PRIMARY}; }}"
        )
        settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(settings_btn)

        minimize_btn = QPushButton("−", bar)
        minimize_btn.setFixedSize(28, 28)
        minimize_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {TEXT_MUTED}; border: none; font-size: 16px; }}"
            f"QPushButton:hover {{ background: {BORDER}; color: {TEXT_PRIMARY}; border-radius: 6px; }}"
        )
        minimize_btn.clicked.connect(self.showMinimized)
        layout.addWidget(minimize_btn)

        close_btn = QPushButton("✕", bar)
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {TEXT_MUTED}; border: none; font-size: 13px; }}"
            f"QPushButton:hover {{ background: #3a1a1a; color: #f87171; border-radius: 6px; }}"
        )
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        return bar

    def _build_tab_bar(self) -> QWidget:
        container = QWidget(self)
        container.setStyleSheet(f"background: {BG_MAIN};")
        self._tab_layout = QHBoxLayout(container)
        self._tab_layout.setContentsMargins(8, 6, 8, 2)
        self._tab_layout.setSpacing(4)
        self._tab_buttons: list[QPushButton] = []
        self._tab_layout.addStretch()
        return container

    def _rebuild_tabs(self) -> None:
        for btn in self._tab_buttons:
            btn.deleteLater()
        self._tab_buttons.clear()
        # Remove stretch before adding buttons
        while self._tab_layout.count():
            item = self._tab_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        projects = ["Alle"] + sorted({t.project for t in self._tasks if t.project})
        for proj in projects:
            btn = QPushButton(proj, self._tab_container)
            btn.setCheckable(True)
            btn.setStyleSheet(self._tab_style())
            active_proj = self._active_project
            btn.setChecked((proj == "Alle" and active_proj is None) or proj == active_proj)
            btn.clicked.connect(lambda checked, p=proj: self._on_tab_clicked(p))
            self._tab_layout.addWidget(btn)
            self._tab_buttons.append(btn)

        self._tab_layout.addStretch()

    def _tab_style(self) -> str:
        return (
            f"QPushButton {{ background: transparent; border: none; color: {TEXT_MUTED}; "
            f"font-size: 12px; padding: 4px 10px; border-radius: 8px; }}"
            f"QPushButton:checked {{ background: {ACCENT_BG_GREEN}; color: {ACCENT_GREEN}; font-weight: bold; }}"
            f"QPushButton:hover:!checked {{ color: {TEXT_PRIMARY}; background: {BORDER}; }}"
        )

    def _on_tab_clicked(self, project: str) -> None:
        self._active_project = None if project == "Alle" else project
        for btn in self._tab_buttons:
            is_active = (btn.text() == "Alle" and self._active_project is None) or btn.text() == self._active_project
            btn.setChecked(is_active)
        self._render_tasks()

    # ── Task rendering ───────────────────────────────────────────────────────

    def _load_tasks(self) -> None:
        self._tasks = self._storage.load()
        self._rebuild_tabs()
        self._render_tasks()

    def _sorted_tasks(self) -> list[Task]:
        filtered = self._tasks
        if self._active_project:
            filtered = [t for t in filtered if t.project == self._active_project]
        pending = sorted([t for t in filtered if not t.done], key=lambda t: t.created_at, reverse=True)
        done = sorted([t for t in filtered if t.done], key=lambda t: t.created_at, reverse=True)
        return pending + done

    def _render_tasks(self) -> None:
        # Remove all existing task items
        for item in self._task_items.values():
            item.setParent(None)
            item.deleteLater()
        self._task_items.clear()

        # Remove all items except trailing stretch
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for task in self._sorted_tasks():
            widget = TaskItem(task, self._list_widget)
            widget.toggled.connect(self._on_task_toggled)
            widget.deleted.connect(self._on_task_deleted)
            self._list_layout.insertWidget(self._list_layout.count() - 1, widget)
            self._task_items[task.id] = widget

    # ── Event handlers ───────────────────────────────────────────────────────

    def _on_task_toggled(self, task_id: str, done: bool) -> None:
        self._storage.update(task_id, done=done)
        for t in self._tasks:
            if t.id == task_id:
                t.done = done
                break

    def _on_task_deleted(self, task_id: str) -> None:
        self._storage.delete(task_id)
        self._tasks = [t for t in self._tasks if t.id != task_id]
        self._rebuild_tabs()
        self._render_tasks()

    def _quick_add(self) -> None:
        self._chat._input.setFocus()

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self)
        dlg.exec()
        self._check_api_key()

    def _check_api_key(self) -> None:
        from config import get_api_key
        if get_api_key():
            self._set_status("green")
        else:
            self._set_status("red")

    def _set_status(self, color: str) -> None:
        colors = {"green": ACCENT_GREEN, "red": "#f87171", "orange": "#f97316"}
        self._status_dot.setStyleSheet(f"color: {colors.get(color, ACCENT_GREEN)}; font-size: 10px;")

    # ── Claude integration ───────────────────────────────────────────────────

    def _task_summary(self) -> str:
        if not self._tasks:
            return "Ingen opgaver endnu."
        lines = []
        for t in self._tasks:
            status = "✓" if t.done else "○"
            proj = f" [{t.project}]" if t.project else ""
            cat = f" ({t.category})" if t.category else ""
            lines.append(f"{status} {t.name}{proj}{cat}")
        return "\n".join(lines)

    def _on_message(self, text: str) -> None:
        from config import get_api_key
        if not get_api_key():
            task = Task(name=text)
            self._storage.add(task)
            self._tasks.append(task)
            self._rebuild_tabs()
            self._render_tasks()
            _Toast("Opgave tilføjet ✓", self)
            return
        if self._worker and self._worker.isRunning():
            return
        self._set_status("orange")
        self._chat.set_loading(True)
        self._worker = _ClaudeWorker(self._claude, text, self._task_summary())
        self._worker.finished.connect(self._on_claude_result)
        self._worker.error.connect(self._on_claude_error)
        self._worker.start()

    def _on_claude_result(self, result: dict[str, Any]) -> None:
        self._set_status("green")
        self._chat.set_loading(False)
        action = result.get("action", "")
        data = result.get("data", {})

        if action == "add_task":
            task = Task(
                name=data.get("name", "Ny opgave"),
                category=data.get("category"),
                project=data.get("project"),
                notes=data.get("notes"),
            )
            self._storage.add(task)
            self._tasks.append(task)
            self._rebuild_tabs()
            self._render_tasks()
            _Toast("Opgave tilføjet ✓", self)

        elif action == "complete_task":
            task_name = data.get("task_name", "")
            task = self._fuzzy_find(task_name, done=False)
            if task:
                self._storage.update(task.id, done=True)
                task.done = True
                self._render_tasks()
                _Toast("Opgave markeret færdig ✓", self)
            else:
                self._chat.show_reply(f"Kunne ikke finde opgave: \"{task_name}\"")

        elif action == "delete_task":
            task_name = data.get("task_name", "")
            task = self._fuzzy_find(task_name)
            if task:
                self._storage.delete(task.id)
                self._tasks = [t for t in self._tasks if t.id != task.id]
                self._rebuild_tabs()
                self._render_tasks()
                _Toast("Opgave slettet ✓", self)
            else:
                self._chat.show_reply(f"Kunne ikke finde opgave: \"{task_name}\"")

        elif action == "update_task":
            task_name = data.get("task_name", "")
            task = self._fuzzy_find(task_name)
            if task:
                kwargs: dict[str, Any] = {}
                if data.get("new_name"):
                    kwargs["name"] = data["new_name"]
                if "category" in data:
                    kwargs["category"] = data["category"]
                if "project" in data:
                    kwargs["project"] = data["project"]
                if "notes" in data:
                    kwargs["notes"] = data["notes"]
                self._storage.update(task.id, **kwargs)
                for k, v in kwargs.items():
                    setattr(task, k, v)
                self._rebuild_tabs()
                self._render_tasks()
                _Toast("Opgave opdateret ✓", self)
            else:
                self._chat.show_reply(f"Kunne ikke finde opgave: \"{task_name}\"")

        elif action == "reply":
            self._chat.show_reply(data.get("message", ""))

    def _on_claude_error(self, error: str) -> None:
        self._set_status("red")
        self._chat.set_loading(False)
        self._chat.show_reply(f"Fejl: {error}")

    def _fuzzy_find(self, name: str, done: bool | None = None) -> Task | None:
        needle = name.lower()
        candidates = self._tasks if done is None else [t for t in self._tasks if t.done == done]
        # Exact match first
        for t in candidates:
            if t.name.lower() == needle:
                return t
        # Substring match
        for t in candidates:
            if needle in t.name.lower() or t.name.lower() in needle:
                return t
        # Word overlap
        needle_words = set(needle.split())
        best, best_score = None, 0
        for t in candidates:
            words = set(t.name.lower().split())
            score = len(needle_words & words)
            if score > best_score:
                best, best_score = t, score
        return best if best_score > 0 else None

    # ── Drag to move ─────────────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_pos = None
