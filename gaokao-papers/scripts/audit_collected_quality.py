import json
import os
from collections import defaultdict

COLLECTED = r"e:\反重力\p1\gaokao-papers\collected"
OUT_MD = r"e:\反重力\p1\gaokao-papers\inventory\quality_audit_report.md"

real_papers = 0
stubs = []
by_year_subj = defaultdict(lambda: defaultdict(int))

for root, dirs, files in os.walk(COLLECTED):
    if "_stubs_filtered" in root:
        continue
    if "meta.json" in files:
        mp = os.path.join(root, "meta.json")
        try:
            m = json.load(open(mp, encoding="utf-8"))
        except Exception:
            continue
        imgs = len(m.get("saved_images", []))
        tlen = m.get("text_length", 0)
        y = m.get("year")
        s = m.get("subject", "未知")
        if imgs >= 1 or tlen >= 1500:
            real_papers += 1
            by_year_subj[y][s] += 1
        else:
            stubs.append((y, s, m.get("region"), m.get("source"), tlen, imgs, root))

# Count PDF and LaTeX too
pdfs = 0
texs = 0
for y_str in os.listdir(COLLECTED):
    yp = os.path.join(COLLECTED, y_str)
    if not os.path.isdir(yp) or not y_str.isdigit():
        continue
    y = int(y_str)
    for subj in os.listdir(yp):
        sp = os.path.join(yp, subj)
        if not os.path.isdir(sp):
            continue
        for item in os.listdir(sp):
            ip = os.path.join(sp, item)
            if item == "_pdf_originals" and os.path.isdir(ip):
                n = sum(1 for f in os.listdir(ip) if f.endswith(".pdf"))
                pdfs += n
                by_year_subj[y][subj] += n
            elif os.path.isdir(ip) and os.path.isdir(os.path.join(ip, "latex")):
                texs += 1
                by_year_subj[y][subj] += 1

lines = [
    "# 高考真题库质量审计报告（纯干货有效试卷 vs 低质空壳占位页）\n",
    f"- 有效图文真题包（含 >=1 张试卷页图 或 >=1500 字正文）：**{real_papers}**",
    f"- 有效 LaTeX 源码试卷：**{texs}**",
    f"- 有效原卷 PDF：**{pdfs}**",
    f"- 疑似低质/空壳占位页（0 图且 <1500 字）：**{len(stubs)}**\n",
    "## 按年份 × 科目有效资源统计\n",
]

SUBJS = ["语文", "数学", "英语", "物理", "化学", "生物", "政治", "历史", "地理", "全科九科汇总"]
lines.append("| 年份 | " + " | ".join(SUBJS) + " |")
lines.append("| --- | " + " | ".join(["---"] * len(SUBJS)) + " |")
for y in range(2026, 2017, -1):
    lines.append("| " + str(y) + " | " + " | ".join(str(by_year_subj[y].get(s, 0) or "-") for s in SUBJS) + " |")

lines.append("\n## 疑似空壳占位页样本（前 30 条）\n")
for st in stubs[:30]:
    lines.append(f"- {st[0]} {st[1]} {st[2]} ({st[3]}): txt={st[4]}, imgs={st[5]} -> `{st[6]}`")

with open(OUT_MD, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Audit done: real_web={real_papers}, tex={texs}, pdfs={pdfs}, stubs={len(stubs)}")
