# 📚 Документация API — AI-анализатор конкурентов «Арт-Афиши»

## Содержание

1. [Структура проекта](#структура-проекта)
2. [Описание API](#описание-api)
3. [Примеры запросов](#примеры-запросов)
4. [Мультимодальные функции](#мультимодальные-функции)
5. [Модели данных](#модели-данных)
6. [Конфигурация](#конфигурация)

---

## Структура проекта

```
art_afisha_competitor_ai_app/
│
├── backend/
│   ├── main.py                  # Главный файл FastAPI и endpoints
│   ├── config.py                # Конфигурация приложения и список конкурентов
│   ├── models/
│   │   └── schemas.py           # Pydantic-модели
│   └── services/
│       ├── openai_service.py    # Интеграция с OpenAI (текст + vision)
│       ├── parser_service.py    # Автоматический сбор данных через Selenium
│       └── history_service.py   # Управление историей
│
├── frontend/                    # Веб-интерфейс
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── desktop/                     # Desktop-приложение (PyQt6)
│   ├── main.py
│   ├── api_client.py
│   ├── styles.py
│   └── build.py
│
├── data/                        # Локальные материалы
├── run.py                       # Запуск backend
├── requirements.txt             # Python зависимости
├── env.example.txt              # Шаблон переменных окружения
├── history.json                 # Файл истории запросов
├── README.md                    # Описание проекта
└── docs.md                      # Эта документация
```

---

## Описание API

### Базовый URL

```
http://localhost:8000
```

### Эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Главная страница (веб-интерфейс) |
| POST | `/analyze_text` | Анализ текста конкурента |
| POST | `/analyze_image` | Анализ изображения конкурента |
| GET | `/competitors` | Список настроенных конкурентов |
| POST | `/parse_demo` | Автоматический сбор и AI-анализ сайта (URL или конкурент) |
| GET | `/history` | Получение истории запросов |
| DELETE | `/history` | Очистка истории запросов |
| GET | `/health` | Проверка работоспособности |
| GET | `/docs` | Swagger UI документация |
| GET | `/redoc` | ReDoc документация |

---

## Примеры запросов

### 1. Анализ текста (`POST /analyze_text`)

**Запрос:**
```bash
curl -X POST "http://localhost:8000/analyze_text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Сервис поиска мероприятий: десятки городов, подборки событий, покупка электронных билетов, панель для организаторов с аналитикой продаж."
  }'
```

**Ответ:**
```json
{
  "success": true,
  "analysis": {
    "strengths": [
      "Широкий охват городов",
      "Подборки и редакционный контент",
      "Инструменты для организаторов"
    ],
    "weaknesses": [
      "Мало данных о персонализации",
      "Неконкретные формулировки"
    ],
    "unique_features": [
      "Панель организатора с аналитикой продаж"
    ],
    "event_discovery_score": 8,
    "personalization_score": null,
    "regional_coverage_score": 9,
    "ticketing_score": 7,
    "organizer_tools_score": 8,
    "content_quality_score": 7,
    "opportunities_for_art_afisha": [
      "Усилить персонализацию подборок",
      "Развить редакционный редконтент о событиях"
    ],
    "summary": "Сервис силён в охвате и инструментах для организаторов, но уступает в персонализации."
  },
  "error": null
}
```

> Значения оценок могут быть `null` — в интерфейсе они отображаются как «н/д».

### 2. Анализ изображения (`POST /analyze_image`)

**Запрос:**
```bash
curl -X POST "http://localhost:8000/analyze_image" \
  -F "file=@main_page.jpg"
```

**Ответ:**
```json
{
  "success": true,
  "analysis": {
    "description": "Скриншот главной страницы сервиса с крупной афишей, поиском по городу и карточками событий.",
    "visual_style_score": 8,
    "navigation_clarity_score": 7,
    "event_card_quality_score": 8,
    "cta_visibility_score": 9,
    "mobile_readability_score": null,
    "information_density": "Средняя: акцент на афише, навигация не перегружена.",
    "visual_strengths": [
      "Крупные карточки событий",
      "Понятный поиск по городу",
      "Заметная кнопка покупки билета"
    ],
    "visual_weaknesses": [
      "Много элементов в шапке",
      "Мало воздуха между блоками"
    ],
    "recommendations": [
      "Сделать подборки ближе к началу страницы",
      "Упростить верхнюю навигацию"
    ]
  },
  "error": null
}
```

### 3. Список конкурентов (`GET /competitors`)

```bash
curl -X GET "http://localhost:8000/competitors"
```

```json
{
  "competitors": [
    { "key": "yandex_afisha", "name": "Яндекс Афиша", "url": "https://afisha.yandex.ru" },
    { "key": "afisha_ru", "name": "Afisha.ru", "url": "https://www.afisha.ru" },
    { "key": "kudago", "name": "KudaGo", "url": "https://kudago.com" },
    { "key": "timepad", "name": "Timepad", "url": "https://timepad.ru" },
    { "key": "kassir", "name": "Kassir.ru", "url": "https://www.kassir.ru" }
  ]
}
```

### 4. Сбор и анализ сайта (`POST /parse_demo`)

Принимает либо `url`, либо `competitor` (ключ/название из списка).

**По ключу конкурента:**
```bash
curl -X POST "http://localhost:8000/parse_demo" \
  -H "Content-Type: application/json" \
  -d '{ "competitor": "kudago" }'
```

**По прямому URL:**
```bash
curl -X POST "http://localhost:8000/parse_demo" \
  -H "Content-Type: application/json" \
  -d '{ "url": "https://example.com" }'
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "url": "https://kudago.com",
    "title": "KudaGo — события в городах",
    "h1": "Куда пойти",
    "first_paragraph": "Афиша лучших событий: концерты, театры, выставки...",
    "meta_description": "Афиша событий города",
    "page_text": "...",
    "analysis": {
      "strengths": ["..."],
      "weaknesses": ["..."],
      "unique_features": ["..."],
      "event_discovery_score": 8,
      "personalization_score": null,
      "regional_coverage_score": 7,
      "ticketing_score": 6,
      "organizer_tools_score": null,
      "content_quality_score": 8,
      "opportunities_for_art_afisha": ["..."],
      "summary": "..."
    },
    "error": null
  },
  "error": null
}
```

> ⚠️ Приложение **не обходит CAPTCHA и антибот-защиту**. Если сайт блокирует автоматический доступ, вернётся ошибка/сообщение о блокировке. Доступность сайта для автоматического сбора не гарантируется.

### 5. История (`GET /history`, `DELETE /history`)

```bash
curl -X GET "http://localhost:8000/history"
```

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2026-01-15T10:30:00",
      "request_type": "parse",
      "request_summary": "URL: https://kudago.com",
      "response_summary": "Афиша KudaGo сильна в подборках событий..."
    }
  ],
  "total": 1
}
```

```bash
curl -X DELETE "http://localhost:8000/history"
```

### 6. Проверка здоровья (`GET /health`)

```json
{
  "status": "healthy",
  "service": "Competitor Monitor",
  "version": "1.0.0"
}
```

---

## Мультимодальные функции

### Поддержка текста

Анализируется любой текстовый контент конкурентов:

- описания сервисов и продуктов;
- тексты с лендингов;
- рекламные объявления;
- описания тарифов для организаторов;
- подборки и редакционный контент.

**Минимальная длина текста:** 10 символов.

### Поддержка изображений

Поддерживаемые форматы: JPEG/JPG, PNG, GIF, WebP.

Что можно анализировать: скриншоты сайта/приложения, баннеры, карточки событий, оформление главной страницы.

**Максимальный размер:** 10 MB (рекомендуется до 4 MB для быстрой обработки).

### Автоматический сбор данных сайта

Сбор выполняется в headless-браузере через Selenium (Selenium Manager подбирает WebDriver). Поддерживается fallback **Google Chrome → Microsoft Edge**; при отсутствии обоих браузеров возвращается понятная ошибка.

Извлекаются:

- `<title>`;
- `<h1>`;
- первый значимый абзац;
- `meta description`;
- основной текст страницы;
- скриншот страницы.

Собранные данные (скриншот + текст) передаются в AI-анализ. Если скриншот недоступен, используется текстовый анализ собранного контента.

---

## Модели данных

### TextAnalysisRequest

```typescript
{
  text: string  // Минимум 10 символов
}
```

### ParseDemoRequest

```typescript
{
  url?: string         // URL страницы (если не передан competitor)
  competitor?: string  // Ключ/название конкурента из списка
}
```

### CompetitorInfo

```typescript
{
  key: string
  name: string
  url: string
}
```

### CompetitorsResponse

```typescript
{
  competitors: CompetitorInfo[]
}
```

### CompetitorAnalysis

```typescript
{
  strengths: string[]
  weaknesses: string[]
  unique_features: string[]
  event_discovery_score: number | null
  personalization_score: number | null
  regional_coverage_score: number | null
  ticketing_score: number | null
  organizer_tools_score: number | null
  content_quality_score: number | null
  opportunities_for_art_afisha: string[]
  summary: string
}
```

Оценки — целые числа от 0 до 10 либо `null` (недостаточно данных).

### ImageAnalysis

```typescript
{
  description: string
  visual_style_score: number | null
  navigation_clarity_score: number | null
  event_card_quality_score: number | null
  cta_visibility_score: number | null
  mobile_readability_score: number | null
  information_density: string
  visual_strengths: string[]
  visual_weaknesses: string[]
  recommendations: string[]
}
```

### ParsedContent

```typescript
{
  url: string
  title: string | null
  h1: string | null
  first_paragraph: string | null
  meta_description: string | null
  page_text: string | null
  analysis: CompetitorAnalysis | null
  error: string | null
}
```

### HistoryItem

```typescript
{
  id: string
  timestamp: datetime
  request_type: string      // "text" | "image" | "parse"
  request_summary: string
  response_summary: string
}
```

---

## Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `OPENAI_API_KEY` | API-ключ официального OpenAI API | — |
| `OPENAI_MODEL` | Модель для текстового анализа | `gpt-4o-mini` |
| `OPENAI_VISION_MODEL` | Модель для анализа изображений | `gpt-4o-mini` |

Шаблон переменных окружения — файл `env.example.txt`. Реальные ключи храните только в `.env` (он в `.gitignore`).

### Настройки анализа и истории

- Максимум записей истории: **10**
- Файл хранения истории: `history.json`
- Таймаут сбора данных: 15 секунд
- Ограничение текста страницы: 3000 символов

---

## Коды ошибок

| Код | Описание |
|-----|----------|
| 200 | Успешный запрос |
| 400 | Некорректный запрос (неверный формат, неподдерживаемый тип файла) |
| 422 | Ошибка валидации данных |
| 500 | Внутренняя ошибка сервера |

---

## Безопасность

⚠️ **Важно:**

- не храните API-ключи в коде — используйте `.env`;
- `.env` добавлен в `.gitignore`;
- CAPTCHA и антибот-защита не обходятся;
- в продакшене используйте HTTPS и настройте CORS для конкретных доменов.
