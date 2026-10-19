"""
Pydantic схемы для API
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# === Запросы ===

class TextAnalysisRequest(BaseModel):
    """Запрос на анализ текста"""
    text: str = Field(..., min_length=10, description="Текст для анализа")


class ParseDemoRequest(BaseModel):
    """Запрос на парсинг страницы конкурента"""
    url: Optional[str] = Field(None, description="URL страницы для парсинга")
    competitor: Optional[str] = Field(
        None,
        description="Ключ или название конкурента из списка (yandex_afisha, afisha_ru, kudago, timepad, kassir)"
    )


class CompetitorInfo(BaseModel):
    """Конкурент из настроенного списка"""
    key: str
    name: str
    url: str


class CompetitorsResponse(BaseModel):
    """Список конкурентов для автоматического сбора данных"""
    competitors: List[CompetitorInfo]


# === Ответы ===

class CompetitorAnalysis(BaseModel):
    """Структурированный анализ конкурента сервиса «Арт-Афиша»"""
    strengths: List[str] = Field(default_factory=list, description="Сильные стороны (3-5)")
    weaknesses: List[str] = Field(default_factory=list, description="Слабые стороны (3-5)")
    unique_features: List[str] = Field(default_factory=list, description="Уникальные функции или предложения")
    event_discovery_score: Optional[int] = Field(None, ge=0, le=10, description="Удобство поиска и обнаружения событий (0-10)")
    personalization_score: Optional[int] = Field(None, ge=0, le=10, description="Персонализация и рекомендации (0-10)")
    regional_coverage_score: Optional[int] = Field(None, ge=0, le=10, description="Охват городов и регионов (0-10)")
    ticketing_score: Optional[int] = Field(None, ge=0, le=10, description="Возможности покупки/бронирования билетов (0-10)")
    organizer_tools_score: Optional[int] = Field(None, ge=0, le=10, description="Возможности для организаторов (0-10)")
    content_quality_score: Optional[int] = Field(None, ge=0, le=10, description="Качество описаний, подборок и редконтента (0-10)")
    opportunities_for_art_afisha: List[str] = Field(default_factory=list, description="Возможности для развития «Арт-Афиши» (3-5)")
    summary: str = Field("", description="Краткое итоговое резюме")


class ImageAnalysis(BaseModel):
    """Анализ изображения интерфейса конкурента"""
    description: str = Field("", description="Описание изображения")
    visual_style_score: Optional[int] = Field(None, ge=0, le=10, description="Оценка визуального стиля (0-10)")
    navigation_clarity_score: Optional[int] = Field(None, ge=0, le=10, description="Ясность навигации (0-10)")
    event_card_quality_score: Optional[int] = Field(None, ge=0, le=10, description="Качество карточек событий (0-10)")
    cta_visibility_score: Optional[int] = Field(None, ge=0, le=10, description="Видимость призывов к действию (0-10)")
    mobile_readability_score: Optional[int] = Field(None, ge=0, le=10, description="Читаемость на мобильных устройствах (0-10)")
    information_density: str = Field("", description="Краткая оценка плотности информации")
    visual_strengths: List[str] = Field(default_factory=list, description="Сильные стороны интерфейса (3-5)")
    visual_weaknesses: List[str] = Field(default_factory=list, description="Слабые стороны интерфейса (3-5)")
    recommendations: List[str] = Field(default_factory=list, description="Рекомендации для «Арт-Афиши» (3-5)")


class ParsedContent(BaseModel):
    """Результат парсинга страницы"""
    url: str
    title: Optional[str] = None
    h1: Optional[str] = None
    first_paragraph: Optional[str] = None
    meta_description: Optional[str] = None
    page_text: Optional[str] = None
    analysis: Optional[CompetitorAnalysis] = None
    error: Optional[str] = None


class TextAnalysisResponse(BaseModel):
    """Ответ на анализ текста"""
    success: bool
    analysis: Optional[CompetitorAnalysis] = None
    error: Optional[str] = None


class ImageAnalysisResponse(BaseModel):
    """Ответ на анализ изображения"""
    success: bool
    analysis: Optional[ImageAnalysis] = None
    error: Optional[str] = None


class ParseDemoResponse(BaseModel):
    """Ответ на парсинг"""
    success: bool
    data: Optional[ParsedContent] = None
    error: Optional[str] = None


# === История ===

class HistoryItem(BaseModel):
    """Элемент истории"""
    id: str
    timestamp: datetime
    request_type: str  # "text", "image", "parse"
    request_summary: str
    response_summary: str


class HistoryResponse(BaseModel):
    """Ответ со списком истории"""
    items: List[HistoryItem]
    total: int

