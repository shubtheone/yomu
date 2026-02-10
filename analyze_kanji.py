"""Analyze kanjiapi_full.json structure and assess usability."""
import json

with open('kanjiapi_full.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

report = []

# Top level
report.append(f"Top-level keys: {list(data.keys())}")
report.append("")

# KANJIS
kanjis = data['kanjis']
report.append(f"=== KANJIS: {len(kanjis)} entries ===")
sample_keys = list(kanjis.keys())[:3]
for sk in sample_keys:
    report.append(f"  '{sk}': {json.dumps(kanjis[sk], ensure_ascii=False, indent=2)[:500]}")
report.append("")

# READINGS  
readings = data['readings']
report.append(f"=== READINGS: {len(readings)} entries ===")
sample_keys = list(readings.keys())[:3]
for sk in sample_keys:
    val = readings[sk]
    report.append(f"  '{sk}': {json.dumps(val, ensure_ascii=False)[:500]}")
report.append("")

# WORDS
words = data['words']
report.append(f"=== WORDS: {len(words)} entries ===")
sample_keys = list(words.keys())[:5]
for sk in sample_keys:
    val = words[sk]
    if isinstance(val, list):
        report.append(f"  '{sk}': list[{len(val)}] = {json.dumps(val[:2], ensure_ascii=False, indent=2)[:600]}")
    else:
        report.append(f"  '{sk}': {json.dumps(val, ensure_ascii=False)[:500]}")

report.append("")

# Size analysis
kanji_size = len(json.dumps(data['kanjis'], ensure_ascii=False))
readings_size = len(json.dumps(data['readings'], ensure_ascii=False))
words_size = len(json.dumps(data['words'], ensure_ascii=False))
report.append(f"=== SIZE BREAKDOWN ===")
report.append(f"  kanjis:   {kanji_size / 1024 / 1024:.2f} MB")
report.append(f"  readings: {readings_size / 1024 / 1024:.2f} MB")
report.append(f"  words:    {words_size / 1024 / 1024:.2f} MB")
report.append(f"  total:    {(kanji_size + readings_size + words_size) / 1024 / 1024:.2f} MB")

with open('kanji_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))
print("Analysis written to kanji_analysis.txt")
