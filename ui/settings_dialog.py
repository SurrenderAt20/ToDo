from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from config import save_api_key
from ui.styles import (
    ACCENT_BG_GREEN,
    ACCENT_GREEN,
    BG_MAIN,
    BORDER,
    INPUT_QSS,
    TEXT_MUTED,
    TEXT_PRIMARY,
)


class _TestThread(QThread):
    result = pyqtSignal(bool, str)

    def __init__(self, key: str) -> None:
        super().__init__()
        self._key = key

    def run(self) -> None:
        import os
        import anthropic
        try:
            client = anthropic.Anthropic(api_key=self._key)
            client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=16,
                messages=[{"role": "user", "content": "ping"}],
            )
            self.result.emit(True, "Forbindelsen er OK ✓")
        except Exception as exc:
            self.result.emit(False, f"Fejl: {exc}")


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Indstillinger")
        self.setFixedSize(380, 200)
        self.setStyleSheet(
            f"QDialog {{ background: {BG_MAIN}; color: {TEXT_PRIMARY}; border-radius: 10px; }}"
            f"QLabel {{ color: {TEXT_PRIMARY}; }}"
        )
        self._thread: _TestThread | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Claude API-nøgle"))

        self._key_input = QLineEdit(self)
        self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_input.setPlaceholderText("sk-ant-xxxxxxxxxxxxxxxx")
        self._key_input.setStyleSheet(INPUT_QSS)
        from config import get_api_key
        self._key_input.setText(get_api_key())
        layout.addWidget(self._key_input)

        self._status_label = QLabel("", self)
        self._status_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self._status_label)

        btn_row = QHBoxLayout()

        self._test_btn = QPushButton("Test forbindelse", self)
        self._test_btn.setStyleSheet(
            f"QPushButton {{ background: {BORDER}; color: {TEXT_PRIMARY}; border: none; "
            f"border-radius: 6px; padding: 6px 14px; }}"
            f"QPushButton:hover {{ background: #3a3a3a; }}"
        )
        self._test_btn.clicked.connect(self._test_connection)
        btn_row.addWidget(self._test_btn)

        btn_row.addStretch()

        self._save_btn = QPushButton("Gem", self)
        self._save_btn.setStyleSheet(
            f"QPushButton {{ background: {ACCENT_BG_GREEN}; color: {ACCENT_GREEN}; border: none; "
            f"border-radius: 6px; padding: 6px 18px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {ACCENT_GREEN}; color: #000; }}"
        )
        self._save_btn.clicked.connect(self._save)
        btn_row.addWidget(self._save_btn)

        layout.addLayout(btn_row)

    def _test_connection(self) -> None:
        key = self._key_input.text().strip()
        if not key:
            self._status_label.setText("Indtast en API-nøgle først.")
            return
        self._test_btn.setEnabled(False)
        self._status_label.setText("Tester…")
        self._thread = _TestThread(key)
        self._thread.result.connect(self._on_test_result)
        self._thread.start()

    def _on_test_result(self, ok: bool, message: str) -> None:
        self._status_label.setText(message)
        color = ACCENT_GREEN if ok else "#f87171"
        self._status_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        self._test_btn.setEnabled(True)

    def _save(self) -> None:
        key = self._key_input.text().strip()
        save_api_key(key)
        self.accept()
