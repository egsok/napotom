"""nnv brand theme: two-ink print aesthetic (magenta + deep violet).

Environments: ink wall (dark, main surface) and kraft paper (queue sheet,
settings sheet). Fonts are bundled in assets/fonts and registered at startup
(see main.py); letter-spacing for mono labels is applied per-widget in code
because QSS cannot express it.
"""

# Font family constants (registered via QFontDatabase at startup)
FONT_DISPLAY = "Unbounded"
FONT_BODY = "IBM Plex Sans"
FONT_MONO = "IBM Plex Mono"

# Color palette — nnv two-ink tokens.
# Legacy keys (bg_dark, accent, ...) are kept so existing call sites work.
COLORS = {
    # ink wall
    "bg_dark": "#160f2c",       # wall
    "bg_card": "#1e1640",       # wall-2
    "bg_input": "#1e1640",
    "wall_3": "#0f0a20",
    # kraft paper
    "paper": "#e9dfc8",
    "paper_2": "#f2ecdc",
    # first ink: magenta
    "accent": "#e11b76",
    "accent_hover": "#ff2f88",
    "accent_pressed": "#b81261",
    # second ink: deep violet
    "violet": "#2c1a72",
    "violet_2": "#452ba6",
    "violet_ink": "#3a2a7a",
    # text on the wall
    "text_primary": "#ece3cd",  # cream
    "text_secondary": "#c8bda1",  # cream muted
    "border": "#383146",
    # statuses stay within the two inks
    "error": "#ff2f88",
    "success": "#ece3cd",
    "warning": "#c8bda1",
    "disabled_bg": "#2a2350",
    "disabled_text": "#6f6795",
}

STYLESHEET = f"""
QMainWindow, QDialog {{
    background-color: {COLORS["bg_dark"]};
}}

QWidget {{
    color: {COLORS["text_primary"]};
    font-size: 13px;
}}

QLabel {{
    color: {COLORS["text_primary"]};
    background-color: transparent;
}}

QLabel#sectionTitle {{
    color: {COLORS["text_secondary"]};
}}

/* --- buttons: primary = magenta ink --- */
QPushButton {{
    background-color: {COLORS["accent"]};
    border: none;
    padding: 9px 18px;
    border-radius: 4px;
    color: {COLORS["paper_2"]};
}}

QPushButton:hover {{
    background-color: {COLORS["accent_hover"]};
}}

QPushButton:pressed {{
    background-color: {COLORS["accent_pressed"]};
}}

QPushButton:disabled {{
    background-color: {COLORS["disabled_bg"]};
    color: {COLORS["disabled_text"]};
}}

QPushButton#iconButton {{
    padding: 6px;
    min-width: 42px;
    max-width: 42px;
    font-size: 20px;
}}

QPushButton#secondaryButton {{
    background-color: transparent;
    border: 1px solid rgba(236, 227, 205, 28%);
    border-radius: 4px;
    color: {COLORS["text_primary"]};
    padding: 8px 14px;
}}

QPushButton#secondaryButton:hover {{
    border-color: {COLORS["accent_hover"]};
    background-color: transparent;
    color: {COLORS["text_primary"]};
}}

QPushButton#secondaryButton:disabled {{
    background-color: transparent;
    border-color: rgba(236, 227, 205, 12%);
    color: {COLORS["disabled_text"]};
}}

QPushButton#dangerButton {{
    background-color: transparent;
    border: 1px solid rgba(236, 227, 205, 28%);
    color: {COLORS["text_primary"]};
    padding: 8px 14px;
}}

QPushButton#dangerButton:hover {{
    border-color: {COLORS["error"]};
    background-color: transparent;
}}

/* --- inputs --- */
QLineEdit {{
    background-color: {COLORS["bg_input"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 4px;
    padding: 10px 14px;
    color: {COLORS["text_primary"]};
    selection-background-color: {COLORS["accent"]};
    selection-color: #ffffff;
}}

QLineEdit:focus {{
    border-color: {COLORS["accent_hover"]};
}}

QLineEdit::placeholder {{
    color: {COLORS["text_secondary"]};
}}

QComboBox {{
    background-color: {COLORS["bg_input"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 4px;
    padding: 8px 14px;
    color: {COLORS["text_primary"]};
    min-width: 96px;
}}

QComboBox:hover {{
    border-color: {COLORS["accent_hover"]};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {COLORS["text_secondary"]};
    margin-right: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 4px;
    selection-background-color: {COLORS["accent"]};
    selection-color: #ffffff;
    outline: none;
}}

QSpinBox {{
    background-color: {COLORS["bg_input"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 4px;
    padding: 6px 10px;
    color: {COLORS["text_primary"]};
    selection-background-color: {COLORS["accent"]};
}}

QSpinBox:hover {{
    border-color: {COLORS["accent_hover"]};
}}

/* --- progress: flat magenta ink pass, squared like a roller stroke --- */
QProgressBar {{
    background-color: rgba(44, 26, 114, 16%);
    border: none;
    border-radius: 0;
    height: 6px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {COLORS["accent"]};
    border-radius: 0;
}}

/* --- scroll --- */
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
    background-color: {COLORS["accent"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* --- checkboxes: square type sorts, filled with ink when set --- */
QCheckBox {{
    spacing: 8px;
    color: {COLORS["text_primary"]};
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 2px;
    border: 2px solid rgba(236, 227, 205, 35%);
    background-color: transparent;
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS["accent"]};
    border-color: {COLORS["accent"]};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS["accent_hover"]};
}}

/* ==================== kraft sheet context ==================== */

QWidget#kraftSheet QLabel {{
    color: {COLORS["violet"]};
}}

QWidget#kraftSheet QGroupBox {{
    background-color: rgba(242, 236, 220, 55%);
    border: 1px solid rgba(44, 26, 114, 22%);
    border-radius: 3px;
    margin-top: 8px;
    padding-top: 6px;
    color: {COLORS["violet"]};
    font-family: "IBM Plex Mono";
    font-size: 10px;
    font-weight: 600;
}}

QWidget#kraftSheet QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: {COLORS["accent_pressed"]};
}}

QWidget#kraftSheet QLineEdit {{
    background-color: {COLORS["paper_2"]};
    border: 1px solid rgba(44, 26, 114, 35%);
    color: {COLORS["violet"]};
    selection-background-color: {COLORS["accent"]};
    selection-color: #ffffff;
}}

QWidget#kraftSheet QLineEdit:focus {{
    border-color: {COLORS["accent"]};
}}

QWidget#kraftSheet QComboBox {{
    background-color: {COLORS["paper_2"]};
    border: 1px solid rgba(44, 26, 114, 35%);
    color: {COLORS["violet"]};
}}

QWidget#kraftSheet QComboBox:hover {{
    border-color: {COLORS["accent"]};
}}

QWidget#kraftSheet QComboBox::down-arrow {{
    border-top-color: {COLORS["violet_ink"]};
}}

QWidget#kraftSheet QComboBox QAbstractItemView {{
    background-color: {COLORS["paper_2"]};
    border: 1px solid rgba(44, 26, 114, 35%);
    color: {COLORS["violet"]};
}}

QWidget#kraftSheet QSpinBox {{
    background-color: {COLORS["paper_2"]};
    border: 1px solid rgba(44, 26, 114, 35%);
    color: {COLORS["violet"]};
}}

QWidget#kraftSheet QCheckBox {{
    color: {COLORS["violet"]};
}}

QWidget#kraftSheet QCheckBox::indicator {{
    border: 2px solid rgba(44, 26, 114, 45%);
}}

QWidget#kraftSheet QCheckBox::indicator:checked {{
    background-color: {COLORS["accent"]};
    border-color: {COLORS["accent"]};
}}

QWidget#kraftSheet QPushButton#secondaryButton {{
    border: 1px solid rgba(44, 26, 114, 40%);
    color: {COLORS["violet"]};
}}

QWidget#kraftSheet QPushButton#secondaryButton:hover {{
    border-color: {COLORS["accent"]};
    color: {COLORS["violet"]};
}}

QWidget#kraftSheet QPushButton#secondaryButton:disabled {{
    border-color: rgba(44, 26, 114, 15%);
    color: rgba(44, 26, 114, 35%);
}}

QWidget#kraftSheet QPushButton#dangerButton {{
    border: 1px solid rgba(44, 26, 114, 40%);
    color: {COLORS["violet"]};
}}

QWidget#kraftSheet QPushButton#dangerButton:hover {{
    border-color: {COLORS["accent"]};
}}

/* queue items: prints separated by perforation dashes */
QueueItemWidget {{
    background: transparent;
    border-bottom: 1px dashed rgba(44, 26, 114, 35%);
}}

QPushButton#kraftAction {{
    background: transparent;
    border: 1px solid rgba(44, 26, 114, 40%);
    border-radius: 3px;
    color: {COLORS["violet"]};
    padding: 3px 9px;
    min-width: 0;
}}

QPushButton#kraftAction:hover {{
    background: transparent;
    border-color: {COLORS["violet"]};
}}

QPushButton#kraftActionMag {{
    background: transparent;
    border: 1px solid rgba(225, 27, 118, 50%);
    border-radius: 3px;
    color: {COLORS["accent_pressed"]};
    padding: 3px 9px;
    min-width: 0;
}}

QPushButton#kraftActionMag:hover {{
    background: transparent;
    border-color: {COLORS["accent"]};
}}

QPushButton#kraftCancel {{
    background: transparent;
    border: 1px solid rgba(44, 26, 114, 30%);
    border-radius: 3px;
    color: {COLORS["violet_ink"]};
    padding: 0;
    font-size: 11px;
    min-width: 0;
}}

QPushButton#kraftCancel:hover {{
    background: transparent;
    border-color: {COLORS["accent"]};
    color: {COLORS["accent"]};
}}
"""
