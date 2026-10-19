"""
Конфигурация приложения
"""
import os
import logging
import sys
from typing import Dict, Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

# === Настройка логирования ===
def setup_logging():
    """Настройка логирования для всего приложения"""
    log_format = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Основной логгер
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Уменьшаем логи от сторонних библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("WDM").setLevel(logging.WARNING)

    return logging.getLogger("competitor_monitor")

# Инициализация логгера
logger = setup_logging()


class Settings(BaseSettings):
    """Настройки приложения"""

    # OpenAI API (официальный)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_vision_model: str = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # История
    history_file: str = "history.json"
    max_history_items: int = 10

    # Парсер
    parser_timeout: int = 15
    parser_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    parser_page_text_max_chars: int = 3000

    # Конкуренты ниши поиска культурных событий, мероприятий и билетов
    competitor_urls: Dict[str, str] = {
        "yandex_afisha": "https://afisha.yandex.ru",
        "afisha_ru": "https://www.afisha.ru",
        "kudago": "https://kudago.com",
        "timepad": "https://timepad.ru",
        "kassir": "https://www.kassir.ru",
    }
    competitor_names: Dict[str, str] = {
        "yandex_afisha": "Яндекс Афиша",
        "afisha_ru": "Afisha.ru",
        "kudago": "KudaGo",
        "timepad": "Timepad",
        "kassir": "Kassir.ru",
    }

    class Config:
        env_file = ".env"
        extra = "ignore"

    def find_competitor(self, value: str) -> Optional[str]:
        """Найти URL конкурента по ключу или названию (регистронезависимо)."""
        if not value:
            return None
        query = value.strip().lower()
        for key, url in self.competitor_urls.items():
            name = self.competitor_names.get(key, key)
            if query in (key.lower(), name.lower(), url.lower()):
                return url
        return None


settings = Settings()

if not settings.openai_api_key:
    raise RuntimeError(
        "OPENAI_API_KEY не задан. Укажите ключ официального OpenAI API "
        "в файле .env (образец: env.example.txt). "
        "Получить ключ: https://platform.openai.com/api-keys"
    )
