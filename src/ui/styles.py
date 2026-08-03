"""nnv brand theme: the light "sheet" register (kraft paper, two inks).

The whole canvas is one sheet of kraft paper: window, queue, settings. The ink
wall survives only as the odd solid "clichE" (stamps, filled state chips) — see
`brand-guidelines-nnv/references/light.md`, model 3 ("full light incarnation").

Type sizes obey the brand's readability floor (computed px, not tokens):
prose 14, meaning-carrying text 13, functional captions 12, colophon 10-11.
Mono uppercase with tracking reads smaller than its size, so its floor is one
step up — utility mono never below 12px. The FS_* constants below are that
ladder; use them instead of literals.

Fonts are bundled in assets/fonts and registered at startup (see main.py);
letter-spacing for mono labels is applied per-widget in code because QSS cannot
express it.
"""

# Font family constants (registered via QFontDatabase at startup)
FONT_DISPLAY = "Unbounded"
FONT_BODY = "IBM Plex Sans"
FONT_MONO = "IBM Plex Mono"

# Type ladder — absolute pixel floors from the brand's readability rules.
FS_DISPLAY = 15   # section display, run numbers
FS_BODY = 14      # setting names, queue titles, prose
FS_META = 13      # descriptions, values, error detail
FS_MONO = 13      # mono uppercase reads smaller than its size: 13, not 12
FS_COLOPHON = 12  # footer credits

# The cancel square. It lives here because QSS min/max-width overrides
# setFixedSize(): with `min-width: 0` the layout squeezed the 28px button into
# an 12px sliver, and the frame around the glyph read as a rendering slip.
CANCEL_BTN = 28

# Color palette — nnv two-ink tokens, paper environment.
# Legacy keys (bg_dark, accent, text_primary, ...) are kept and remapped onto
# paper values, so any call site missed by the repaint still lands in the light
# register instead of punching a dark hole through the sheet.
COLORS = {
    # kraft paper — the page and its nested surfaces
    "paper": "#e9dfc8",
    "paper_2": "#f2ecdc",
    # second ink: deep violet — text and state
    "violet": "#2c1a72",        # headings, labels, names          10.6:1
    "prose": "#241a56",         # paragraphs                       11.7:1
    "violet_ink": "#3a2a7a",    # secondary text, meta, mono        8.9:1
    "violet_2": "#452ba6",      # state/selection — solid fill only
    # first ink: magenta — action
    "accent": "#e11b76",        # fills, rules, dots (never small text)
    "accent_hover": "#ff2f88",  # hover on solid ink
    "mag_text": "#b81261",      # magenta TEXT on paper             4.8:1
    "mag_ghost": "rgba(225, 27, 118, 50%)",  # resting misregistration
    # hairlines and borders (violet at low alpha — never grey)
    "line_soft": "rgba(44, 26, 114, 16%)",
    "line": "rgba(44, 26, 114, 28%)",
    "line_strong": "rgba(44, 26, 114, 40%)",
    # ink wall — kept for the rare solid clichE and the disabled register
    "wall": "#160f2c",
    "wall_2": "#1e1640",
    "wall_3": "#0f0a20",
    "on_ink": "#f2ecdc",        # type over solid ink (never #fff)
    "disabled_text": "rgba(44, 26, 114, 35%)",
    "disabled_bg": "rgba(44, 26, 114, 10%)",

    # --- legacy aliases, remapped onto paper ---
    "bg_dark": "#e9dfc8",
    "bg_card": "#f2ecdc",
    "bg_input": "#f2ecdc",
    "accent_pressed": "#b81261",
    "text_primary": "#2c1a72",
    "text_secondary": "#3a2a7a",
    "border": "rgba(44, 26, 114, 28%)",
    "error": "#b81261",
    "success": "#2c1a72",
    "warning": "#3a2a7a",
}

STYLESHEET = f"""
QMainWindow, QDialog {{
    background-color: {COLORS["paper"]};
}}

/* Colour only — NO font here.
   A `font-family`/`font-size` on QWidget wins over every setFont() in code,
   so this rule silently overrode the whole brand type register: the "ннв" mark
   rendered as Plex Sans 14 instead of Unbounded Black, and every mono label
   with tracking rendered as Plex Sans too. The base font is set once in
   main.py via app.setFont(); QSS only overrides it for specific object names
   below, where no setFont() is involved. */
QWidget {{
    color: {COLORS["violet"]};
}}

QLabel {{
    color: {COLORS["violet"]};
    background-color: transparent;
}}

/* mono uppercase section header — never below the mono floor */
QLabel#sectionTitle {{
    color: {COLORS["violet_ink"]};
}}

/* a settings row: name on top, explanation under it */
QLabel#rowTitle {{
    color: {COLORS["violet"]};
    font-size: {FS_BODY}px;
    font-weight: 600;
}}

QLabel#rowDesc {{
    color: {COLORS["violet_ink"]};
    font-size: {FS_META}px;
}}

QLabel#value {{
    color: {COLORS["prose"]};
    font-size: {FS_META}px;
}}

/* a settings section: rows sit on the page, fenced by one hairline.
   Giving each group its own fill turns it into an island and chops the sheet
   into slabs — the mistake this repaint undoes. */
QWidget#section {{
    background-color: transparent;
    border: 1px solid {COLORS["line_soft"]};
    border-radius: 6px;
}}

/* row divider: perforation, like a sheet meant to be torn */
QFrame#rowSep {{
    background-color: transparent;
    border: none;
    border-top: 1px dashed {COLORS["line_soft"]};
    max-height: 1px;
}}

/* hairline rules — the fence a section sits in */
QFrame#rule {{
    background-color: {COLORS["line"]};
    border: none;
    max-height: 1px;
}}

QFrame#ruleSoft {{
    background-color: {COLORS["line_soft"]};
    border: none;
    max-height: 1px;
}}

/* --- buttons: primary = magenta ink --- */
QPushButton {{
    background-color: {COLORS["accent"]};
    border: none;
    padding: 10px 18px;
    border-radius: 4px;
    color: {COLORS["on_ink"]};
}}

QPushButton:hover {{
    background-color: {COLORS["accent_hover"]};
}}

QPushButton:pressed {{
    background-color: {COLORS["mag_text"]};
}}

QPushButton:disabled {{
    background-color: {COLORS["disabled_bg"]};
    color: {COLORS["disabled_text"]};
}}

QPushButton#secondaryButton {{
    background-color: transparent;
    border: 1px solid {COLORS["line_strong"]};
    border-radius: 4px;
    color: {COLORS["violet"]};
    padding: 9px 14px;
}}

QPushButton#secondaryButton:hover {{
    border-color: {COLORS["accent"]};
    background-color: transparent;
    color: {COLORS["mag_text"]};
}}

QPushButton#secondaryButton:pressed {{
    background-color: rgba(225, 27, 118, 10%);
}}

QPushButton#secondaryButton:disabled {{
    background-color: transparent;
    border-color: {COLORS["line_soft"]};
    color: {COLORS["disabled_text"]};
}}

QPushButton#dangerButton {{
    background-color: transparent;
    border: 1px solid {COLORS["line_strong"]};
    border-radius: 4px;
    color: {COLORS["violet"]};
    padding: 9px 14px;
}}

QPushButton#dangerButton:hover {{
    border-color: {COLORS["accent"]};
    color: {COLORS["mag_text"]};
    background-color: transparent;
}}

/* text link — magenta ink text, underlined like a proof mark */
QPushButton#linkButton {{
    background-color: transparent;
    border: none;
    color: {COLORS["mag_text"]};
    text-decoration: underline;
    padding: 4px 0;
}}

QPushButton#linkButton:hover {{
    background-color: transparent;
    color: {COLORS["accent"]};
}}

/* --- inputs --- */
QLineEdit {{
    background-color: {COLORS["paper_2"]};
    border: 1px solid {COLORS["line"]};
    border-radius: 4px;
    padding: 10px 14px;
    color: {COLORS["violet"]};
    selection-background-color: {COLORS["accent"]};
    selection-color: {COLORS["on_ink"]};
}}

QLineEdit:focus {{
    border-color: {COLORS["accent"]};
}}

QLineEdit:read-only {{
    background-color: rgba(44, 26, 114, 6%);
    color: {COLORS["prose"]};
}}

QLineEdit:disabled {{
    color: {COLORS["disabled_text"]};
}}

QComboBox {{
    background-color: {COLORS["paper_2"]};
    border: 1px solid {COLORS["line"]};
    border-radius: 4px;
    padding: 8px 12px;
    color: {COLORS["violet"]};
    min-width: 110px;
}}

QComboBox:hover {{
    border-color: {COLORS["accent"]};
}}

/* the drop-down zone is fenced off by a hairline — a printer's gutter */
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 26px;
    border: none;
    border-left: 1px solid {COLORS["line"]};
}}

/* No arrow here on purpose: Qt renders the CSS border-triangle trick as a
   solid rectangle, and a bitmap would blur at 150% scaling. InkComboBox
   (ui.common) paints a vector triangle instead — this only clears the default. */
QComboBox::down-arrow {{
    image: none;
    width: 0;
    height: 0;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS["paper_2"]};
    border: 1px solid {COLORS["line_strong"]};
    border-radius: 3px;
    color: {COLORS["violet"]};
    /* Both mechanisms on purpose: the delegate paints the row under the
       pointer through selection-*, while ::item:hover covers the views that
       do not move the selection with the mouse. Without the first, Qt drew a
       grey focus frame and no highlight at all. */
    selection-background-color: {COLORS["violet_2"]};
    selection-color: {COLORS["on_ink"]};
    outline: none;
    padding: 3px;
}}

/* The open list had no hover at all: styling the view without an ::item rule
   drops Qt's own highlight. The row under the pointer takes the second ink,
   solid, with paper type on it — the brand's "state = solid violet" chip. */
QComboBox QAbstractItemView::item {{
    padding: 6px 9px;
    border-radius: 3px;
    color: {COLORS["violet"]};
}}

QComboBox QAbstractItemView::item:hover,
QComboBox QAbstractItemView::item:selected {{
    background-color: {COLORS["violet_2"]};
    color: {COLORS["on_ink"]};
}}

QSpinBox {{
    background-color: {COLORS["paper_2"]};
    border: 1px solid {COLORS["line"]};
    border-radius: 4px;
    padding: 7px 10px;
    color: {COLORS["violet"]};
    selection-background-color: {COLORS["accent"]};
    selection-color: {COLORS["on_ink"]};
}}

QSpinBox:hover {{
    border-color: {COLORS["accent"]};
}}

/* Qt's default spin arrows render as two specks; give them room and ink */
QSpinBox::up-button, QSpinBox::down-button {{
    subcontrol-origin: border;
    width: 22px;
    border-left: 1px solid {COLORS["line"]};
    background-color: transparent;
}}

QSpinBox::up-button {{ subcontrol-position: top right; }}
QSpinBox::down-button {{ subcontrol-position: bottom right; }}

/* Same story as the combo arrow — cleared here, painted in InkSpinBox */
QSpinBox::up-arrow, QSpinBox::down-arrow {{
    image: none;
    width: 0;
    height: 0;
}}

/* --- progress: flat magenta ink pass, squared like a roller stroke --- */
QProgressBar {{
    background-color: {COLORS["line_soft"]};
    border: none;
    border-radius: 0;
    height: 6px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {COLORS["accent"]};
    border-radius: 0;
}}

/* --- scroll: in the paper register, not the wall's --- */
QScrollArea {{
    background-color: transparent;
    border: none;
}}

/* The scrolled widget must be transparent too, or it fills itself from the
   palette and hides the kraft page behind an opaque slab — which also makes
   the sheet's colour depend on the OS theme instead of on the brand. */
QScrollArea > QWidget > QWidget {{
    background-color: transparent;
}}

QScrollBar:vertical {{
    background-color: transparent;
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS["line"]};
    border-radius: 5px;
    min-height: 32px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS["accent"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

/* --- checkboxes: square type sorts. The painted InkCheckBox (ui.common) is
   the one users see; this keeps any plain QCheckBox in the same register. --- */
QCheckBox {{
    spacing: 9px;
    color: {COLORS["violet"]};
}}

QCheckBox::indicator {{
    width: 17px;
    height: 17px;
    border-radius: 2px;
    border: 2px solid rgba(44, 26, 114, 45%);
    background-color: {COLORS["paper_2"]};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS["accent"]};
    border-color: {COLORS["accent"]};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS["accent"]};
}}

/* --- the info sheet (InfoPopover): prose on paper, painted in ui.common.
   Only the type lives here; the sheet, its hairline and its flat offset
   shadow are painted, because a translucent window has no QSS background. --- */
QLabel#infoPopoverText {{
    color: {COLORS["prose"]};
    font-size: {FS_BODY}px;
    background-color: transparent;
}}

/* --- tooltips: a small sheet, not the system's white slab.
   Still used for supplementary hints (truncated paths, icon buttons); an
   explanation someone has to read gets an InfoMark instead. --- */
QToolTip {{
    background-color: {COLORS["paper_2"]};
    border: 1px solid {COLORS["line_strong"]};
    color: {COLORS["prose"]};
    font-size: {FS_META}px;
    padding: 7px 9px;
}}

/* --- message boxes: paper too, and only the default button carries ink --- */
QMessageBox {{
    background-color: {COLORS["paper"]};
}}

QMessageBox QLabel {{
    color: {COLORS["prose"]};
    font-size: {FS_BODY}px;
}}

QMessageBox QPushButton {{
    background-color: transparent;
    border: 1px solid {COLORS["line_strong"]};
    border-radius: 4px;
    color: {COLORS["violet"]};
    padding: 8px 16px;
    min-width: 84px;
}}

QMessageBox QPushButton:hover {{
    border-color: {COLORS["accent"]};
    color: {COLORS["mag_text"]};
}}

QMessageBox QPushButton:default {{
    background-color: {COLORS["accent"]};
    border-color: {COLORS["accent"]};
    color: {COLORS["on_ink"]};
}}

QMessageBox QPushButton:default:hover {{
    background-color: {COLORS["accent_hover"]};
    border-color: {COLORS["accent_hover"]};
    color: {COLORS["on_ink"]};
}}

/* --- queue: prints separated by perforation dashes --- */
QueueItemWidget {{
    background: transparent;
    border-bottom: 1px dashed {COLORS["line"]};
}}

QPushButton#kraftAction {{
    background: transparent;
    border: 1px solid {COLORS["line_strong"]};
    border-radius: 3px;
    color: {COLORS["violet"]};
    padding: 4px 10px;
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
    color: {COLORS["mag_text"]};
    padding: 4px 10px;
    min-width: 0;
}}

QPushButton#kraftActionMag:hover {{
    background: transparent;
    border-color: {COLORS["accent"]};
}}

/* No font-size here: the glyph size is set in code, and a QSS rule would
   override that setFont() the same way the old QWidget rule did. */
QPushButton#kraftCancel {{
    background: transparent;
    border: 1px solid {COLORS["line"]};
    border-radius: 3px;
    color: {COLORS["violet_ink"]};
    padding: 0;
    min-width: {CANCEL_BTN}px;
    max-width: {CANCEL_BTN}px;
    min-height: {CANCEL_BTN}px;
    max-height: {CANCEL_BTN}px;
}}

QPushButton#kraftCancel:hover {{
    background: transparent;
    border-color: {COLORS["accent"]};
    color: {COLORS["mag_text"]};
}}
"""
