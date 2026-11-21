import re
import urllib.request
from urllib.parse import urljoin

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch(u):
    raw = urllib.request.urlopen(urllib.request.Request(u, headers=HEADERS), timeout=15).read()
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")

# 1. Inspect 555edu/beikao/zhenti/
hz = fetch("https://www.555edu.com/beikao/zhenti/")
links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', hz, re.S)
good = []
for h, t in links:
    tc = re.sub(r"<[^>]+>", "", t).strip()
    if any(y in tc for y in ["2026", "2025", "2024", "2023", "2022", "2021", "2020", "2019", "2018"]) and "文综" not in tc and "理综" not in tc:
        good.append((tc[:45], urljoin("https://www.555edu.com/beikao/zhenti/", h)))
print(f"=== 555edu/beikao/zhenti/ matched={len(good)} ===")
for tc, fu in good[:25]:
    print(" ", tc, "->", fu)

# 2. Inspect 172181.html body structure
h1 = fetch("https://www.555edu.com/shanghai/GaoKaoZhenTi/2019-06-04/172181.html")
idx = h1.find("2019年上海高考语文")
print("\n=== 172181.html snippet ===")
chunk = h1[max(0, idx):idx+4000]
imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', chunk)
txt = re.sub(r"<[^>]+>", "\n", chunk)
txt = re.sub(r"\n+", "\n", txt).strip()
print("imgs:", imgs[:8])
print("txt preview:", txt[:450])
