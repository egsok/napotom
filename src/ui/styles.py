"""Dark theme stylesheet with purple/magenta accents."""

# Color palette
COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_card": "#16213e",
    "bg_input": "#0f1526",
    "accent_purple": "#9b59b6",
    "accent_magenta": "#e91e9b",
    "text_primary": "#eaeaea",
    "text_secondary": "#a0a0a0",
    "border": "#2a2a4a",
    "error": "#e74c3c",
    "success": "#2ecc71",
}

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {COLORS["bg_dark"]};
    color: {COLORS["text_primary"]};
    font-family: "Segoe UI", sans-serif;
    font-size: 14px;
}}

QLabel {{
    color: {COLORS["text_primary"]};
    background-color: transparent;
}}

QLabel#sectionTitle {{
    font-size: 12px;
    font-weight: bold;
    color: {COLORS["text_secondary"]};
    text-transform: uppercase;
    letter-spacing: 1px;
}}

QPushButton {{
    background-color: {COLORS["accent_purple"]};
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    color: white;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {COLORS["accent_magenta"]};
}}

QPushButton:pressed {{
    background-color: #7b2d8e;
}}

QPushButton:disabled {{
    background-color: #3a3a5a;
    color: #6a6a8a;
}}

QPushButton#iconButton {{
    padding: 8px;
    min-width: 40px;
    max-width: 40px;
}}

QLineEdit {{
    background-color: {COLORS["bg_input"]};
    border: 2px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 10px 14px;
    color: {COLORS["text_primary"]};
    selection-background-color: {COLORS["accent_purple"]};
}}

QLineEdit:focus {{
    border-color: {COLORS["accent_purple"]};
}}

QLineEdit::placeholder {{
    color: {COLORS["text_secondary"]};
}}

QComboBox {{
    background-color: {COLORS["bg_input"]};
    border: 2px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 8px 14px;
    color: {COLORS["text_primary"]};
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {COLORS["accent_purple"]};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS["text_secondary"]};
    margin-right: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS["bg_card"]};
    border: 2px solid {COLORS["border"]};
    border-radius: 6px;
    selection-background-color: {COLORS["accent_purple"]};
    outline: none;
}}

QProgressBar {{
    background-color: {COLORS["bg_input"]};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS["accent_purple"]},
        stop:1 {COLORS["accent_magenta"]}
    );
    border-radius: 4px;
}}

QScrollArea {{
    background-color: transparent;
    border: none;
}}

QScrollBar:vertical {{
    background-color: {COLORS["bg_dark"]};
    width: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS["border"]};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS["accent_purple"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QCheckBox {{
    spacing: 8px;
    color: {COLORS["text_primary"]};
}}

QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid {COLORS["border"]};
    background-color: {COLORS["bg_input"]};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS["accent_purple"]};
    border-color: {COLORS["accent_purple"]};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS["accent_purple"]};
}}
"""
