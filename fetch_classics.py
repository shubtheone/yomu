"""
Fetch complete short stories from Aozora Bunko for Yomu library.
"""
import requests
from bs4 import BeautifulSoup
from janome.tokenizer import Tokenizer
import json
import re
import os

def katakana_to_hiragana(text):
    if not text: return ""
    return "".join([chr(ord(ch) - 96) if ("\u30a1" <= ch <= "\u30f6") else ch for ch in text])

def clean_text(text):
    if not text: return []
    lines = []
    for line in text.split('\n'):
        cleaned = line.strip()
        if cleaned:
            lines.append(cleaned)
    return lines

def fetch_aozora(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error: {response.status_code} fetching {url}")
            return None

        response.encoding = 'shift_jis'
        soup = BeautifulSoup(response.text, 'html.parser')

        title_elem = soup.select_one('.title')
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

        content_div = soup.select_one('.main_text')
        if not content_div:
            content_div = soup.select_one('#main_text')
        if not content_div:
            print(f"Could not find content div for {url}")
            return None

        for rt in content_div.find_all('rt'):
            rt.decompose()
        for rp in content_div.find_all('rp'):
            rp.decompose()

        return title, clean_text(content_div.get_text())
    except Exception as e:
        print(f"Error fetching: {e}")
        return None

def process_text(lines):
    t = Tokenizer()
    processed = []

    for line in lines:
        if not line.strip():
            continue
        tokens_data = []
        try:
            for token in t.tokenize(line):
                surface = token.surface
                reading = token.reading
                reading_hira = katakana_to_hiragana(reading) if reading != '*' else ""
                has_kanji = any('\u4e00' <= char <= '\u9fff' for char in surface)
                tokens_data.append({
                    "s": surface,
                    "r": reading_hira if has_kanji else "",
                })
        except Exception as e:
            print(f"Tokenizer error: {e}")
            tokens_data.append({"s": line, "r": ""})
        processed.append(tokens_data)

    return processed

def save_story(filename, title, content):
    output = {"title": title, "content": content}
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=None)
    print(f"  -> Saved {filename} ({len(content)} paragraphs)")

def main():
    stories = [
        {
            "url": "https://www.aozora.gr.jp/cards/000879/files/92_14545.html",
            "filename": "kumo_no_ito.json",
            "expected_title": "蜘蛛の糸"
        },
        {
            "url": "https://www.aozora.gr.jp/cards/000035/files/1567_14913.html",
            "filename": "hashire_melos.json",
            "expected_title": "走れメロス"
        },
        {
            "url": "https://www.aozora.gr.jp/cards/000081/files/43754_17659.html",
            "filename": "chumon.json",
            "expected_title": "注文の多い料理店"
        },
    ]

    for story in stories:
        if os.path.exists(story["filename"]):
            print(f"Skipping {story['filename']} (already exists)")
            continue

        print(f"Fetching {story['expected_title']}...")
        data = fetch_aozora(story["url"])
        if not data:
            print(f"  -> FAILED to fetch {story['expected_title']}")
            continue

        title, lines = data
        print(f"  -> Got '{title}' ({len(lines)} lines)")
        processed = process_text(lines)
        save_story(story["filename"], title, processed)

    print("\nDone! Don't forget to update library.json and sw.js.")

if __name__ == "__main__":
    main()
