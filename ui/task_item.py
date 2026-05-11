from PyQt6.QtCore import QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from models import Task
from ui.styles import (
    ACCENT_GREEN,
    BG_CARD,
    BORDER,
    TEXT_MUTED,
    TEXT_PRIMARY,
    category_color,
)


class TaskItem(QWidget):
    toggled = pyqtSignal(str, bool)   # task_id, new done state
    deleted = pyqtSignal(str)         # task_id

    def __init__(self, task: Task, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._task = task
        self._expanded = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 4)
        outer.setSpacing(0)

        self._card = QFrame(self)
        self._card.setObjectName("TaskCard")
        accent, bg = category_color(self._task.category)
        self._card.setStyleSheet(
            f"QFrame#TaskCard {{ background: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 8px; }}"
        )
        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(8, 6, 8, 6)
        card_layout.setSpacing(4)

        row = QHBoxLayout()
        row.setSpacing(6)

        self._check_btn = QPushButton(self._card)
        self._check_btn.setFixedSize(20, 20)
        self._check_btn.setCheckable(True)
        self._check_btn.setChecked(self._task.done)
        self._apply_checkbox_style(accent)
        self._check_btn.clicked.connect(self._on_toggle)
        row.addWidget(self._check_btn)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        self._name_label = QLabel(self._task.name, self._card)
        self._name_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(11)
        self._name_label.setFont(font)
        self._apply_name_style()
        text_col.addWidget(self._name_label)

        tags_row = QHBoxLayout()
        tags_row.setSpacing(4)
        tags_row.setContentsMargins(0, 0, 0, 0)

        if self._task.project:
            proj_label = QLabel(self._task.project, self._card)
            proj_label.setStyleSheet(
                f"QLabel {{ background: #1e1e1e; color: {TEXT_MUTED}; "
                f"border: 1px solid {BORDER}; border-radius: 4px; padding: 1px 5px; font-size: 10px; }}"
            )
            tags_row.addWidget(proj_label)

        if self._task.category:
            cat_label = QLabel(self._task.category, self._card)
            cat_label.setStyleSheet(
                f"QLabel {{ background: {bg}; color: {accent}; "
                f"border-radius: 4px; padding: 1px 5px; font-size: 10px; }}"
            )
            tags_row.addWidget(cat_label)

        tags_row.addStretch()
        text_col.addLayout(tags_row)
        row.addLayout(text_col, 1)

        if self._task.notes:
            self._expand_btn = QPushButton("›", self._card)
            self._expand_btn.setFixedSize(18, 18)
            self._expand_btn.setStyleSheet(
                f"QPushButton {{ background: transparent; color: {TEXT_MUTED}; "
                f"border: none; font-size: 14px; padding: 0; }}"
                f"QPushButton:hover {{ color: {TEXT_PRIMARY}; }}"
            )
            self._expand_btn.clicked.connect(self._toggle_expand)
            row.addWidget(self._expand_btn)

        self._delete_btn = QPushButton("x", self._card)
        self._delete_btn.setFixedSize(18, 18)
        self._delete_btn.setToolTip("Slet opgave")
        self._delete_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #f87171; border: none; font-size: 12px; font-weight: bold; }"
            "QPushButton:hover { background: #3a1a1a; border-radius: 4px; }"
        )
        self._delete_btn.clicked.connect(lambda: self.deleted.emit(self._task.id))
        row.addWidget(self._delete_btn)

        card_layout.addLayout(row)

        self._notes_label = QLabel(self._task.notes or "", self._card)
        self._notes_label.setWordWrap(True)
        self._notes_label.setStyleSheet(
            f"QLabel {{ color: {TEXT_MUTED}; font-size: 11px; padding: 4px 0 0 26px; }}"
        )
        self._notes_label.setVisible(False)
        card_layout.addWidget(self._notes_label)

        outer.addWidget(self._card)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _apply_checkbox_style(self, accent: str) -> None:
        if self._check_btn.isChecked():
            self._check_btn.setStyleSheet(
                f"QPushButton {{ background: {ACCENT_GREEN}; border: 2px solid {ACCENT_GREEN}; "
                f"border-radius: 4px; color: #000; font-size: 11px; font-weight: bold; }}"
            )
            self._check_btn.setText("✓")
        else:
            self._check_btn.setStyleSheet(
                f"QPushButton {{ background: transparent; border: 2px solid {accent}; "
                f"border-radius: 4px; color: transparent; }}"
                f"QPushButton:hover {{ background: {accent}22; }}"
            )
            self._check_btn.setText("")

    def _apply_name_style(self) -> None:
        if self._task.done:
            self._name_label.setStyleSheet(
                f"QLabel {{ color: {TEXT_MUTED}; text-decoration: line-through; }}"
            )
            self._card.setStyleSheet(
                f"QFrame#TaskCard {{ background: {BG_CARD}; border: 1px solid {BORDER}; "
                f"border-radius: 8px; opacity: 0.5; }}"
            )
        else:
            self._name_label.setStyleSheet(f"QLabel {{ color: {TEXT_PRIMARY}; }}")

    def _on_toggle(self) -> None:
        done = self._check_btn.isChecked()
        self._task.done = done
        accent, _ = category_color(self._task.category)
        self._apply_checkbox_style(accent)
        self._apply_name_style()
        if done:
            self._fire_particles()
        self.toggled.emit(self._task.id, done)

    def _fire_particles(self) -> None:
        from ui.particles import ParticleOverlay
        # Find top-level scrollarea or widget parent
        target = self.parent()
        while target and not hasattr(target, "viewport"):
            target = target.parent()
        if target:
            viewport = target.viewport() if hasattr(target, "viewport") else target
            btn_center = self._check_btn.mapTo(viewport, self._check_btn.rect().center())
            ParticleOverlay(viewport, QPointF(btn_center))

    def _toggle_expand(self) -> None:
        self._expanded = not self._expanded
        self._notes_label.setVisible(self._expanded)
        if hasattr(self, "_expand_btn"):
            self._expand_btn.setText("˅" if self._expanded else "›")

    def _show_context_menu(self, pos) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background: #1e1e1e; color: #e0e0e0; border: 1px solid #2a2a2a; border-radius: 6px; }"
            "QMenu::item { padding: 6px 16px; }"
            "QMenu::item:selected { background: #2a2a2a; }"
        )
        delete_action = menu.addAction("Slet")
        action = menu.exec(self.mapToGlobal(pos))
        if action == delete_action:
            self.deleted.emit(self._task.id)

    def update_task(self, task: Task) -> None:
        self._task = task
        self._name_label.setText(task.name)
        self._check_btn.setChecked(task.done)
        accent, _ = category_color(task.category)
        self._apply_checkbox_style(accent)
        self._apply_name_style()
        self._notes_label.setText(task.notes or "")

    @property
    def task(self) -> Task:
        return self._task
