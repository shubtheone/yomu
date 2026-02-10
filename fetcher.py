import requests
from bs4 import BeautifulSoup
from janome.tokenizer import Tokenizer
import json
import re
import os

# Ensure output directory exists
OUTPUT_DIR = "projects/yomu-pwa"

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
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
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
            # Fallback for newer Aozora layout or different class
            content_div = soup.select_one('#main_text')
            
        if not content_div:
            print(f"Could not find content div (.main_text) for {url}")
            return None

        for rt in content_div.find_all('rt'):
            rt.decompose()
        for rp in content_div.find_all('rp'):
            rp.decompose()
            
        return title, clean_text(content_div.get_text())
    except Exception as e:
        print(f"Error fetching Aozora story: {e}")
        return None

def fetch_syosetu(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Cookie': 'over18=yes; sas_c=1'
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
             print(f"Error: {response.status_code} fetching {url}")
             return None
             
        response.encoding = 'utf-8' 
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Debug: Print title to see if we got the page
        title_debug = soup.title.string if soup.title else 'No Title'
        print(f"DEBUG: Page Title: {title_debug}")
        
        title_elem = soup.select_one('.novel_subtitle') 
        if not title_elem:
            title_elem = soup.select_one('title')
        
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
        
        content_div = soup.select_one('#novel_honbun')
        if not content_div:
            content_div = soup.select_one('#honbun')
        
        if not content_div:
            # Fallback: Find the div with the most text characters
            divs = soup.find_all('div')
            if divs:
                content_div = max(divs, key=lambda d: len(d.get_text()))
                if len(content_div.get_text()) < 200: # Threshold
                    print("Found largest div but text too short.")
                    content_div = None

        if not content_div:
            print(f"Could not find content div (#novel_honbun) for {url}")
            return None
            
        return title, clean_text(content_div.get_text())
    except Exception as e:
        print(f"Error fetching Syosetu story: {e}")
        return None

def process_text(lines):
    t = Tokenizer()
    processed_story = []
    
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
                
                token_info = {
                    "s": surface,
                    "r": reading_hira if has_kanji else "", 
                }
                tokens_data.append(token_info)
        except Exception as e:
            # Fallback for tokenizer errors on specific lines
            print(f"Tokenizer error on line: {line[:20]}... {e}")
            tokens_data.append({"s": line, "r": ""})
            
        processed_story.append(tokens_data)
        
    return processed_story

def save_story(filename, title, content):
    output = {
        "title": title,
        "content": content
    }
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=None)
    print(f"Saved {title} to {path}")

def main():
    stories = [
        {
            "type": "aozora",
            "url": "https://www.aozora.gr.jp/cards/000879/files/127_15260.html",
            "filename": "rashomon.json",
            "id": "rashomon",
            "summary_ja": "下人が羅生門の下で雨やみを待っていた。彼は生きるために悪を選ぶ老婆を見て、自らも悪に染まる決意をする。",
            "summary_en": "A servant waits under the Rashomon gate. Witnessing an old woman doing evil to survive, he decides to embrace evil himself."
        },
        {
            "type": "syosetu",
            "url": "https://ncode.syosetu.com/n2267be/1/", # Re:Zero
            "filename": "isekai_rezero.json",
            "id": "isekai_rezero",
            "summary_ja": "コンビニ帰りに異世界へ召喚された少年、ナツキ・スバル。彼の過酷な運命がここから始まる。",
            "summary_en": "Subaru Natsuki, a boy summoned to another world on his way back from a convenience store. His harsh fate begins here."
        },
        {
            "type": "syosetu",
            "url": "https://ncode.syosetu.com/n9669bk/1/", # Mushoku Tensei
            "filename": "isekai_mushoku.json",
            "id": "isekai_mushoku",
            "summary_ja": "34歳無職が異世界に転生し、本気で生きることを決意する。剣と魔法の世界での新たな人生。",
            "summary_en": "A 34-year-old unemployed man reincarnates into a fantasy world, determined to live his new life to the fullest."
        },
        {
            "type": "syosetu",
            "url": "https://ncode.syosetu.com/n4830bu/1/", # Ascendance of a Bookworm
            "filename": "isekai_bookworm.json",
            "id": "isekai_bookworm",
            "summary_ja": "本好きの女子大生が異世界の兵士の娘として転生。本がない世界で、自ら本を作る戦いが始まる。",
            "summary_en": "A book-loving student is reborn as a soldier's daughter in a world without books. She begins her battle to create them herself."
        }
    ]

    library = []

    for story in stories:
        print(f"Fetching {story['url']}...")
        if story["type"] == "aozora":
            data = fetch_aozora(story["url"])
        else:
            data = fetch_syosetu(story["url"])
            
        if not data:
            print(f"Failed to fetch {story['filename']}")
            continue

        title, lines = data
        print(f"Processing '{title}' (Lines: {len(lines)})...")
        
        processed_content = process_text(lines)
        save_story(story["filename"], title, processed_content)
        
        # Add to library metadata
        library.append({
            "id": story["id"],
            "title": title,
            "filename": story["filename"],
            "summary_ja": story["summary_ja"],
            "summary_en": story["summary_en"]
        })

    # Save library index
    lib_path = os.path.join(OUTPUT_DIR, "library.json")
    with open(lib_path, "w", encoding="utf-8") as f:
        json.dump(library, f, ensure_ascii=False, indent=2)
    print(f"Library index saved to {lib_path}")

if __name__ == "__main__":
    main()
