I have successfully built **Yomu-PWA**, an offline-first Japanese reading web app.

### Accomplishments:
1.  **Content Source (`fetcher.py`)**:
    - Created a Python script that scrapes *Rashomon* by Akutagawa Ryunosuke from **Aozora Bunko**.
    - It handles Shift_JIS encoding, strips existing ruby tags, and uses **Janome** to re-tokenize and generate fresh Furigana (readings) for Kanji.
    - Output is saved to `story.json`.

2.  **Frontend (PWA)**:
    - **`index.html`**: A clean reader interface.
    - **`style.css`**: Supports **Vertical Text** (Tategaki) by default, with a toggle for Horizontal. Uses proper Japanese typography (`Yu Mincho`, etc.).
    - **`app.js`**:
        - Loads `story.json` and renders text with `<ruby>` tags for Furigana.
        - Implements "tap word to see meaning" functionality.
        - Includes a toggle for Vertical/Horizontal reading modes.
        - Fetches a small embedded dictionary (`dict.json`) for demonstration (definitions for words like "Rashomon", "rain", "sun").
    - **`sw.js`**: A Service Worker that caches all assets (`index.html`, `style.css`, `app.js`, `story.json`, `dict.json`) for **Offline Use**.
    - **`manifest.json`**: Metadata to make the app installable.

3.  **Dictionary**:
    - Created `dict.json` with sample definitions to demonstrate the lookup feature.

### How to Run:
1.  Navigate to the project directory:
    ```bash
    cd projects/yomu-pwa
    ```
2.  Start a local server (needed for Service Worker and Fetch API):
    ```bash
    python3 -m http.server
    ```
3.  Open your browser to:
    `http://localhost:8000`

The app is ready to use and will work offline after the first load!
# yomu
