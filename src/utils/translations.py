"""Translation dictionaries for i18n support."""

TRANSLATIONS = {
    'en': {
        # Main window
        'app_title': 'Video Downloader 2',
        'url_placeholder': 'Paste video URL here...',
        'quality_label': 'Quality:',
        'save_to_label': 'Save to:',
        'change_btn': 'Change',
        'queue_title': 'QUEUE',
        'empty_queue': 'Paste a video URL and click + to start downloading',
        'open_folder_btn': 'Open Folder',
        'settings_btn': 'Settings',
        'invalid_url_title': 'Invalid URL',
        'invalid_url_message': 'Please enter a valid URL',
        'select_download_folder': 'Select Download Folder',
        'getting_video_info': 'Getting video info...',
        
        # Quality options
        'quality_best': 'Best',
        'quality_1080p': '1080p',
        'quality_720p': '720p',
        'quality_audio': 'Audio only',
        
        # Settings dialog
        'settings_title': 'Settings',
        'language_section': 'Language',
        'language_label': 'Interface language:',
        'language_restart_hint': 'Restart app to apply language change',
        'download_settings': 'Download Settings',
        'download_path_label': 'Download Path:',
        'browse_btn': 'Browse...',
        'default_quality_label': 'Default Quality:',
        'parallel_downloads_label': 'Parallel Downloads:',
        'parallel_downloads_tooltip': 'Number of videos to download simultaneously',
        'preferences_section': 'Preferences',
        'enable_notifications': 'Enable notifications',
        'enable_sound': 'Enable sound',
        'check_updates_startup': 'Check for updates on startup',
        'ytdlp_section': 'yt-dlp',
        'version_label': 'Version:',
        'check_now_btn': 'Check Now',
        'cookies_section': 'Cookies (for age-restricted videos)',
        'cookies_description': 'Required for age-restricted or members-only videos. Use cookies.txt file (recommended) or browser import.',
        'cookies_file_label': 'Cookies file:',
        'no_file_selected': 'No file selected',
        'clear_btn': 'Clear',
        'how_to_export_cookies': 'How to export cookies?',
        'or_use_browser': '— or use browser import (may not work on Windows) —',
        'browser_label': 'Browser:',
        'browser_none': 'None',
        'test_import_btn': 'Test Import',
        'logging_section': 'Logging',
        'log_file_label': 'Log file:',
        'not_configured': 'Not configured',
        'cancel_btn': 'Cancel',
        'save_btn': 'Save',
        
        # Cookie help dialog
        'cookie_help_title': 'How to Export Cookies',
        'cookie_help_when_needed': '<b>When do you need cookies?</b><br>'
            'Only for age-restricted or members-only videos. '
            'Regular videos download without cookies.<br><br>',
        'cookie_help_warning': '⚠️ <b>Important:</b> YouTube rotates cookies on open tabs. '
            'Use a <b>private/incognito window</b> to export cookies that stay valid.<br><br>',
        'export_from_chrome': 'Export Cookies (Chrome, Edge, Firefox)',
        'cookie_step_1': '<b>Step 1:</b> Install the '
            '<a href="https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc">'
            'Get cookies.txt LOCALLY</a> browser extension<br><br>',
        'cookie_step_2': '<b>Step 2:</b> Open a <b>private/incognito window</b> and log into YouTube<br><br>',
        'cookie_step_3': '<b>Step 3:</b> In the <b>same tab</b>, go to <code>https://www.youtube.com/robots.txt</code><br><br>',
        'cookie_step_4': '<b>Step 4:</b> Click the extension icon → export cookies → save as <code>cookies.txt</code><br><br>',
        'cookie_step_5': '<b>Step 5:</b> <b>Close the private window</b> (so cookies don\'t rotate)<br><br>',
        'cookie_step_6': '<b>Step 6:</b> In this app, click <b>"Browse..."</b> and select the saved file',
        'open_extension_page': 'Open Extension Page (Chrome Web Store)',
        'firefox_note': "For Firefox: Use 'cookies.txt' extension from Firefox Add-ons. Same incognito steps apply.",
        'close_btn': 'Close',
        'select_cookies_file': 'Select Cookies File',
        
        # Cookie status messages
        'cookie_file_loaded': 'Cookie file loaded successfully.',
        'cookie_file_invalid': 'Invalid format. Use Netscape/Mozilla cookie format.',
        'cookie_file_error': 'Could not read file: {error}',
        'cookie_file_cleared': 'Cookie file cleared.',
        'select_browser_first': 'Select a browser first.',
        'testing_cookies': 'Testing...',
        'cookie_import_success': 'Found {count} cookies from {browser}',
        'cookie_import_empty': 'No cookies found in {browser}. Make sure you\'re logged into YouTube.',
        'cookie_import_permission_error': 'Permission denied. Close {browser} and try again.',
        'cookie_import_dpapi_error': 'Cannot decrypt cookies. Use cookies.txt file instead.',
        'cookie_import_error': 'Import failed: {error}',
        
        # Update messages
        'checking_btn': 'Checking...',
        'update_available_title': 'Update Available',
        'update_available_message': 'yt-dlp {latest} is available (current: {current}).\n\nUpdate now?',
        'updating_btn': 'Updating...',
        'up_to_date_title': 'Up to Date',
        'up_to_date_message': 'yt-dlp {version} is the latest version.',
        'update_check_failed_title': 'Update Check Failed',
        'update_check_failed_message': 'Could not check for updates:\n{error}',
        'update_complete_title': 'Update Complete',
        'update_failed_title': 'Update Failed',
        
        # Queue item statuses
        'status_waiting': 'Waiting',
        'status_downloading': '{progress}%',
        'status_processing': 'Processing...',
        'status_done': 'Done',
        'status_failed': 'Failed',
        'status_cancelled': 'Cancelled',
        'retry_tooltip': 'Retry download',
        'open_folder_tooltip': 'Open folder',

        # Credits
        'credits_text': 'Сделано ИИ 🤖 · проверено человеком',
        'credits_subscribe': 'подписывайся → @neiroset_ne_vinovata',
        'credits_url': 'https://t.me/+GpZ_G6I4yl1jZDcy',
    },
    
    'ru': {
        # Main window
        'app_title': 'Video Downloader 2',
        'url_placeholder': 'Вставьте URL видео...',
        'quality_label': 'Качество:',
        'save_to_label': 'Сохранить в:',
        'change_btn': 'Изменить',
        'queue_title': 'ОЧЕРЕДЬ',
        'empty_queue': 'Вставьте URL видео и нажмите + для начала загрузки',
        'open_folder_btn': 'Открыть папку',
        'settings_btn': 'Настройки',
        'invalid_url_title': 'Неверный URL',
        'invalid_url_message': 'Пожалуйста, введите корректный URL',
        'select_download_folder': 'Выберите папку для загрузки',
        'getting_video_info': 'Получение информации о видео...',
        
        # Quality options
        'quality_best': 'Лучшее',
        'quality_1080p': '1080p',
        'quality_720p': '720p',
        'quality_audio': 'Только аудио',
        
        # Settings dialog
        'settings_title': 'Настройки',
        'language_section': 'Язык',
        'language_label': 'Язык интерфейса:',
        'language_restart_hint': 'Перезапустите приложение для применения изменений',
        'download_settings': 'Настройки загрузки',
        'download_path_label': 'Путь загрузки:',
        'browse_btn': 'Обзор...',
        'default_quality_label': 'Качество по умолчанию:',
        'parallel_downloads_label': 'Параллельных загрузок:',
        'parallel_downloads_tooltip': 'Количество одновременно загружаемых видео',
        'preferences_section': 'Настройки',
        'enable_notifications': 'Включить уведомления',
        'enable_sound': 'Включить звук',
        'check_updates_startup': 'Проверять обновления при запуске',
        'ytdlp_section': 'yt-dlp',
        'version_label': 'Версия:',
        'check_now_btn': 'Проверить',
        'cookies_section': 'Cookies (для видео с ограничением по возрасту)',
        'cookies_description': 'Требуется для видео с возрастными ограничениями или только для участников. Используйте файл cookies.txt (рекомендуется) или импорт из браузера.',
        'cookies_file_label': 'Файл cookies:',
        'no_file_selected': 'Файл не выбран',
        'clear_btn': 'Очистить',
        'how_to_export_cookies': 'Как экспортировать cookies?',
        'or_use_browser': '— или используйте импорт из браузера (может не работать на Windows) —',
        'browser_label': 'Браузер:',
        'browser_none': 'Не выбран',
        'test_import_btn': 'Тест импорта',
        'logging_section': 'Логирование',
        'log_file_label': 'Файл логов:',
        'not_configured': 'Не настроено',
        'cancel_btn': 'Отмена',
        'save_btn': 'Сохранить',
        
        # Cookie help dialog
        'cookie_help_title': 'Как экспортировать Cookies',
        'cookie_help_when_needed': '<b>Когда нужны cookies?</b><br>'
            'Только для видео с возрастными ограничениями или для участников. '
            'Обычные видео скачиваются без cookies.<br><br>',
        'cookie_help_warning': '⚠️ <b>Важно:</b> YouTube обновляет cookies в открытых вкладках. '
            'Используйте <b>приватное/инкогнито окно</b> для экспорта cookies, которые будут работать.<br><br>',
        'export_from_chrome': 'Экспорт Cookies (Chrome, Edge, Firefox)',
        'cookie_step_1': '<b>Шаг 1:</b> Установите расширение '
            '<a href="https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc">'
            'Get cookies.txt LOCALLY</a><br><br>',
        'cookie_step_2': '<b>Шаг 2:</b> Откройте <b>приватное/инкогнито окно</b> и войдите на YouTube<br><br>',
        'cookie_step_3': '<b>Шаг 3:</b> В <b>той же вкладке</b> перейдите на <code>https://www.youtube.com/robots.txt</code><br><br>',
        'cookie_step_4': '<b>Шаг 4:</b> Нажмите на иконку расширения → экспорт cookies → сохраните как <code>cookies.txt</code><br><br>',
        'cookie_step_5': '<b>Шаг 5:</b> <b>Закройте приватное окно</b> (чтобы cookies не обновились)<br><br>',
        'cookie_step_6': '<b>Шаг 6:</b> В этом приложении нажмите <b>"Обзор..."</b> и выберите сохранённый файл',
        'open_extension_page': 'Открыть страницу расширения (Chrome Web Store)',
        'firefox_note': "Для Firefox: используйте расширение 'cookies.txt' из Firefox Add-ons. Те же шаги с инкогнито.",
        'close_btn': 'Закрыть',
        'select_cookies_file': 'Выберите файл Cookies',
        
        # Cookie status messages
        'cookie_file_loaded': 'Файл cookies успешно загружен.',
        'cookie_file_invalid': 'Неверный формат. Используйте формат Netscape/Mozilla.',
        'cookie_file_error': 'Не удалось прочитать файл: {error}',
        'cookie_file_cleared': 'Файл cookies очищен.',
        'select_browser_first': 'Сначала выберите браузер.',
        'testing_cookies': 'Проверка...',
        'cookie_import_success': 'Найдено {count} cookies из {browser}',
        'cookie_import_empty': 'Cookies не найдены в {browser}. Убедитесь, что вы вошли на YouTube.',
        'cookie_import_permission_error': 'Отказано в доступе. Закройте {browser} и попробуйте снова.',
        'cookie_import_dpapi_error': 'Не удаётся расшифровать cookies. Используйте файл cookies.txt.',
        'cookie_import_error': 'Ошибка импорта: {error}',
        
        # Update messages
        'checking_btn': 'Проверка...',
        'update_available_title': 'Доступно обновление',
        'update_available_message': 'Доступен yt-dlp {latest} (текущая: {current}).\n\nОбновить сейчас?',
        'updating_btn': 'Обновление...',
        'up_to_date_title': 'Актуальная версия',
        'up_to_date_message': 'yt-dlp {version} — последняя версия.',
        'update_check_failed_title': 'Ошибка проверки обновлений',
        'update_check_failed_message': 'Не удалось проверить обновления:\n{error}',
        'update_complete_title': 'Обновление завершено',
        'update_failed_title': 'Ошибка обновления',
        
        # Queue item statuses
        'status_waiting': 'Ожидание',
        'status_downloading': '{progress}%',
        'status_processing': 'Обработка...',
        'status_done': 'Готово',
        'status_failed': 'Ошибка',
        'status_cancelled': 'Отменено',
        'retry_tooltip': 'Повторить загрузку',
        'open_folder_tooltip': 'Открыть папку',

        # Credits
        'credits_text': 'Сделано ИИ 🤖 · проверено человеком',
        'credits_subscribe': 'подписывайся → @neiroset_ne_vinovata',
        'credits_url': 'https://t.me/+GpZ_G6I4yl1jZDcy',
    }
}
