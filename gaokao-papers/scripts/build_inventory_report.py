import json
import os

COLLECTED = r"e:\反重力\p1\gaokao-papers\collected"
OUT_MD = r"e:\反重力\p1\gaokao-papers\inventory\master_inventory_report.md"

SUBJECTS = ["语文", "数学", "英语", "物理", "化学", "生物", "政治", "历史", "地理", "技术", "全科九科汇总"]

summary = {}  # (year, subj) -> list of paper entries
counts = {"dirs": 0, "pdfs": 0, "tex": 0, "eol": 0, "gk100": 0, "6617": 0, "555edu": 0, "files": 0}

if os.path.isdir(COLLECTED):
    for y_str in sorted(os.listdir(COLLECTED)):
        yp = os.path.join(COLLECTED, y_str)
        if not os.path.isdir(yp) or not y_str.isdigit():
            continue
        year = int(y_str)
        for subj in sorted(os.listdir(yp)):
            sp = os.path.join(yp, subj)
            if not os.path.isdir(sp):
                continue
            entries = []
            for item in sorted(os.listdir(sp)):
                ip = os.path.join(sp, item)
                if item == "_pdf_originals" and os.path.isdir(ip):
                    pdfs = [f for f in os.listdir(ip) if f.endswith(".pdf")]
                    counts["pdfs"] += len(pdfs)
                    for pf in sorted(pdfs):
                        entries.append(f"[PDF]{pf[:-4]}")
                    continue
                if os.path.isdir(ip):
                    tags = []
                    if os.path.isdir(os.path.join(ip, "latex")):
                        counts["tex"] += 1
                        tags.append("LaTeX")
                    for src_key in ["eol", "gk100", "6617", "555edu"]:
                        sub_p = os.path.join(ip, src_key)
                        if os.path.isdir(sub_p):
                            n = sum(1 for d in os.listdir(sub_p) if os.path.isfile(os.path.join(sub_p, d, "meta.json")))
                            if n:
                                counts[src_key] += n
                                tags.append(f"{src_key}:{n}")
                    entries.append(f"{item}({'+'.join(tags) if tags else 'dir'})")
                    counts["dirs"] += 1
            summary[(year, subj)] = entries

for root, dirs, files in os.walk(COLLECTED):
    counts["files"] += len(files)

lines = []
lines.append("# 2018–2026 全国无文理综高考真题库·实时入库盘点\n")
lines.append(f"- 已入库考区×科目目录：**{counts['dirs']}**")
lines.append(f"- 原卷 PDF：**{counts['pdfs']} 份**")
lines.append(f"- 高精度 LaTeX 源码：**{counts['tex']} 套**")
lines.append(f"- 中国教育在线（`eol.cn`）真题/答案包：**{counts['eol']} 份**")
lines.append(f"- 高考100（`gk100.com`）真题/答案包：**{counts['gk100']} 份**")
lines.append(f"- 圆梦小灯塔（`6617.com`）全科/单科包：**{counts['6617']} 份**")
lines.append(f"- 无忧高考（`555edu.com`）历史补全包：**{counts['555edu']} 份**")
lines.append(f"- 磁盘总文件数：**{counts['files']}**\n")

lines.append("## 按年份 × 科目覆盖统计\n")
header = "| 年份 | " + " | ".join(SUBJECTS) + " |"
sep = "| --- | " + " | ".join(["---"] * len(SUBJECTS)) + " |"
lines.append(header)
lines.append(sep)
for y in range(2026, 2017, -1):
    row = [str(y)]
    for s in SUBJECTS:
        cnt = len(summary.get((y, s), []))
        row.append(str(cnt) if cnt else "-")
    lines.append("| " + " | ".join(row) + " |")

lines.append("\n## 详细目录清单\n")
for (y, s), ents in sorted(summary.items(), key=lambda x: (-x[0][0], x[0][1])):
    lines.append(f"### {y} 年 · {s}（{len(ents)} 项）")
    lines.append(", ".join(ents))
    lines.append("")

with open(OUT_MD, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Report written: {OUT_MD}")
print("Counts:", counts)
