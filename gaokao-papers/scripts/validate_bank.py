import glob
import json
import os
import re

BANK_ROOT = r"e:\反重力\p1\gaokao-papers\bank"
PAPERS_DIR = os.path.join(BANK_ROOT, "papers")

bad_macros = re.compile(
    r"\\(?:xzanswer|tkanswer|jdanswer|memoanswer|fourchoices|twochoices|threechoices|fivechoices|sixchoices|onepicture|twopicture|threepicture|fourpicture|examdisplay\w+|texfigure|bitmapfigure|choicetexfigure|solutionfigure|U[A-Z][A-Za-z]+)\b"
)

totals = {
    "papers": 0,
    "questions": 0,
    "empty_stem": 0,
    "empty_ans": 0,
    "bad_choices": 0,
    "missing_assets": 0,
    "leftover_macros": 0,
    "multi_method_q": 0,
    "has_solution_q": 0,
}

samples_macro = []
samples_missing = []
samples_bad_choice = []

for fp in sorted(glob.glob(os.path.join(PAPERS_DIR, "*.json"))):
    p = json.load(open(fp, encoding="utf-8"))
    totals["papers"] += 1
    for q in p.get("questions", []):
        totals["questions"] += 1
        stem = q.get("stem_md", "")
        if not stem.strip():
            totals["empty_stem"] += 1
        ans = q.get("answer", {})
        if not ans.get("raw") and not ans.get("choices") and not ans.get("sub_answers"):
            totals["empty_ans"] += 1
        if q["type"] in ("single_choice", "multiple_choice"):
            if len(q.get("choices", [])) < 2 or not ans.get("choices"):
                totals["bad_choices"] += 1
                if len(samples_bad_choice) < 10:
                    samples_bad_choice.append((q["qid"], len(q.get("choices", [])), ans))

        # Verify all referenced asset files exist on disk
        refs = list(q.get("figures", [])) + list(q.get("solution_figures", []))
        for c in q.get("choices", []):
            if c.get("image"):
                refs.append(c["image"])
        for rel in refs:
            if not os.path.isfile(os.path.join(BANK_ROOT, rel)):
                totals["missing_assets"] += 1
                if len(samples_missing) < 10:
                    samples_missing.append((q["qid"], rel))

        # Check leftover custom macros
        all_txt = stem + "\n" + "\n".join(c.get("text_md", "") for c in q.get("choices", [])) + "\n" + "\n".join(m.get("content_md", "") for m in q.get("solution_methods", []))
        m = bad_macros.search(all_txt)
        if m:
            totals["leftover_macros"] += 1
            if len(samples_macro) < 15:
                samples_macro.append((q["qid"], m.group(0)))

        if q.get("solution_methods"):
            totals["has_solution_q"] += 1
        if q.get("has_multi_method"):
            totals["multi_method_q"] += 1

print("VALIDATION TOTALS:", totals)
if samples_macro:
    print("Leftover macro samples:", samples_macro)
if samples_missing:
    print("Missing asset samples:", samples_missing)
if samples_bad_choice:
    print("Bad choice samples:", samples_bad_choice)
