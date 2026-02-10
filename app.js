document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const libraryView = document.getElementById('library-view');
    const libraryList = document.getElementById('library-list');
    const readerView = document.getElementById('reader-view');
    const readerContent = document.getElementById('reader-content');
    const headerTitle = document.getElementById('header-title');
    const backBtn = document.getElementById('back-btn');
    const toggleBtn = document.getElementById('toggle-mode');
    
    // Popup Elements
    const popup = document.getElementById('definition-popup');
    const popupWord = document.getElementById('popup-word');
    const popupReading = document.getElementById('popup-reading');
    const popupMeaning = document.getElementById('popup-meaning');
    const closePopupBtn = document.getElementById('close-popup');

    // State
    let isVertical = true;
    let dictionary = {};

    // Load Dictionary
    fetch('dict.json')
        .then(response => response.json())
        .then(data => {
            dictionary = data;
        })
        .catch(err => console.error('Error loading dict:', err));

    // Initial Load
    init();

    function init() {
        showLibrary();
        fetch('library.json')
            .then(res => res.json())
            .then(data => {
                renderLibrary(data);
            })
            .catch(err => {
                console.error('Error loading library:', err);
                libraryList.innerHTML = '<p class="error">Failed to load library.</p>';
            });
    }

    function showLibrary() {
        libraryView.classList.remove('hidden');
        readerView.classList.add('hidden');
        
        // Reset Header
        headerTitle.textContent = "Yomu Library";
        backBtn.classList.add('hidden');
        toggleBtn.classList.add('hidden');
    }

    function renderLibrary(stories) {
        libraryList.innerHTML = '';
        
        stories.forEach(story => {
            const card = document.createElement('div');
            card.className = 'story-card';
            
            const title = document.createElement('h2');
            title.textContent = story.title;
            
            const summaryJa = document.createElement('p');
            summaryJa.className = 'summary-ja';
            summaryJa.textContent = story.summary_ja;
            
            const summaryEn = document.createElement('p');
            summaryEn.className = 'summary-en';
            summaryEn.textContent = story.summary_en;
            
            card.appendChild(title);
            card.appendChild(summaryJa);
            card.appendChild(summaryEn);
            
            card.addEventListener('click', () => loadStory(story));
            
            libraryList.appendChild(card);
        });
    }

    function loadStory(story) {
        // Show loading state if needed
        headerTitle.textContent = "Loading...";
        
        fetch(story.filename)
            .then(res => res.json())
            .then(data => {
                renderStory(data.title, data.content);
                // Switch View
                libraryView.classList.add('hidden');
                readerView.classList.remove('hidden');
                
                // Update Header
                headerTitle.textContent = data.title;
                backBtn.classList.remove('hidden');
                toggleBtn.classList.remove('hidden');
                
                // Reset scroll
                window.scrollTo(0, 0);
            })
            .catch(err => {
                console.error('Error loading story:', err);
                alert('Failed to load story.');
                headerTitle.textContent = "Yomu Library";
            });
    }

    function renderStory(title, content) {
        readerContent.innerHTML = '';
        const fragment = document.createDocumentFragment();

        content.forEach(lineTokens => {
            const p = document.createElement('p');
            
            lineTokens.forEach(token => {
                const span = document.createElement('span');
                span.className = 'word';
                span.dataset.surface = token.s;
                span.dataset.reading = token.r || '';
                
                if (token.r) {
                    const ruby = document.createElement('ruby');
                    ruby.textContent = token.s;
                    const rt = document.createElement('rt');
                    rt.textContent = token.r;
                    ruby.appendChild(rt);
                    span.innerHTML = ''; 
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
            
            fragment.appendChild(p);
        });
        
        readerContent.appendChild(fragment);
    }

    function showDefinition(token) {
        popupWord.textContent = token.s;
        popupReading.textContent = token.r || '';
        
        const meaning = dictionary[token.s];
        if (meaning) {
            popupMeaning.textContent = meaning;
        } else {
            popupMeaning.textContent = `Offline definition not available for "${token.s}".`; 
        }
        
        popup.classList.remove('hidden');
    }

    // Event Listeners
    backBtn.addEventListener('click', showLibrary);

    closePopupBtn.addEventListener('click', () => {
        popup.classList.add('hidden');
    });

    // Close popup when clicking outside
    document.addEventListener('click', (e) => {
        if (!popup.contains(e.target) && !e.target.closest('.word')) {
            popup.classList.add('hidden');
        }
    });

    toggleBtn.addEventListener('click', () => {
        isVertical = !isVertical;
        if (isVertical) {
            readerView.classList.remove('horizontal-text');
            readerView.classList.add('vertical-text');
            toggleBtn.textContent = '⟲'; // Symbol for vertical
        } else {
            readerView.classList.remove('vertical-text');
            readerView.classList.add('horizontal-text');
            toggleBtn.textContent = '⟳'; // Symbol for horizontal
        }
    });
});
