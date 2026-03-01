/* ========================================
   YOMU 2.0 — App Logic
   ======================================== */

document.addEventListener('DOMContentLoaded', () => {

    // ─── State ───
    const state = {
        currentView: 'library',
        currentNovel: null,
        currentChapter: null,
        library: [],
        dictionary: {},
        grammar: [],
        flashcards: loadFromStorage('yomu-flashcards', []),
        readingProgress: loadFromStorage('yomu-progress', {}),
        theme: loadFromStorage('yomu-theme', 'dark'),
        fontSize: loadFromStorage('yomu-fontsize', 18),
        readingMode: loadFromStorage('yomu-readingmode', 'vertical'),
        showFurigana: loadFromStorage('yomu-furigana', true),
        reviewQueue: [],
        reviewIndex: 0,
        customDictionary: loadFromStorage('yomu-custom-dict', {}),
        searchQuery: '',
        chapterWordCount: 0,
    };

    // ─── DOM References ───
    const views = {
        library: document.getElementById('library-view'),
        novel: document.getElementById('novel-view'),
        reader: document.getElementById('reader-view'),
        flashcards: document.getElementById('flashcards-view'),
        grammar: document.getElementById('grammar-view'),
        settings: document.getElementById('settings-view'),
    };

    const bottomNav = document.getElementById('bottom-nav');
    const toastContainer = document.getElementById('toast-container');

    // ─── Initialize ───
    init();

    function init() {
        setTheme(state.theme);
        loadDictionary();
        loadLibrary();
        loadGrammar();
        setupEventListeners();
        updateFlashcardStats();
        setupSearch();
    }

    function setupSearch() {
        const searchInput = document.getElementById('library-search');
        if (!searchInput) return;
        searchInput.addEventListener('input', (e) => {
            state.searchQuery = e.target.value;
            renderLibrary(state.library);
        });
    }

    // ═══════════════════════════════════════
    // Theme
    // ═══════════════════════════════════════
    function setTheme(theme) {
        state.theme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        saveToStorage('yomu-theme', theme);

        // Update meta theme-color
        const meta = document.querySelector('meta[name="theme-color"]');
        if (meta) meta.content = theme === 'dark' ? '#0d0d14' : '#f5f0e8';

        // Update settings buttons
        document.querySelectorAll('.theme-option').forEach(btn => {
            btn.classList.toggle('active-theme', btn.dataset.theme === theme);
        });
    }

    function toggleTheme() {
        setTheme(state.theme === 'dark' ? 'light' : 'dark');
    }

    // ═══════════════════════════════════════
    // Navigation
    // ═══════════════════════════════════════
    function navigateTo(viewName, options = {}) {
        const { skipHistory = false } = options;

        // Hide current view
        const currentView = views[state.currentView];
        if (currentView) {
            currentView.classList.remove('active-view');
            currentView.classList.add('slide-out');
            setTimeout(() => currentView.classList.remove('slide-out'), 300);
        }

        // Show new view
        const newView = views[viewName];
        if (newView) {
            newView.classList.add('active-view');
        }

        state.currentView = viewName;

        // Update bottom nav
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.view === viewName);
        });

        // Show/hide bottom nav (hide in reader and novel detail)
        const hideNav = viewName === 'reader' || viewName === 'novel';
        bottomNav.classList.toggle('nav-hidden', hideNav);
    }

    // ═══════════════════════════════════════
    // Library
    // ═══════════════════════════════════════
    function loadLibrary() {
        fetch('library.json')
            .then(res => res.json())
            .then(data => {
                state.library = data;
                renderLibrary(data);
            })
            .catch(err => {
                console.error('Error loading library:', err);
                document.getElementById('library-grid').innerHTML =
                    '<p style="color:var(--text-secondary);text-align:center;padding:2rem;grid-column:1/-1">Failed to load library.</p>';
            });
    }

    function renderLibrary(novels) {
        const grid = document.getElementById('library-grid');
        grid.innerHTML = '';

        const searchTerm = (state.searchQuery || '').toLowerCase();
        const filtered = searchTerm
            ? novels.filter(n =>
                (n.title || '').toLowerCase().includes(searchTerm) ||
                (n.title_en || '').toLowerCase().includes(searchTerm) ||
                (n.author || '').toLowerCase().includes(searchTerm) ||
                (n.author_en || '').toLowerCase().includes(searchTerm) ||
                (n.tags || []).some(t => t.toLowerCase().includes(searchTerm))
            )
            : novels;

        document.getElementById('novel-count').textContent = `${filtered.length}`;
        novels = filtered;

        novels.forEach((novel, index) => {
            const card = document.createElement('div');
            card.className = 'novel-card';
            card.style.animationDelay = `${index * 0.08}s`;

            const gradient = novel.gradient || ['#e2725b', '#c0392b', '#2D0A0A'];
            const firstChar = novel.title.charAt(0);
            const gradientCSS = gradient.length === 3
                ? `linear-gradient(160deg, ${gradient[0]} 0%, ${gradient[1]} 50%, ${gradient[2]} 100%)`
                : `linear-gradient(160deg, ${gradient[0]}, ${gradient[1]})`;

            // Check if there's saved progress
            const progress = state.readingProgress[novel.id];

            // Check if complete or prologue
            const isComplete = (novel.tags || []).includes('complete');
            const isPrologue = (novel.tags || []).includes('prologue');
            const typeBadge = isComplete ? '<span class="type-badge complete">Complete</span>'
                : isPrologue ? '<span class="type-badge prologue">Prologue</span>' : '';

            // Cover image or gradient fallback
            const hasCover = !!novel.cover_image;
            const coverBg = hasCover
                ? `<div class="novel-card-bg" style="background: ${gradientCSS}"><img class="novel-card-cover-img" src="${novel.cover_image}" alt="${novel.title}" onerror="this.style.display='none'"></div>`
                : `<div class="novel-card-bg" style="background: ${gradientCSS}"></div>`;

            card.innerHTML = `
                ${coverBg}
                ${hasCover ? '' : `<span class="novel-card-char">${firstChar}</span>`}
                ${progress ? '<span class="progress-badge">Reading</span>' : ''}
                ${typeBadge}
                <div class="novel-card-info">
                    <div class="novel-card-title">${novel.title}</div>
                    <div class="novel-card-subtitle">${novel.title_en || ''}</div>
                    <div class="novel-card-author">${novel.author_en || novel.author}</div>
                    <div class="novel-card-chapters">${novel.chapters.length} chapter${novel.chapters.length > 1 ? 's' : ''}</div>
                </div>
            `;

            card.addEventListener('click', () => showNovelDetail(novel));
            grid.appendChild(card);
        });
    }

    // ═══════════════════════════════════════
    // Novel Detail
    // ═══════════════════════════════════════
    function showNovelDetail(novel) {
        state.currentNovel = novel;

        const gradient = novel.gradient || ['#e2725b', '#c0392b', '#2D0A0A'];
        const firstChar = novel.title.charAt(0);
        const gradientCSS = gradient.length === 3
            ? `linear-gradient(160deg, ${gradient[0]} 0%, ${gradient[1]} 50%, ${gradient[2]} 100%)`
            : `linear-gradient(160deg, ${gradient[0]}, ${gradient[1]})`;

        // Header
        document.getElementById('novel-header-title').textContent = novel.title_en || novel.title;

        // Cover
        const cover = document.getElementById('novel-cover');
        cover.style.background = gradientCSS;

        // Cover image or kanji fallback
        const coverChar = document.getElementById('cover-char');
        const existingImg = cover.querySelector('.cover-img');
        if (existingImg) existingImg.remove();

        if (novel.cover_image) {
            coverChar.style.display = 'none';
            const img = document.createElement('img');
            img.className = 'cover-img';
            img.src = novel.cover_image;
            img.alt = novel.title;
            img.onerror = () => {
                img.remove();
                coverChar.style.display = '';
                coverChar.textContent = firstChar;
            };
            cover.appendChild(img);
        } else {
            coverChar.style.display = '';
            coverChar.textContent = firstChar;
        }

        // Meta
        document.getElementById('novel-title').textContent = novel.title;
        document.getElementById('novel-author').textContent =
            (novel.author_en ? `${novel.author} · ${novel.author_en}` : novel.author);

        // Tags
        const tagsContainer = document.getElementById('novel-tags');
        tagsContainer.innerHTML = (novel.tags || []).map(t =>
            `<span class="tag">${t}</span>`
        ).join('');

        // Synopsis
        document.getElementById('novel-synopsis-ja').textContent = novel.summary_ja;
        document.getElementById('novel-synopsis-en').textContent = novel.summary_en;

        // Continue Reading
        const progress = state.readingProgress[novel.id];
        const progressSection = document.getElementById('novel-progress-section');
        if (progress) {
            progressSection.style.display = 'block';
        } else {
            progressSection.style.display = 'none';
        }

        // Chapter List
        const chapterList = document.getElementById('chapter-list');
        chapterList.innerHTML = '';
        document.getElementById('chapter-count').textContent = `${novel.chapters.length}`;

        novel.chapters.forEach((chapter, index) => {
            const isRead = progress && progress.chapterId === chapter.id;

            const item = document.createElement('div');
            item.className = 'chapter-item';
            item.innerHTML = `
                <span class="chapter-number">${index + 1}</span>
                <div class="chapter-info">
                    <div class="chapter-title">${chapter.title}</div>
                    ${chapter.title_en ? `<div class="chapter-title-en">${chapter.title_en}</div>` : ''}
                </div>
                ${isRead ? '<span class="chapter-read-indicator">📖</span>' : ''}
                <span class="chapter-arrow">›</span>
            `;

            item.addEventListener('click', () => loadChapter(novel, chapter));
            chapterList.appendChild(item);
        });

        navigateTo('novel');
    }

    // ═══════════════════════════════════════
    // Reader
    // ═══════════════════════════════════════
    function loadChapter(novel, chapter) {
        state.currentNovel = novel;
        state.currentChapter = chapter;

        document.getElementById('reader-header-title').textContent = chapter.title;

        const readerContent = document.getElementById('reader-content');
        readerContent.innerHTML = '<p style="color:var(--text-tertiary);text-align:center;padding:3rem">Loading...</p>';

        // Apply settings
        applyReaderSettings();

        navigateTo('reader');

        fetch(chapter.filename)
            .then(res => res.json())
            .then(data => {
                renderStory(data.content);

                // Restore scroll position
                const progress = state.readingProgress[novel.id];
                if (progress && progress.chapterId === chapter.id && progress.scrollPos) {
                    const wrapper = document.getElementById('reader-content-wrapper');
                    setTimeout(() => {
                        if (state.readingMode === 'vertical') {
                            wrapper.scrollLeft = progress.scrollPos;
                        } else {
                            wrapper.scrollTop = progress.scrollPos;
                        }
                    }, 100);
                }
            })
            .catch(err => {
                console.error('Error loading chapter:', err);
                readerContent.innerHTML =
                    '<p style="color:var(--danger);text-align:center;padding:3rem">Failed to load chapter.</p>';
            });
    }

    function renderStory(content) {
        const readerContent = document.getElementById('reader-content');
        readerContent.innerHTML = '';
        const fragment = document.createDocumentFragment();

        let totalChars = 0;
        content.forEach(lineTokens => {
            lineTokens.forEach(t => { totalChars += t.s.length; });
        });
        state.chapterWordCount = totalChars;

        const readingTimeMin = Math.max(1, Math.round(totalChars / 500));
        const progressBar = document.getElementById('reading-progress-bar');
        if (progressBar) progressBar.style.width = '0%';
        const readingInfo = document.getElementById('reading-info');
        if (readingInfo) readingInfo.textContent = `${totalChars.toLocaleString()} chars · ~${readingTimeMin} min`;

        content.forEach((lineTokens, index) => {
            const p = document.createElement('p');

            lineTokens.forEach(token => {
                const span = document.createElement('span');
                span.className = 'word';
                span.dataset.surface = token.s;
                span.dataset.reading = token.r || '';

                if (token.r && state.showFurigana) {
                    const ruby = document.createElement('ruby');
                    ruby.textContent = token.s;
                    const rt = document.createElement('rt');
                    rt.textContent = token.r;
                    ruby.appendChild(rt);
                    span.appendChild(ruby);
                } else {
                    span.textContent = token.s;
                }

                span.addEventListener('click', (e) => {
                    e.stopPropagation();
                    showDefinition(token);
                });

                p.appendChild(span);
            });

            // Add Translate Button
            const text = lineTokens.map(t => t.s).join('').trim();
            if (text.length > 0) {
                const translateBtn = document.createElement('button');
                translateBtn.className = 'translate-btn';
                translateBtn.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 8l6 6M4 14h6M2 5h12M7 2v3M22 22l-5-10-5 10M14 18h6"/></svg>`;
                translateBtn.title = 'Translate paragraph';
                translateBtn.onclick = (e) => {
                    e.stopPropagation();
                    toggleTranslation(p, text, index);
                };
                p.appendChild(translateBtn);
            }

            fragment.appendChild(p);
        });

        readerContent.appendChild(fragment);
    }

    async function translateText(text) {
        // Use MyMemory Translation API (free, no auth required)
        // Note: Free tier has 5000 character limit per request and ~100 requests/day limit
        
        // Split text if too long (max 4500 chars to be safe)
        if (text.length > 4500) {
            console.warn('Text too long for single translation request, truncating to 4500 characters');
            text = text.substring(0, 4500);
        }
        
        const encodedText = encodeURIComponent(text);
        const url = `https://api.mymemory.translated.net/get?q=${encodedText}&langpair=ja|en`;
        
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            
            // Check for valid translation response
            if (data.responseData && data.responseData.translatedText) {
                return data.responseData.translatedText;
            } else {
                throw new Error('Translation failed: ' + (data.responseDetails || 'Invalid response'));
            }
        } catch (error) {
            console.error('Translation API error:', error);
            throw error;
        }
    }

    function toggleTranslation(paragraphEl, text, index) {
        // vertical mode handling: the box should be inserted differently?
        // In vertical mode, 'after' means to the left visually (next sibling in DOM).

        // precise check for existing box
        let next = paragraphEl.nextElementSibling;
        if (next && next.classList.contains('translation-box')) {
            next.remove();
            return;
        }

        const box = document.createElement('div');
        box.className = 'translation-box';

        // cache key: unique per chapter line
        const cacheKey = `yomu-trans-${state.currentNovel.id}-${state.currentChapter.id}-${index}`;
        const cached = localStorage.getItem(cacheKey);

        if (cached) {
            box.textContent = cached;
            box.classList.add('cached'); // Optional styling
            paragraphEl.after(box);
            return;
        }

        box.textContent = 'Translating...';
        paragraphEl.after(box);

        translateText(text)
            .then(translation => {
                box.textContent = translation;
                // Save to cache
                try {
                    localStorage.setItem(cacheKey, translation);
                } catch (e) {
                    console.warn('Quota exceeded for localStorage translation cache');
                }
            })
            .catch(err => {
                console.error('Translation error:', err);
                box.textContent = 'Translation unavailable. Please check your internet connection and try again.';
                box.classList.add('error');
            });
    }

    async function downloadChapterTranslations() {
        if (!state.currentNovel || !state.currentChapter) return;

        if (!confirm('Download translations for this chapter?')) return;

        const btn = document.getElementById('download-translations-btn');
        if (btn) btn.classList.add('pulse');

        try {
            showToast('Starting download...', 'info');

            // Re-fetch content
            const response = await fetch(state.currentChapter.filename);
            const data = await response.json();
            const content = data.content;

            // Identify needed translations
            const itemsToFetch = [];
            content.forEach((lineTokens, index) => {
                const text = lineTokens.map(t => t.s).join('').trim();
                // Filter out empty lines
                if (text.length === 0) return;

                const cacheKey = `yomu-trans-${state.currentNovel.id}-${state.currentChapter.id}-${index}`;
                if (!localStorage.getItem(cacheKey)) {
                    itemsToFetch.push({ index, text, cacheKey });
                }
            });

            const total = itemsToFetch.length;
            if (total === 0) {
                showToast('All paragraphs already downloaded!', 'success');
                if (btn) btn.classList.remove('pulse');
                return;
            }

            // Process in batches with delay to respect API rate limits
            // Note: MyMemory free tier allows ~100 requests/day from an IP
            const batchSize = 5;
            let completed = 0;

            for (let i = 0; i < total; i += batchSize) {
                const batch = itemsToFetch.slice(i, i + batchSize);

                // Update progress with correct count
                showToast(`Downloading: ${completed} / ${total}`, 'info');

                await Promise.all(batch.map(async (item) => {
                    try {
                        const translation = await translateText(item.text);
                        if (translation) {
                            localStorage.setItem(item.cacheKey, translation);
                        }
                    } catch (err) {
                        console.error('Download error line ' + item.index, err);
                    }
                }));

                completed += batch.length;
                // Delay between batches to avoid overwhelming the API
                if (i + batchSize < total) {
                    await new Promise(r => setTimeout(r, 1000)); // 1 second delay
                }
            }

            showToast(`Download complete! (${completed} new translations)`, 'success');

            // Visual feedback on button
            if (btn) {
                const originalHTML = btn.innerHTML;
                btn.innerHTML = `<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`;
                btn.classList.add('success');
                btn.style.color = '#2ecc71';
                btn.style.borderColor = '#2ecc71';

                setTimeout(() => {
                    btn.innerHTML = originalHTML;
                    btn.classList.remove('success');
                    btn.style.color = '';
                    btn.style.borderColor = '';
                }, 3000);
            }

        } catch (e) {
            console.error(e);
            showToast('Download failed', 'error');
        } finally {
            if (btn) btn.classList.remove('pulse');
        }
    }

    function applyReaderSettings() {
        const wrapper = document.getElementById('reader-content-wrapper');
        const content = document.getElementById('reader-content');

        // Reading mode
        wrapper.classList.toggle('vertical-mode', state.readingMode === 'vertical');
        wrapper.classList.toggle('horizontal-mode', state.readingMode === 'horizontal');

        // Font size
        content.style.fontSize = `${state.fontSize}px`;
        document.getElementById('font-size-display').textContent = `${state.fontSize}px`;

        // Furigana
        wrapper.classList.toggle('hide-furigana', !state.showFurigana);

        // Reading mode buttons
        document.querySelectorAll('.mode-btn[data-mode]').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === state.readingMode);
        });

        // Furigana buttons
        document.querySelectorAll('.mode-btn[data-furigana]').forEach(btn => {
            const isOn = btn.dataset.furigana === 'on';
            btn.classList.toggle('active', isOn === state.showFurigana);
        });
    }

    function saveReadingProgress() {
        if (!state.currentNovel || !state.currentChapter) return;

        const wrapper = document.getElementById('reader-content-wrapper');
        const scrollPos = state.readingMode === 'vertical'
            ? wrapper.scrollLeft
            : wrapper.scrollTop;

        state.readingProgress[state.currentNovel.id] = {
            chapterId: state.currentChapter.id,
            chapterTitle: state.currentChapter.title,
            scrollPos: scrollPos,
            timestamp: Date.now(),
        };

        saveToStorage('yomu-progress', state.readingProgress);
    }

    // ═══════════════════════════════════════
    // Dictionary & Definition Popup
    // ═══════════════════════════════════════
    function loadDictionary() {
        fetch('dict.json')
            .then(res => res.json())
            .then(data => {
                state.dictionary = data;
            })
            .catch(err => console.error('Error loading dictionary:', err));
    }

    function showDefinition(token) {
        const popup = document.getElementById('definition-popup');
        const wordEl = document.getElementById('popup-word');
        const readingEl = document.getElementById('popup-reading');
        const meaningEl = document.getElementById('popup-meaning');
        const flashcardBtn = document.getElementById('add-flashcard-btn');
        const flashcardBtnText = document.getElementById('flashcard-btn-text');

        wordEl.textContent = token.s;
        readingEl.textContent = token.r || '';

        // Check dictionary and custom dictionary
        let meaning = lookupWord(token.s, token.r);

        const setMeaning = (m) => {
            meaningEl.textContent = m;
            flashcardBtn.dataset.meaning = m || '';

            const isInFlashcards = state.flashcards.some(fc => fc.word === token.s);
            if (isInFlashcards) {
                flashcardBtn.classList.add('added');
                flashcardBtnText.textContent = '✓ In Flashcards';
            } else {
                flashcardBtn.classList.remove('added');
                flashcardBtnText.textContent = 'Add to Flashcards';
            }
        };

        flashcardBtn.dataset.word = token.s;
        flashcardBtn.dataset.reading = token.r || '';

        if (meaning) {
            setMeaning(meaning);
        } else {
            meaningEl.textContent = 'Looking up...';

            const encodedText = encodeURIComponent(token.s);
            const url = `https://api.mymemory.translated.net/get?q=${encodedText}&langpair=ja|en`;

            fetch(url)
                .then(res => res.json())
                .then(data => {
                    if (data.responseData && data.responseData.translatedText) {
                        const trans = data.responseData.translatedText;
                        state.customDictionary[token.s] = trans;
                        saveToStorage('yomu-custom-dict', state.customDictionary);
                        setMeaning(trans);
                    } else {
                        setMeaning('');
                        meaningEl.textContent = `No definition found for "${token.s}"`;
                    }
                })
                .catch(() => {
                    meaningEl.textContent = `No definition found for "${token.s}". Tap to search online.`;
                    meaningEl.style.cursor = 'pointer';
                    meaningEl.onclick = () => {
                        window.open(`https://jisho.org/search/${encodeURIComponent(token.s)}`, '_blank');
                    };
                    setMeaning('');
                });
        }

        popup.classList.remove('hidden');
    }

    function lookupWord(surface, reading) {
        if (state.dictionary[surface]) return state.dictionary[surface];
        if (state.customDictionary[surface]) return state.customDictionary[surface];

        if (reading) {
            if (state.dictionary[reading]) return state.dictionary[reading];
        }

        const tryForms = [];
        if (surface.endsWith('っ') || surface.endsWith('ん')) {
            tryForms.push(surface + 'だ');
            tryForms.push(surface + 'で');
        }
        if (surface.endsWith('し')) tryForms.push(surface.slice(0, -1) + 'す');
        if (surface.endsWith('き')) tryForms.push(surface.slice(0, -1) + 'く');
        if (surface.endsWith('ぎ')) tryForms.push(surface.slice(0, -1) + 'ぐ');
        if (surface.endsWith('い')) tryForms.push(surface.slice(0, -1) + 'う');
        if (surface.endsWith('ち')) tryForms.push(surface.slice(0, -1) + 'つ');
        if (surface.endsWith('り')) tryForms.push(surface.slice(0, -1) + 'る');
        if (surface.endsWith('み')) tryForms.push(surface.slice(0, -1) + 'む');
        if (surface.endsWith('び')) tryForms.push(surface.slice(0, -1) + 'ぶ');
        if (surface.endsWith('に')) tryForms.push(surface.slice(0, -1) + 'ぬ');
        if (surface.endsWith('て') || surface.endsWith('で')) {
            tryForms.push(surface.slice(0, -1) + 'る');
            tryForms.push(surface.slice(0, -1) + 'つ');
        }
        if (surface.endsWith('た')) {
            tryForms.push(surface.slice(0, -1) + 'る');
            tryForms.push(surface.slice(0, -1) + 'つ');
        }
        if (surface.endsWith('ない')) tryForms.push(surface.slice(0, -2) + 'る');
        if (surface.endsWith('ます')) tryForms.push(surface.slice(0, -2) + 'る');
        if (surface.endsWith('られ')) tryForms.push(surface.slice(0, -2) + 'る');
        if (surface.endsWith('され')) tryForms.push(surface.slice(0, -2) + 'する');

        for (const form of tryForms) {
            if (state.dictionary[form]) return state.dictionary[form];
        }

        return null;
    }

    function hideDefinition() {
        document.getElementById('definition-popup').classList.add('hidden');
    }

    // ═══════════════════════════════════════
    // Flashcards (SRS)
    // ═══════════════════════════════════════
    function addFlashcard(word, reading, meaning) {
        if (state.flashcards.some(fc => fc.word === word)) {
            showToast('Already in flashcards', 'error');
            return;
        }

        const card = {
            word,
            reading: reading || '',
            meaning: meaning || state.dictionary[word] || '',
            added: Date.now(),
            nextReview: Date.now(),
            interval: 0,
            easeFactor: 2.5,
            reviews: 0,
            level: 0, // 0=new, 1=learning, 2=reviewed, 3=mastered
        };

        state.flashcards.push(card);
        saveToStorage('yomu-flashcards', state.flashcards);
        updateFlashcardStats();
        showToast(`Added "${word}" to flashcards ✓`, 'success');
    }

    function removeFlashcard(word) {
        state.flashcards = state.flashcards.filter(fc => fc.word !== word);
        saveToStorage('yomu-flashcards', state.flashcards);
        updateFlashcardStats();
        renderFlashcardList();
    }

    function reviewFlashcard(rating) {
        // rating: 1=again, 2=hard, 3=good, 4=easy
        const card = state.reviewQueue[state.reviewIndex];
        if (!card) return;

        const now = Date.now();
        const dayMs = 86400000;

        switch (rating) {
            case 1: // Again
                card.interval = 0;
                card.easeFactor = Math.max(1.3, card.easeFactor - 0.2);
                card.nextReview = now + 60000; // 1 minute
                card.level = 1;
                break;
            case 2: // Hard
                card.interval = Math.max(1, card.interval * 1.2);
                card.easeFactor = Math.max(1.3, card.easeFactor - 0.15);
                card.nextReview = now + card.interval * dayMs;
                card.level = 2;
                break;
            case 3: // Good
                card.interval = card.interval === 0 ? 1 : card.interval * card.easeFactor;
                card.nextReview = now + card.interval * dayMs;
                card.level = card.interval > 21 ? 3 : 2;
                break;
            case 4: // Easy
                card.interval = card.interval === 0 ? 4 : card.interval * card.easeFactor * 1.3;
                card.easeFactor += 0.15;
                card.nextReview = now + card.interval * dayMs;
                card.level = card.interval > 14 ? 3 : 2;
                break;
        }

        card.reviews++;

        // Update in state
        const idx = state.flashcards.findIndex(fc => fc.word === card.word);
        if (idx !== -1) state.flashcards[idx] = card;
        saveToStorage('yomu-flashcards', state.flashcards);

        // Next card
        state.reviewIndex++;
        if (state.reviewIndex < state.reviewQueue.length) {
            showReviewCard();
        } else {
            showToast('Review complete! 🎉', 'success');
            updateFlashcardStats();
            renderFlashcardView();
        }
    }

    function updateFlashcardStats() {
        const now = Date.now();
        const total = state.flashcards.length;
        const due = state.flashcards.filter(fc => fc.nextReview <= now).length;
        const mastered = state.flashcards.filter(fc => fc.level >= 3).length;

        document.getElementById('stat-total').textContent = total;
        document.getElementById('stat-due').textContent = due;
        document.getElementById('stat-mastered').textContent = mastered;
    }

    function renderFlashcardView() {
        const emptyEl = document.getElementById('flashcard-empty');
        const deckEl = document.getElementById('flashcard-deck');

        if (state.flashcards.length === 0) {
            emptyEl.classList.remove('hidden');
            deckEl.classList.add('hidden');
        } else {
            emptyEl.classList.add('hidden');
            deckEl.classList.remove('hidden');
            startReview();
        }

        renderFlashcardList();
        updateFlashcardStats();
    }

    function startReview() {
        const now = Date.now();
        state.reviewQueue = state.flashcards
            .filter(fc => fc.nextReview <= now)
            .sort((a, b) => a.nextReview - b.nextReview);

        state.reviewIndex = 0;

        if (state.reviewQueue.length > 0) {
            showReviewCard();
        } else {
            // Show a random card if no reviews due
            if (state.flashcards.length > 0) {
                state.reviewQueue = [...state.flashcards];
                state.reviewIndex = 0;
                showReviewCard();
                document.getElementById('deck-progress').textContent = 'No cards due — browse mode';
            }
        }
    }

    function showReviewCard() {
        const card = state.reviewQueue[state.reviewIndex];
        if (!card) return;

        document.getElementById('card-word').textContent = card.word;
        document.getElementById('card-reading').textContent = card.reading;
        document.getElementById('card-meaning').textContent = card.meaning || 'No definition available';

        // Reset to front
        document.getElementById('card-front').classList.remove('hidden');
        document.getElementById('card-back').classList.add('hidden');
        document.getElementById('card-actions').style.display = 'none';

        document.getElementById('deck-progress').textContent =
            `${state.reviewIndex + 1} / ${state.reviewQueue.length}`;
    }

    function flipCard() {
        const front = document.getElementById('card-front');
        const back = document.getElementById('card-back');
        const actions = document.getElementById('card-actions');

        if (front.classList.contains('hidden')) {
            // Go back to front
            front.classList.remove('hidden');
            back.classList.add('hidden');
            actions.style.display = 'none';
        } else {
            // Show back
            front.classList.add('hidden');
            back.classList.remove('hidden');
            actions.style.display = 'grid';
        }
    }

    function renderFlashcardList() {
        const list = document.getElementById('flashcard-list');
        list.innerHTML = '';

        if (state.flashcards.length === 0) {
            return;
        }

        state.flashcards.forEach(fc => {
            const item = document.createElement('div');
            item.className = 'flashcard-list-item';
            item.innerHTML = `
                <div>
                    <span class="fc-item-word">${fc.word}</span>
                    <span class="fc-item-reading">${fc.reading}</span>
                </div>
                <span class="fc-item-meaning">${fc.meaning || '—'}</span>
                <button class="fc-delete-btn" data-word="${fc.word}" title="Remove">×</button>
            `;
            list.appendChild(item);
        });

        // Delete button handlers
        list.querySelectorAll('.fc-delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                removeFlashcard(btn.dataset.word);
                showToast('Card removed', 'error');
            });
        });
    }

    // ═══════════════════════════════════════
    // Event Listeners
    // ═══════════════════════════════════════
    function setupEventListeners() {
        // Theme Toggle
        document.getElementById('theme-toggle-btn').addEventListener('click', toggleTheme);

        // Download Translations
        const dlBtn = document.getElementById('download-translations-btn');
        if (dlBtn) {
            dlBtn.addEventListener('click', downloadChapterTranslations);
        }

        // Bottom Nav
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                const view = item.dataset.view;
                if (view === 'flashcards') renderFlashcardView();
                navigateTo(view);
            });
        });

        // Novel Detail Back
        document.getElementById('novel-back-btn').addEventListener('click', () => {
            navigateTo('library');
        });

        // Continue Reading
        document.getElementById('continue-reading-btn').addEventListener('click', () => {
            if (state.currentNovel) {
                const progress = state.readingProgress[state.currentNovel.id];
                if (progress) {
                    const chapter = state.currentNovel.chapters.find(c => c.id === progress.chapterId);
                    if (chapter) {
                        loadChapter(state.currentNovel, chapter);
                        return;
                    }
                }
                // Fallback: load first chapter
                if (state.currentNovel.chapters.length > 0) {
                    loadChapter(state.currentNovel, state.currentNovel.chapters[0]);
                }
            }
        });

        // Reader Back
        document.getElementById('reader-back-btn').addEventListener('click', () => {
            saveReadingProgress();
            if (state.currentNovel) {
                showNovelDetail(state.currentNovel);
            } else {
                navigateTo('library');
            }
        });

        // Reader Settings Toggle
        document.getElementById('reader-settings-btn').addEventListener('click', () => {
            const panel = document.getElementById('reader-settings-panel');
            panel.classList.toggle('hidden');
        });

        document.getElementById('close-reader-settings').addEventListener('click', () => {
            document.getElementById('reader-settings-panel').classList.add('hidden');
        });

        // Font Size
        document.getElementById('font-decrease').addEventListener('click', () => {
            state.fontSize = Math.max(12, state.fontSize - 2);
            saveToStorage('yomu-fontsize', state.fontSize);
            applyReaderSettings();
        });

        document.getElementById('font-increase').addEventListener('click', () => {
            state.fontSize = Math.min(32, state.fontSize + 2);
            saveToStorage('yomu-fontsize', state.fontSize);
            applyReaderSettings();
        });

        // Reading Mode
        document.querySelectorAll('.mode-btn[data-mode]').forEach(btn => {
            btn.addEventListener('click', () => {
                state.readingMode = btn.dataset.mode;
                saveToStorage('yomu-readingmode', state.readingMode);
                applyReaderSettings();
            });
        });

        // Furigana
        document.querySelectorAll('.mode-btn[data-furigana]').forEach(btn => {
            btn.addEventListener('click', () => {
                state.showFurigana = btn.dataset.furigana === 'on';
                saveToStorage('yomu-furigana', state.showFurigana);
                applyReaderSettings();
                // Re-render if content exists
                if (state.currentChapter) {
                    loadChapter(state.currentNovel, state.currentChapter);
                }
            });
        });

        // Definition Popup
        document.getElementById('popup-backdrop').addEventListener('click', hideDefinition);
        document.getElementById('close-popup-btn').addEventListener('click', hideDefinition);

        // Add to Flashcards from popup
        document.getElementById('add-flashcard-btn').addEventListener('click', (e) => {
            const btn = e.currentTarget;
            const word = btn.dataset.word;
            const reading = btn.dataset.reading;
            const meaning = btn.dataset.meaning;

            if (state.flashcards.some(fc => fc.word === word)) {
                showToast('Already in flashcards', 'error');
                return;
            }

            addFlashcard(word, reading, meaning);
            btn.classList.add('added');
            document.getElementById('flashcard-btn-text').textContent = '✓ In Flashcards';
        });

        // Flashcard flip
        document.getElementById('flashcard-card').addEventListener('click', flipCard);

        // Review buttons
        document.querySelectorAll('.review-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                reviewFlashcard(parseInt(btn.dataset.rating));
            });
        });

        // Settings: Theme Options
        document.querySelectorAll('.theme-option').forEach(btn => {
            btn.addEventListener('click', () => {
                setTheme(btn.dataset.theme);
            });
        });

        // Settings: Clear Flashcards
        document.getElementById('clear-flashcards-btn').addEventListener('click', () => {
            if (confirm('Delete all flashcards? This cannot be undone.')) {
                state.flashcards = [];
                saveToStorage('yomu-flashcards', []);
                updateFlashcardStats();
                showToast('Flashcards cleared', 'success');
            }
        });

        // Settings: Clear Progress
        document.getElementById('clear-progress-btn').addEventListener('click', () => {
            if (confirm('Reset all reading progress?')) {
                state.readingProgress = {};
                saveToStorage('yomu-progress', {});
                renderLibrary(state.library);
                showToast('Progress reset', 'success');
            }
        });

        // Settings: Refresh Cache
        document.getElementById('refresh-cache-btn').addEventListener('click', () => {
            if ('caches' in window) {
                caches.keys().then(names => {
                    names.forEach(name => caches.delete(name));
                });
                showToast('Cache refreshed — reload page', 'success');
            }
        });

        // Save progress on scroll (debounced) + update progress bar
        let progressTimeout;
        const readerWrapper = document.getElementById('reader-content-wrapper');
        readerWrapper.addEventListener('scroll', () => {
            clearTimeout(progressTimeout);
            progressTimeout = setTimeout(saveReadingProgress, 500);

            const progressBar = document.getElementById('reading-progress-bar');
            if (progressBar) {
                let pct = 0;
                if (state.readingMode === 'vertical') {
                    const max = readerWrapper.scrollWidth - readerWrapper.clientWidth;
                    if (max > 0) pct = Math.abs(readerWrapper.scrollLeft) / max * 100;
                } else {
                    const max = readerWrapper.scrollHeight - readerWrapper.clientHeight;
                    if (max > 0) pct = readerWrapper.scrollTop / max * 100;
                }
                progressBar.style.width = `${Math.min(100, Math.max(0, pct))}%`;
            }
        });

        // Swipe-to-go-back gesture for mobile reader
        let touchStartX = 0;
        let touchStartY = 0;
        const readerView = document.getElementById('reader-view');
        readerView.addEventListener('touchstart', (e) => {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
        }, { passive: true });

        readerView.addEventListener('touchend', (e) => {
            const dx = e.changedTouches[0].clientX - touchStartX;
            const dy = e.changedTouches[0].clientY - touchStartY;
            if (state.readingMode === 'horizontal' && dx > 80 && Math.abs(dy) < 50 && touchStartX < 40) {
                saveReadingProgress();
                if (state.currentNovel) {
                    showNovelDetail(state.currentNovel);
                } else {
                    navigateTo('library');
                }
            }
        }, { passive: true });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                hideDefinition();
                document.getElementById('reader-settings-panel').classList.add('hidden');
            }
        });
    }

    // ═══════════════════════════════════════
    // Grammar
    // ═══════════════════════════════════════
    function loadGrammar() {
        fetch('grammar.json')
            .then(res => res.json())
            .then(data => {
                state.grammar = data;
                renderGrammar(data);
            })
            .catch(err => {
                console.error('Error loading grammar:', err);
                document.getElementById('grammar-content').innerHTML =
                    '<p style="color:var(--text-secondary);text-align:center;padding:2rem;">Failed to load grammar.</p>';
            });
    }

    function renderGrammar(grammarData) {
        const container = document.getElementById('grammar-content');
        container.innerHTML = '';

        grammarData.forEach(section => {
            const sectionEl = document.createElement('div');
            sectionEl.className = 'grammar-section';

            sectionEl.innerHTML = `
                <div class="grammar-header">
                    <span class="grammar-level">${section.level}</span>
                    <h2 class="grammar-title">${section.title}</h2>
                    <p class="grammar-desc">${section.description}</p>
                </div>
                <div class="grammar-points">
                    ${section.points.map(point => `
                        <div class="grammar-card">
                            <div class="grammar-pattern">${point.pattern}</div>
                            <div class="grammar-meaning">${point.meaning}</div>
                            <div class="grammar-usage">
                                <strong>Usage:</strong> ${point.usage}
                            </div>
                            <div class="grammar-example">
                                ${point.example.replace(/\n/g, '<br>')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            container.appendChild(sectionEl);
        });
    }



    // ═══════════════════════════════════════
    // Utilities
    // ═══════════════════════════════════════
    function loadFromStorage(key, defaultValue) {
        try {
            const data = localStorage.getItem(key);
            return data ? JSON.parse(data) : defaultValue;
        } catch {
            return defaultValue;
        }
    }

    function saveToStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.error('Storage error:', e);
        }
    }

    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
});
