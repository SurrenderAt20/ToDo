from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.styles import (
    ACCENT_BG_GREEN,
    ACCENT_GREEN,
    BG_CARD,
    BORDER,
    INPUT_QSS,
    TEXT_HINT,
    TEXT_MUTED,
    TEXT_PRIMARY,
)


class _EnterLineEdit(QLineEdit):
    submitted = pyqtSignal(str)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            text = self.text().strip()
            if text:
                self.submitted.emit(text)
                self.clear()
        else:
            super().keyPressEvent(event)


class ChatInput(QWidget):
    message_submitted = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._reply_timer = QTimer(self)
        self._reply_timer.setSingleShot(True)
        self._reply_timer.timeout.connect(self._hide_reply)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 8)
        layout.setSpacing(4)

        self._reply_box = QLabel("", self)
        self._reply_box.setWordWrap(True)
        self._reply_box.setStyleSheet(
            f"QLabel {{ background: {BG_CARD}; color: {TEXT_PRIMARY}; "
            f"border: 1px solid {BORDER}; border-radius: 8px; padding: 8px 10px; font-size: 12px; }}"
        )
        self._reply_box.hide()
        layout.addWidget(self._reply_box)

        row = QHBoxLayout()
        row.setSpacing(6)

        self._input = _EnterLineEdit(self)
        self._input.setPlaceholderText("Skriv hvad der skal ske...")
        self._input.setStyleSheet(INPUT_QSS)
        self._input.submitted.connect(self.message_submitted)
        row.addWidget(self._input, 1)

        self._send_btn = QPushButton("→", self)
        self._send_btn.setFixedSize(32, 32)
        self._send_btn.setStyleSheet(
            f"QPushButton {{ background: {ACCENT_BG_GREEN}; color: {ACCENT_GREEN}; "
            f"border: none; border-radius: 8px; font-size: 16px; }}"
            f"QPushButton:hover {{ background: {ACCENT_GREEN}; color: #000; }}"
            f"QPushButton:disabled {{ background: {BORDER}; color: {TEXT_HINT}; }}"
        )
        self._send_btn.clicked.connect(self._on_send_clicked)
        row.addWidget(self._send_btn)

        layout.addLayout(row)

        self._status_label = QLabel("", self)
        self._status_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.hide()
        layout.addWidget(self._status_label)

    def _on_send_clicked(self) -> None:
        text = self._input.text().strip()
        if text:
            self.message_submitted.emit(text)
            self._input.clear()

    def set_loading(self, loading: bool) -> None:
        self._input.setEnabled(not loading)
        self._send_btn.setEnabled(not loading)
        if loading:
            self._status_label.setText("Claude tænker…")
            self._status_label.show()
        else:
            self._status_label.hide()

    def show_reply(self, message: str) -> None:
        self._reply_box.setText(message)
        self._reply_box.show()
        self._reply_timer.start(5000)

    def _hide_reply(self) -> None:
        self._reply_box.hide()

    def save_input(self) -> str:
        return self._input.text()

    def restore_input(self, text: str) -> None:
        self._input.setText(text)
