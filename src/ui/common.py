"""Shared UI helpers and nnv brand widgets (paper register)."""

import html
import random
import sys

from PyQt6.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QColor, QCursor, QFont, QFontMetricsF, QGuiApplication, QIcon, QImage,
    QPainter, QPainterPath, QPen, QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QGraphicsDropShadowEffect, QLabel, QSpinBox,
    QVBoxLayout, QWidget,
)

from ui.styles import COLORS, FONT_DISPLAY, FONT_MONO, FS_MONO
from utils.i18n import tr


def apply_brand_titlebar(window: QWidget) -> None:
    """Paint the native Windows title bar in kraft (Windows 11 DWM API).

    The window is one sheet of paper — a dark caption above it would read as a
    foreign strip. Falls back to plain light mode on Windows 10; no-op elsewhere.
    """
    if sys.platform != 'win32':
        return
    import ctypes

    def colorref(hex_color: str) -> int:
        r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
        return (b << 16) | (g << 8) | r

    try:
        hwnd = int(window.winId())
        dwm = ctypes.windll.dwmapi
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_BORDER_COLOR = 34
        DWMWA_CAPTION_COLOR = 35
        DWMWA_TEXT_COLOR = 36

        light = ctypes.c_int(0)
        dwm.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                                  ctypes.byref(light), 4)

        caption = ctypes.c_uint(colorref(COLORS['paper']))
        if dwm.DwmSetWindowAttribute(hwnd, DWMWA_CAPTION_COLOR,
                                     ctypes.byref(caption), 4) == 0:
            text = ctypes.c_uint(colorref(COLORS['violet']))
            dwm.DwmSetWindowAttribute(hwnd, DWMWA_TEXT_COLOR,
                                      ctypes.byref(text), 4)
            border = ctypes.c_uint(colorref(COLORS['paper']))
            dwm.DwmSetWindowAttribute(hwnd, DWMWA_BORDER_COLOR,
                                      ctypes.byref(border), 4)
    except Exception:
        pass  # cosmetic only — never break startup over a title bar


def populate_quality_combo(combo, selected_key=None):
    """(Re)fill a quality combo box with translated items.

    Selects the item matching selected_key; with no match (or None),
    the first item stays selected.
    """
    combo.clear()
    combo.addItem(tr("quality_best"), "best")
    combo.addItem(tr("quality_1080p"), "1080p")
    combo.addItem(tr("quality_720p"), "720p")
    combo.addItem(tr("quality_audio"), "audio")
    for i in range(combo.count()):
        if combo.itemData(i) == selected_key:
            combo.setCurrentIndex(i)
            break


def update_prompt_text(updater, current: str, latest: str) -> str:
    """Word the yt-dlp update prompt: a newer version, or a channel switch.

    A channel switch can install an *older* version (nightly -> stable), so the
    plain "X is available" wording would read as nonsense there.
    """
    from core.updater import get_update_channel

    if updater.channel_switch:
        return tr("update_channel_switch_message",
                  channel=get_update_channel(), latest=latest, current=current)
    return tr("update_available_message", latest=latest, current=current)


def mono_font(px: int = FS_MONO, weight: QFont.Weight = QFont.Weight.DemiBold,
              tracking: float = 1.2) -> QFont:
    """Utility mono font (IBM Plex Mono) with letter-spacing — QSS can't do tracking.

    Mono uppercase with tracking reads smaller than its nominal size, so the
    brand floor for it is 12px; that is the default here on purpose.
    """
    font = QFont(FONT_MONO)
    font.setPixelSize(px)
    font.setWeight(weight)
    font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, tracking)
    return font


def display_font(px: int, weight: QFont.Weight = QFont.Weight.ExtraBold) -> QFont:
    """Display font (Unbounded) for run numbers and the brand glyph."""
    font = QFont(FONT_DISPLAY)
    font.setPixelSize(px)
    font.setWeight(weight)
    return font


def ink_offset(widget: QWidget, dx: float = 1.0, dy: float = 1.0,
               color: str = COLORS["accent"]) -> None:
    """Misregistration signature: hard ink offset (no blur) behind a label.

    Whole pixels only — 0.7px does not physically render.
    """
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(0)
    effect.setOffset(round(dx), round(dy))
    effect.setColor(QColor(color))
    widget.setGraphicsEffect(effect)


def optical_shift(font: QFont, text: str) -> int:
    """How many px the ink of `text` sits below the em box's centre.

    A QLabel centres text by the font's em box (ascent + descent). A word with
    no ascenders or descenders — "ннв" — has its ink entirely in the x-height
    band, so it lands visibly low. Measured, not eyeballed.
    """
    metrics = QFontMetricsF(font)
    ink = metrics.tightBoundingRect(text)
    if ink.isEmpty():
        return 0
    baseline_from_centre = (metrics.ascent() - metrics.descent()) / 2
    ink_centre = baseline_from_centre + (ink.top() + ink.bottom()) / 2
    return round(ink_centre)


def apply_optical_center(label, extra: int = 0) -> None:
    """Lift a label's text so its ink — not its em box — centres in the row.

    A bottom margin of 2k shrinks the content rect from below, which moves
    vertically centred text up by k.
    """
    shift = optical_shift(label.font(), label.text()) + extra
    if shift > 0:
        label.setContentsMargins(0, 0, 0, shift * 2)


class RegMark(QWidget):
    """Registration mark: circle with crosshair, in magenta ink."""

    def __init__(self, size: int = 13, color: str = COLORS["accent"], parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self._color, 1.3)
        painter.setPen(pen)
        w, h = self.width(), self.height()
        radius = w * 0.30
        painter.drawEllipse(QRectF(w / 2 - radius, h / 2 - radius, radius * 2, radius * 2))
        painter.drawLine(QPointF(w / 2, 1.0), QPointF(w / 2, h - 1.0))
        painter.drawLine(QPointF(1.0, h / 2), QPointF(w - 1.0, h / 2))


class InfoPopover(QWidget):
    """The explanation sheet an InfoMark prints — ours, not the system's.

    QToolTip is the wrong mechanism for an explanation you actually have to
    read: it waits ~700ms, and it dies on the first mouse press, so clicking it
    to keep it makes it vanish under the cursor. This is a plain widget, so it
    prints at once, a click *pins* it, the pointer may walk into it, and the
    text can be selected.
    """

    GAP = 6            # air between the mark and the sheet
    SHADOW = 3         # flat offset shadow, zero blur — a sheet pressed to the desk
    MAX_TEXT = 360     # wrap width for prose
    MIN_TEXT = 210
    PAD_X = 15
    PAD_Y = 13

    OPEN_DELAY = 130   # a guard against a fly-over, not a system tooltip's wait
    CLOSE_DELAY = 230  # forgiving: time to travel from the mark into the sheet
    INK_STEP = 40      # one ink pass in 3 discrete takts (~120ms), never a fade-glow

    def __init__(self, mark: QWidget):
        # Parented to the mark (so it dies with it) but flagged as a window.
        super().__init__(mark, Qt.WindowType.ToolTip)
        self.setObjectName("infoPopover")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._mark = mark
        self._pinned = False
        self._step = 0

        self._label = QLabel(self)
        self._label.setObjectName("infoPopoverText")
        self._label.setWordWrap(True)
        self._label.setTextFormat(Qt.TextFormat.RichText)
        self._label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(self.PAD_X, self.PAD_Y,
                                  self.PAD_X + self.SHADOW, self.PAD_Y + self.SHADOW)
        layout.addWidget(self._label)

        self._close_timer = QTimer(self)
        self._close_timer.setSingleShot(True)
        self._close_timer.timeout.connect(self.dismiss)
        self._ink_timer = QTimer(self)
        self._ink_timer.timeout.connect(self._ink_pass)

    # --- content ------------------------------------------------------
    def setText(self, text: str) -> None:
        self._label.ensurePolished()  # the QSS font decides how wide the text wraps
        self._label.setText(self._as_paragraphs(text))
        self._label.setFixedWidth(self._wrap_width(text))
        self.adjustSize()
        if self.isVisible():  # a language switch while it is open
            self._place()

    @staticmethod
    def _as_paragraphs(text: str) -> str:
        """Blank lines become spaced blocks — a blank text line is too big a gap."""
        blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        return "".join(
            '<div{}>{}</div>'.format(
                ' style="margin-top:9px"' if i else "",
                html.escape(block).replace("\n", "<br>"),
            )
            for i, block in enumerate(blocks)
        )

    def _wrap_width(self, text: str) -> int:
        metrics = QFontMetricsF(self._label.font())
        rect = metrics.boundingRect(QRectF(0, 0, self.MAX_TEXT, 1 << 20),
                                    int(Qt.TextFlag.TextWordWrap), text)
        return int(max(self.MIN_TEXT, min(self.MAX_TEXT, rect.width() + 1)))

    # --- state --------------------------------------------------------
    def isPinned(self) -> bool:
        return self._pinned

    def reveal(self, pinned: bool = False) -> None:
        self._pinned = self._pinned or pinned
        self._close_timer.stop()
        if not self.isVisible():
            self._place()
            self.setWindowOpacity(0.34)
            self.show()
            self.raise_()
            self._step = 0
            self._ink_timer.start(self.INK_STEP)
            QApplication.instance().installEventFilter(self)
        self._mark.update()

    def dismiss(self) -> None:
        self._close_timer.stop()
        self._ink_timer.stop()
        self._pinned = False
        if self.isVisible():
            QApplication.instance().removeEventFilter(self)
            self.hide()
        self._mark.update()

    def togglePin(self) -> None:
        """What a click on the mark does: pin it, or put it away."""
        if self._pinned:
            self.dismiss()
        else:
            self.reveal(pinned=True)

    def scheduleClose(self) -> None:
        """Hover-out: close, but not before the grace period."""
        if self.isVisible() and not self._pinned:
            self._close_timer.start(self.CLOSE_DELAY)

    def _ink_pass(self) -> None:
        self._step += 1
        self.setWindowOpacity(min(1.0, 0.34 + 0.33 * self._step))
        if self._step >= 2:
            self._ink_timer.stop()

    # --- placement ----------------------------------------------------
    def _mark_rect(self) -> QRect:
        return QRect(self._mark.mapToGlobal(QPoint(0, 0)), self._mark.size())

    def _place(self) -> None:
        self.adjustSize()
        mark = self._mark_rect()
        screen = QGuiApplication.screenAt(mark.center()) or QGuiApplication.primaryScreen()
        area = screen.availableGeometry()
        width, height = self.width(), self.height()

        below = mark.bottom() + self.GAP
        above = mark.top() - self.GAP - height
        # flip above only when the sheet would hang off the bottom and there is room
        if below + height > area.bottom() and above >= area.top():
            top = above
        else:
            top = min(below, max(area.top(), area.bottom() - height + 1))

        left = mark.left() - self.PAD_X + 1  # the text lines up under the mark
        left = max(area.left() + 4, min(left, area.right() - width - 3))
        self.move(left, top)

    # --- dismissal ----------------------------------------------------
    def _inside(self, point: QPoint) -> bool:
        return self.geometry().contains(point) or self._mark_rect().contains(point)

    def eventFilter(self, obj, event):
        """Installed app-wide only while open: Esc, outside click, any scroll."""
        kind = event.type()
        if kind in (QEvent.Type.MouseButtonPress,
                    QEvent.Type.NonClientAreaMouseButtonPress, QEvent.Type.Wheel):
            if not self._inside(event.globalPosition().toPoint()):
                self.dismiss()
        elif kind == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
            self.dismiss()
            return True  # Esc puts the sheet away, it does not close the dialog
        return super().eventFilter(obj, event)

    def enterEvent(self, event):
        self._close_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        # Moving onto the label inside also sends Leave here — geometry decides.
        if not self.geometry().contains(QCursor.pos()):
            self.scheduleClose()
        super().leaveEvent(event)

    # --- paint --------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        sheet = QRectF(0.5, 0.5, self.width() - self.SHADOW - 1,
                       self.height() - self.SHADOW - 1)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(22, 15, 44, 97))  # rgba(22,15,44,.38), no blur
        painter.drawRoundedRect(sheet.translated(self.SHADOW, self.SHADOW), 4, 4)

        painter.setBrush(QColor(COLORS["paper_2"]))
        painter.setPen(QPen(QColor(44, 26, 114, 102), 1))
        painter.drawRoundedRect(sheet, 4, 4)


class InfoMark(QWidget):
    """A quiet "?" that prints an explanation sheet next to the row.

    Rest = violet ink, hover = magenta, open = struck (magenta filled): the
    brand's "actives are printed in register". Hover prints the sheet, a click
    pins it — see InfoPopover for why this is not a tooltip.
    """

    def __init__(self, text: str, size: int = 17, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hover = False
        self._popover = InfoPopover(self)
        self._open_timer = QTimer(self)
        self._open_timer.setSingleShot(True)
        self._open_timer.timeout.connect(self._popover.reveal)
        self.setText(text)

    def setText(self, text: str) -> None:
        self._popover.setText(text)
        self.setAccessibleDescription(text)

    def enterEvent(self, event):
        self._hover = True
        self.update()
        self._open_timer.start(InfoPopover.OPEN_DELAY)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        self._open_timer.stop()
        self._popover.scheduleClose()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._open_timer.stop()
        self._popover.togglePin()

    def hideEvent(self, event):
        self._open_timer.stop()
        self._popover.dismiss()
        super().hideEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(0.8, 0.8, self.width() - 1.6, self.height() - 1.6)

        if self._popover.isVisible():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(COLORS["accent"]))
            painter.drawEllipse(rect)
            ink = QColor(COLORS["on_ink"])
        else:
            ink = QColor(COLORS["mag_text"] if self._hover else COLORS["violet_ink"])
            painter.setPen(QPen(ink, 1.2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(rect)

        painter.setPen(ink)
        painter.setFont(mono_font(11, QFont.Weight.Bold, 0))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "?")


def _draw_arrow(painter: QPainter, cx: float, cy: float, color: QColor,
                up: bool = False, width: float = 11.0, height: float = 6.5) -> None:
    """A solid ink triangle, drawn as vector so it survives any DPI scaling."""
    path = QPainterPath()
    if up:
        path.moveTo(cx - width / 2, cy + height / 2)
        path.lineTo(cx + width / 2, cy + height / 2)
        path.lineTo(cx, cy - height / 2)
    else:
        path.moveTo(cx - width / 2, cy - height / 2)
        path.lineTo(cx + width / 2, cy - height / 2)
        path.lineTo(cx, cy + height / 2)
    path.closeSubpath()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawPath(path)


def folder_icon(px: int = 15, color: str = COLORS["violet"]) -> QIcon:
    """A small folder, drawn as vector.

    The bundled Plex/Unbounded faces carry no folder glyph, and the ▶ that
    stood in for one read as "play". Drawn here so it scales with the display
    instead of blurring like a bitmap would.
    """
    ratio = QGuiApplication.primaryScreen().devicePixelRatio() if \
        QGuiApplication.primaryScreen() else 1.0
    height = round(px * 0.82)
    pixmap = QPixmap(round(px * ratio), round(height * ratio))
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), 1.3)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    top = 2.2
    body = QRectF(0.9, top, px - 1.8, height - top - 0.9)
    painter.drawRoundedRect(body, 1.6, 1.6)
    # the tab: a short lid over the left third, the way a folder is drawn
    tab = QPainterPath()
    tab.moveTo(0.9, top)
    tab.lineTo(0.9, 0.9)
    tab.lineTo(px * 0.44, 0.9)
    tab.lineTo(px * 0.55, top)
    painter.drawPath(tab)
    painter.end()

    return QIcon(pixmap)


class InkComboBox(QComboBox):
    """Combo box whose arrow is actually visible.

    QSS cannot draw it: Qt renders the CSS border-triangle trick as a solid
    rectangle, and a bitmap arrow blurs at 150% display scaling. So the QSS
    clears the default arrow and we paint a vector one over the drop-down zone.
    """

    ZONE = 26  # must match the QComboBox::drop-down width in styles.py

    def __init__(self, parent=None):
        super().__init__(parent)
        # The open list is a top-level container, and the app-wide
        # `QComboBox QAbstractItemView` rule never reaches it — the rows kept
        # Qt's grey focus frame and no highlight at all, which read as "this
        # list has no hover". Styling the view itself does reach it.
        view = self.view()
        view.setMouseTracking(True)
        view.setStyleSheet(f"""
            QAbstractItemView {{
                background-color: {COLORS["paper_2"]};
                border: 1px solid {COLORS["line_strong"]};
                color: {COLORS["violet"]};
                outline: none;
                padding: 3px;
            }}
            QAbstractItemView::item {{
                padding: 6px 9px;
                border: none;
                border-radius: 3px;
            }}
            QAbstractItemView::item:hover,
            QAbstractItemView::item:selected {{
                background-color: {COLORS["violet_2"]};
                color: {COLORS["on_ink"]};
            }}
        """)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(COLORS["mag_text"] if self.underMouse() else COLORS["violet_ink"])
        if not self.isEnabled():
            color = QColor(44, 26, 114, 90)
        _draw_arrow(painter, self.width() - self.ZONE / 2 - 1, self.height() / 2, color)


class InkSpinBox(QSpinBox):
    """Spin box with arrows big enough to aim at (Qt's default are two specks)."""

    ZONE = 22  # must match QSpinBox::up-button/down-button width in styles.py

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(COLORS["violet_ink"]) if self.isEnabled() else QColor(44, 26, 114, 90)
        cx = self.width() - self.ZONE / 2 - 1
        _draw_arrow(painter, cx, self.height() * 0.32, color, up=True, height=5.5)
        _draw_arrow(painter, cx, self.height() * 0.68, color, up=False, height=5.5)


class InkCheckBox(QCheckBox):
    """Square type sort that actually prints a mark when it is set.

    A bare magenta fill reads as a colour swatch: the box is inked but nothing
    is struck on it. Checked = magenta fill plus a cream tick with a 1px violet
    misregistration under it.
    """

    BOX = 18
    GAP = 10

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def sizeHint(self):
        hint = super().sizeHint()
        metrics = QFontMetricsF(self.font())
        width = self.BOX + (self.GAP + round(metrics.horizontalAdvance(self.text()))
                            if self.text() else 0)
        height = max(self.BOX + 4, round(metrics.height()) + 4)
        hint.setWidth(width + 2)
        hint.setHeight(max(hint.height(), height))
        return hint

    def minimumSizeHint(self):
        return self.sizeHint()

    def _tick_path(self, left: float, top: float) -> QPainterPath:
        path = QPainterPath()
        path.moveTo(left + self.BOX * 0.24, top + self.BOX * 0.52)
        path.lineTo(left + self.BOX * 0.43, top + self.BOX * 0.71)
        path.lineTo(left + self.BOX * 0.78, top + self.BOX * 0.31)
        return path

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        top = (self.height() - self.BOX) / 2
        box = QRectF(1, top, self.BOX, self.BOX)
        enabled = self.isEnabled()
        checked = self.isChecked()

        if checked:
            fill = QColor(COLORS["accent"] if enabled else COLORS["violet_ink"])
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(fill)
            painter.drawRoundedRect(box, 2, 2)

            # second ink under the first: the tick is printed twice, 1px apart
            ghost = QPen(QColor(COLORS["violet"]), 2.0)
            ghost.setCapStyle(Qt.PenCapStyle.RoundCap)
            ghost.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(ghost)
            painter.drawPath(self._tick_path(box.left() + 1, box.top() + 1))

            tick = QPen(QColor(COLORS["on_ink"]), 2.0)
            tick.setCapStyle(Qt.PenCapStyle.RoundCap)
            tick.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(tick)
            painter.drawPath(self._tick_path(box.left(), box.top()))
        else:
            border = QColor(COLORS["accent"]) if (self.underMouse() and enabled) \
                else QColor(44, 26, 114, 115)
            painter.setPen(QPen(border, 1.6))
            painter.setBrush(QColor(COLORS["paper_2"]))
            painter.drawRoundedRect(box.adjusted(0.8, 0.8, -0.8, -0.8), 2, 2)

        if self.text():
            painter.setPen(QColor(COLORS["violet"] if enabled else COLORS["violet_ink"]))
            painter.setFont(self.font())
            text_rect = self.rect().adjusted(self.BOX + self.GAP, 0, 0, 0)
            painter.drawText(
                text_rect,
                int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                self.text(),
            )


class SegmentedControl(QWidget):
    """A row of printed keys: exactly one is struck.

    Used where a spin box or a checkbox was lying about the choice — picking
    one of five parallel downloads, or one of two update channels. Active key =
    solid second ink with paper type on it; the others are quiet outlines.
    """

    changed = pyqtSignal(int)

    def __init__(self, options, parent=None, padding: int = 12, height: int = 30):
        """options: list of (label, data) pairs."""
        super().__init__(parent)
        self._options = list(options)
        self._index = 0
        self._hover = -1
        self._padding = padding
        self._height = height
        self._font = mono_font(FS_MONO, QFont.Weight.DemiBold, 1.0)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(height)

    # --- data ---------------------------------------------------------
    def setOptions(self, options) -> None:
        """Replace the labels (a language switch) keeping the selection."""
        data = self.currentData()
        self._options = list(options)
        self.updateGeometry()
        self.setCurrentData(data)
        self.update()

    def currentIndex(self) -> int:
        return self._index

    def setCurrentIndex(self, index: int) -> None:
        if 0 <= index < len(self._options) and index != self._index:
            self._index = index
            self.update()
            self.changed.emit(index)

    def currentData(self):
        if 0 <= self._index < len(self._options):
            return self._options[self._index][1]
        return None

    def setCurrentData(self, data) -> None:
        for i, (_, value) in enumerate(self._options):
            if value == data:
                if i != self._index:
                    self._index = i
                    self.update()
                return

    # --- geometry -----------------------------------------------------
    def _seg_width(self) -> float:
        metrics = QFontMetricsF(self._font)
        widest = max((metrics.horizontalAdvance(label) for label, _ in self._options),
                     default=0)
        return widest + self._padding * 2

    def sizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(round(self._seg_width() * len(self._options)) + 2, self._height)

    def minimumSizeHint(self):
        return self.sizeHint()

    def _index_at(self, x: float) -> int:
        seg = self._seg_width()
        if seg <= 0:
            return -1
        index = int(x // seg)
        return index if 0 <= index < len(self._options) else -1

    # --- interaction --------------------------------------------------
    def mousePressEvent(self, event):
        index = self._index_at(event.position().x())
        if index >= 0:
            self.setCurrentIndex(index)

    def mouseMoveEvent(self, event):
        index = self._index_at(event.position().x())
        if index != self._hover:
            self._hover = index
            self.update()

    def leaveEvent(self, event):
        self._hover = -1
        self.update()
        super().leaveEvent(event)

    # --- paint --------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self._font)

        seg = self._seg_width()
        outer = QRectF(0.5, 0.5, seg * len(self._options), self.height() - 1)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLORS["paper_2"]))
        painter.drawRoundedRect(outer, 4, 4)

        for i, (label, _) in enumerate(self._options):
            cell = QRectF(outer.left() + seg * i, outer.top(), seg, outer.height())
            if i == self._index:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(COLORS["violet_2"]))
                path = QPainterPath()
                path.addRoundedRect(cell.adjusted(0.5, 0.5, -0.5, -0.5), 3, 3)
                painter.drawPath(path)
                painter.setPen(QColor(COLORS["on_ink"]))
            else:
                if i == self._hover:
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QColor(225, 27, 118, 20))
                    painter.drawRoundedRect(cell.adjusted(0.5, 0.5, -0.5, -0.5), 3, 3)
                painter.setPen(QColor(COLORS["violet_ink"]))
            painter.drawText(cell, Qt.AlignmentFlag.AlignCenter, label)

            if i and i != self._index and i - 1 != self._index:
                painter.setPen(QPen(QColor(44, 26, 114, 45), 1))
                painter.drawLine(QPointF(cell.left(), cell.top() + 6),
                                 QPointF(cell.left(), cell.bottom() - 6))

        painter.setPen(QPen(QColor(44, 26, 114, 100), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(outer, 4, 4)


class TaktDots(QWidget):
    """Four halftone dots printing in discrete takts.

    Stands in for the progress bar while ffmpeg merges: a bar frozen at the
    last download percent lies about what is happening. Dots say "working"
    without claiming a number.
    """

    def __init__(self, count: int = 4, dot: int = 5, gap: int = 7, parent=None):
        super().__init__(parent)
        self._count = count
        self._dot = dot
        self._gap = gap
        self._step = 0
        self._timer = QTimer(self)
        self._timer.setInterval(220)
        self._timer.timeout.connect(self._advance)
        self.setFixedSize(count * dot + (count - 1) * gap, dot + 2)

    def _advance(self):
        self._step = (self._step + 1) % (self._count + 1)
        self.update()

    def showEvent(self, event):
        self._timer.start()
        super().showEvent(event)

    def hideEvent(self, event):
        self._timer.stop()
        self._step = 0
        super().hideEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        y = (self.height() - self._dot) / 2
        for i in range(self._count):
            painter.setBrush(QColor(COLORS["accent"]) if i < self._step
                             else QColor(44, 26, 114, 45))
            painter.drawEllipse(QRectF(i * (self._dot + self._gap), y,
                                       self._dot, self._dot))


class KraftSheet(QWidget):
    """The page itself: kraft fill with paper grain, optional tape corners.

    The whole window is one sheet now, so this is the window's background
    rather than an island inside a dark shell.
    """

    _noise_tile: QPixmap | None = None

    def __init__(self, parent=None, tape: bool = False):
        super().__init__(parent)
        self.setObjectName("kraftSheet")
        self._tape = tape

    @classmethod
    def _get_noise_tile(cls) -> QPixmap:
        if cls._noise_tile is None:
            size = 160
            image = QImage(size, size, QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.transparent)
            rng = random.Random(17)  # fixed seed — same grain every run
            for y in range(size):
                for x in range(size):
                    alpha = rng.randint(0, 14)
                    if alpha:
                        image.setPixelColor(x, y, QColor(58, 42, 122, alpha))
            cls._noise_tile = QPixmap.fromImage(image)
        return cls._noise_tile

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(COLORS["paper"]))
        painter.drawTiledPixmap(self.rect(), self._get_noise_tile())

        if self._tape and self.width() > 140:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            tape_color = QColor(242, 236, 220, 150)
            edge_color = QColor(44, 26, 114, 28)
            for x, angle in ((26, -20), (self.width() - 26, 18)):
                painter.save()
                painter.translate(x, 6)
                painter.rotate(angle)
                painter.fillRect(-37, -11, 74, 22, tape_color)
                painter.setPen(QPen(edge_color, 1))
                painter.drawRect(-37, -11, 74, 22)
                painter.restore()
