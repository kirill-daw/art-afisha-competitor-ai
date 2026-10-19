"""
Главный модуль FastAPI приложения
Мониторинг конкурентов - MVP ассистент
"""
import base64
import time
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from backend.config import settings
from backend.models.schemas import (
    TextAnalysisRequest,
    TextAnalysisResponse,
    ImageAnalysisResponse,
    ParseDemoRequest,
    ParseDemoResponse,
    ParsedContent,
    HistoryResponse,
    CompetitorInfo,
    CompetitorsResponse
)
from backend.services.openai_service import openai_service
from backend.services.parser_service import parser_service
from backend.services.history_service import history_service

# Логгер для API
logger = logging.getLogger("competitor_monitor.api")

# Инициализация приложения
logger.info("=" * 60)
logger.info("🚀 ЗАПУСК ПРИЛОЖЕНИЯ: Мониторинг конкурентов")
logger.info("=" * 60)

app = FastAPI(
    title="Мониторинг конкурентов",
    description="MVP ассистент для анализа конкурентов с поддержкой текста и изображений",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS для работы с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("CORS middleware добавлен ✓")


# === Middleware для логирования запросов ===

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логирование всех HTTP запросов"""
    start_time = time.time()

    # Логируем входящий запрос
    logger.info(f"➡️  {request.method} {request.url.path}")
    if request.query_params:
        logger.debug(f"    Query params: {dict(request.query_params)}")

    # Выполняем запрос
    response = await call_next(request)

    # Логируем ответ
    elapsed = time.time() - start_time
    status_emoji = "✅" if response.status_code < 400 else "❌"
    logger.info(f"{status_emoji} {request.method} {request.url.path} -> {response.status_code} ({elapsed:.3f}s)")

    return response


# === События жизненного цикла ===

@app.on_event("startup")
async def startup_event():
    """Событие при запуске сервера"""
    logger.info("=" * 60)
    logger.info("🟢 СЕРВЕР ЗАПУЩЕН")
    logger.info(f"  Адрес: http://{settings.api_host}:{settings.api_port}")
    logger.info(f"  Документация: http://localhost:{settings.api_port}/docs")
    logger.info(f"  Модель текста: {settings.openai_model}")
    logger.info(f"  Модель vision: {settings.openai_vision_model}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Закрытие ресурсов при остановке сервера"""
    logger.info("=" * 60)
    logger.info("🔴 ОСТАНОВКА СЕРВЕРА")
    logger.info("  Закрытие Parser сервиса...")
    await parser_service.close()
    logger.info("  ✓ Все ресурсы освобождены")
    logger.info("=" * 60)


# === Эндпоинты ===

@app.get("/")
async def root():
    """Главная страница - отдаём фронтенд"""
    logger.debug("Запрос главной страницы")
    return FileResponse("frontend/index.html")


@app.post("/analyze_text", response_model=TextAnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    """
    Анализ текста конкурента
    """
    logger.info("=" * 50)
    logger.info("📝 API: АНАЛИЗ ТЕКСТА")
    logger.info(f"  Длина текста: {len(request.text)} символов")
    logger.info(f"  Превью: {request.text[:80]}...")

    try:
        start_time = time.time()

        analysis = await openai_service.analyze_text(request.text)

        elapsed = time.time() - start_time
        logger.info(f"  ✓ Анализ завершён за {elapsed:.2f} сек")

        # Сохраняем в историю
        logger.info("  💾 Сохранение в историю...")
        history_service.add_entry(
            request_type="text",
            request_summary=request.text[:100] + "..." if len(request.text) > 100 else request.text,
            response_summary=analysis.summary
        )

        logger.info("  ✅ УСПЕХ: Анализ текста завершён")
        logger.info("=" * 50)

        return TextAnalysisResponse(
            success=True,
            analysis=analysis
        )
    except Exception as e:
        logger.error(f"  ❌ ОШИБКА: {e}")
        logger.error("=" * 50)
        return TextAnalysisResponse(
            success=False,
            error=str(e)
        )


@app.post("/analyze_image", response_model=ImageAnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    """
    Анализ изображения конкурента
    """
    logger.info("=" * 50)
    logger.info("🖼️ API: АНАЛИЗ ИЗОБРАЖЕНИЯ")
    logger.info(f"  Имя файла: {file.filename}")
    logger.info(f"  Тип: {file.content_type}")

    # Проверяем тип файла
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        logger.warning(f"  ⚠ Неподдерживаемый тип файла: {file.content_type}")
        logger.info("=" * 50)
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый тип файла. Разрешены: {', '.join(allowed_types)}"
        )

    try:
        start_time = time.time()

        # Читаем и кодируем изображение
        logger.info("  📥 Чтение файла...")
        content = await file.read()
        file_size_kb = len(content) / 1024
        logger.info(f"  Размер файла: {file_size_kb:.1f} KB")

        image_base64 = base64.b64encode(content).decode('utf-8')
        logger.info(f"  Base64 размер: {len(image_base64)} символов")

        # Анализируем
        logger.info("  🔍 Отправка на анализ...")
        analysis = await openai_service.analyze_image(
            image_base64=image_base64,
            mime_type=file.content_type
        )

        elapsed = time.time() - start_time
        logger.info(f"  ✓ Анализ завершён за {elapsed:.2f} сек")

        # Сохраняем в историю
        logger.info("  💾 Сохранение в историю...")
        history_service.add_entry(
            request_type="image",
            request_summary=f"Изображение: {file.filename}",
            response_summary=analysis.description[:200] if analysis.description else "Анализ изображения"
        )

        logger.info("  ✅ УСПЕХ: Анализ изображения завершён")
        logger.info("=" * 50)

        return ImageAnalysisResponse(
            success=True,
            analysis=analysis
        )
    except Exception as e:
        logger.error(f"  ❌ ОШИБКА: {e}")
        logger.error("=" * 50)
        return ImageAnalysisResponse(
            success=False,
            error=str(e)
        )


@app.get("/competitors", response_model=CompetitorsResponse)
async def get_competitors():
    """
    Список конкурентов для автоматического сбора данных
    """
    logger.debug("📋 API: Список конкурентов")
    return CompetitorsResponse(
        competitors=[
            CompetitorInfo(
                key=key,
                name=settings.competitor_names.get(key, key),
                url=url
            )
            for key, url in settings.competitor_urls.items()
        ]
    )


@app.post("/parse_demo", response_model=ParseDemoResponse)
async def parse_demo(request: ParseDemoRequest):
    """
    Парсинг и анализ сайта конкурента через Chrome (Selenium).
    Принимает либо прямой URL, либо ключ/название конкурента из списка.
    """
    logger.info("=" * 50)
    logger.info("🌐 API: ПАРСИНГ САЙТА")

    # Определяем URL: конкурент из списка или прямой URL
    url = None
    if request.competitor:
        url = settings.find_competitor(request.competitor)
        logger.info(f"  🏷 Конкурент: {request.competitor}")
        if not url:
            available = ", ".join(settings.competitor_urls.keys())
            logger.warning(f"  ⚠ Конкурент не найден: {request.competitor}")
            logger.info("=" * 50)
            return ParseDemoResponse(
                success=False,
                error=f"Конкурент «{request.competitor}» не найден. Доступные ключи: {available}"
            )
    elif request.url and request.url.strip():
        url = request.url.strip()

    if not url:
        available = ", ".join(settings.competitor_urls.keys())
        logger.warning("  ⚠ URL не указан")
        logger.info("=" * 50)
        return ParseDemoResponse(
            success=False,
            error=f"Укажите URL или конкурента. Доступные ключи: {available}"
        )

    logger.info(f"  URL: {url}")

    try:
        total_start = time.time()

        # Открываем страницу в Chrome и собираем данные + скриншот
        logger.info("  🔍 Запуск парсинга...")
        parse_start = time.time()
        parse_result = await parser_service.parse_url(url)
        parse_elapsed = time.time() - parse_start
        logger.info(f"  ✓ Парсинг завершён за {parse_elapsed:.2f} сек")

        if parse_result.error:
            logger.error(f"  ❌ Ошибка парсинга: {parse_result.error}")
            logger.info("=" * 50)
            return ParseDemoResponse(
                success=False,
                error=parse_result.error
            )

        title = parse_result.title
        h1 = parse_result.h1
        first_paragraph = parse_result.first_paragraph
        meta_description = parse_result.meta_description
        page_text = parse_result.page_text
        screenshot_bytes = parse_result.screenshot_bytes

        logger.info(f"  📌 Title: {title[:50] if title else 'N/A'}...")
        logger.info(f"  📌 H1: {h1[:50] if h1 else 'N/A'}...")
        logger.info(f"  📌 Meta: {meta_description[:50] if meta_description else 'N/A'}...")
        logger.info(f"  📌 Текст страницы: {len(page_text) if page_text else 0} символов")
        logger.info(f"  📌 Screenshot: {len(screenshot_bytes) / 1024:.1f} KB" if screenshot_bytes else "  📌 Screenshot: N/A")

        # Конвертируем скриншот в base64
        screenshot_base64 = parser_service.screenshot_to_base64(screenshot_bytes) if screenshot_bytes else None

        # Анализируем сайт через AI (скриншот + собранный контент)
        logger.info("  🤖 Запуск AI анализа...")
        ai_start = time.time()

        if screenshot_base64:
            analysis = await openai_service.analyze_website_screenshot(
                screenshot_base64=screenshot_base64,
                url=url,
                title=title,
                h1=h1,
                first_paragraph=first_paragraph,
                meta_description=meta_description,
                page_text=page_text
            )
        else:
            logger.warning("  ⚠ Скриншот недоступен, fallback на текстовый анализ")
            analysis = await openai_service.analyze_parsed_content(
                title=title,
                h1=h1,
                paragraph=first_paragraph,
                meta_description=meta_description,
                page_text=page_text,
                url=url
            )

        ai_elapsed = time.time() - ai_start
        logger.info(f"  ✓ AI анализ завершён за {ai_elapsed:.2f} сек")

        parsed_content = ParsedContent(
            url=url,
            title=title,
            h1=h1,
            first_paragraph=first_paragraph,
            meta_description=meta_description,
            page_text=page_text,
            analysis=analysis
        )

        # Сохраняем в историю через существующий механизм
        logger.info("  💾 Сохранение в историю...")
        history_service.add_entry(
            request_type="parse",
            request_summary=f"URL: {url}",
            response_summary=analysis.summary[:100] if analysis.summary else f"Title: {title or 'N/A'}"
        )

        total_elapsed = time.time() - total_start
        logger.info(f"  ✅ УСПЕХ: Парсинг и анализ завершён за {total_elapsed:.2f} сек")
        logger.info(f"    - Парсинг: {parse_elapsed:.2f} сек")
        logger.info(f"    - AI анализ: {ai_elapsed:.2f} сек")
        logger.info("=" * 50)

        return ParseDemoResponse(
            success=True,
            data=parsed_content
        )
    except Exception as e:
        logger.error(f"  ❌ ОШИБКА: {e}")
        logger.error("=" * 50)
        return ParseDemoResponse(
            success=False,
            error=str(e)
        )


@app.get("/history", response_model=HistoryResponse)
async def get_history():
    """
    Получить историю последних 10 запросов
    """
    logger.info("📋 API: Получение истории")
    items = history_service.get_history()
    logger.info(f"  Записей: {len(items)}")
    return HistoryResponse(
        items=items,
        total=len(items)
    )


@app.delete("/history")
async def clear_history():
    """
    Очистить историю запросов
    """
    logger.info("🗑️ API: Очистка истории")
    history_service.clear_history()
    logger.info("  ✓ История очищена")
    return {"success": True, "message": "История очищена"}


@app.get("/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    logger.debug("❤️ Health check")
    return {
        "status": "healthy",
        "service": "Competitor Monitor",
        "version": "1.0.0"
    }


# Статические файлы для фронтенда
app.mount("/static", StaticFiles(directory="frontend"), name="static")
logger.info("Статические файлы подключены: /static -> frontend/")


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
