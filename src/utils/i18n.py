"""Internationalization (i18n) support for the application."""

from utils.config import config_manager
from utils.translations import TRANSLATIONS


def get_current_language() -> str:
    """Get the current language from config.
    
    Returns:
        Language code ('en' or 'ru')
    """
    return config_manager.get('language', 'en')


def set_language(lang: str) -> None:
    """Set the current language in config.
    
    Args:
        lang: Language code ('en' or 'ru')
    """
    if lang in TRANSLATIONS:
        config_manager.set('language', lang)


def tr(key: str, **kwargs) -> str:
    """Translate a string key to the current language.
    
    Args:
        key: Translation key
        **kwargs: Format arguments for the translated string
    
    Returns:
        Translated string, or English fallback, or key itself if not found
    """
    lang = get_current_language()
    
    # Try current language
    if lang in TRANSLATIONS and key in TRANSLATIONS[lang]:
        text = TRANSLATIONS[lang][key]
        if kwargs:
            return text.format(**kwargs)
        return text
    
    # Fallback to English
    if key in TRANSLATIONS.get('en', {}):
        text = TRANSLATIONS['en'][key]
        if kwargs:
            return text.format(**kwargs)
        return text
    
    # Fallback to key itself (helps debugging)
    return key
