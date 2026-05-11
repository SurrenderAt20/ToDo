BG_MAIN          = "#1a1a1a"
BG_CARD          = "#111111"
BG_TITLEBAR      = "#111111"
BORDER           = "#2a2a2a"
TEXT_PRIMARY     = "#e0e0e0"
TEXT_MUTED       = "#666666"
TEXT_HINT        = "#444444"
ACCENT_GREEN     = "#4ade80"
ACCENT_BG_GREEN  = "#1e3a2e"
ACCENT_ORANGE    = "#f97316"
ACCENT_BG_ORANGE = "#2a1a00"
ACCENT_BLUE      = "#3b82f6"
ACCENT_BG_BLUE   = "#0a1a2a"
ACCENT_PURPLE    = "#a78bfa"
ACCENT_BG_PURPLE = "#1e1a3a"
STATUS_BAR_BG    = "#0d1f18"
STATUS_BAR_TEXT  = "#2a6a48"

CATEGORY_COLORS: dict[str, tuple[str, str]] = {
    "arbejde": (ACCENT_BLUE,   ACCENT_BG_BLUE),
    "privat":  (ACCENT_GREEN,  ACCENT_BG_GREEN),
    "møde":    (ACCENT_ORANGE, ACCENT_BG_ORANGE),
    "andet":   (ACCENT_PURPLE, ACCENT_BG_PURPLE),
}

CATEGORY_COLOR_LIST = [
    (ACCENT_BLUE,   ACCENT_BG_BLUE),
    (ACCENT_GREEN,  ACCENT_BG_GREEN),
    (ACCENT_ORANGE, ACCENT_BG_ORANGE),
    (ACCENT_PURPLE, ACCENT_BG_PURPLE),
]


def category_color(name: str | None) -> tuple[str, str]:
    if name is None:
        return (TEXT_MUTED, BG_CARD)
    key = name.lower()
    if key in CATEGORY_COLORS:
        return CATEGORY_COLORS[key]
    idx = hash(name) % len(CATEGORY_COLOR_LIST)
    return CATEGORY_COLOR_LIST[idx]


SCROLLBAR_QSS = f"""
QScrollBar:vertical {{
    background: {BG_MAIN};
    width: 6px;
    margin: 0;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {TEXT_HINT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}
"""

MAIN_WIDGET_QSS = f"""
QWidget#MainWidget {{
    background-color: {BG_MAIN};
    border-radius: 12px;
    border: 1px solid {BORDER};
}}
"""

TAB_BAR_QSS = f"""
QPushButton {{
    background: transparent;
    border: none;
    color: {TEXT_MUTED};
    font-size: 12px;
    padding: 4px 10px;
    border-radius: 8px;
}}
QPushButton:checked {{
    background: {ACCENT_BG_GREEN};
    color: {ACCENT_GREEN};
    font-weight: bold;
}}
QPushButton:hover:!checked {{
    color: {TEXT_PRIMARY};
    background: {BORDER};
}}
"""

INPUT_QSS = f"""
QLineEdit {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    color: {TEXT_PRIMARY};
    font-size: 13px;
    padding: 6px 10px;
    selection-background-color: {ACCENT_BG_BLUE};
}}
QLineEdit:focus {{
    border: 1px solid {ACCENT_GREEN};
}}
QLineEdit::placeholder {{
    color: {TEXT_HINT};
}}
"""
