import json
import os
import re
import time
import requests
from collections import Counter

# Configuration
STORY_FILES = [
    "rashomon.json",
    "isekai_rezero.json",
    "isekai_mushoku.json",
    "isekai_bookworm.json"
]
DICT_FILE = "dict.json"
JISHO_API_URL = "https://jisho.org/api/v1/search/words?keyword={}"

def load_stories():
    words = []
    for filename in STORY_FILES:
        if not os.path.exists(filename):
            print(f"Warning: {filename} not found.")
            continue
            
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # data structure: {"title": ..., "content": [[{"s": "word", "r": "reading"}, ...], ...]}
            for sentence in data.get("content", []):
                for token in sentence:
                    s = token.get("s", "")
                    if s:
                        words.append(s)
    return words

def filter_words(words):
    # Filter for words with Kanji (likely complex)
    # Using a simple regex for CJK Unified Ideographs
    kanji_pattern = re.compile(r'[\u4e00-\u9faf]')
    
    complex_words = [w for w in words if kanji_pattern.search(w)]
    return complex_words

def fetch_definition(word):
    try:
        response = requests.get(JISHO_API_URL.format(word))
        if response.status_code == 200:
            data = response.json()
            if data["data"]:
                # Extract first definition
                entry = data["data"][0]
                readings = [r.get("reading") for r in entry["japanese"] if "reading" in r]
                reading = readings[0] if readings else ""
                
                senses = entry["senses"]
                definitions = []
                for sense in senses:
                    definitions.extend(sense["english_definitions"])
                
                definition = "; ".join(definitions[:3]) # Take top 3 definitions
                
                if reading:
                    return f"{reading}: {definition}"
                else:
                    return definition
    except Exception as e:
        print(f"Error fetching {word}: {e}")
    return None

def main():
    print("Loading stories...")
    all_words = load_stories()
    print(f"Total words found: {len(all_words)}")
    
    word_counts = Counter(all_words)
    unique_words = list(word_counts.keys())
    print(f"Unique words: {len(unique_words)}")
    
    # Load existing dictionary
    if os.path.exists(DICT_FILE):
        with open(DICT_FILE, 'r', encoding='utf-8') as f:
            current_dict = json.load(f)
    else:
        current_dict = {}
        
    print(f"Current dictionary size: {len(current_dict)}")
    
    # Filter for complex words (Kanji)
    complex_words = filter_words(unique_words)
    print(f"Complex words (with Kanji): {len(complex_words)}")
    
    # Sort by frequency (descending)
    sorted_complex = sorted(complex_words, key=lambda w: word_counts[w], reverse=True)
    
    # Identify missing definitions
    missing_words = [w for w in sorted_complex if w not in current_dict]
    print(f"Missing complex definitions: {len(missing_words)}")
    
    # Fetch top 50 missing words
    to_fetch = missing_words[:50]
    print(f"Fetching definitions for top {len(to_fetch)} missing words...")
    
    count = 0
    for word in to_fetch:
        print(f"Fetching: {word}")
        definition = fetch_definition(word)
        if definition:
            current_dict[word] = definition
            count += 1
            print(f"  -> {definition}")
            
            # Save immediately to preserve progress
            with open(DICT_FILE, 'w', encoding='utf-8') as f:
                json.dump(current_dict, f, ensure_ascii=False, indent=4)
        else:
            print("  -> Not found")
        
        # Be nice to the API
        time.sleep(1.0) # 1.0 second delay
        
    print(f"Added {count} new definitions.")
    print("Dictionary updated.")

if __name__ == "__main__":
    main()
