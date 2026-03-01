# Agents

## Cursor Cloud specific instructions

### Overview

Yomu is a static Japanese Reader PWA (Progressive Web App). There is **no build step, no bundler, no package manager, and no Node.js dependency**. The frontend is vanilla HTML/CSS/JS served as static files.

### Running the dev server

Serve the repository root with any static HTTP server:

```
python3 -m http.server 8000
```

Open http://localhost:8000 in a browser. The app loads `library.json`, `dict.json`, `grammar.json`, and story `*.json` files at runtime from the same origin.

### Linting / Testing

There are no configured lint tools or automated test suites in this project. Code quality is validated by manual browser testing.

### Python utilities (optional)

- `server.py` — Legacy HTTP server with `/api/translate` endpoint (requires `pip install deep-translator`). The static app now uses the client-side MyMemory API instead, so this server is not needed for normal development.
- `fetch_story.py` — CLI to fetch/add stories from Aozora Bunko or Syosetu (requires `pip install requests beautifulsoup4 janome`). Run `python3 fetch_story.py --list` to see available stories.
- `build_dict.py` — Rebuilds `dict.json` from kanjiapi data (requires a `kanjiapi_full.json` file that is gitignored).

### Key gotchas

- The service worker (`sw.js`) uses stale-while-revalidate caching. During development, you may need to hard-refresh or unregister the service worker to see file changes. In Chrome DevTools, check "Bypass for network" under Application > Service Workers.
- All user data (flashcards, reading progress, settings) lives in `localStorage`. There is no database.
- Translation uses the free MyMemory API (`api.mymemory.translated.net`) client-side — no API keys required.
