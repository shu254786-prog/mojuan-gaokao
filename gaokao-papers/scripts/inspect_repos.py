import json
import urllib.request

REPOS = [
    "jackyjinjing/gaokao_exam",
    "deekur/gaokaomath",
    "deekur/gaokaophysics",
    "DxAThing/Gaokao-Math-Problems-Compilation",
    "daligao/awesome-gaokao",
]

YEARS = [str(y) for y in range(2018, 2027)]

for repo in REPOS:
    for branch in ["main", "master"]:
        url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            tree = data.get("tree", [])
            blobs = [x["path"] for x in tree if x.get("type") == "blob"]
            recent = [p for p in blobs if any(y in p for y in YEARS)]
            print(
                f"=== {repo} ({branch}) | total={len(blobs)} | 2018-2026={len(recent)} | truncated={data.get('truncated')} ==="
            )
            for p in recent[:30]:
                print("  ", p)
            if len(recent) > 30:
                print(f"   ... (+{len(recent) - 30} more)")
            if not recent:
                for p in blobs[:15]:
                    print("   [sample]", p)
            break
        except urllib.error.HTTPError as e:
            if e.code == 404 and branch == "main":
                continue
            print(f"=== {repo} ({branch}) HTTP {e.code} ===")
            break
        except Exception as e:
            print(f"=== {repo} ERROR: {e} ===")
            break
