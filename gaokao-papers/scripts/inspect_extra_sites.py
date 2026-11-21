import re
import urllib.request
from urllib.parse import urljoin

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch(u):
    raw = urllib.request.urlopen(urllib.request.Request(u, headers=HEADERS), timeout=12).read()
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")

for u in ["https://www.555edu.com/", "https://www.6617.com/", "https://www.gzywtk.com/"]:
    html = fetch(u)
    links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S)
    matched = []
    for h, t in links:
        tc = re.sub(r"<[^>]+>", "", t)
        tc = re.sub(r"\s+", " ", tc).strip()
        if any(k in tc for k in ["真题", "试题", "试卷", "2026", "2025", "2019"]):
            matched.append((tc[:45], urljoin(u, h)))
    print(f"=== {u} (matched={len(matched)}) ===")
    for tc, fu in matched[:20]:
        print(" ", tc, "->", fu)
