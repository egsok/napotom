# Video Downloader 2

Простой загрузчик видео с YouTube, VK и 1000+ других сайтов.

## Скачать

**[Последний релиз](../../releases/latest)**

| Платформа | Файл | Инструкция |
|-----------|------|------------|
| Windows | `VideoDownloader2-Windows.zip` | Распакуйте и запустите .exe |
| macOS | `VideoDownloader2-macOS.dmg` | Откройте и перетащите в Applications |

> ffmpeg включён, дополнительная установка не требуется.

## Возможности

- Загрузка видео в разных качествах (Best, 1080p, 720p)
- Извлечение только аудио (MP3)
- Очередь загрузок с параллельным скачиванием
- Уведомления о завершении
- Автоматическое обновление yt-dlp

## Сборка из исходников

```bash
# Windows
pip install -r requirements.txt
pyinstaller build.spec

# macOS
git checkout mac
pip install -r requirements.txt
iconutil -c icns assets/icon.iconset -o assets/icon.icns
pyinstaller build_mac.spec
```

## Лицензия

MIT
