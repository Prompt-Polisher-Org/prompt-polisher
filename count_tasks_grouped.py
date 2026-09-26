import re

with open(r'd:\FINAL-YEAR-PROJECT\project-docs\task.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

current_phase = ""
counts = {}
total_completed = 0
total_incomplete = 0

for line in lines:
    header_match = re.match(r'^##\s+(.*)', line)
    if header_match:
        current_phase = header_match.group(1).strip()
        if "Week" in current_phase:
            counts[current_phase] = {'completed': 0, 'incomplete': 0}
        continue
    
    if current_phase in counts:
        completed_match = re.search(r'-\s+\[[xX]\]', line)
        incomplete_match = re.search(r'-\s+\[\s\]', line)
        if completed_match:
            counts[current_phase]['completed'] += 1
            total_completed += 1
        elif incomplete_match:
            counts[current_phase]['incomplete'] += 1
            total_incomplete += 1

print("| Phase | Completed | Total | Progress |")
print("|---|---|---|---|")
for phase, data in counts.items():
    completed = data['completed']
    total = completed + data['incomplete']
    pct = (completed / total * 100) if total > 0 else 0
    clean_phase = phase.split(':')[0].strip().encode('ascii', 'ignore').decode()
    print(f"| {clean_phase} | {completed} | {total} | {pct:.0f}% |")

grand_total = total_completed + total_incomplete
grand_pct = (total_completed / grand_total * 100) if grand_total > 0 else 0
print(f"| **TOTAL** | **{total_completed}** | **{grand_total}** | **{grand_pct:.0f}%** |")
