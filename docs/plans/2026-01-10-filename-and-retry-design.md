# Исправление имён файлов и кнопка Retry

## Проблемы

1. **Конфликт имён файлов** — при загрузке видео с одинаковым названием но разным качеством, yt-dlp пропускает загрузку (файл уже существует)
2. **Нет retry для failed** — при ошибке загрузки нужно удалять элемент и добавлять заново

## Решения

### 1. Шаблон имени файла с качеством

**Было:**
```python
opts['outtmpl'] = os.path.join(output_path, '%(title)s.%(ext)s')
```

**Стало:**
```python
# Для видео
opts['outtmpl'] = os.path.join(output_path, '%(title)s [%(height)sp].%(ext)s')

# Для audio-only
opts['outtmpl'] = os.path.join(output_path, '%(title)s [audio].%(ext)s')
```

**Примеры результатов:**
- `Me at the zoo [240p].mp4`
- `Rick Astley - Never Gonna Give You Up [1080p].mp4`
- `Some Podcast [audio].mp3`

### 2. Кнопка Retry

**UI изменения в queue_item_widget.py:**
- При статусе FAILED: кнопка X меняется на ↻ (retry)
- Добавляется отдельная кнопка X для удаления
- Layout при Failed: `[Title - Failed] [↻] [X]`

**Новый сигнал:**
```python
retry_requested = pyqtSignal(str)  # item_id
```

**Логика в queue.py:**
```python
def retry_item(self, item_id: str):
    # Сбросить статус на PENDING
    # Сбросить progress и error
    # Запустить заново через _process_next()
```

### 3. Перезапись существующих файлов

```python
opts['overwrites'] = True
```

Гарантирует перезапись при повторной загрузке.

## Файлы для изменения

1. `src/core/downloader.py` — шаблон имени, overwrites
2. `src/ui/widgets/queue_item_widget.py` — retry button
3. `src/core/queue.py` — retry_item метод
