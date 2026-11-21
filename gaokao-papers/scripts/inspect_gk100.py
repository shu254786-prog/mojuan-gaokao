import json
import re
import urllib.request
from urllib.parse import urljoin

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch(u):
    req = urllib.request.Request(u, headers=HEADERS)
    raw = urllib.request.urlopen(req, timeout=15).read()
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")

# 1. Inspect gk100.com/zhenti/ full link table and one 2026 article
html = fetch("https://www.gk100.com/zhenti/")
links = re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S)
gk100_items = []
for h, t in links:
    tc = re.sub(r"<[^>]+>", "", t).strip()
    tc = re.sub(r"\s+", " ", tc)
    if any(str(y) in tc for y in range(2018, 2027)) and "read_" in h:
        if "文综" in tc or "理综" in tc:
            continue
        gk100_items.append((tc, urljoin("https://www.gk100.com/zhenti/", h)))
print(f"=== gk100.com/zhenti/ items (2018-2026, non-zong): {len(gk100_items)} ===")
for tc, fu in gk100_items[:30]:
    print(f"  {tc} -> {fu}")

# Check one 2026 article on gk100
art = fetch("https://www.gk100.com/read_35811218.htm")
m = re.search(r'<div[^>]*class=["\'][^"\']*(?:content|article|news_con|art_con)[^"\']*["\'][^>]*>(.*?)</div>', art, re.S)
if m:
    txt = re.sub(r"<[^>]+>", "\n", m.group(1))
    txt = re.sub(r"\n+", "\n", txt).strip()
    print("\n=== Sample gk100 article text len:", len(txt), "===")
    print(txt[:500])
else:
    txt = re.sub(r"<[^>]+>", "\n", art)
    txt = re.sub(r"\n+", "\n", txt).strip()
    idx = txt.find("2026")
    print("\n=== Sample gk100 raw text ===", txt[max(0, idx):idx+500])
