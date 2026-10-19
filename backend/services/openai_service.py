"""
Сервис для работы с официальным OpenAI API
https://platform.openai.com/docs
"""
import base64
import json
import re
import time
import logging
from typing import Optional

from openai import OpenAI

from backend.config import settings
from backend.models.schemas import CompetitorAnalysis, ImageAnalysis

# Логгер для сервиса
logger = logging.getLogger("competitor_monitor.openai")


class OpenAIService:
    """Сервис для анализа через OpenAI API"""
    
    def __init__(self):
        logger.info("=" * 50)
        logger.info("Инициализация OpenAI сервиса")
        logger.info(f"  Модель текста: {settings.openai_model}")
        logger.info(f"  Модель vision: {settings.openai_vision_model}")
        
        # Официальный OpenAI API (стандартный base_url)
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.vision_model = settings.openai_vision_model
        
        logger.info("OpenAI сервис инициализирован успешно ✓")
        logger.info("=" * 50)
    
    def _parse_json_response(self, content: str) -> dict:
        """Извлечь JSON из ответа модели"""
        logger.debug(f"Парсинг JSON ответа, длина: {len(content)} символов")
        
        # Пробуем найти JSON в markdown блоке
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            content = json_match.group(1)
            logger.debug("JSON найден в markdown блоке")
        
        # Пробуем найти JSON объект
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            content = json_match.group(0)
            logger.debug("JSON объект извлечён")
        
        try:
            result = json.loads(content)
            logger.debug(f"JSON успешно распарсен, ключей: {len(result)}")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"Ошибка парсинга JSON: {e}")
            logger.debug(f"Проблемный контент: {content[:200]}...")
            return {}
    
    async def analyze_text(self, text: str) -> CompetitorAnalysis:
        """Анализ текста конкурента"""
        logger.info("=" * 50)
        logger.info("📝 АНАЛИЗ ТЕКСТА КОНКУРЕНТА")
        logger.info(f"  Длина текста: {len(text)} символов")
        logger.info(f"  Превью: {text[:100]}...")
        logger.info(f"  Модель: {self.model}")
        
        system_prompt = """Ты — эксперт по конкурентному анализу в нише поиска культурных событий, мероприятий и билетов. Твоя задача — проанализировать конкурента сервиса «Арт-Афиша» по предоставленному тексту и верни строго валидный JSON-ответ.

Формат ответа (строго JSON):
{
    "strengths": ["сильная сторона 1", "сильная сторона 2", ...],
    "weaknesses": ["слабая сторона 1", "слабая сторона 2", ...],
    "unique_features": ["уникальная функция/предложение 1", "уникальная функция/предложение 2", ...],
    "event_discovery_score": 7,
    "personalization_score": 5,
    "regional_coverage_score": 8,
    "ticketing_score": 6,
    "organizer_tools_score": 4,
    "content_quality_score": 7,
    "opportunities_for_art_afisha": ["возможность 1", "возможность 2", ...],
    "summary": "Краткое итоговое резюме анализа"
}

Описание показателей (все оцениваются по шкале от 0 до 10):
- event_discovery_score — удобство поиска и обнаружения событий (фильтры, подборки, календарь, поиск по дате/жанру/локации)
- personalization_score — персонализация и рекомендации (подборки «для вас», история просмотров, умные подсказки)
- regional_coverage_score — охват городов и регионов
- ticketing_score — возможности покупки или бронирования билетов
- organizer_tools_score — возможности для организаторов событий (публикация, статистика, продажи)
- content_quality_score — качество описаний событий, подборок и редакционного контента

Правила:
1. Анализируй только те данные, которые действительно присутствуют во входном тексте. Не придумывай функции сервиса, которых нельзя подтвердить входными данными.
2. Если какой-то показатель невозможно оценить по входным данным, укажи в JSON null, а не выдумывай оценку.
3. strengths: 3-5 пунктов. weaknesses: 3-5 пунктов. unique_features: столько, сколько подтверждается текстом.
4. opportunities_for_art_afisha: 3-5 возможностей, которые можно использовать при развитии сервиса «Арт-Афиша».
5. Пиши все строковые значения на русском языке.
6. Ответ должен быть строго валидным JSON без пояснений вне его."""

        start_time = time.time()
        logger.info("  Отправка запроса к API...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Проанализируй текст конкурента:\n\n{text}"}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            elapsed = time.time() - start_time
            logger.info(f"  ✓ Ответ получен за {elapsed:.2f} сек")
            
            content = response.choices[0].message.content
            logger.info(f"  Длина ответа: {len(content)} символов")
            logger.debug(f"  Использовано токенов: {response.usage.total_tokens if response.usage else 'N/A'}")
            
            data = self._parse_json_response(content)
            
            result = CompetitorAnalysis(
                strengths=data.get("strengths", []),
                weaknesses=data.get("weaknesses", []),
                unique_features=data.get("unique_features", []),
                event_discovery_score=data.get("event_discovery_score"),
                personalization_score=data.get("personalization_score"),
                regional_coverage_score=data.get("regional_coverage_score"),
                ticketing_score=data.get("ticketing_score"),
                organizer_tools_score=data.get("organizer_tools_score"),
                content_quality_score=data.get("content_quality_score"),
                opportunities_for_art_afisha=data.get("opportunities_for_art_afisha", []),
                summary=data.get("summary", "")
            )
            
            logger.info(f"  Результат: {len(result.strengths)} сильных, {len(result.weaknesses)} слабых сторон")
            logger.info("=" * 50)
            
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"  ✗ Ошибка API за {elapsed:.2f} сек: {e}")
            logger.error("=" * 50)
            raise
    
    async def analyze_image(self, image_base64: str, mime_type: str = "image/jpeg") -> ImageAnalysis:
        """Анализ изображения (баннер, сайт, упаковка)"""
        logger.info("=" * 50)
        logger.info("🖼️ АНАЛИЗ ИЗОБРАЖЕНИЯ")
        logger.info(f"  Размер base64: {len(image_base64)} символов")
        logger.info(f"  MIME тип: {mime_type}")
        logger.info(f"  Модель: {self.vision_model}")
        
        system_prompt = """Ты — эксперт по UX/UI и визуальному дизайну в нише поиска культурных событий, мероприятий и билетов. Проанализируй изображение интерфейса конкурента сервиса «Арт-Афиша» (скриншот сайта или приложения, баннер, карточка события) и верни строго валидный JSON-ответ.

Формат ответа (строго JSON):
{
    "description": "Детальное описание того, что изображено",
    "visual_style_score": 7,
    "navigation_clarity_score": 6,
    "event_card_quality_score": 5,
    "cta_visibility_score": 8,
    "mobile_readability_score": 7,
    "information_density": "Краткая оценка плотности информации на изображении",
    "visual_strengths": ["сильная сторона интерфейса 1", "сильная сторона интерфейса 2", ...],
    "visual_weaknesses": ["слабая сторона интерфейса 1", "слабая сторона интерфейса 2", ...],
    "recommendations": ["рекомендация для «Арт-Афиши» 1", "рекомендация для «Арт-Афиши» 2", ...]
}

Описание показателей (все оцениваются по шкале от 0 до 10):
- visual_style_score — общий визуальный стиль (цветовая палитра, типографика, композиция)
- navigation_clarity_score — ясность и очевидность навигации
- event_card_quality_score — качество отображения карточек событий
- cta_visibility_score — видимость призывов к действию (купить билет, подробнее и т.п.)
- mobile_readability_score — читаемость и удобство восприятия на мобильных устройствах
- information_density — краткая текстовая оценка плотности информации (не число)

Правила:
1. Анализируй только то, что действительно видно на изображении. Не придумывай элементы интерфейса, функции или экраны, которых нет на входном изображении.
2. Если какой-то показатель невозможно оценить по изображению, укажи в JSON null, а не выдумывай оценку.
3. visual_strengths: 3-5 пунктов. visual_weaknesses: 3-5 пунктов. recommendations: 3-5 рекомендаций для развития «Арт-Афиши».
4. Пиши все строковые значения на русском языке.
5. Ответ должен быть строго валидным JSON без пояснений вне его."""

        start_time = time.time()
        logger.info("  Отправка запроса к Vision API...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Проанализируй это изображение конкурента с точки зрения маркетинга и дизайна:"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            elapsed = time.time() - start_time
            logger.info(f"  ✓ Ответ получен за {elapsed:.2f} сек")
            
            content = response.choices[0].message.content
            logger.info(f"  Длина ответа: {len(content)} символов")
            
            data = self._parse_json_response(content)
            
            result = ImageAnalysis(
                description=data.get("description", ""),
                visual_style_score=data.get("visual_style_score"),
                navigation_clarity_score=data.get("navigation_clarity_score"),
                event_card_quality_score=data.get("event_card_quality_score"),
                cta_visibility_score=data.get("cta_visibility_score"),
                mobile_readability_score=data.get("mobile_readability_score"),
                information_density=data.get("information_density", ""),
                visual_strengths=data.get("visual_strengths", []),
                visual_weaknesses=data.get("visual_weaknesses", []),
                recommendations=data.get("recommendations", [])
            )
            
            logger.info(f"  Результат: оценка стиля {result.visual_style_score if result.visual_style_score is not None else 'н/д'}/10")
            logger.info(f"  Сильных сторон: {len(result.visual_strengths)}, слабых: {len(result.visual_weaknesses)}, рекомендаций: {len(result.recommendations)}")
            logger.info("=" * 50)
            
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"  ✗ Ошибка Vision API за {elapsed:.2f} сек: {e}")
            logger.error("=" * 50)
            raise
    
    async def analyze_parsed_content(
        self, 
        title: Optional[str], 
        h1: Optional[str], 
        paragraph: Optional[str],
        meta_description: Optional[str] = None,
        page_text: Optional[str] = None,
        url: Optional[str] = None
    ) -> CompetitorAnalysis:
        """Анализ распарсенного контента сайта"""
        logger.info("📄 Анализ распарсенного контента")
        logger.info(f"  Title: {title[:50] if title else 'N/A'}...")
        logger.info(f"  H1: {h1[:50] if h1 else 'N/A'}...")
        logger.info(f"  Абзац: {paragraph[:50] if paragraph else 'N/A'}...")
        logger.info(f"  Meta description: {meta_description[:50] if meta_description else 'N/A'}...")
        logger.info(f"  Текст страницы: {len(page_text) if page_text else 0} символов")
        
        content_parts = []
        if url:
            content_parts.append(f"URL сайта: {url}")
        if title:
            content_parts.append(f"Заголовок страницы (title): {title}")
        if h1:
            content_parts.append(f"Главный заголовок (H1): {h1}")
        if meta_description:
            content_parts.append(f"Meta description: {meta_description}")
        if paragraph:
            content_parts.append(f"Первый абзац: {paragraph}")
        if page_text:
            content_parts.append(f"Текст на странице: {page_text}")
        
        combined_text = "\n\n".join(content_parts)
        
        if not combined_text.strip():
            logger.warning("  ⚠ Контент пустой, возвращаем пустой анализ")
            return CompetitorAnalysis(
                summary="Не удалось извлечь контент для анализа"
            )
        
        return await self.analyze_text(combined_text)
    
    async def analyze_website_screenshot(
        self,
        screenshot_base64: str,
        url: str,
        title: Optional[str] = None,
        h1: Optional[str] = None,
        first_paragraph: Optional[str] = None,
        meta_description: Optional[str] = None,
        page_text: Optional[str] = None
    ) -> CompetitorAnalysis:
        """Комплексный анализ сайта конкурента по скриншоту"""
        logger.info("=" * 50)
        logger.info("🌐 КОМПЛЕКСНЫЙ АНАЛИЗ САЙТА")
        logger.info(f"  URL: {url}")
        logger.info(f"  Title: {title[:50] if title else 'N/A'}...")
        logger.info(f"  H1: {h1[:50] if h1 else 'N/A'}...")
        logger.info(f"  Meta description: {meta_description[:50] if meta_description else 'N/A'}...")
        logger.info(f"  Текст страницы: {len(page_text) if page_text else 0} символов")
        logger.info(f"  Размер скриншота: {len(screenshot_base64)} символов base64")
        logger.info(f"  Модель: {self.vision_model}")
        
        # Формируем контекст из извлечённых данных
        context_parts = [f"URL сайта: {url}"]
        if title:
            context_parts.append(f"Title страницы: {title}")
        if h1:
            context_parts.append(f"Главный заголовок (H1): {h1}")
        if meta_description:
            context_parts.append(f"Meta description: {meta_description}")
        if first_paragraph:
            context_parts.append(f"Текст на странице: {first_paragraph[:300]}")
        if page_text:
            context_parts.append(f"Содержимое страницы (текст): {page_text}")
        
        context = "\n".join(context_parts)
        logger.debug(f"  Контекст:\n{context}")
        
        system_prompt = """Ты — эксперт по конкурентному анализу и UX/UI в нише поиска культурных событий, мероприятий и билетов. Проанализируй скриншот сайта конкурента сервиса «Арт-Афиша» (переданный как изображение) вместе с контекстом и верни строго валидный JSON-ответ.

Формат ответа (строго JSON):
{
    "strengths": ["сильная сторона 1", "сильная сторона 2", ...],
    "weaknesses": ["слабая сторона 1", "слабая сторона 2", ...],
    "unique_features": ["уникальная функция/предложение 1", "уникальная функция/предложение 2", ...],
    "event_discovery_score": 7,
    "personalization_score": 5,
    "regional_coverage_score": 8,
    "ticketing_score": 6,
    "organizer_tools_score": 4,
    "content_quality_score": 7,
    "opportunities_for_art_afisha": ["возможность 1", "возможность 2", ...],
    "summary": "Комплексное резюме анализа сайта конкурента"
}

Описание показателей (все оцениваются по шкале от 0 до 10):
- event_discovery_score — удобство поиска и обнаружения событий
- personalization_score — персонализация и рекомендации
- regional_coverage_score — охват городов и регионов
- ticketing_score — возможности покупки или бронирования билетов
- organizer_tools_score — возможности для организаторов событий
- content_quality_score — качество описаний, подборок и редакционного контента

При анализе обращай внимание на скриншоте:
- Дизайн и визуальный стиль (цвета, шрифты, композиция)
- UX/UI: навигация, расположение элементов, CTA-кнопки
- Карточки событий: что видно, какая информация представлена
- Поиск и фильтры, если видны на изображении
- Контент: заголовки, тексты, призывы к действию

Правила:
1. Анализируй только те данные, которые действительно присутствуют на скриншоте и в переданном контексте. Не придумывай функции сервиса, которых нельзя подтвердить входными данными.
2. Если какой-то показатель невозможно оценить по входным данным, укажи в JSON null, а не выдумывай оценку.
3. strengths: 3-5 пунктов. weaknesses: 3-5 пунктов. opportunities_for_art_afisha: 3-5 возможностей для развития «Арт-Афиши».
4. Пиши все строковые значения на русском языке.
5. Ответ должен быть строго валидным JSON без пояснений вне его."""

        start_time = time.time()
        logger.info("  Отправка скриншота в Vision API...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Проведи комплексный конкурентный анализ этого сайта:\n\n{context}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{screenshot_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            elapsed = time.time() - start_time
            logger.info(f"  ✓ Ответ получен за {elapsed:.2f} сек")
            
            content = response.choices[0].message.content
            logger.info(f"  Длина ответа: {len(content)} символов")
            
            data = self._parse_json_response(content)
            
            result = CompetitorAnalysis(
                strengths=data.get("strengths", []),
                weaknesses=data.get("weaknesses", []),
                unique_features=data.get("unique_features", []),
                event_discovery_score=data.get("event_discovery_score"),
                personalization_score=data.get("personalization_score"),
                regional_coverage_score=data.get("regional_coverage_score"),
                ticketing_score=data.get("ticketing_score"),
                organizer_tools_score=data.get("organizer_tools_score"),
                content_quality_score=data.get("content_quality_score"),
                opportunities_for_art_afisha=data.get("opportunities_for_art_afisha", []),
                summary=data.get("summary", "")
            )
            
            logger.info(f"  Результат:")
            logger.info(f"    - Сильных сторон: {len(result.strengths)}")
            logger.info(f"    - Слабых сторон: {len(result.weaknesses)}")
            logger.info(f"    - Уникальных функций: {len(result.unique_features)}")
            logger.info(f"    - Возможностей для «Арт-Афиши»: {len(result.opportunities_for_art_afisha)}")
            logger.info(f"  Резюме: {result.summary[:100]}...")
            logger.info("=" * 50)
            
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"  ✗ Ошибка Vision API за {elapsed:.2f} сек: {e}")
            logger.error("=" * 50)
            raise


# Глобальный экземпляр
logger.info("Создание глобального экземпляра OpenAI сервиса...")
openai_service = OpenAIService()
