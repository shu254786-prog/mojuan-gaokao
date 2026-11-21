import os
import subprocess

BASE = r"e:\反重力\p1\gaokao-papers\sources"
YEARS = [str(y) for y in range(2018, 2027)]

lines_out = []
lines_out.append("# 2018–2026 高考真题开源数据源实地盘点报告\n")
lines_out.append("> 统计规则：仅统计 2018–2026 年份，已主动排除路径/名称中明确标为 `文综`、`理综` 的综合卷。\n")

# 1. gaokao-physics-archive
lines_out.append("## 1. 物理（LaTeX 源码：`YLXDXX/gaokao-physics-archive`）\n")
phys_dir = os.path.join(BASE, "gaokao-physics-archive", "试卷")
total_phys = 0
for y in YEARS:
    yp = os.path.join(phys_dir, y)
    if os.path.isdir(yp):
        subs = sorted([d for d in os.listdir(yp) if os.path.isdir(os.path.join(yp, d))])
        single = [d for d in subs if "理综" not in d]
        lz = [d for d in subs if "理综" in d]
        total_phys += len(single)
        lines_out.append(f"- **{y} 年**：单科卷 **{len(single)}** 套（已排除理综 {len(lz)} 套）— {', '.join(single)}")
lines_out.append(f"\n> 合计单科物理 LaTeX 试卷：**{total_phys} 套**\n")

# 2. Gaokao-Math-Problems-Compilation
lines_out.append("## 2. 数学（LaTeX + 配图 + 解析：`DxAThing/Gaokao-Math-Problems-Compilation`）\n")
gmp = os.path.join(BASE, "Gaokao-Math-Problems-Compilation")
out = subprocess.check_output(["git", "-C", gmp, "-c", "core.quotePath=false", "ls-tree", "-r", "--name-only", "HEAD"], encoding="utf-8", errors="replace")
tex_files = [l.strip() for l in out.splitlines() if l.strip().startswith("content/") and l.strip().endswith(".tex")]
total_math_tex = 0
for y in YEARS:
    yf = sorted([os.path.basename(f).replace(".tex", "") for f in tex_files if f.startswith(f"content/{y}/")])
    total_math_tex += len(yf)
    lines_out.append(f"- **{y} 年**：**{len(yf)}** 套 — {', '.join(yf)}")
lines_out.append(f"\n> 合计数学 LaTeX 试卷：**{total_math_tex} 套**\n")

# 3. deekur/gaokaomath (PDFs)
lines_out.append("## 3. 数学原卷 PDF（`deekur/gaokaomath`）\n")
gm = os.path.join(BASE, "gaokaomath")
out = subprocess.check_output(["git", "-C", gm, "-c", "core.quotePath=false", "ls-tree", "-r", "--name-only", "HEAD"], encoding="utf-8", errors="replace")
pdfs = [l.strip() for l in out.splitlines() if l.strip().endswith(".pdf")]
total_math_pdf = 0
for y in YEARS:
    yf = sorted([os.path.basename(f).replace(".pdf", "") for f in pdfs if f"/{y}/" in f])
    total_math_pdf += len(yf)
    lines_out.append(f"- **{y} 年**：**{len(yf)}** 份 PDF — {', '.join(yf)}")
lines_out.append(f"\n> 合计数学 PDF：**{total_math_pdf} 份**\n")

# 4. deekur/gaokaophysics (PDFs, excluding 理综)
lines_out.append("## 4. 物理单科原卷 PDF（`deekur/gaokaophysics`，已排除理综）\n")
gp = os.path.join(BASE, "gaokaophysics")
out = subprocess.check_output(["git", "-C", gp, "-c", "core.quotePath=false", "ls-tree", "-r", "--name-only", "HEAD"], encoding="utf-8", errors="replace")
pdfs = [l.strip() for l in out.splitlines() if l.strip().endswith(".pdf")]
total_phys_pdf = 0
for y in YEARS:
    all_y = sorted([os.path.basename(f).replace(".pdf", "") for f in pdfs if f"/{y}/" in f])
    single = [x for x in all_y if "理综" not in x]
    lz = [x for x in all_y if "理综" in x]
    total_phys_pdf += len(single)
    lines_out.append(f"- **{y} 年**：单科 **{len(single)}** 份（已排除理综 {len(lz)} 份）— {', '.join(single)}")
lines_out.append(f"\n> 合计物理单科 PDF：**{total_phys_pdf} 份**\n")

out_path = r"e:\反重力\p1\gaokao-papers\inventory\source_coverage_summary.md"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines_out))

print(f"Wrote {out_path}")
print(f"Summary: phys_tex={total_phys}, math_tex={total_math_tex}, math_pdf={total_math_pdf}, phys_pdf={total_phys_pdf}")
