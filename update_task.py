import re

def get_emoji(pct):
    if pct == 100:
        return "🟢"
    elif pct == 0:
        return "🔴"
    else:
        return "🟡"

text = open('d:/FINAL-YEAR-PROJECT/project-docs/task.md', encoding='utf-8').read()
sections = re.split(r'\n## ', text)

counts = []
for sec in sections[1:]:
    lines = sec.split('\n')
    title = lines[0].strip()
    # Count all checkboxes
    x = len(re.findall(r'\[x\]', sec))
    u = len(re.findall(r'\[ \]', sec))
    p = len(re.findall(r'\[/\]', sec))
    
    if 'Exit Criteria' not in title and 'Progress Summary' not in title and 'Quick Reference' not in title:
        counts.append({
            'title': title,
            'x': x,
            'total': x+u+p
        })

# Map phase names
phases = [
    ("Foundation", "1-2"),
    ("Auth & Database", "3-4"),
    ("AI Model & Inference", "5-6"),
    ("RAG & Chat Experience", "7-8"),
    ("System Integration", "9-10"),
    ("RLHF & Optimization", "11-12"),
    ("Polish & Load Testing", "13"),
    ("Cloud Deploy & Presentation", "14")
]

new_table_lines = [
    "| Phase | Weeks | Total Tasks | Completed | Progress |",
    "|---|---|---|---|---|"
]

total_x = 0
total_all = 0

for i, count in enumerate(counts):
    if i >= len(phases):
        break
    phase, weeks = phases[i]
    x = count['x']
    total = count['total']
    total_x += x
    total_all += total
    
    pct = round((x / total * 100) if total > 0 else 0)
    emoji = get_emoji(pct)
    
    # ensure weeks uses en-dash if originally there
    weeks = weeks.replace("-", "–")
    
    new_table_lines.append(f"| {phase} | {weeks} | {total} | {x} | {emoji} {pct}% |")

total_pct = round((total_x / total_all * 100) if total_all > 0 else 0)
total_emoji = get_emoji(total_pct)
new_table_lines.append(f"| **TOTAL** | **1–14** | **{total_all}** | **{total_x}** | **{total_emoji} {total_pct}%** |")

new_table = "\n".join(new_table_lines)

# Replace in text
table_pattern = re.compile(r'\| Phase \| Weeks \| Total Tasks \| Completed \| Progress \|\n\|---\|---\|---\|---\|---\|\n(?:\|.*\|\n)+')

new_text = table_pattern.sub(new_table + "\n", text)

with open('d:/FINAL-YEAR-PROJECT/project-docs/task.md', 'w', encoding='utf-8') as f:
    f.write(new_text)

print(f"Updated task.md: Total {total_x}/{total_all} ({total_pct}%)")
