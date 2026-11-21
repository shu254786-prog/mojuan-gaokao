import json
import re
import urllib.request

print("=== eol 2019 extra ===")
for x in json.load(open(r"e:\反重力\p1\gaokao-papers\inventory\eol_2019_2026_extra.json", encoding="utf-8")):
    print(" ", x["subject"], x["title"], x["url"])

print("\n=== 555edu 172181.html body ===")
h = urllib.request.urlopen(
    urllib.request.Request("https://www.555edu.com/shanghai/GaoKaoZhenTi/2019-06-04/172181.html", headers={"User-Agent": "Mozilla/5.0"}),
    timeout=10,
).read().decode("gb18030", errors="replace")

# find longest text block or class="news-content" etc
for pat in [r'<div[^>]*class=["\'][^"\']*(?:art|content|nr|body|detail|main)[^"\']*["\'][^>]*>(.*?)</div>', r'<div[^>]*id=["\'][^"\']*(?:content|article|main)[^"\']*["\'][^>]*>(.*?)</div>']:
    for m in re.finditer(pat, h, re.S | re.I):
        t = re.sub(r"<[^>]+>", " ", m.group(1))
        t = re.sub(r"\s+", " ", t).strip()
        if len(t) > 500:
            print("Matched block len=", len(t), "sample=", t[:300])
            break
