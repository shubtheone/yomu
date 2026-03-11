#!/usr/bin/env python3
"""
Fetch latest news from NHK News Web Easy and save as JSON in Yomu's token format.

1. Tries NHK's top-list.json + article HTML (works when NHK allows access).
2. If NHK returns 401/403, falls back to NHK Easier RSS (https://nhkeasier.com/feed/)
   which includes full article HTML with ruby in each item — no auth needed.

Requires: pip install requests beautifulsoup4
"""
import html
import json
import os
import re
import sys
import time

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Install dependencies: pip install requests beautifulsoup4")
    sys.exit(1)

BASE_URL = "https://www3.nhk.or.jp/news/easy"
RSS_URL = "https://nhkeasier.com/feed/"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
NEWS_DIR = os.path.join(OUTPUT_DIR, "news")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
    "Accept-Language": "ja,en;q=0.9",
}


def _safe_print(s):
    """Print without UnicodeEncodeError on Windows console."""
    try:
        print(s)
    except UnicodeEncodeError:
        # Fallback: ASCII-safe version (replace non-ASCII)
        print(s.encode("ascii", errors="replace").decode("ascii"))


def html_to_tokens(soup_fragment):
    """Convert HTML fragment (with <ruby>/<rt>) into Yomu token format: list of lines, each line list of {s, r}."""
    lines = []
    # Get all block elements (recursive so we find <p> inside <div> etc.)
    for elem in soup_fragment.find_all(["p", "h1", "h2", "h3"]):
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


def fetch_top_list():
    """Fetch NHK Easy top-list.json (article IDs and titles). Same API as nhk-easy package."""
    try:
        url = f"{BASE_URL}/top-list.json?_={int(time.time())}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        # API returns a list of dicts with news_id, title, news_prearranged_time, etc.
        if isinstance(data, list):
            return data[:30]
        if isinstance(data, dict) and "list" in data:
            return data["list"][:30]
        return []
    except Exception as e:
        print(f"Could not fetch top-list.json: {e}")
        return []


def fetch_from_rss(max_items=25):
    """
    Fallback: fetch articles from NHK Easier RSS. Full HTML with ruby is in each item's description.
    Returns list of dicts: { "id", "title", "content" (token lines), "url" }.
    """
    try:
        r = requests.get(RSS_URL, headers=HEADERS, timeout=20)
        r.encoding = "utf-8"
        r.raise_for_status()
    except Exception as e:
        print(f"Could not fetch RSS: {e}")
        return []

    from xml.etree import ElementTree as ET
    raw = r.text

    # Extract items: use regex to get description from raw XML (handles CDATA and entities reliably)
    item_blocks = re.findall(r"<item[^>]*>(.*?)</item>", raw, re.DOTALL)
    if not item_blocks:
        root = ET.fromstring(raw)
        items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
        item_blocks = [ET.tostring(it, encoding="unicode") for it in items[:max_items]]

    results = []
    for block in item_blocks[:max_items]:
        # Get title and link from block (regex so we don't depend on ET .text)
        title = ""
        m = re.search(r"<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", block, re.DOTALL)
        if m:
            title = html.unescape(m.group(1).strip())
        link = ""
        m = re.search(r"<link[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>", block, re.DOTALL)
        if m:
            link = m.group(1).strip()
        if not link:
            m = re.search(r"<guid[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</guid>", block, re.DOTALL)
            if m:
                link = m.group(1).strip()

        # Get description content (may be CDATA or entity-encoded)
        desc_html = ""
        m = re.search(r"<description[^>]*>(.*?)</description>", block, re.DOTALL)
        if m:
            desc_html = m.group(1).strip()
            if desc_html.startswith("<![CDATA[") and desc_html.endswith("]]>"):
                desc_html = desc_html[9:-3]
            desc_html = html.unescape(desc_html)

        if not desc_html:
            continue
        # Strip img, audio, ul and keep only article paragraphs
        soup = BeautifulSoup(desc_html, "html.parser")
        for tag in soup.find_all(["img", "audio", "ul", "script"]):
            tag.decompose()
        try:
            content = html_to_tokens(soup)
        except Exception as e:
            continue
        if not content or (len(content) == 1 and not content[0]):
            continue
        # Use slug from link (e.g. story/9456 -> 9456) or from title
        slug_base = os.path.basename(link.rstrip("/")) if link else ""
        if not slug_base:
            slug_base = re.sub(r"[^\w\-]", "_", (title or "news")[:30])
        aid = "rss_" + re.sub(r"[^\w\-]", "_", slug_base)[:60]
        results.append({"id": aid, "title": title or "ニュース", "content": content, "url": link or RSS_URL})
    return results


def fetch_article_by_id(news_id):
    """Fetch one article by ID (e.g. k1234567890_12345678). Returns (title, content_tokens) or None."""
    try:
        url = f"{BASE_URL}/{news_id}/{news_id}.html"
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.encoding = "utf-8"
        if r.status_code != 200:
            return None
        # Consent gate: if we get the terms page instead of article
        if "ご利用にあたって" in r.text and "js-article-body" not in r.text:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        body = soup.find("div", id="js-article-body")
        if not body:
            return None
        title_el = soup.find("h1") or soup.find("title")
        title = (title_el.get_text(strip=True) if title_el else "").split("|")[0].strip()
        if not title:
            title = "ニュース"
        content = html_to_tokens(body)
        if not content or (len(content) == 1 and not content[0]):
            return None
        return title, content
    except Exception as e:
        print(f"Error fetching article {news_id}: {e}")
        return None


def main():
    os.makedirs(NEWS_DIR, exist_ok=True)
    top_list = fetch_top_list()
    articles = []

    if top_list:
        # NHK API worked: fetch each article by ID
        for item in top_list:
            news_id = item.get("news_id") or item.get("id") or item.get("newsId")
            title_from_list = (item.get("title") or item.get("title_with_ruby") or "").strip()
            if not news_id:
                continue
            result = fetch_article_by_id(news_id)
            if not result:
                continue
            title, content = result
            if not title_from_list:
                title_from_list = title
            aid = re.sub(r"[^\w\-]", "_", str(news_id))[:80]
            filename = f"news/{aid}.json"
            path = os.path.join(OUTPUT_DIR, filename)
            obj = {"title": title_from_list or title, "content": content}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=None)
            article_url = f"{BASE_URL}/{news_id}/{news_id}.html"
            articles.append({"id": aid, "title": obj["title"], "url": article_url, "filename": filename})
        _safe_print(f"Saved: {(obj['title'])[:50]}... -> {filename}")
        time.sleep(0.3)
    else:
        # Fallback: NHK Easier RSS (full content in feed, no auth)
        print("Using NHK Easier RSS (nhkeasier.com/feed/)...")
        rss_items = fetch_from_rss()
        for item in rss_items:
            aid = item["id"]
            filename = f"news/{aid}.json"
            path = os.path.join(OUTPUT_DIR, filename)
            obj = {"title": item["title"], "content": item["content"]}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=None)
            articles.append({"id": aid, "title": obj["title"], "url": item["url"], "filename": filename})
            _safe_print(f"Saved: {(obj['title'])[:50]}... -> {filename}")

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
