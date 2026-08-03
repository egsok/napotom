"""Tests for the yt-dlp update channel (stable wheel vs nightly sdist)."""

import io
import tarfile
import zipfile

import pytest

from core import updater as up


def _make_wheel(path):
    """A PyPI-style wheel: yt_dlp/ lives at the archive root."""
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('yt_dlp/__init__.py', '')
        zf.writestr('yt_dlp/version.py', "__version__ = '2026.7.4'\n")
        zf.writestr('yt_dlp-2026.7.4.dist-info/METADATA', 'Name: yt-dlp\n')


def _make_sdist(path):
    """A nightly-style sdist: yt_dlp/ sits under a yt-dlp-<version>/ top level."""
    with tarfile.open(path, 'w:gz') as tf:
        for name, body in (
            ('yt-dlp/yt_dlp/__init__.py', b''),
            ('yt-dlp/yt_dlp/version.py', b"__version__ = '2026.07.23.234303'\n"),
            ('yt-dlp/README.md', b'not part of the package\n'),
        ):
            info = tarfile.TarInfo(name)
            info.size = len(body)
            tf.addfile(info, io.BytesIO(body))


def test_wheel_extraction_yields_importable_package(tmp_path):
    archive = tmp_path / 'yt_dlp.whl'
    _make_wheel(archive)
    override = tmp_path / 'override'

    up._extract_package(str(archive), override)

    assert (override / 'yt_dlp' / '__init__.py').is_file()
    assert "2026.7.4" in (override / 'yt_dlp' / 'version.py').read_text()


def test_sdist_extraction_strips_the_top_level_dir(tmp_path):
    # Nightly releases ship no wheel; the sdist nests yt_dlp one level deep, and
    # a copied-as-is layout would never be importable from the override dir
    archive = tmp_path / 'yt-dlp.tar.gz'
    _make_sdist(archive)
    override = tmp_path / 'override'

    up._extract_package(str(archive), override)

    assert (override / 'yt_dlp' / '__init__.py').is_file()
    assert not (override / 'yt-dlp').exists()
    assert not (override / 'README.md').exists()  # only the package is extracted


def test_extraction_replaces_a_previous_install(tmp_path):
    override = tmp_path / 'override'
    override.mkdir()
    (override / 'yt_dlp').mkdir()
    (override / 'yt_dlp' / 'leftover.py').write_text('stale')

    archive = tmp_path / 'yt_dlp.whl'
    _make_wheel(archive)
    up._extract_package(str(archive), override)

    assert not (override / 'yt_dlp' / 'leftover.py').exists()


def test_unknown_archive_is_rejected(tmp_path):
    archive = tmp_path / 'garbage.bin'
    archive.write_bytes(b'not an archive')

    with pytest.raises(ValueError):
        up._extract_package(str(archive), tmp_path / 'override')


@pytest.fixture
def fake_config(monkeypatch):
    values = {'ytdlp_nightly': False, 'ytdlp_installed_channel': 'stable',
              'ytdlp_update_pending_restart': False, 'last_dismissed_ytdlp_version': ''}
    monkeypatch.setattr(up.config_manager, 'get',
                        lambda key, default=None: values.get(key, default))
    monkeypatch.setattr(up.config_manager, 'set', values.__setitem__)
    return values


def test_channel_switch_offers_an_older_build(qapp, fake_config):
    # Going nightly -> stable installs a *lower* version number; without the
    # channel check the app would report "up to date" and silently keep nightly
    fake_config['ytdlp_installed_channel'] = 'nightly'
    fake_config['ytdlp_nightly'] = False
    updater = up.Updater()
    offered = []
    updater.update_available.connect(lambda c, l: offered.append((c, l)))

    updater._on_version_checked('2026.07.23.234303', '2026.7.4')

    assert offered == [('2026.07.23.234303', '2026.7.4')]
    assert updater.channel_switch is True


def test_same_channel_and_same_version_is_up_to_date(qapp, fake_config):
    updater = up.Updater()
    up_to_date = []
    updater.already_up_to_date.connect(up_to_date.append)

    updater._on_version_checked('2026.7.4', '2026.7.4')

    assert up_to_date == ['2026.7.4']
    assert updater.channel_switch is False


def test_channel_switch_ignores_a_dismissed_version(qapp, fake_config):
    fake_config['ytdlp_installed_channel'] = 'stable'
    fake_config['ytdlp_nightly'] = True
    fake_config['last_dismissed_ytdlp_version'] = '2026.07.23.234303'
    updater = up.Updater()
    updater._on_version_checked('2026.7.4', '2026.07.23.234303')

    assert updater.should_prompt_for_update('2026.07.23.234303') is True


def test_worker_is_held_until_its_result_arrives(qapp, fake_config, monkeypatch):
    # The pool owns the C++ runnable, but the Python object carries the signals;
    # drop the last reference and a long install delivers its result to nobody
    updater = up.Updater()
    monkeypatch.setattr(updater.thread_pool, 'start', lambda runnable: None)

    updater.install_update()
    assert updater._installer is not None

    updater.check_for_updates()
    assert updater._checker is not None


def test_worker_reference_is_released_after_delivery(qapp, fake_config, monkeypatch):
    updater = up.Updater()
    monkeypatch.setattr(updater.thread_pool, 'start', lambda runnable: None)
    updater.install_update()

    updater._on_update_complete(True, 'done')

    assert updater._installer is None


def test_install_records_the_channel_it_came_from(qapp, fake_config):
    fake_config['ytdlp_nightly'] = True
    updater = up.Updater()
    updater.channel_switch = True

    updater._on_update_complete(True, 'Updated yt-dlp to 2026.07.23.234303.')

    assert fake_config['ytdlp_installed_channel'] == 'nightly'
    assert fake_config['ytdlp_update_pending_restart'] is True
    assert updater.channel_switch is False
