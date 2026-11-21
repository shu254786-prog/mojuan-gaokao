import glob
import json
import os
from collections import defaultdict

BANK_ROOT = r"e:\反重力\p1\gaokao-papers\bank"
PAPERS_DIR = os.path.join(BANK_ROOT, "papers")
OUT_MD = os.path.join(BANK_ROOT, "README.md")

by_subj_year = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # [papers, questions]
qtypes = defaultdict(int)
multi_m = 0
with_sol = 0
total_q = 0
total_p = 0

for fp in sorted(glob.glob(os.path.join(PAPERS_DIR, "*.json"))):
    p = json.load(open(fp, encoding="utf-8"))
    total_p += 1
    s = p["subject"]
    y = p["year"]
    qs = p.get("questions", [])
    by_subj_year[s][y][0] += 1
    by_subj_year[s][y][1] += len(qs)
    for q in qs:
        total_q += 1
        qtypes[q["type"]] += 1
        if q.get("solution_methods"):
            with_sol += 1
        if q.get("has_multi_method"):
            multi_m += 1

lines = [
    "# 2018–2026 全国无文理综高考交互题库（结构化汇总）\n",
    f"- 结构化试卷总计：**{total_p} 套**",
    f"- 结构化单题总计：**{total_q} 道**",
    f"- 含完整解析题目：**{with_sol} 道**（其中原卷自带多种解法拆分：**{multi_m} 道**）",
    f"- 题型分布：单选题 `{qtypes['single_choice']}` / 多选题 `{qtypes['multiple_choice']}` / 填空与实验 `{qtypes['fill_blank']}` / 解答与阅读大题 `{qtypes['open_ended']}`\n",
    "## 按科目 × 年份结构化统计（套数 / 题数）\n",
    "| 年份 | 数学 | 物理 | 语文 |",
    "| --- | --- | --- | --- |",
]

for y in range(2026, 2017, -1):
    row = [str(y)]
    for s in ["数学", "物理", "语文"]:
        pc, qc = by_subj_year[s].get(y, [0, 0])
        row.append(f"{pc} 套 / {qc} 题" if pc else "-")
    lines.append("| " + " | ".join(row) + " |")

with open(OUT_MD, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Wrote {OUT_MD} | total_p={total_p}, total_q={total_q}, with_sol={with_sol}, multi_m={multi_m}")
