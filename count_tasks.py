import re

with open("project-docs/task.md", "r", encoding="utf-8") as f:
    lines = f.readlines()

sections = [
    ("Foundation", "1–2"),
    ("Auth & Database", "3–4"),
    ("AI Model & Inference", "5–6"),
    ("RAG & Chat Experience", "7–8"),
    ("System Integration", "9–10"),
    ("RLHF & Optimization", "11–12"),
    ("Polish & Load Testing", "13"),
    ("Cloud Deploy & Presentation", "14")
]

current_section = None
section_counts = {sec[0]: {"total": 0, "completed": 0} for sec in sections}

for line in lines:
    if line.startswith("## "):
        if line.startswith("### "):
            continue
        for sec, _ in sections:
            if sec in line:
                current_section = sec
                break
    elif current_section and re.search(r"^\s*- \[([x/ ])\]", line):
        section_counts[current_section]["total"] += 1
        if "[x]" in line.lower():
            section_counts[current_section]["completed"] += 1

with open("output.txt", "w", encoding="utf-8") as out_f:
    out_f.write("| Phase | Weeks | Total Tasks | Completed | Progress |\n")
    out_f.write("|---|---|---|---|---|\n")

    total_all = 0
    completed_all = 0

    for sec, weeks in sections:
        tot = section_counts[sec]["total"]
        comp = section_counts[sec]["completed"]
        total_all += tot
        completed_all += comp
        pct = int(comp / tot * 100) if tot > 0 else 0
        emoji = "🟢" if pct == 100 else ("🟡" if pct > 0 else "🔴")
        out_f.write(f"| {sec} | {weeks} | {tot} | {comp} | {emoji} {pct}% |\n")

    pct_all = int(completed_all / total_all * 100) if total_all > 0 else 0
    emoji_all = "🟢" if pct_all == 100 else ("🟡" if pct_all > 0 else "🔴")
    out_f.write(f"| **TOTAL** | **1–14** | **{total_all}** | **{completed_all}** | **{emoji_all} {pct_all}%** |\n")
