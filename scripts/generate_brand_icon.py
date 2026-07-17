#!/usr/bin/env python3
"""Generate the nnv brand app icon (K1 "print-run arrow") for all platforms.

Draws the two-ink misregistered download arrow with QPainter at each target
size (per-size stroke tuning, no downscaling blur), then writes:
  - assets/icon.iconset/icon_*.png  (macOS iconset, converted to .icns in CI)
  - assets/icon.ico                 (Windows multi-size ICO, via Pillow)

Usage:
    .venv/Scripts/python.exe scripts/generate_brand_icon.py
"""

import sys
from pathlib import Path

from PIL import Image
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPainterPath, QPen

REPO_ROOT = Path(__file__).resolve().parent.parent
ICONSET_DIR = REPO_ROOT / "assets" / "icon.iconset"
OUTPUT_ICO = REPO_ROOT / "assets" / "icon.ico"

WALL = QColor("#160f2c")
VIOLET = QColor("#2c1a72")
MAGENTA = QColor("#e11b76")
CREAM = QColor("#ece3cd")


def _arrow_path(scale: float, dx: float, dy: float) -> QPainterPath:
    """Arrow + tray polylines in 64-unit space, offset by (dx, dy)."""
    path = QPainterPath()
    # shaft
    path.moveTo(QPointF((33 + dx) * scale, (13.5 + dy) * scale))
    path.lineTo(QPointF((33 + dx) * scale, (35.5 + dy) * scale))
    # chevron
    path.moveTo(QPointF((23 + dx) * scale, (27.5 + dy) * scale))
    path.lineTo(QPointF((33 + dx) * scale, (37.5 + dy) * scale))
    path.lineTo(QPointF((43 + dx) * scale, (27.5 + dy) * scale))
    # tray
    path.moveTo(QPointF((17 + dx) * scale, (46 + dy) * scale))
    path.lineTo(QPointF((49 + dx) * scale, (46 + dy) * scale))
    return path


def render_icon(size: int) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    scale = size / 64.0
    small = size <= 24

    # ink-wall plate with rounded corners
    radius = 13 * scale
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(WALL)
    painter.drawRoundedRect(QRectF(0, 0, size, size), radius, radius)

    # three ink passes with misregistration: violet, magenta, cream on top
    stroke = (6 if small else 5) * scale
    offset = 1.2 if small else 1.5
    passes = [
        (VIOLET, offset, offset),
        (MAGENTA, -offset, -offset * 0.7),
        (CREAM, 0.0, 0.0),
    ]
    for color, dx, dy in passes:
        pen = QPen(color, stroke)
        pen.setCapStyle(Qt.PenCapStyle.SquareCap)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(_arrow_path(scale, dx / scale, dy / scale))

    # registration dot (dropped on tiny sizes)
    if not small:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(MAGENTA)
        dot_r = 3.4 * scale
        painter.drawEllipse(QPointF(53 * scale, 49 * scale), dot_r, dot_r)

    painter.end()
    return image


def qimage_to_pil(image: QImage) -> Image.Image:
    image = image.convertToFormat(QImage.Format.Format_RGBA8888)
    width, height = image.width(), image.height()
    ptr = image.constBits()
    ptr.setsize(height * image.bytesPerLine())
    return Image.frombytes("RGBA", (width, height), bytes(ptr), "raw", "RGBA",
                           image.bytesPerLine())


def main() -> None:
    app = QGuiApplication(sys.argv)  # noqa: F841 — QPainter needs a Gui app

    ICONSET_DIR.mkdir(parents=True, exist_ok=True)

    # macOS iconset: base sizes with @2x doubles
    for base in (16, 32, 64, 128, 256, 512):
        render_icon(base).save(str(ICONSET_DIR / f"icon_{base}x{base}.png"))
        render_icon(base * 2).save(str(ICONSET_DIR / f"icon_{base}x{base}@2x.png"))
    print(f"iconset: 12 PNGs -> {ICONSET_DIR}")

    # Windows ICO: independent per-size renders as separate frames
    sizes = [256, 128, 64, 48, 32, 24, 16]
    frames = [qimage_to_pil(render_icon(s)) for s in sizes]
    frames[0].save(
        str(OUTPUT_ICO), format="ICO",
        append_images=frames[1:],
        sizes=[(s, s) for s in sizes],
    )
    print(f"ico: {OUTPUT_ICO} — {OUTPUT_ICO.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
