"""
Сервис для парсинга веб-страниц через Selenium (Chrome / Microsoft Edge)
"""
import base64
import asyncio
import time
import logging
from dataclasses import dataclass
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from backend.config import settings

# Логгер для сервиса
logger = logging.getLogger("competitor_monitor.parser")

# Маркеры страниц-блокировок (CAPTCHA / антибот-защита / ошибки доступа)
BLOCK_PAGE_MARKERS: List[str] = [
    "captcha",
    "recaptcha",
    "hcaptcha",
    "гугл капча",
    "подтвердите, что вы не робот",
    "подтвердите, что вы человек",
    "are you a robot",
    "verify you are human",
    "unusual traffic",
    "access denied",
    "request blocked",
    "forbidden",
    "too many requests",
    "just a moment",
    "checking your browser",
    "security check",
    "доступ запрещён",
    "доступ запрещен",
    "защита от автоматических запросов",
    "проверка браузера",
    "cloudflare",
]


@dataclass
class ParseResult:
    """Результат парсинга страницы"""
    url: str
    title: Optional[str] = None
    h1: Optional[str] = None
    first_paragraph: Optional[str] = None
    meta_description: Optional[str] = None
    page_text: Optional[str] = None
    screenshot_bytes: Optional[bytes] = None
    status_code: Optional[int] = None
    error: Optional[str] = None


class BrowserNotAvailableError(Exception):
    """Не удалось запустить ни один поддерживаемый браузер"""
    pass


BROWSER_NOT_FOUND_MESSAGE = "Не найден поддерживаемый браузер Chrome или Microsoft Edge"


class ParserService:
    """Парсинг веб-страниц через Chrome с созданием скриншота"""

    def __init__(self):
        logger.info("=" * 50)
        logger.info("Инициализация Parser сервиса")
        logger.info(f"  Timeout: {settings.parser_timeout} сек")
        logger.info(f"  User-Agent: {settings.parser_user_agent[:50]}...")
        logger.info(f"  Конкурентов в списке: {len(settings.competitor_urls)}")

        self.timeout = settings.parser_timeout
        self._executor = ThreadPoolExecutor(max_workers=2)

        logger.info("Parser сервис инициализирован ✓")
        logger.info("=" * 50)

    @staticmethod
    def _apply_common_options(options):
        """Общие аргументы запуска для Chrome и Edge (headless + безопасность)"""
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument(f'--user-agent={settings.parser_user_agent}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        return options

    def _create_chrome_driver(self) -> webdriver.Chrome:
        """Создать Chrome WebDriver (драйвер подбирается Selenium Manager)"""
        logger.info("  🌐 Попытка запуска Google Chrome...")
        options = self._apply_common_options(Options())
        driver = webdriver.Chrome(options=options)
        logger.info("  ✓ Запущен браузер: Google Chrome")
        return driver

    def _create_edge_driver(self) -> webdriver.Edge:
        """Создать Microsoft Edge WebDriver (драйвер подбирается Selenium Manager)"""
        logger.info("  🌐 Попытка запуска Microsoft Edge...")
        options = self._apply_common_options(EdgeOptions())
        driver = webdriver.Edge(options=options)
        logger.info("  ✓ Запущен браузер: Microsoft Edge")
        return driver

    def _create_driver(self) -> webdriver.Remote:
        """
        Создать WebDriver: сначала Chrome, при недоступности — Microsoft Edge.
        Драйверы подбираются автоматически через Selenium Manager.
        """
        start_time = time.time()

        try:
            driver = self._create_chrome_driver()
            logger.info(f"  ✓ WebDriver создан за {time.time() - start_time:.2f} сек")
            return driver
        except WebDriverException as e:
            logger.warning(f"  ⚠ Chrome недоступен: {str(e)[:200]}")
            logger.info("  🔁 Переключение на Microsoft Edge...")

        try:
            driver = self._create_edge_driver()
            logger.info(f"  ✓ WebDriver создан за {time.time() - start_time:.2f} сек")
            return driver
        except WebDriverException as e:
            logger.error(f"  ✗ Edge недоступен: {str(e)[:200]}")
            logger.error(f"  ✗ {BROWSER_NOT_FOUND_MESSAGE}")
            raise BrowserNotAvailableError(BROWSER_NOT_FOUND_MESSAGE)

    @staticmethod
    def _get_status_code(driver: webdriver.Remote) -> Optional[int]:
        """Получить HTTP-статус первой загрузки страницы (Chrome 109+)"""
        try:
            status = driver.execute_script(
                "return (performance.getEntriesByType('navigation')[0] || {}).responseStatus"
            )
            return int(status) if status else None
        except Exception:
            return None

    @staticmethod
    def _extract_page_text(driver: webdriver.Remote) -> str:
        """Извлечь видимый текст страницы (без скриптов и стилей)"""
        try:
            text = driver.execute_script(
                "return document.body ? (document.body.innerText || '') : '';"
            ) or ""
        except Exception:
            try:
                text = driver.find_element(By.TAG_NAME, 'body').text or ""
            except Exception:
                text = ""

        # Нормализуем пробелы и ограничиваем длину
        normalized = " ".join(text.split())
        max_chars = settings.parser_page_text_max_chars
        if len(normalized) > max_chars:
            normalized = normalized[:max_chars]
        return normalized

    @staticmethod
    def _detect_block_page(title: str, page_text: str, status_code: Optional[int],
                           current_url: str) -> Optional[str]:
        """
        Обнаружить страницу-блокировку (CAPTCHA, антибот-защита, запрет доступа).
        Обход не выполняется — возвращаем понятную ошибку.
        """
        if status_code in (401, 403, 407, 429, 451, 503):
            return (
                f"Сайт отклонил запрос (HTTP {status_code}). "
                "Возможна CAPTCHA или антибот-защита — обход не выполняется. "
                "Попробуйте позже или укажите другой URL."
            )

        haystack = f"{title} {page_text[:1000]} {current_url}".lower()
        for marker in BLOCK_PAGE_MARKERS:
            if marker in haystack:
                return (
                    f"Обнаружена страница-блокировка (маркер: «{marker}») — "
                    "возможно CAPTCHA или антибот-защита. Обход не выполняется, "
                    "проанализируйте сайт вручную или укажите другой URL."
                )
        return None

    def _parse_sync(self, url: str) -> ParseResult:
        """
        Синхронный парсинг URL (выполняется в отдельном потоке)
        """
        logger.info("=" * 50)
        logger.info(f"🔍 ПАРСИНГ САЙТА: {url}")

        result = ParseResult(url=url)
        driver = None
        total_start = time.time()

        try:
            driver = self._create_driver()
            driver.set_page_load_timeout(self.timeout)

            # Переходим на страницу
            logger.info(f"  📄 Загрузка страницы...")
            page_start = time.time()
            driver.get(url)
            page_elapsed = time.time() - page_start
            logger.info(f"  ✓ Страница загружена за {page_elapsed:.2f} сек")

            # Ждём загрузки body
            logger.info("  ⏳ Ожидание body элемента...")
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info("  ✓ Body элемент найден")

            # Даём странице время на загрузку динамического контента
            logger.info("  ⏳ Ожидание динамического контента (2 сек)...")
            time.sleep(2)

            # HTTP-статус загрузки
            result.status_code = self._get_status_code(driver)
            if result.status_code:
                logger.info(f"  📊 HTTP статус: {result.status_code}")

            # Извлекаем title
            result.title = driver.title
            logger.info(f"  📌 Title: {result.title[:60] if result.title else 'N/A'}...")

            # Извлекаем h1
            try:
                h1_element = driver.find_element(By.TAG_NAME, 'h1')
                result.h1 = h1_element.text.strip() if h1_element.text else None
                logger.info(f"  📌 H1: {result.h1[:60] if result.h1 else 'N/A'}...")
            except Exception as e:
                logger.debug(f"  H1 не найден: {e}")

            # Извлекаем meta description
            try:
                meta = driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
                content = meta.get_attribute('content') or ""
                result.meta_description = content.strip()[:500] or None
                logger.info(f"  📌 Meta description: {result.meta_description[:60] if result.meta_description else 'N/A'}...")
            except Exception as e:
                logger.debug(f"  Meta description не найдена: {e}")

            # Извлекаем первый абзац
            try:
                paragraphs = driver.find_elements(By.TAG_NAME, 'p')
                logger.debug(f"  Найдено абзацев: {len(paragraphs)}")
                for i, p in enumerate(paragraphs):
                    text = p.text.strip() if p.text else ""
                    if len(text) > 50:
                        result.first_paragraph = text[:500]
                        logger.info(f"  📌 Первый абзац (p[{i}]): {result.first_paragraph[:60]}...")
                        break
            except Exception as e:
                logger.debug(f"  Абзацы не найдены: {e}")

            # Извлекаем видимый текст страницы
            result.page_text = self._extract_page_text(driver)
            logger.info(f"  📌 Текст страницы: {len(result.page_text)} символов")

            # Проверка на страницу-блокировку (CAPTCHA / антибот)
            current_url = driver.current_url or url
            block_error = self._detect_block_page(
                result.title or "", result.page_text or "", result.status_code, current_url
            )
            if block_error:
                logger.warning(f"  ⛔ Страница-блокировка обнаружена")
                result.error = block_error
                # Скриншот всё равно полезен для визуальной диагностики
                try:
                    result.screenshot_bytes = driver.get_screenshot_as_png()
                except Exception:
                    pass
                return result

            # Проверка: страница вернула хоть какой-то контент
            if not (result.title or result.page_text):
                logger.warning("  ⛔ Страница пуста")
                result.error = "Страница не содержит контента (возможно, требуется JavaScript или доступ ограничен)"
                return result

            # Делаем скриншот
            logger.info("  📸 Создание скриншота...")
            screenshot_start = time.time()
            result.screenshot_bytes = driver.get_screenshot_as_png()
            screenshot_elapsed = time.time() - screenshot_start
            screenshot_size_kb = len(result.screenshot_bytes) / 1024
            logger.info(f"  ✓ Скриншот создан за {screenshot_elapsed:.2f} сек ({screenshot_size_kb:.1f} KB)")

            total_elapsed = time.time() - total_start
            logger.info(f"  ✅ ПАРСИНГ ЗАВЕРШЁН за {total_elapsed:.2f} сек")
            logger.info("=" * 50)

            return result

        except BrowserNotAvailableError:
            total_elapsed = time.time() - total_start
            logger.error(f"  ✗ Ни один браузер недоступен за {total_elapsed:.2f} сек")
            logger.error("=" * 50)
            result.error = BROWSER_NOT_FOUND_MESSAGE
            return result

        except TimeoutException:
            total_elapsed = time.time() - total_start
            logger.error(f"  ✗ TIMEOUT за {total_elapsed:.2f} сек")
            logger.error("=" * 50)
            result.error = "Превышено время ожидания загрузки страницы"
            return result

        except WebDriverException as e:
            total_elapsed = time.time() - total_start
            error_msg = str(e)
            logger.error(f"  ✗ WebDriver ошибка за {total_elapsed:.2f} сек")
            logger.error(f"  Детали: {error_msg[:200]}")
            logger.error("=" * 50)

            if 'net::ERR_NAME_NOT_RESOLVED' in error_msg:
                result.error = "Не удалось найти сайт по указанному адресу"
            elif 'net::ERR_CONNECTION_REFUSED' in error_msg:
                result.error = "Соединение отклонено сервером"
            elif 'net::ERR_CONNECTION_TIMED_OUT' in error_msg:
                result.error = "Превышено время ожидания соединения"
            elif 'net::ERR_CERT' in error_msg:
                result.error = "Ошибка SSL-сертификата сайта"
            else:
                result.error = f"Ошибка браузера: {error_msg[:200]}"
            return result

        except Exception as e:
            total_elapsed = time.time() - total_start
            logger.error(f"  ✗ Неизвестная ошибка за {total_elapsed:.2f} сек: {e}")
            logger.error("=" * 50)
            result.error = f"Ошибка при загрузке страницы: {str(e)[:200]}"
            return result

        finally:
            if driver:
                try:
                    logger.debug("  Закрытие драйвера...")
                    driver.quit()
                    logger.debug("  ✓ Драйвер закрыт")
                except Exception as e:
                    logger.warning(f"  Ошибка при закрытии драйвера: {e}")

    async def parse_url(self, url: str) -> ParseResult:
        """
        Асинхронный парсинг URL через Chrome
        """
        # Добавляем протокол если его нет
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            logger.info(f"  URL дополнен протоколом -> {url}")

        logger.info(f"🚀 Запуск асинхронного парсинга: {url}")

        # Запускаем синхронный парсинг в отдельном потоке
        loop = asyncio.get_event_loop()
        result: ParseResult = await loop.run_in_executor(
            self._executor,
            self._parse_sync,
            url
        )

        return result

    def screenshot_to_base64(self, screenshot_bytes: bytes) -> str:
        """Конвертировать скриншот в base64"""
        base64_str = base64.b64encode(screenshot_bytes).decode('utf-8')
        logger.debug(f"Скриншот конвертирован в base64: {len(base64_str)} символов")
        return base64_str

    async def close(self):
        """Закрыть executor"""
        logger.info("Закрытие Parser сервиса...")
        self._executor.shutdown(wait=False)
        logger.info("Parser сервис закрыт ✓")


# Глобальный экземпляр
logger.info("Создание глобального экземпляра Parser сервиса...")
parser_service = ParserService()
