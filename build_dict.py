"""
Build an optimized dictionary from kanjiapi_full.json for Yomu.
Only extracts words/kanji relevant to our story files + common vocabulary.
"""
import json
import os
import glob
import re

def load_story_words(story_files):
    """Extract all unique surface forms from story files."""
    words = set()
    kanji_chars = set()

    for filepath in story_files:
        if not os.path.exists(filepath):
            continue
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for line in data.get('content', []):
                for token in line:
                    surface = token.get('s', '')
                    reading = token.get('r', '')
                    if surface:
                        words.add(surface)
                    if reading:
                        words.add(reading)
                    # Collect individual kanji chars
                    for ch in surface:
                        if '\u4e00' <= ch <= '\u9fff':
                            kanji_chars.add(ch)
        except Exception as e:
            print(f"  Error reading {filepath}: {e}")

    return words, kanji_chars

def build_dict(kanjiapi_path, story_words, story_kanji, existing_dict):
    """Build optimized dictionary from kanjiapi data."""
    print(f"Loading {kanjiapi_path}...")
    with open(kanjiapi_path, 'r', encoding='utf-8') as f:
        api = json.load(f)

    new_dict = dict(existing_dict)  # Start with existing entries
    stats = {"kanji_added": 0, "word_added": 0, "skipped": 0}

    # 1. Add kanji character definitions
    print("Processing kanji characters...")
    kanjis = api.get('kanjis', {})
    for kanji_char in story_kanji:
        if kanji_char in new_dict:
            continue  # Already defined
        if kanji_char in kanjis:
            k = kanjis[kanji_char]
            meanings = k.get('meanings', [])
            kun = k.get('kun_readings', [])
            on = k.get('on_readings', [])
            if not meanings:
                continue

            # Build definition string
            parts = []
            if kun:
                parts.append(f"Kun: {', '.join(kun[:3])}")
            if on:
                parts.append(f"On: {', '.join(on[:3])}")
            parts.append('; '.join(meanings[:5]))

            jlpt = k.get('jlpt')
            grade = k.get('grade')
            if jlpt:
                parts.append(f"JLPT N{jlpt}")
            if grade:
                parts.append(f"Grade {grade}")

            new_dict[kanji_char] = ' | '.join(parts)
            stats['kanji_added'] += 1

    # 2. Add word definitions from words section
    print("Processing words...")
    words_data = api.get('words', {})
    for kanji_key, word_list in words_data.items():
        if not word_list:
            continue

        for word_entry in word_list:
            variants = word_entry.get('variants', [])
            meanings_data = word_entry.get('meanings', [])

            if not meanings_data:
                continue

            # Collect all glosses
            all_glosses = []
            for m in meanings_data:
                all_glosses.extend(m.get('glosses', []))

            if not all_glosses:
                continue

            # Check each variant
            for variant in variants:
                written = variant.get('written', '')
                pronounced = variant.get('pronounced', '')

                # Only add if this word appears in our stories
                if written not in story_words and pronounced not in story_words:
                    stats['skipped'] += 1
                    continue

                # Skip if already in dict
                if written in new_dict:
                    continue

                # Build definition
                reading_part = f"{pronounced}: " if pronounced and pronounced != written else ""
                meaning_str = '; '.join(all_glosses[:5])
                definition = f"{reading_part}{meaning_str}"

                new_dict[written] = definition
                stats['word_added'] += 1

    print(f"\nStats:")
    print(f"  Kanji chars added: {stats['kanji_added']}")
    print(f"  Words added: {stats['word_added']}")
    print(f"  Words skipped (not in stories): {stats['skipped']}")
    print(f"  Total dict entries: {len(new_dict)}")

    return new_dict


def main():
    # Find all story files
    story_files = glob.glob('*.json')
    story_files = [f for f in story_files if f not in [
        'library.json', 'dict.json', 'manifest.json',
        'kanjiapi_full.json', 'package.json', 'kanji_analysis.txt'
    ]]
    print(f"Story files found: {story_files}")

    # Extract words from stories
    print("Extracting words from stories...")
    story_words, story_kanji = load_story_words(story_files)
    print(f"  Unique surface forms: {len(story_words)}")
    print(f"  Unique kanji chars: {len(story_kanji)}")

    # Load existing dict
    existing = {}
    if os.path.exists('dict.json'):
        with open('dict.json', 'r', encoding='utf-8') as f:
            existing = json.load(f)
        print(f"  Existing dict entries: {len(existing)}")

    # Build optimized dict
    new_dict = build_dict('kanjiapi_full.json', story_words, story_kanji, existing)

    # Save
    with open('dict.json', 'w', encoding='utf-8') as f:
        json.dump(new_dict, f, ensure_ascii=False, indent=4)

    file_size = os.path.getsize('dict.json')
    print(f"\nSaved dict.json: {file_size / 1024:.1f} KB with {len(new_dict)} entries")
    print(f"(Down from {os.path.getsize('kanjiapi_full.json') / 1024 / 1024:.1f} MB original)")

if __name__ == '__main__':
    main()
