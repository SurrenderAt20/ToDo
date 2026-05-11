import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from config import load_config


def main() -> None:
    load_config()

    # Ensure Windows taskbar groups this as its own app (not generic Python).
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SurrenderAt20.ToDo")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("todo-widget")

    image_dir = Path(__file__).resolve().parent / "image"
    icon_path = image_dir / "todoimg.ico"
    if not icon_path.exists():
        icon_path = image_dir / "todoimg.png"

    if icon_path.exists():
        icon = QIcon(str(icon_path))
        app.setWindowIcon(icon)

    from ui.widget import TodoWidget
    widget = TodoWidget()
    widget.setWindowTitle("ToDo")
    if icon_path.exists():
        widget.setWindowIcon(QIcon(str(icon_path)))

    # Position in bottom-right corner
    screen = app.primaryScreen().availableGeometry()
    widget.move(screen.right() - widget.width() - 20, screen.bottom() - widget.height() - 20)
    widget.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
