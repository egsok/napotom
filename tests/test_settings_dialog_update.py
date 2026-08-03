"""Tests for the settings dialog behaviour while a yt-dlp update installs."""

import pytest


@pytest.fixture
def dialog(qapp, monkeypatch):
    from utils import config as config_module
    # Keep the test off the real config file
    monkeypatch.setattr(config_module.config_manager, 'set', lambda *a, **k: None)

    from ui.settings_dialog import SettingsDialog
    dlg = SettingsDialog()
    yield dlg
    dlg._updating = False
    dlg.deleteLater()


def test_dialog_refuses_to_close_while_updating(dialog):
    # The install result lands on this dialog; an application-modal message box
    # owned by a closed dialog blocks the main window while staying invisible
    dialog.show()
    dialog._set_updating(True)

    dialog.reject()
    assert dialog.isVisible(), 'Cancel closed the dialog mid-install'

    dialog.close()
    assert dialog.isVisible(), 'The window X closed the dialog mid-install'

    assert not dialog.save_btn.isEnabled()
    assert not dialog.cancel_btn.isEnabled()


def test_dialog_closes_normally_once_the_update_is_done(dialog):
    dialog.show()
    dialog._set_updating(True)
    dialog._set_updating(False)

    dialog.reject()
    assert not dialog.isVisible()


def test_dialog_unlocks_when_the_update_finishes(dialog):
    dialog._set_updating(True)
    dialog._set_updating(False)

    assert dialog.save_btn.isEnabled()
    assert dialog.cancel_btn.isEnabled()
    assert dialog.check_updates_btn.isEnabled()


@pytest.mark.parametrize('caption_key', ['check_now_btn', 'checking_btn', 'updating_btn'])
def test_update_button_fits_every_caption_it_can_show(dialog, caption_key):
    # Without a reserved width the longer captions clip ("БНОВЛЕНИЕ..") and
    # squeeze the neighbouring group out of the row
    from utils.i18n import tr

    button = dialog.check_updates_btn
    button.setText(tr(caption_key).upper())

    assert button.minimumWidth() >= button.sizeHint().width()
