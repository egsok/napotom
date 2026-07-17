"""Shared UI helpers and nnv brand widgets."""

import random
import sys

from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QWidget

from ui.styles import COLORS, FONT_DISPLAY, FONT_MONO
from utils.i18n import tr


def apply_brand_titlebar(window: QWidget) -> None:
    """Paint the native Windows title bar in wall ink (Windows 11 DWM API).

    Falls back to plain dark mode on Windows 10; no-op elsewhere.
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
        DWMWA_CAPTION_COLOR = 35
        DWMWA_TEXT_COLOR = 36
        caption = ctypes.c_uint(colorref(COLORS['bg_dark']))
        text = ctypes.c_uint(colorref(COLORS['text_primary']))
        if dwm.DwmSetWindowAttribute(hwnd, DWMWA_CAPTION_COLOR,
                                     ctypes.byref(caption), 4) != 0:
            # Windows 10: no caption color — at least force dark title bar
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            dark = ctypes.c_int(1)
            dwm.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                                      ctypes.byref(dark), 4)
        else:
            dwm.DwmSetWindowAttribute(hwnd, DWMWA_TEXT_COLOR,
                                      ctypes.byref(text), 4)
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


def mono_font(px: int = 10, weight: QFont.Weight = QFont.Weight.Medium,
              tracking: float = 1.2) -> QFont:
    """Utility mono font (IBM Plex Mono) with letter-spacing — QSS can't do tracking."""
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


def ink_offset(widget: QWidget, dx: float = 1.5, dy: float = 1.5,
               color: str = COLORS["accent"]) -> None:
    """Misregistration signature: hard ink offset (no blur) behind a label."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(0)
    effect.setOffset(dx, dy)
    effect.setColor(QColor(color))
    widget.setGraphicsEffect(effect)


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


class KraftSheet(QWidget):
    """Kraft paper sheet: paper fill, paper-grain noise, tape corners.

    Children get paper-context styling via the ``#kraftSheet`` QSS scope.
    """

    _noise_tile: QPixmap | None = None

    def __init__(self, parent=None, tape: bool = True):
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
