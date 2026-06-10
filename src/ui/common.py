"""Shared UI helpers."""

from utils.i18n import tr


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
