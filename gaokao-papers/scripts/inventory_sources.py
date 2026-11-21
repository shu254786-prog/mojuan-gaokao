import os
import subprocess

BASE = r"e:\反重力\p1\gaokao-papers\sources"
YEARS = [str(y) for y in range(2018, 2027)]

print("=== 1. gaokao-physics-archive (2018-2026) ===")
phys_dir = os.path.join(BASE, "gaokao-physics-archive", "试卷")
for y in YEARS:
    yp = os.path.join(phys_dir, y)
    if os.path.isdir(yp):
        subs = sorted([d for d in os.listdir(yp) if os.path.isdir(os.path.join(yp, d))])
        non_lz = [d for d in subs if "理综" not in d]
        lz = [d for d in subs if "理综" in d]
        print(f"  {y}: total={len(subs)} | single={len(non_lz)} {non_lz} | lizong_excluded={len(lz)}")

print("\n=== 2. rainewhk/gaokao (dataset/ subdirs) ===")
gk_dir = os.path.join(BASE, "gaokao", "dataset")
for subj in sorted(os.listdir(gk_dir)):
    sp = os.path.join(gk_dir, subj)
    if os.path.isdir(sp):
        dirs = sorted([d for d in os.listdir(sp) if os.path.isdir(os.path.join(sp, d))])
        recent = [d for d in dirs if any(y in d for y in YEARS)]
        print(f"  {subj}: all_years={dirs} | 2018-2026={recent}")
        # inspect sample files in 2018-2026
        for d in recent[:2]:
            dp = os.path.join(sp, d)
            files = sorted(os.listdir(dp))
            print(f"    {d}: {len(files)} files, sample={files[:4]}")

print("\n=== 3. Blobless git trees (2018-2026 summary) ===")
for name in ["gaokao_exam", "gaokaomath", "gaokaophysics", "Gaokao-Math-Problems-Compilation"]:
    rp = os.path.join(BASE, name)
    out = subprocess.check_output(["git", "-C", rp, "ls-tree", "-r", "--name-only", "HEAD"], encoding="utf-8", errors="replace")
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    recent = [l for l in lines if any(y in l for y in YEARS)]
    print(f"  {name}: total_files={len(lines)} | 2018-2026={len(recent)}")
    for l in recent[:25]:
        print("   ", l)
    if len(recent) > 25:
        print(f"    ... (+{len(recent) - 25} more)")
