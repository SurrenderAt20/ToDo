import math
import random

from PyQt6.QtCore import QPointF, QPropertyAnimation, QTimer, Qt, pyqtProperty
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QWidget

from ui.styles import ACCENT_BLUE, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_PURPLE

PARTICLE_COLORS = [ACCENT_GREEN, ACCENT_ORANGE, ACCENT_BLUE, ACCENT_PURPLE]
PARTICLE_COUNT = 14
DURATION_MS = 600


class _Particle:
    def __init__(self, origin: QPointF) -> None:
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(60, 160)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.x = origin.x()
        self.y = origin.y()
        self.radius = random.uniform(3, 6)
        self.color = QColor(random.choice(PARTICLE_COLORS))

    def position_at(self, t: float) -> tuple[float, float]:
        # t in [0,1]
        return self.x + self.vx * t, self.y + self.vy * t + 80 * t * t  # slight gravity


class ParticleOverlay(QWidget):
    def __init__(self, parent: QWidget, origin: QPointF) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(parent.rect())
        self._particles = [_Particle(origin) for _ in range(PARTICLE_COUNT)]
        self._progress: float = 0.0
        self._anim = QPropertyAnimation(self, b"progress", self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(DURATION_MS)
        self._anim.finished.connect(self._cleanup)
        self.show()
        self._anim.start()

    @pyqtProperty(float)
    def progress(self) -> float:
        return self._progress

    @progress.setter
    def progress(self, value: float) -> None:
        self._progress = value
        self.update()

    def paintEvent(self, _event) -> None:
        t = self._progress
        if t <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        alpha = max(0, int(255 * (1 - t)))
        for p in self._particles:
            x, y = p.position_at(t)
            color = QColor(p.color)
            color.setAlpha(alpha)
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(x, y), p.radius, p.radius)
        painter.end()

    def _cleanup(self) -> None:
        self.hide()
        self.deleteLater()
