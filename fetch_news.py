#!/usr/bin/env python3
"""
Fetch latest news from NHK News Web Easy (https://www3.nhk.or.jp/news/easy/)
and save as JSON in the same format as Yomu chapter content (tokenized with furigana).
Run daily (e.g. via cron) to refresh news. Requires: pip install requests beautifulsoup4
"""
import json
import os
import re
import sys
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Install dependencies: pip install requests beautifulsoup4")
    sys.exit(1)

BASE_URL = "https://www3.nhk.or.jp/news/easy/"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
NEWS_DIR = os.path.join(OUTPUT_DIR, "news")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en;q=0.9",
}


def html_to_tokens(soup_fragment):
    """Convert HTML fragment (with <ruby>/<rt>) into Yomu token format: list of lines, each line list of {s, r}."""
    lines = []
    # Get all block elements or wrap in one
    for elem in soup_fragment.find_all(["p", "h1", "h2", "h3"], recursive=False):
        line_tokens = _element_to_tokens(elem)
        if line_tokens:
            lines.append(line_tokens)
    # If no block elements, treat whole as one paragraph
    if not lines:
        line_tokens = _element_to_tokens(soup_fragment)
        if line_tokens:
            lines.append(line_tokens)
    return lines if lines else [[]]


def _element_to_tokens(elem):
    tokens = []
    for child in elem.descendants:
        if child.name == "ruby":
            base_parts = []
            for c in child.children:
                if getattr(c, "name", None) == "rt":
                    continue
                base_parts.append(c.get_text() if hasattr(c, "get_text") else str(c))
            base = "".join(base_parts).strip()
            rt = child.find("rt")
            reading = (rt.get_text(strip=True) if rt else "") or ""
            if base:
                tokens.append({"s": base, "r": reading})
        elif child.name == "rt":
            continue
        elif child.name is None and child.string and not child.find_parent("rt"):
            for part in re.split(r"(\s+)", child.string):
                if part:
                    tokens.append({"s": part, "r": ""})
    return tokens


def fetch_main_page():
    """Fetch NHK Easy top page and return list of article URLs."""
    try:
        r = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            full = urljoin(BASE_URL, href)
            if "/news/easy/article/" in full and full.endswith(".html"):
                if full not in links:
                    links.append(full)
        return links[:30]  # limit
    except Exception as e:
        print(f"Could not fetch main page: {e}")
        return []


def fetch_article(url):
    """Fetch one article page and return (title, content_tokens) or None."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        # Consent gate: page may show ご利用にあたって
        if "ご利用にあたって" in r.text and "article" not in url:
            return None
        # Find article body – NHK Easy uses different containers
        body = (
            soup.find("div", class_=re.compile(r"article|content|body|main", re.I))
            or soup.find("article")
            or soup.find("div", id=re.compile(r"content|article|main", re.I))
        )
        if not body:
            # Fallback: get all paragraphs
            body = soup
        title_el = soup.find("h1") or soup.find("title")
        title = (title_el.get_text(strip=True) if title_el else "").split("|")[0].strip()
        if not title:
            title = "ニュース"
        content = html_to_tokens(body)
        if not content or (len(content) == 1 and not content[0]):
            return None
        return title, content
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def slug_from_url(url):
    base = urlparse(url).path
    return re.sub(r"[^\w\-]", "_", os.path.splitext(os.path.basename(base))[0])[:80]


def main():
    os.makedirs(NEWS_DIR, exist_ok=True)
    urls = fetch_main_page()
    articles = []
    for url in urls:
        result = fetch_article(url)
        if not result:
            continue
        title, content = result
        aid = slug_from_url(url)
        filename = f"news/{aid}.json"
        path = os.path.join(OUTPUT_DIR, filename)
        obj = {"title": title, "content": content}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=None)
        articles.append({"id": aid, "title": title, "url": url, "filename": filename})
        print(f"Saved: {title[:50]}... -> {filename}")

    if not articles:
        # Sample article so the news view is never empty
        sample_id = "sample_easy_news"
        sample_file = os.path.join(NEWS_DIR, f"{sample_id}.json")
        sample = {
            "title": "やさしい日本語のニュース",
            "content": [
                [{"s": "「NHK", "r": ""}, {"s": "やさしい", "r": "やさしい"}, {"s": "ことば", "r": "ことば"}, {"s": "ニュース」は、", "r": ""}],
                [{"s": "日本", "r": "にほん"}, {"s": "に", "r": ""}, {"s": "住んで", "r": "すんで"}, {"s": "いる", "r": ""}, {"s": "外国人", "r": "がいこくじん"}, {"s": "の", "r": ""}, {"s": "皆さん", "r": "みなさん"}, {"s": "や、", "r": ""}],
                [{"s": "子どもたち", "r": "こどもたち"}, {"s": "に、", "r": ""}, {"s": "できるだけ", "r": ""}, {"s": "やさしい", "r": "やさしい"}, {"s": "日本語", "r": "にほんご"}, {"s": "で", "r": ""}, {"s": "ニュース", "r": ""}, {"s": "を", "r": ""}, {"s": "伝える", "r": "つたえる"}, {"s": "サイト", "r": ""}, {"s": "です。", "r": ""}],
            ],
        }
        with open(sample_file, "w", encoding="utf-8") as f:
            json.dump(sample, f, ensure_ascii=False, indent=None)
        articles.append({
            "id": sample_id,
            "title": sample["title"],
            "url": BASE_URL,
            "filename": f"news/{sample_id}.json",
        })
        print("Added sample article (no articles could be fetched). Run from a network that can access NHK for live news.")

    index = {"lastUpdated": __import__("datetime").datetime.utcnow().isoformat() + "Z", "articles": articles}
    index_path = os.path.join(OUTPUT_DIR, "news.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"Wrote {index_path} with {len(articles)} articles.")


if __name__ == "__main__":
    main()
