#!/usr/bin/env python3
"""
Sefaria-Export → High-quality Hebrew halachic instruction dataset
All code/comments in English – training data in Hebrew (perfect)
"""

import argparse
import json
import random
import sys
from pathlib import Path
from tqdm import tqdm


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate Hebrew halachic instruction dataset from local Sefaria-Export"
    )
    parser.add_argument("export_root", type=Path, help="Path to your Sefaria-Export folder")
    parser.add_argument("-o", "--output", type=Path, default=Path("sefaria_halachic_hebrew.jsonl"))
    parser.add_argument("-m", "--max", type=int, default=100_000, help="Max samples to keep")
    parser.add_argument("--seed", type=int, default=4242)
    return parser.parse_args()


def main():
    args = parse_args()
    random.seed(args.seed)

    EXPORT_ROOT = args.export_root.resolve()
    TOC_PATH = EXPORT_ROOT / "table_of_contents.json"

    if not TOC_PATH.exists():
        print(f"Error: table_of_contents.json not found at {TOC_PATH}")
        sys.exit(1)

    print(f"Loading table of contents from {TOC_PATH}")
    with open(TOC_PATH, encoding="utf-8") as f:
        toc = json.load(f)  # list of root nodes

    # Build title → metadata (categories path)
    title_to_meta = {}

    def crawl(node, path=None):
        if path is None:
            path = []
        if node.get("title"):
            path = path + [node["title"]]
        if not node.get("contents"):  # leaf = real text
            if node.get("title"):
                title_to_meta[node["title"]] = {
                    "heTitle": node.get("heTitle", node["title"]),
                    "categories": path[:-1],  # don't include the text title itself
                }
            return
        for child in node.get("contents", []):
            crawl(child, path)
        if node.get("title"):
            path.pop()

    for root in toc:
        crawl(root)

    print(f"Indexed {len(title_to_meta):,} texts")

    # High-priority categories & Hebrew title keywords
    PRIORITY_CATS = {
        "Talmud", "Halakhah", "Mishnah", "Midrash", "Tanakh",
        "Rambam", "Shulchan Aruch", "Tur", "Responsa", "Mishneh Torah",
        "Commentary", "Poskim", "Acharonim", "Rishonim"
    }
    PRIORITY_HEBREW_KEYWORDS = [
        "שולחן ערוך", "משנה ברורה", "רמב״ם", "טור", "חזון איש",
        "אגרות משה", "שו״ת", "פסקי", "הלכות", "רמב״ן", "רש״י", "תוספות"
    ]

    def is_relevant(meta):
        cats = set(meta["categories"])
        he_title = meta["heTitle"]
        return bool(cats & PRIORITY_CATS) or any(kw in he_title for kw in PRIORITY_HEBREW_KEYWORDS)

    samples = []
    for path in tqdm(list((EXPORT_ROOT / "json").rglob("*.json"))):
        try:
            data = json.load(open(path, encoding="utf-8"))
            title = data.get("title")
            if not title or title not in title_to_meta:
                continue

            meta = title_to_meta[title]
            if not is_relevant(meta):
                continue

            # Hebrew text
            hebrew = data.get("he")
            if isinstance(hebrew, list):
                hebrew = " ".join(str(x).strip() for x in hebrew if x)
            if not hebrew or len(hebrew) < 100:
                continue

            # Optional English translation
            english = None
            if data.get("language") == "en" and isinstance(data.get("text"), list):
                english = " ".join(str(x).strip() for x in data["text"] if x)

            ref = data.get("ref", title)

            # Hebrew questions (this is what we want the model to learn)
            questions = [
                f"מה הדין ב{ref}?",
                f"ביאור הלכתי קצר על {ref}",
                f"מה פסק ה{meta['heTitle'].split()[0]} בנושא זה?",
            ]
            if "שולחן ערוך" in meta["heTitle"]:
                siman = ref.split()[-1] if len(ref.split()) > 1 else ""
                questions.append(f"מה פסק השולחן ערוך בסימן {siman}?")

            for q in questions[:random.randint(1, 3)]:
                output = hebrew[:1600]
                if english:
                    output += f"\n\nEnglish translation: {english[:900]}"
                output += f"\n\nSource: {ref}"

                samples.append({
                    "instruction": "Answer in clear, reasoned Hebrew halachic style with precise sources. " + q,
                    "input": "",
                    "output": output.strip()
                })

        except Exception:
            continue

    random.shuffle(samples)
    samples = samples[:args.max]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"\nDone! Generated {len(samples):,} high-quality Hebrew halachic samples")
    print(f"Saved to: {args.output}")
    print("Ready to train the best halachic LLM in existence.")


if __name__ == "__main__":
    main()