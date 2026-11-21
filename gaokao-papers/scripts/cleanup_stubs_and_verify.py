import json
import os
import shutil

COLLECTED = r"e:\反重力\p1\gaokao-papers\collected"
STUBS_DIR = r"e:\反重力\p1\gaokao-papers\_stubs_filtered"

moved_stubs = 0
moved_bad = 0

bad_keywords = ["文综", "理综", "文科综合", "理科综合", "一模", "二模", "三模", "期中", "期末", "月考"]

for root, dirs, files in list(os.walk(COLLECTED, topdown=False)):
    if "meta.json" in files:
        mp = os.path.join(root, "meta.json")
        try:
            m = json.load(open(mp, encoding="utf-8"))
        except Exception:
            continue
        title = m.get("title", "")
        imgs = len(m.get("saved_images", []))
        tlen = m.get("text_length", 0)
        rel = os.path.relpath(root, COLLECTED)

        if any(b in title for b in bad_keywords):
            dst = os.path.join(STUBS_DIR, "bad_title", rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(root, dst)
            moved_bad += 1
        elif imgs == 0 and tlen < 1500:
            dst = os.path.join(STUBS_DIR, "short_stub", rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(root, dst)
            moved_stubs += 1

# Prune empty directories left behind in collected/
for root, dirs, files in list(os.walk(COLLECTED, topdown=False)):
    if root != COLLECTED and not os.listdir(root):
        os.rmdir(root)

print(f"Cleanup complete: moved_stubs={moved_stubs}, moved_bad={moved_bad}")
