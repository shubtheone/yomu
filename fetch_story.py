#!/usr/bin/env python3
"""
Yomu Story Fetcher
==================
Fetch Japanese stories from Aozora Bunko and Syosetu (Narou),
tokenize them with Janome for furigana readings, and add them
to the Yomu library.

Usage:
    # List available pre-configured stories
    python fetch_story.py --list

    # Fetch a story by its catalog key
    python fetch_story.py --add rashomon
    python fetch_story.py --add gingatetsudo

    # Fetch from a custom Aozora Bunko URL
    python fetch_story.py --aozora "https://www.aozora.gr.jp/cards/000081/files/456_15050.html" \\
        --id "gingatetsudo" --title-en "Night on the Galactic Railroad" \\
        --author "宮沢賢治" --author-en "Miyazawa Kenji"

    # Fetch from a custom Syosetu URL
    python fetch_story.py --syosetu "https://ncode.syosetu.com/n2267be/1/" \\
        --id "rezero_ch1" --title-en "Re:Zero Ch1" \\
        --author "長月達平" --author-en "Tappei Nagatsuki"

    # Fetch ALL catalog stories at once
    python fetch_story.py --add-all
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import os
import sys
import argparse
import time

# ─── Janome import (with graceful fallback) ───
try:
    from janome.tokenizer import Tokenizer
    TOKENIZER = Tokenizer()
    HAS_JANOME = True
except ImportError:
    HAS_JANOME = False
    TOKENIZER = None
    print("⚠  Janome not found. Install with: pip install janome")
    print("   Without Janome, furigana readings will not be generated.\n")


# ═══════════════════════════════════════════════
# Story Catalog — ready-to-fetch stories
# ═══════════════════════════════════════════════
CATALOG = {
    # ── Aozora Bunko (public domain classics) ──
    "rashomon": {
        "type": "aozora",
        "url": "https://www.aozora.gr.jp/cards/000879/files/127_15260.html",
        "id": "rashomon",
        "title_en": "Rashomon",
        "author": "芥川龍之介",
        "author_en": "Akutagawa Ryunosuke",
        "summary_ja": "下人が羅生門の下で雨やみを待っていた。彼は生きるために悪を選ぶ老婆を見て、自らも悪に染まる決意をする。",
        "summary_en": "A servant waits under the Rashomon gate. Witnessing an old woman doing evil to survive, he decides to embrace evil himself.",
        "gradient": ["#c0392b", "#8B1A1A", "#2D0A0A"],
        "tags": ["classic", "complete", "short-story", "literary"],
    },
    "kumo_no_ito": {
        "type": "aozora",
        "url": "https://www.aozora.gr.jp/cards/000879/files/92_14545.html",
        "id": "kumo_no_ito",
        "title_en": "The Spider's Thread",
        "author": "芥川龍之介",
        "author_en": "Akutagawa Ryunosuke",
        "summary_ja": "極楽から地獄を覗いた釈迦は、地獄に落ちた大泥棒カンダタに一筋の蜘蛛の糸を下ろす。カンダタは糸を辿り地獄を脱出しようとするが…",
        "summary_en": "Buddha lowers a single spider's thread from Paradise to the great thief Kandata in Hell. As Kandata climbs toward salvation, his selfishness leads to his downfall.",
        "gradient": ["#e8b44a", "#8B4513", "#2d1a08"],
        "tags": ["classic", "complete", "short-story", "moral-tale"],
    },
    "hashire_melos": {
        "type": "aozora",
        "url": "https://www.aozora.gr.jp/cards/000035/files/1567_14913.html",
        "id": "hashire_melos",
        "title_en": "Run, Melos!",
        "author": "太宰治",
        "author_en": "Dazai Osamu",
        "summary_ja": "暴君ディオニスに死刑を宣告されたメロスは、友人を人質にして妹の結婚式へ向かう。約束の三日目、様々な困難を乗り越え走り続けるメロスの姿を描く。",
        "summary_en": "Sentenced to death by the tyrant Dionysius, Melos leaves his friend as hostage and races back for his sister's wedding. A tale of trust, friendship, and perseverance.",
        "gradient": ["#2980b9", "#1B4F72", "#0A1929"],
        "tags": ["classic", "complete", "short-story", "friendship"],
    },
    "chumon": {
        "type": "aozora",
        "url": "https://www.aozora.gr.jp/cards/000081/files/43754_17659.html",
        "id": "chumon",
        "title_en": "The Restaurant of Many Orders",
        "author": "宮沢賢治",
        "author_en": "Miyazawa Kenji",
        "summary_ja": "二人の紳士が山中で「山猫軒」という不思議な料理店に入る。次々と出される奇妙な「注文」に従ううちに、恐ろしい真実に気づく。",
        "summary_en": "Two gentlemen enter a mysterious restaurant called 'Wildcat House' in the mountains. As they follow increasingly bizarre instructions, they discover a terrifying truth.",
        "gradient": ["#27ae60", "#145A32", "#0A2D19"],
        "tags": ["classic", "complete", "short-story", "fantasy", "horror"],
    },
    "gingatetsudo": {
        "type": "aozora",
        "url": "https://www.aozora.gr.jp/cards/000081/files/456_15050.html",
        "id": "gingatetsudo",
        "title_en": "Night on the Galactic Railroad",
        "author": "宮沢賢治",
        "author_en": "Miyazawa Kenji",
        "summary_ja": "少年ジョバンニは友人カムパネルラと銀河を走る不思議な汽車に乗る。幻想的な旅の果てに待つ、悲しい真実とは。",
        "summary_en": "A boy named Giovanni boards a mysterious train traveling across the Milky Way with his friend Campanella. A fantastical journey leading to a sorrowful truth.",
        "gradient": ["#1a1a2e", "#16213e", "#0f3460"],
        "tags": ["classic", "complete", "novella", "fantasy"],
    },
    "ningen_shikkaku": {
        "type": "aozora",
        "url": "https://www.aozora.gr.jp/cards/000035/files/301_14912.html",
        "id": "ningen_shikkaku",
        "title_en": "No Longer Human",
        "author": "太宰治",
        "author_en": "Dazai Osamu",
        "summary_ja": "「恥の多い生涯を送って来ました」——人間の資格がないと感じる男の手記。太宰治の代表作であり、遺作となった自伝的小説。",
        "summary_en": "\"Mine has been a life of much shame.\" — The notebooks of a man who feels disqualified from being human. Dazai's masterpiece and semi-autobiographical final work.",
        "gradient": ["#2c2c34", "#1a1a2e", "#0d0d14"],
        "tags": ["classic", "complete", "novel", "literary", "dark"],
    },
    "takasebune": {
        "type": "aozora",
        "url": "https://www.aozora.gr.jp/cards/000129/files/691_15353.html",
        "id": "takasebune",
        "title_en": "The Boat on the Takase River",
        "author": "森鷗外",
        "author_en": "Mori Ogai",
        "summary_ja": "島流しの罪人を乗せた高瀬舟。護送する同心・庄兵衛は、弟を殺した罪人の穏やかな表情に疑問を抱く。安楽死と知足の問題を問う短編。",
        "summary_en": "A boat on the Takase River carries a convict sentenced to exile. The escorting officer is puzzled by the convict's serene expression. A story exploring euthanasia and contentment.",
        "gradient": ["#3a6186", "#89253e", "#1a0a14"],
        "tags": ["classic", "complete", "short-story", "philosophical"],
    },
    "yamanashi": {
        "type": "aozora",
        "url": "https://www.aozora.gr.jp/cards/000081/files/46605_31178.html",
        "id": "yamanashi",
        "title_en": "Wild Pear",
        "author": "宮沢賢治",
        "author_en": "Miyazawa Kenji",
        "summary_ja": "川底に住む蟹の兄弟の視点から、五月と十二月の二つの場面を描く。「クラムボンはかぷかぷわらったよ」という独特の表現で知られる童話。",
        "summary_en": "Two scenes — May and December — as seen by crab brothers living at the bottom of a stream. Famous for its unique expression 'Crambon laughed kap-kap.'",
        "gradient": ["#56ab2f", "#a8e063", "#1a3a0a"],
        "tags": ["classic", "complete", "short-story", "nature"],
    },
    "hana": {
        "type": "aozora",
        "url": "https://www.aozora.gr.jp/cards/000879/files/42_15228.html",
        "id": "hana",
        "title_en": "The Nose",
        "author": "芥川龍之介",
        "author_en": "Akutagawa Ryunosuke",
        "summary_ja": "長い鼻を持つ内供の鼻が、ある方法で短くなる。しかし周囲の反応は変わらず、彼は再び鼻が長くなることを願う。",
        "summary_en": "A monk with an extraordinarily long nose manages to shorten it, but finds the world's reaction just as unkind — and wishes it would grow back.",
        "gradient": ["#e74c3c", "#d35400", "#2d0a0a"],
        "tags": ["classic", "complete", "short-story", "satire"],
    },
    "yume_juuya": {
        "type": "aozora",
        "url": "https://www.aozora.gr.jp/cards/000148/files/799_14972.html",
        "id": "yume_juuya",
        "title_en": "Ten Nights of Dreams",
        "author": "夏目漱石",
        "author_en": "Natsume Soseki",
        "summary_ja": "「こんな夢を見た」で始まる十の夢。漱石が描く幻想的で不思議な夢の世界。怪談的な雰囲気を持つ連作短編。",
        "summary_en": "Ten dreams, each beginning with 'I had this dream.' Soseki's fantastical, eerie dreamscapes — a collection of surreal short tales.",
        "gradient": ["#6c5ce7", "#a29bfe", "#1a0a28"],
        "tags": ["classic", "complete", "short-story", "surreal"],
    },
    "botchan": {
        "type": "aozora",
        "url": "https://www.aozora.gr.jp/cards/000148/files/752_14964.html",
        "id": "botchan",
        "title_en": "Botchan",
        "author": "夏目漱石",
        "author_en": "Natsume Soseki",
        "summary_ja": "無鉄砲な主人公「坊っちゃん」が、四国の中学校の数学教師として赴任する。個性豊かな同僚たちとの騒動を描くユーモア小説。",
        "summary_en": "The reckless young 'Botchan' takes a math teaching job at a middle school in Shikoku. A humorous novel about clashes with colorful colleagues.",
        "gradient": ["#f39c12", "#e67e22", "#2d1a08"],
        "tags": ["classic", "complete", "novel", "humor"],
    },
    "kokoro": {
        "type": "aozora",
        "url": "https://www.aozora.gr.jp/cards/000148/files/773_14560.html",
        "id": "kokoro",
        "title_en": "Kokoro",
        "author": "夏目漱石",
        "author_en": "Natsume Soseki",
        "summary_ja": "「先生」と呼ぶ謎めいた男との出会い。先生の遺書に綴られた過去の秘密。人間の孤独と罪を描く漱石の代表作。",
        "summary_en": "A young man befriends a mysterious man he calls 'Sensei.' Sensei's testament reveals secrets of guilt and loneliness. Soseki's masterpiece on human isolation.",
        "gradient": ["#2c3e50", "#34495e", "#1a252f"],
        "tags": ["classic", "complete", "novel", "literary", "psychological"],
    },
}


# ═══════════════════════════════════════════════
# Text Processing Utilities
# ═══════════════════════════════════════════════

def katakana_to_hiragana(text):
    """Convert katakana to hiragana."""
    if not text:
        return ""
    return "".join(
        chr(ord(ch) - 96) if ("\u30a1" <= ch <= "\u30f6") else ch
        for ch in text
    )


def clean_text(raw_text):
    """Split raw text into non-empty lines."""
    lines = []
    for line in raw_text.split("\n"):
        cleaned = line.strip()
        if cleaned:
            lines.append(cleaned)
    return lines


def tokenize_lines(lines):
    """Tokenize lines with Janome, producing [{s, r}, ...] per line."""
    if not HAS_JANOME:
        # Fallback: no furigana
        return [
            [{"s": line, "r": ""}]
            for line in lines
        ]

    processed = []
    for line in lines:
        if not line.strip():
            continue
        tokens_data = []
        try:
            for token in TOKENIZER.tokenize(line):
                surface = token.surface
                reading = token.reading
                reading_hira = (
                    katakana_to_hiragana(reading)
                    if reading and reading != "*"
                    else ""
                )
                has_kanji = any("\u4e00" <= ch <= "\u9fff" for ch in surface)
                tokens_data.append({
                    "s": surface,
                    "r": reading_hira if has_kanji else "",
                })
        except Exception as e:
            print(f"  ⚠ Tokenizer error on line: {line[:30]}... ({e})")
            tokens_data.append({"s": line, "r": ""})
        processed.append(tokens_data)
    return processed


# ═══════════════════════════════════════════════
# Fetchers
# ═══════════════════════════════════════════════

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_aozora(url):
    """
    Fetch a story from Aozora Bunko.
    Returns (title, [lines]) or None on failure.
    """
    print(f"  📖 Fetching from Aozora Bunko: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            print(f"  ✗ HTTP {resp.status_code}")
            return None

        # Aozora uses Shift_JIS encoding
        resp.encoding = "shift_jis"
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract title
        title_el = soup.select_one(".title")
        title = title_el.get_text(strip=True) if title_el else "Unknown Title"

        # Extract main text
        content_div = soup.select_one(".main_text") or soup.select_one("#main_text")
        if not content_div:
            print("  ✗ Could not find .main_text or #main_text")
            return None

        # Remove existing ruby annotations (we'll regenerate with Janome)
        for tag in content_div.find_all(["rt", "rp"]):
            tag.decompose()

        lines = clean_text(content_div.get_text())
        print(f"  ✓ Got '{title}' — {len(lines)} lines")
        return title, lines

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None


def fetch_syosetu(url):
    """
    Fetch a chapter from Syosetu (Narou / ncode.syosetu.com).
    Returns (title, [lines]) or None on failure.
    """
    print(f"  📖 Fetching from Syosetu: {url}")

    headers = {
        **HEADERS,
        "Cookie": "over18=yes",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code != 200:
            print(f"  ✗ HTTP {resp.status_code}")
            return None

        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        # ── Title ──
        # Try multiple selectors used by different Syosetu layouts
        title_el = (
            soup.select_one(".novel_subtitle")        # chapter subtitle
            or soup.select_one(".p-novel__subtitle")   # newer layout
            or soup.select_one("h1.p-novel__title")    # novel title
        )
        title = title_el.get_text(strip=True) if title_el else "Unknown Title"

        # ── Content ──
        # Try selectors from both old and new Syosetu layouts
        content_div = (
            soup.select_one("#novel_honbun")            # old layout
            or soup.select_one(".p-novel__body")        # newer layout
            or soup.select_one("#honbun")               # alternative
        )

        if not content_div:
            print("  ✗ Could not find story content (#novel_honbun / .p-novel__body)")
            print("  ✗ The page structure may have changed. Try viewing the page source.")
            return None

        # Extract text from each paragraph
        paragraphs = content_div.find_all("p")
        if paragraphs:
            lines = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text:
                    lines.append(text)
        else:
            lines = clean_text(content_div.get_text())

        # Sanity check — if we got very few lines or mostly short ones,
        # we probably scraped junk
        if len(lines) < 3:
            print(f"  ✗ Only got {len(lines)} lines — likely a parsing failure.")
            return None

        avg_len = sum(len(l) for l in lines) / max(len(lines), 1)
        if avg_len < 5:
            print(f"  ✗ Average line length is {avg_len:.1f} chars — likely UI junk, not story text.")
            return None

        print(f"  ✓ Got '{title}' — {len(lines)} lines")
        return title, lines

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None


# ═══════════════════════════════════════════════
# Library Management
# ═══════════════════════════════════════════════

LIBRARY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.json")


def load_library():
    """Load the current library.json."""
    if os.path.exists(LIBRARY_PATH):
        with open(LIBRARY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_library(library):
    """Save library.json."""
    with open(LIBRARY_PATH, "w", encoding="utf-8") as f:
        json.dump(library, f, ensure_ascii=False, indent=2)
    print(f"  💾 Library saved ({len(library)} novels)")


def add_to_library(library, entry):
    """Add or update a library entry."""
    # Check if already exists
    for i, item in enumerate(library):
        if item["id"] == entry["id"]:
            library[i] = entry
            print(f"  ↻ Updated existing entry: {entry['id']}")
            return library

    library.append(entry)
    print(f"  + Added new entry: {entry['id']}")
    return library


def save_story_json(story_id, title, content):
    """Save the processed story to a JSON file."""
    filename = f"{story_id}.json"
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

    output = {
        "title": title,
        "content": content,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False)

    size_kb = os.path.getsize(filepath) / 1024
    print(f"  💾 Saved {filename} ({size_kb:.1f} KB, {len(content)} paragraphs)")
    return filename


def save_cover_image(story_id, cover_src):
    """
    Save a cover image to the covers/ directory.
    cover_src can be a local file path or a URL.
    Returns the relative path (e.g. 'covers/rashomon.jpg') or empty string on failure.
    """
    import shutil

    base_dir = os.path.dirname(os.path.abspath(__file__))
    covers_dir = os.path.join(base_dir, "covers")
    os.makedirs(covers_dir, exist_ok=True)

    # Determine file extension
    ext = os.path.splitext(cover_src)[-1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        ext = ".jpg"

    dest_filename = f"{story_id}{ext}"
    dest_path = os.path.join(covers_dir, dest_filename)

    if cover_src.startswith("http://") or cover_src.startswith("https://"):
        # Download from URL
        try:
            print(f"  🖼  Downloading cover image from {cover_src}...")
            resp = requests.get(cover_src, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                with open(dest_path, "wb") as f:
                    f.write(resp.content)
                size_kb = os.path.getsize(dest_path) / 1024
                print(f"  ✓ Cover saved: covers/{dest_filename} ({size_kb:.1f} KB)")
                return f"covers/{dest_filename}"
            else:
                print(f"  ⚠ Failed to download cover: HTTP {resp.status_code}")
                return ""
        except Exception as e:
            print(f"  ⚠ Error downloading cover: {e}")
            return ""
    else:
        # Local file — copy it
        if os.path.exists(cover_src):
            try:
                shutil.copy2(cover_src, dest_path)
                size_kb = os.path.getsize(dest_path) / 1024
                print(f"  ✓ Cover copied: covers/{dest_filename} ({size_kb:.1f} KB)")
                return f"covers/{dest_filename}"
            except Exception as e:
                print(f"  ⚠ Error copying cover: {e}")
                return ""
        else:
            print(f"  ⚠ Cover file not found: {cover_src}")
            return ""


# ═══════════════════════════════════════════════
# Main Fetch & Add Logic
# ═══════════════════════════════════════════════

def fetch_and_add(story_config):
    """
    Fetch a story based on config, tokenize it, save the JSON,
    and update library.json.
    """
    story_type = story_config["type"]
    url = story_config["url"]
    story_id = story_config["id"]

    print(f"\n{'─' * 50}")
    print(f"📚 Fetching: {story_id}")
    print(f"{'─' * 50}")

    # Fetch
    if story_type == "aozora":
        result = fetch_aozora(url)
    elif story_type == "syosetu":
        result = fetch_syosetu(url)
    else:
        print(f"  ✗ Unknown source type: {story_type}")
        return False

    if not result:
        print(f"  ✗ Failed to fetch {story_id}")
        return False

    title, lines = result

    # Tokenize
    print(f"  ⚙ Tokenizing {len(lines)} lines...")
    processed = tokenize_lines(lines)
    print(f"  ✓ Tokenized into {len(processed)} paragraphs")

    # Save story JSON
    filename = save_story_json(story_id, title, processed)

    # Handle cover image
    cover_image_path = ""
    cover_src = story_config.get("cover_image", "")
    if cover_src:
        cover_image_path = save_cover_image(story_id, cover_src)

    # Build library entry
    entry = {
        "id": story_id,
        "title": title,
        "title_en": story_config.get("title_en", ""),
        "author": story_config.get("author", ""),
        "author_en": story_config.get("author_en", ""),
        "cover_image": cover_image_path,
        "gradient": story_config.get("gradient", ["#667eea", "#764ba2", "#1a0a28"]),
        "summary_ja": story_config.get("summary_ja", ""),
        "summary_en": story_config.get("summary_en", ""),
        "tags": story_config.get("tags", []),
        "chapters": [
            {
                "id": "ch1",
                "title": title,
                "title_en": story_config.get("title_en", title),
                "filename": filename,
            }
        ],
    }

    # Update library
    library = load_library()
    library = add_to_library(library, entry)
    save_library(library)

    print(f"  ✅ Done: {story_id}")
    return True


# ═══════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════

def list_catalog():
    """Print available stories in the catalog."""
    library = load_library()
    existing_ids = {item["id"] for item in library}

    print("\n📚 Available Stories")
    print("=" * 60)

    for key, info in CATALOG.items():
        status = "✓ installed" if info["id"] in existing_ids else "  available"
        source = info["type"].upper()
        title_en = info.get("title_en", "")
        author_en = info.get("author_en", "")
        print(f"  [{status}] {key:<20} {title_en:<35} ({author_en}) [{source}]")

    print(f"\n  Total: {len(CATALOG)} stories in catalog, {len(existing_ids)} installed")
    print(f"\n  Usage: python fetch_story.py --add <key>")
    print(f"         python fetch_story.py --add-all")


def main():
    parser = argparse.ArgumentParser(
        description="Yomu Story Fetcher — fetch Japanese stories for the Yomu reader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fetch_story.py --list                          # List available stories
  python fetch_story.py --add rashomon                  # Fetch a catalog story
  python fetch_story.py --add-all                       # Fetch ALL catalog stories
  python fetch_story.py --aozora URL --id my_story      # Custom Aozora URL
  python fetch_story.py --syosetu URL --id my_story      # Custom Syosetu URL
        """,
    )

    parser.add_argument("--list", action="store_true", help="List available stories in the catalog")
    parser.add_argument("--add", type=str, metavar="KEY", help="Fetch a story from the catalog by key")
    parser.add_argument("--add-all", action="store_true", help="Fetch ALL stories from the catalog")
    parser.add_argument("--aozora", type=str, metavar="URL", help="Fetch from a custom Aozora Bunko URL")
    parser.add_argument("--syosetu", type=str, metavar="URL", help="Fetch from a custom Syosetu (Narou) URL")
    parser.add_argument("--id", type=str, help="Story ID (used for filename and library)")
    parser.add_argument("--title-en", type=str, default="", help="English title")
    parser.add_argument("--author", type=str, default="", help="Author name (Japanese)")
    parser.add_argument("--author-en", type=str, default="", help="Author name (English)")
    parser.add_argument("--summary-ja", type=str, default="", help="Japanese summary")
    parser.add_argument("--summary-en", type=str, default="", help="English summary")
    parser.add_argument("--cover", type=str, default="", help="Cover image path (local file) or URL")

    args = parser.parse_args()

    if args.list:
        list_catalog()
        return

    if args.add:
        key = args.add.lower().strip()
        if key not in CATALOG:
            print(f"✗ Unknown catalog key: '{key}'")
            print(f"  Use --list to see available stories.")
            sys.exit(1)
        success = fetch_and_add(CATALOG[key])
        sys.exit(0 if success else 1)

    if args.add_all:
        print(f"\n🚀 Fetching ALL {len(CATALOG)} stories from catalog...\n")
        results = []
        for key, config in CATALOG.items():
            success = fetch_and_add(config)
            results.append((key, success))
            time.sleep(1)  # Be polite to servers

        print(f"\n{'═' * 50}")
        print(f"Results:")
        for key, success in results:
            status = "✅" if success else "❌"
            print(f"  {status} {key}")
        succeeded = sum(1 for _, s in results if s)
        print(f"\n  {succeeded}/{len(results)} stories fetched successfully")
        return

    if args.aozora or args.syosetu:
        url = args.aozora or args.syosetu
        story_type = "aozora" if args.aozora else "syosetu"

        if not args.id:
            print("✗ --id is required for custom URLs")
            sys.exit(1)

        config = {
            "type": story_type,
            "url": url,
            "id": args.id,
            "title_en": args.title_en,
            "author": args.author,
            "author_en": args.author_en,
            "summary_ja": args.summary_ja,
            "summary_en": args.summary_en,
            "cover_image": args.cover,
            "gradient": ["#667eea", "#764ba2", "#1a0a28"],
            "tags": [story_type],
        }
        success = fetch_and_add(config)
        sys.exit(0 if success else 1)

    # No arguments — show help
    parser.print_help()


if __name__ == "__main__":
    main()
