import glob
import re

print("=== MATH SPECIAL CONSTRUCTS ===")
math_files = glob.glob(r"e:\反重力\p1\gaokao-papers\collected\*\数学\*\latex\*.tex")
for pat_name, pat in [
    ("examdisplay", r"\\examdisplay\w+.*"),
    ("examfiguregroup", r"\\examfiguregroup.*"),
    ("examstatpanels", r"\\examstatpanels.*"),
    ("choicetexfigure", r"\\choicetexfigure.*"),
    ("circlelist", r"\\begin\{circlelist\}.*?\\end\{circlelist\}"),
    ("fillinblank", r".{0,25}\\fillinblank.{0,25}"),
    ("multi_method", r"【法[一二三四]】.{0,40}"),
]:
    samples = []
    for fp in math_files:
        t = open(fp, encoding="utf-8", errors="replace").read()
        for m in re.findall(pat, t, re.S):
            s = re.sub(r"\s+", " ", m)[:120]
            if s not in samples:
                samples.append(s)
            if len(samples) >= 3:
                break
        if len(samples) >= 3:
            break
    print(f"  {pat_name}: {samples}")

print("\n=== PHYSICS SPECIAL CONSTRUCTS ===")
phys_files = glob.glob(r"e:\反重力\p1\gaokao-papers\collected\*\物理\*\latex\*.tex")
types = set()
for fp in phys_files:
    t = open(fp, encoding="utf-8", errors="replace").read()
    types.update(re.findall(r"%% type:\s*(.+)", t))
print("  %% type values:", sorted(types))
for pat_name, pat in [
    ("pictures", r"\\(?:two|three|four)picture(?:\[[^\]]*\])?(?:\s*\{[^}]*\}){2,4}"),
    ("tblr", r"\\begin\{tblr\}.*?\\end\{tblr\}"),
    ("odv_odif", r".{0,15}\\od(?:v|if)\b.{0,25}"),
    ("ce", r".{0,10}\\ce\{[^}]+\}.{0,10}"),
    ("tkanswer", r".{0,20}\\tkanswer\{[^}]*\}.{0,20}"),
]:
    samples = []
    for fp in phys_files:
        t = open(fp, encoding="utf-8", errors="replace").read()
        for m in re.findall(pat, t, re.S):
            s = re.sub(r"\s+", " ", m)[:130]
            if s not in samples:
                samples.append(s)
            if len(samples) >= 3:
                break
        if len(samples) >= 3:
            break
    print(f"  {pat_name}: {samples}")
