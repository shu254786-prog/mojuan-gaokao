import os
import re
import shutil
import subprocess

SOURCES = r"e:\反重力\p1\gaokao-papers\sources"
OUT_ROOT = r"e:\反重力\p1\gaokao-papers\collected"

def is_eligible_physics_dir(year, dirname):
    if "理综" in dirname:
        return False
    # Exclude split-from-lizong national papers
    if any(k in dirname for k in ["全国甲", "全国乙", "全国新课标", "全国1", "全国2", "全国3", "全国I", "全国II", "全国III"]):
        return False
    if year <= 2019:
        return any(p in dirname for p in ["上海", "浙江", "江苏", "海南"])
    return True

def is_eligible_math_tex(year, fname):
    base = fname.replace(".tex", "")
    # Exclude old liberal/science split & old national papers
    if "liberal" in base or "science" in base:
        return False
    if "national_paper_a" in base or "national_paper_b" in base:
        return False
    if base.startswith("national_paper_") and year < 2025:
        return False
    if year <= 2019:
        return any(k in base for k in ["shanghai", "zhejiang", "jiangsu"])
    return True

def is_eligible_math_pdf(year, fname):
    if any(k in fname for k in ["全国1文", "全国1理", "全国2文", "全国2理", "全国3文", "全国3理", "全国甲", "全国乙", "全国文", "全国理", "北京文", "北京理", "天津文", "天津理"]):
        return False
    if year <= 2019:
        return any(k in fname for k in ["上海", "浙江", "江苏"])
    return True

def is_eligible_phys_pdf(year, fname):
    if "理综" in fname:
        return False
    if any(k in fname for k in ["全国甲", "全国乙", "全国新课标", "全国1", "全国2", "全国3"]):
        return False
    if year <= 2019:
        return any(k in fname for k in ["上海", "浙江", "江苏", "海南"])
    return True

stats = {"phys_tex": 0, "math_tex": 0, "math_pdf": 0, "phys_pdf": 0}

# 1. Copy filtered gaokao-physics-archive (2018-2026)
phys_src = os.path.join(SOURCES, "gaokao-physics-archive", "试卷")
for year in range(2018, 2027):
    yp = os.path.join(phys_src, str(year))
    if not os.path.isdir(yp):
        continue
    for d in sorted(os.listdir(yp)):
        dp = os.path.join(yp, d)
        if not os.path.isdir(dp) or not is_eligible_physics_dir(year, d):
            continue
        dst = os.path.join(OUT_ROOT, str(year), "物理", d, "latex")
        if not os.path.exists(dst):
            shutil.copytree(dp, dst)
        stats["phys_tex"] += 1

# 2. Extract filtered DxAThing/Gaokao-Math-Problems-Compilation (blobless -> git show)
math_repo = os.path.join(SOURCES, "Gaokao-Math-Problems-Compilation")
# First checkout only content/2018..2026 and img/2018..2026 if not present
out = subprocess.check_output(["git", "-C", math_repo, "-c", "core.quotePath=false", "ls-tree", "-r", "--name-only", "HEAD"], encoding="utf-8", errors="replace")
all_math_files = [l.strip() for l in out.splitlines() if l.strip()]
needed_paths = []
eligible_tex = []
for f in all_math_files:
    m = re.match(r"content/(20(?:1[89]|2[0-6]))/([^/]+\.tex)$", f)
    if m:
        y = int(m.group(1))
        fn = m.group(2)
        if is_eligible_math_tex(y, fn):
            eligible_tex.append((y, fn.replace(".tex", ""), f))
            needed_paths.append(f)
for y, paper, _ in eligible_tex:
    prefix = f"img/{y}/{paper}/"
    for f in all_math_files:
        if f.startswith(prefix):
            needed_paths.append(f)

if needed_paths:
    subprocess.run(["git", "-C", math_repo, "sparse-checkout", "init", "--no-cone"], check=True)
    subprocess.run(["git", "-C", math_repo, "sparse-checkout", "set", "--no-cone"] + needed_paths, check=True)
    subprocess.run(["git", "-C", math_repo, "checkout", "HEAD"], check=True)
    for y, paper, tex_rel in eligible_tex:
        dst_dir = os.path.join(OUT_ROOT, str(y), "数学", paper, "latex")
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy2(os.path.join(math_repo, tex_rel), os.path.join(dst_dir, f"{paper}.tex"))
        img_src = os.path.join(math_repo, "img", str(y), paper)
        if os.path.isdir(img_src):
            img_dst = os.path.join(dst_dir, "img")
            if not os.path.exists(img_dst):
                shutil.copytree(img_src, img_dst)
        stats["math_tex"] += 1

# 3. Extract filtered PDFs from deekur/gaokaomath and deekur/gaokaophysics
def extract_pdfs(repo_name, subj_name, filter_fn, stat_key):
    rp = os.path.join(SOURCES, repo_name)
    out = subprocess.check_output(["git", "-C", rp, "-c", "core.quotePath=false", "ls-tree", "-r", "--name-only", "HEAD"], encoding="utf-8", errors="replace")
    files = [l.strip() for l in out.splitlines() if l.strip().endswith(".pdf")]
    selected = []
    for f in files:
        m = re.search(r"/(20(?:1[89]|2[0-6]))/([^/]+\.pdf)$", f)
        if m:
            y = int(m.group(1))
            fn = m.group(2)
            if filter_fn(y, fn):
                selected.append((y, fn, f))
    if selected:
        paths = [x[2] for x in selected]
        subprocess.run(["git", "-C", rp, "sparse-checkout", "init", "--no-cone"], check=True)
        subprocess.run(["git", "-C", rp, "sparse-checkout", "set", "--no-cone"] + paths, check=True)
        subprocess.run(["git", "-C", rp, "checkout", "HEAD"], check=True)
        for y, fn, rel in selected:
            dst_dir = os.path.join(OUT_ROOT, str(y), subj_name, "_pdf_originals")
            os.makedirs(dst_dir, exist_ok=True)
            src_f = os.path.join(rp, rel)
            if os.path.isfile(src_f):
                shutil.copy2(src_f, os.path.join(dst_dir, fn))
                stats[stat_key] += 1

extract_pdfs("gaokaomath", "数学", is_eligible_math_pdf, "math_pdf")
extract_pdfs("gaokaophysics", "物理", is_eligible_phys_pdf, "phys_pdf")

print("Ingestion complete:", stats)
