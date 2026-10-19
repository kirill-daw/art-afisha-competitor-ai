/**
 * Competitor Monitor - Frontend Application
 * Мониторинг конкурентов - MVP ассистент
 */

// === State ===
const state = {
    currentTab: 'text',
    selectedImage: null,
    isLoading: false
};

// === DOM Elements ===
const elements = {
    // Navigation
    navButtons: document.querySelectorAll('.nav-btn'),
    tabContents: document.querySelectorAll('.tab-content'),

    // Text analysis
    competitorText: document.getElementById('competitor-text'),
    analyzeTextBtn: document.getElementById('analyze-text-btn'),

    // Image analysis
    uploadZone: document.getElementById('upload-zone'),
    imageInput: document.getElementById('image-input'),
    previewContainer: document.getElementById('preview-container'),
    imagePreview: document.getElementById('image-preview'),
    removeImageBtn: document.getElementById('remove-image'),
    analyzeImageBtn: document.getElementById('analyze-image-btn'),

    // Parse demo
    urlInput: document.getElementById('url-input'),
    competitorSelect: document.getElementById('competitor-select'),
    parseBtn: document.getElementById('parse-btn'),

    // History
    historyList: document.getElementById('history-list'),
    clearHistoryBtn: document.getElementById('clear-history-btn'),

    // Results
    resultsSection: document.getElementById('results-section'),
    resultsContent: document.getElementById('results-content'),
    closeResultsBtn: document.getElementById('close-results'),

    // Loading
    loadingOverlay: document.getElementById('loading-overlay')
};

// === API Functions ===
const api = {
    baseUrl: '',

    async analyzeText(text) {
        const response = await fetch(`${this.baseUrl}/analyze_text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        return response.json();
    },

    async analyzeImage(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${this.baseUrl}/analyze_image`, {
            method: 'POST',
            body: formData
        });
        return response.json();
    },

    async parseDemo(url, competitor) {
        const payload = competitor ? { competitor } : { url };
        const response = await fetch(`${this.baseUrl}/parse_demo`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return response.json();
    },

    async getCompetitors() {
        const response = await fetch(`${this.baseUrl}/competitors`);
        return response.json();
    },

    async getHistory() {
        const response = await fetch(`${this.baseUrl}/history`);
        return response.json();
    },

    async clearHistory() {
        const response = await fetch(`${this.baseUrl}/history`, {
            method: 'DELETE'
        });
        return response.json();
    }
};

// === UI Functions ===
const ui = {
    showLoading() {
        state.isLoading = true;
        elements.loadingOverlay.style.display = 'flex';
    },

    hideLoading() {
        state.isLoading = false;
        elements.loadingOverlay.style.display = 'none';
    },

    showTab(tabId) {
        state.currentTab = tabId;

        // Update navigation
        elements.navButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabId);
        });

        // Update content
        elements.tabContents.forEach(content => {
            content.classList.toggle('active', content.id === `${tabId}-tab`);
        });

        // Load history if needed
        if (tabId === 'history') {
            this.loadHistory();
        }
    },

    showResults(html) {
        elements.resultsContent.innerHTML = html;
        elements.resultsSection.hidden = false;
        elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
    },

    hideResults() {
        elements.resultsSection.hidden = true;
    },

    showError(message) {
        const html = `
            <div class="error-message">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <span>${message}</span>
            </div>
        `;
        this.showResults(html);
    },

    renderTextAnalysis(analysis) {
        const scores = [
            { key: 'event_discovery_score', label: 'Поиск и обнаружение событий' },
            { key: 'personalization_score', label: 'Персонализация и рекомендации' },
            { key: 'regional_coverage_score', label: 'Охват городов и регионов' },
            { key: 'ticketing_score', label: 'Покупка и бронирование билетов' },
            { key: 'organizer_tools_score', label: 'Инструменты для организаторов' },
            { key: 'content_quality_score', label: 'Качество описаний и редконтента' }
        ];

        return `
            ${this.renderResultBlock('Сильные стороны', analysis.strengths, 'strengths')}
            ${this.renderResultBlock('Слабые стороны', analysis.weaknesses, 'weaknesses')}
            ${this.renderResultBlock('Уникальные функции и предложения', analysis.unique_features, 'unique')}
            ${this.renderScores(scores.map(s => ({ label: s.label, value: analysis[s.key] })))}
            ${this.renderResultBlock('Возможности для «Арт-Афиши»', analysis.opportunities_for_art_afisha, 'opportunities')}
            ${analysis.summary ? `
                <div class="result-block result-summary">
                    <h3>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                            <polyline points="14 2 14 8 20 8"/>
                        </svg>
                        Резюме
                    </h3>
                    <p>${analysis.summary}</p>
                </div>
            ` : ''}
        `;
    },

    renderScores(scores) {
        if (!scores || scores.length === 0) return '';

        return `
            <div class="result-block scores-block">
                <h3>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                    </svg>
                    Оценки по ключевым направлениям
                </h3>
                <div class="scores-list">
                    ${scores.map(s => this.renderScoreRow(s.label, s.value)).join('')}
                </div>
            </div>
        `;
    },

    renderScoreRow(label, value) {
        const hasValue = value !== null && value !== undefined && !Number.isNaN(Number(value));
        const num = Number(value);
        const percent = hasValue ? (num / 10) * 100 : 0;

        return `
            <div class="score-row">
                <span class="score-row-label">${label}</span>
                <div class="score-bar">
                    <div class="score-fill" style="width: ${percent}%"></div>
                </div>
                <span class="score-row-value${hasValue ? '' : ' score-na'}">${hasValue ? num + '/10' : 'н/д'}</span>
            </div>
        `;
    },

    renderImageAnalysis(analysis) {
        const scores = [
            { key: 'visual_style_score', label: 'Визуальный стиль' },
            { key: 'navigation_clarity_score', label: 'Ясность навигации' },
            { key: 'event_card_quality_score', label: 'Качество карточек событий' },
            { key: 'cta_visibility_score', label: 'Видимость CTA' },
            { key: 'mobile_readability_score', label: 'Читаемость на мобильных' }
        ];

        return `
            <div class="result-block">
                <h3>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                        <circle cx="8.5" cy="8.5" r="1.5"/>
                        <polyline points="21 15 16 10 5 21"/>
                    </svg>
                    Описание изображения
                </h3>
                <p>${analysis.description}</p>
            </div>

            ${this.renderScores(scores.map(s => ({ label: s.label, value: analysis[s.key] })))}

            ${analysis.information_density ? `
                <div class="result-block">
                    <h3>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="8" y1="6" x2="21" y2="6"/>
                            <line x1="8" y1="12" x2="21" y2="12"/>
                            <line x1="8" y1="18" x2="21" y2="18"/>
                            <line x1="3" y1="6" x2="3.01" y2="6"/>
                            <line x1="3" y1="12" x2="3.01" y2="12"/>
                            <line x1="3" y1="18" x2="3.01" y2="18"/>
                        </svg>
                        Плотность информации
                    </h3>
                    <p>${analysis.information_density}</p>
                </div>
            ` : ''}

            ${this.renderResultBlock('Сильные стороны интерфейса', analysis.visual_strengths, 'strengths')}
            ${this.renderResultBlock('Слабые стороны интерфейса', analysis.visual_weaknesses, 'weaknesses')}
            ${this.renderResultBlock('Рекомендации для «Арт-Афиши»', analysis.recommendations, 'opportunities')}
        `;
    },

    renderParsedContent(data) {
        const parsed = data;

        return `
            <div class="parsed-content">
                <div class="label">URL:</div>
                <div class="value">${parsed.url}</div>

                <div class="label">Title:</div>
                <div class="value">${parsed.title || 'Не найден'}</div>

                <div class="label">H1:</div>
                <div class="value">${parsed.h1 || 'Не найден'}</div>

                <div class="label">Meta description:</div>
                <div class="value">${parsed.meta_description || 'Не найдена'}</div>

                <div class="label">Первый абзац:</div>
                <div class="value">${parsed.first_paragraph || 'Не найден'}</div>
            </div>

            ${parsed.analysis ? this.renderTextAnalysis(parsed.analysis) : ''}
        `;
    },

    renderResultBlock(title, items, type) {
        if (!items || items.length === 0) return '';

        const icons = {
            strengths: '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
            weaknesses: '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
            unique: '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
            recommendations: '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
            insights: '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>',
            opportunities: '<path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>'
        };

        return `
            <div class="result-block">
                <h3>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        ${icons[type] || icons.recommendations}
                    </svg>
                    ${title}
                </h3>
                <ul>
                    ${items.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>
        `;
    },

    async loadHistory() {
        try {
            const data = await api.getHistory();
            this.renderHistory(data.items);
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    },

    renderHistory(items) {
        if (!items || items.length === 0) {
            elements.historyList.innerHTML = `
                <div class="history-empty">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <polyline points="12 6 12 12 16 14"/>
                    </svg>
                    <p>История пуста</p>
                </div>
            `;
            return;
        }

        const icons = {
            text: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
            image: '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>',
            parse: '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>'
        };

        const typeLabels = {
            text: 'Анализ текста',
            image: 'Анализ изображения',
            parse: 'Парсинг сайта'
        };

        elements.historyList.innerHTML = items.map(item => {
            const date = new Date(item.timestamp);
            const timeStr = date.toLocaleString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });

            return `
                <div class="history-item">
                    <div class="history-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            ${icons[item.request_type] || icons.text}
                        </svg>
                    </div>
                    <div class="history-content">
                        <div class="history-type">${typeLabels[item.request_type] || item.request_type}</div>
                        <div class="history-summary">${item.request_summary}</div>
                    </div>
                    <div class="history-time">${timeStr}</div>
                </div>
            `;
        }).join('');
    }
};

// === Event Handlers ===
const handlers = {
    // Navigation
    handleNavClick(e) {
        const btn = e.target.closest('.nav-btn');
        if (btn) {
            ui.showTab(btn.dataset.tab);
        }
    },

    // Text analysis
    async handleAnalyzeText() {
        const text = elements.competitorText.value.trim();

        if (text.length < 10) {
            ui.showError('Введите текст минимум 10 символов для анализа');
            return;
        }

        ui.showLoading();

        try {
            const result = await api.analyzeText(text);

            if (result.success && result.analysis) {
                ui.showResults(ui.renderTextAnalysis(result.analysis));
            } else {
                ui.showError(result.error || 'Произошла ошибка при анализе');
            }
        } catch (error) {
            ui.showError('Ошибка соединения с сервером');
            console.error(error);
        } finally {
            ui.hideLoading();
        }
    },

    // Image upload
    handleUploadClick() {
        elements.imageInput.click();
    },

    handleImageSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.processImage(file);
        }
    },

    handleDragOver(e) {
        e.preventDefault();
        elements.uploadZone.classList.add('dragover');
    },

    handleDragLeave(e) {
        e.preventDefault();
        elements.uploadZone.classList.remove('dragover');
    },

    handleDrop(e) {
        e.preventDefault();
        elements.uploadZone.classList.remove('dragover');

        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            this.processImage(file);
        }
    },

    processImage(file) {
        state.selectedImage = file;

        const reader = new FileReader();
        reader.onload = (e) => {
            elements.imagePreview.src = e.target.result;
            elements.previewContainer.hidden = false;
            elements.uploadZone.querySelector('.upload-content').hidden = true;
            elements.analyzeImageBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    },

    handleRemoveImage() {
        state.selectedImage = null;
        elements.imageInput.value = '';
        elements.imagePreview.src = '';
        elements.previewContainer.hidden = true;
        elements.uploadZone.querySelector('.upload-content').hidden = false;
        elements.analyzeImageBtn.disabled = true;
    },

    async handleAnalyzeImage() {
        if (!state.selectedImage) {
            ui.showError('Выберите изображение для анализа');
            return;
        }

        ui.showLoading();

        try {
            const result = await api.analyzeImage(state.selectedImage);

            if (result.success && result.analysis) {
                ui.showResults(ui.renderImageAnalysis(result.analysis));
            } else {
                ui.showError(result.error || 'Произошла ошибка при анализе изображения');
            }
        } catch (error) {
            ui.showError('Ошибка соединения с сервером');
            console.error(error);
        } finally {
            ui.hideLoading();
        }
    },

    // Parse demo
    async handleParse() {
        const competitor = elements.competitorSelect.value;

        let url = elements.urlInput.value.trim();

        if (!competitor && !url) {
            ui.showError('Выберите конкурента или введите URL сайта');
            return;
        }

        // Add protocol if missing (только для своего URL)
        if (!competitor && !url.startsWith('http://') && !url.startsWith('https://')) {
            url = 'https://' + url;
        }

        ui.showLoading();

        try {
            const result = await api.parseDemo(url, competitor);

            if (result.success && result.data) {
                ui.showResults(ui.renderParsedContent(result.data));
            } else {
                ui.showError(result.error || 'Не удалось собрать данные сайта');
            }
        } catch (error) {
            ui.showError('Ошибка соединения с сервером');
            console.error(error);
        } finally {
            ui.hideLoading();
        }
    },

    // Competitor selection: заполняем URL выбранного конкурента
    handleCompetitorChange() {
        const competitor = elements.competitorSelect.value;
        const option = elements.competitorSelect.selectedOptions[0];

        if (competitor && option && option.dataset.url) {
            elements.urlInput.value = option.dataset.url.replace(/^https?:\/\//, '');
            elements.urlInput.disabled = true;
        } else {
            elements.urlInput.value = '';
            elements.urlInput.disabled = false;
        }
    },

    async loadCompetitors() {
        try {
            const data = await api.getCompetitors();
            const competitors = data.competitors || [];

            const options = competitors.map(c =>
                `<option value="${c.key}" data-url="${c.url}">${c.name} (${c.url})</option>`
            ).join('');

            elements.competitorSelect.innerHTML = '<option value="">— Свой URL —</option>' + options;
        } catch (error) {
            console.error('Failed to load competitors:', error);
        }
    },

    // History
    async handleClearHistory() {
        if (!confirm('Вы уверены, что хотите очистить историю?')) {
            return;
        }

        try {
            await api.clearHistory();
            ui.renderHistory([]);
        } catch (error) {
            console.error('Failed to clear history:', error);
        }
    },

    // Results
    handleCloseResults() {
        ui.hideResults();
    }
};

// === Initialize ===
function init() {
    // Navigation
    elements.navButtons.forEach(btn => {
        btn.addEventListener('click', handlers.handleNavClick.bind(handlers));
    });

    // Text analysis
    elements.analyzeTextBtn.addEventListener('click', handlers.handleAnalyzeText.bind(handlers));

    // Image upload
    elements.uploadZone.addEventListener('click', handlers.handleUploadClick.bind(handlers));
    elements.imageInput.addEventListener('change', handlers.handleImageSelect.bind(handlers));
    elements.uploadZone.addEventListener('dragover', handlers.handleDragOver.bind(handlers));
    elements.uploadZone.addEventListener('dragleave', handlers.handleDragLeave.bind(handlers));
    elements.uploadZone.addEventListener('drop', handlers.handleDrop.bind(handlers));
    elements.removeImageBtn.addEventListener('click', handlers.handleRemoveImage.bind(handlers));
    elements.analyzeImageBtn.addEventListener('click', handlers.handleAnalyzeImage.bind(handlers));

    // Parse demo
    elements.parseBtn.addEventListener('click', handlers.handleParse.bind(handlers));
    elements.competitorSelect.addEventListener('change', handlers.handleCompetitorChange.bind(handlers));
    elements.urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handlers.handleParse.call(handlers);
    });
    handlers.loadCompetitors.call(handlers);

    // History
    elements.clearHistoryBtn.addEventListener('click', handlers.handleClearHistory.bind(handlers));

    // Results
    elements.closeResultsBtn.addEventListener('click', handlers.handleCloseResults.bind(handlers));

    // Show default tab
    ui.showTab('text');
}

// Start app
document.addEventListener('DOMContentLoaded', init);
