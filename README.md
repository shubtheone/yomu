# 読む Yomu — Japanese Reader PWA

An offline-first Japanese reading web app with furigana, built-in dictionary, flashcards (SRS), and grammar reference.

## Features

- 📖 **Japanese text reader** with vertical (tategaki) and horizontal modes
- 🔤 **Furigana** — auto-generated readings above kanji
- 📚 **Built-in dictionary** — tap any word for its definition
- 🃏 **Flashcard system** with SRS (spaced repetition) for vocabulary review
- 📝 **Grammar reference** — common Japanese grammar patterns
- 🌐 **Instant Translation** — translate any paragraph with a single click
- 🌙 **Dark / Light themes** — proper Japanese typography (Yu Mincho)
- 📱 **PWA** — installable, works offline after first load

## Quick Start

### 1. Install dependencies

```bash
pip install deep-translator
```

### 2. Run the app

```bash
# Start the server (handles translation API)
python3 server.py
```

Open **http://localhost:8000** in your browser.

### 3. Add stories with the fetcher

The `fetch_story.py` script fetches Japanese stories from [Aozora Bunko](https://www.aozora.gr.jp/) (public domain classics), tokenizes them with [Janome](https://github.com/mocobeta/janome) for furigana, and adds them to the library.

#### Install dependencies

```bash
pip install requests beautifulsoup4 janome
```

#### List available stories

```bash
python3 fetch_story.py --list
```

This shows the built-in catalog of 12 classic Japanese stories with their install status.

#### Add a story from the catalog

```bash
# Add a single story
python3 fetch_story.py --add kokoro

# Add ALL catalog stories at once
python3 fetch_story.py --add-all
```

#### Add from a custom Aozora Bunko URL

```bash
python3 fetch_story.py --aozora "https://www.aozora.gr.jp/cards/000148/files/773_14560.html" \
    --id "kokoro" \
    --title-en "Kokoro" \
    --author "夏目漱石" \
    --author-en "Natsume Soseki"
```

#### Add from a custom Syosetu (Narou) URL

```bash
python3 fetch_story.py --syosetu "https://ncode.syosetu.com/nXXXXXX/1/" \
    --id "my_story" \
    --title-en "My Story" \
    --author "作者名" \
    --author-en "Author Name"
```

## Story Catalog

| Key | Title | Author | Source |
|-----|-------|--------|--------|
| `rashomon` | 羅生門 (Rashomon) | 芥川龍之介 | Aozora |
| `kumo_no_ito` | 蜘蛛の糸 (The Spider's Thread) | 芥川龍之介 | Aozora |
| `hana` | 鼻 (The Nose) | 芥川龍之介 | Aozora |
| `hashire_melos` | 走れメロス (Run, Melos!) | 太宰治 | Aozora |
| `ningen_shikkaku` | 人間失格 (No Longer Human) | 太宰治 | Aozora |
| `chumon` | 注文の多い料理店 (The Restaurant of Many Orders) | 宮沢賢治 | Aozora |
| `gingatetsudo` | 銀河鉄道の夜 (Night on the Galactic Railroad) | 宮沢賢治 | Aozora |
| `yamanashi` | やまなし (Wild Pear) | 宮沢賢治 | Aozora |
| `takasebune` | 高瀬舟 (The Boat on the Takase River) | 森鷗外 | Aozora |
| `yume_juuya` | 夢十夜 (Ten Nights of Dreams) | 夏目漱石 | Aozora |
| `botchan` | 坊っちゃん (Botchan) | 夏目漱石 | Aozora |
| `kokoro` | こころ (Kokoro) | 夏目漱石 | Aozora |

## Project Structure

```
yomu/
├── index.html          # Main app HTML
├── style.css           # Styles (dark/light themes, vertical/horizontal text)
├── app.js              # App logic (reader, flashcards, dictionary, navigation)
├── grammar.css         # Grammar reference styles
├── sw.js               # Service Worker for offline caching
├── manifest.json       # PWA manifest
├── icon.svg            # App icon (SVG source)
├── icon-192.png        # App icon 192x192
├── icon-512.png        # App icon 512x512
├── library.json        # Library index (list of available novels)
├── dict.json           # Japanese-English dictionary
├── grammar.json        # Grammar patterns data
├── fetch_story.py      # Story fetcher (Aozora Bunko / Syosetu)
├── build_dict.py       # Dictionary builder from kanjiapi data
├── *.json              # Story content files (rashomon.json, etc.)
└── README.md
```

## License

Stories from Aozora Bunko are in the public domain in Japan.
