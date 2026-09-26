import re

with open(r'd:\FINAL-YEAR-PROJECT\project-docs\task.md', 'r', encoding='utf-8') as f:
    content = f.read()

completed = len(re.findall(r'-\s+\[[xX]\]', content))
incomplete = len(re.findall(r'-\s+\[\s\]', content))
total = completed + incomplete

if total > 0:
    pct = (completed / total) * 100
    print(f"Completed: {completed}")
    print(f"Incomplete: {incomplete}")
    print(f"Total: {total}")
    print(f"Percentage: {pct:.2f}%")
else:
    print("No tasks found.")
