#!/usr/bin/env python3
import json, random
from pathlib import Path
from tqdm import tqdm

EXPORT_ROOT = YOUR_EXPORT_ROOT
OUT_PATH = YOUR_OUT_PATH
MAX_SAMPLES = 45000


def flatten_text(obj):
    """Recursively flatten nested dicts/lists of strings"""
    if isinstance(obj, str):
        return obj.strip()
    if isinstance(obj, list):
        parts = [flatten_text(item) for item in obj]
        return " ".join(p for p in parts if p)
    if isinstance(obj, dict):
        parts = [flatten_text(v) for v in obj.values()]
        return " ".join(p for p in parts if p)
    return ""


def is_halachic(path_str):
    """Check if path indicates halachic content"""
    path_lower = path_str.lower()
    halachic_paths = [
        "halakhah", "talmud", "mishnah", "responsa",
        "shulchan", "mishneh torah", "tur/", "rishonim",
        "acharonim", "midrash"
    ]
    return any(h in path_lower for h in halachic_paths)


samples = []
stats = {"scanned": 0, "no_text": 0, "not_halachic": 0, "too_short": 0, "success": 0}

print(f"Scanning: {EXPORT_ROOT}")

# Get all JSON files
all_files = list(EXPORT_ROOT.rglob("*.json"))
print(f"Found {len(all_files)} JSON files")

for file_path in tqdm(all_files):
    stats["scanned"] += 1
    path_str = str(file_path)

    # Skip non-halachic paths
    if not is_halachic(path_str):
        stats["not_halachic"] += 1
        continue

    try:
        data = json.load(open(file_path, "r", encoding="utf-8"))

        # Get the text content
        text_content = data.get("text")
        if not text_content:
            stats["no_text"] += 1
            continue

        # Flatten the nested structure
        flat_text = flatten_text(text_content)

        if len(flat_text) < 100:
            stats["too_short"] += 1
            continue

        stats["success"] += 1

        # Get metadata
        title = data.get("title", file_path.stem)
        language = data.get("language", "he")
        version_title = data.get("versionTitle", "")

        # Determine if Hebrew or English based on path/metadata
        is_hebrew = "Hebrew" in path_str or language == "he"

        if is_hebrew:
            questions = [
                f"מה הדין ב{title}?",
                f"ביאור על {title}",
                f"הסבר את {title}",
            ]
            instruction_prefix = "ענה בעברית הלכתית ברורה ומנומקת. "
        else:
            questions = [
                f"What is the halacha in {title}?",
                f"Explain {title}",
                f"What does {title} teach?",
            ]
            instruction_prefix = "Provide a clear halachic explanation with sources. "

        # Take a chunk of text (not the whole thing)
        text_chunk = flat_text[:2000]

        for q in questions[:random.randint(1, 2)]:
            samples.append({
                "instruction": instruction_prefix + q,
                "input": "",
                "output": f"{text_chunk}\n\nמקור/Source: {title} ({version_title})"
            })

    except Exception as e:
        continue

print(f"\nStats: {stats}")
print(f"Total samples before limit: {len(samples)}")

random.shuffle(samples)
samples = samples[:MAX_SAMPLES]

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    for s in samples:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")

print(f"\nSaved {len(samples):,} samples to {OUT_PATH}")