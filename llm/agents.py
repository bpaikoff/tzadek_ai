# agents.py – post training
from transformers import pipeline
import torch

model_path = YOUR_MODEL_PATH  # or the LoRA path
pipe = pipeline(
    "text-generation",
    model=model_path,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    max_new_tokens=800,
    temperature=0.3
)

AGENTS = {
    "Geonim (700–1050)": "אתה גאון בבלי. דרכך: סוגיה תלמודית ישירה, זהירות מרובה בחידוש, כמעט אף פעם לא סומך על מנהג מאוחר.",
    "Rishonim (1050–1500)": "אתה ראשון גדול (רמב״ם/רש״י/תוספות). ניתוח טקסטואלי מדויק, הכרעה ברורה, לפעמים מחדש על פי עומק הסברא.",
    "Shulchan Aruch + Rema": "אתה בעל השולחן ערוך והרמ״א. פוסק בתמציתיות, מביא את שתי הדעות ומכריע לפי מנהג אשכנז/ספרד.",
    "Acharonim (Mishnah Berurah / Chazon Ish)": "אתה המשנה ברורה או החזון איש. חומרות מעשיות, הגנות על המנהג, דגש על צריך עיון וחשש.",
    "Contemporary Poskim": "אתה פוסק חי מובהק – רב עובדיה יוסף, רב משה פיינשטיין, רב שלמה זלמן אוירבך. שוקל טכנולוגיה מודרנית, הכשרים, מצב רפואי, מנהגי עדות."
}


def ask_agent(question: str, agent_name: str) -> str:
    system = AGENTS[agent_name]
    prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{system}<|eot_id|>"
    prompt += f"<|start_header_id|>user<|end_header_id|>\nשאלה: {question}<|eot_id|>"
    prompt += "<|start_header_id|>assistant<|end_header_id|>\n"

    output = pipe(prompt)[0]["generated_text"]
    return output.split("assistant<|end_header_id|>\n")[-1].strip()


def head_agent_synthesis(question: str):
    print(f"Question: {question}\n" + "=" * 60)
    opinions = {}
    for name in AGENTS:
        print(f"{name}")
        print("-" * 40)
        ans = ask_agent(question, name)
        opinions[name] = ans
        print(ans[:800] + "...\n")

    # Head posek reads everything and gives final psak
    synthesis_prompt = "שאלה: " + question + "\n\n"
    for name, text in opinions.items():
        synthesis_prompt += f"{name}:\n{text}\n\n"
    synthesis_prompt += """אתה ראש ישיבה גדול ופוסק הדור. קראת את כל חמש הדעות של הגאונים, הראשונים, השולחן ערוך, האחרונים והפוסקים בני זמננו.
    תן פסק הלכה סופי ברור, מנומק היטב, עם ציון המחלוקות העיקריות והכרעה מעשית להיום."""

    final = ask_agent(synthesis_prompt, "Contemporary Poskim")
    print("FINAL PSAK".center(60, "="))
    print(final)
    return final