import re

with open("project-docs/task.md", "r", encoding="utf-8") as f:
    content = f.read()

blocks = re.split(r'\n## ', content)
out = open("out.txt", "w", encoding="utf-8")

for b in blocks:
    if 'Week' in b:
        title = b.split('\n')[0][:30]
        uncompleted = len(re.findall(r'(?m)^- \[ \]', b))
        completed = len(re.findall(r'(?m)^- \[[xX]\]', b))
        total = uncompleted + completed
        pct = int((completed / total) * 100) if total > 0 else 0
        emoji = "🟢" if pct == 100 else ("🟡" if pct > 0 else "🔴")
        out.write(f"| {title.split(':')[0].strip()} | {total} | {completed} | {emoji} {pct}% |\n")

out.close()
