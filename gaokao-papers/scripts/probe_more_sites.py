import re
import urllib.request
from urllib.parse import urljoin

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

for u in [
    "https://www.gk100.com/read_13825.htm",
    "https://www.gk100.com/zhenti/",
    "https://www.gaokao.com/zhenti/",
    "https://www.gaokao.com/e/20260607/",
]:
    print(f"=== {u} ===")
    try:
        req = urllib.request.Request(u, headers=HEADERS)
        raw = urllib.request.urlopen(req, timeout=12).read()
        for enc in ("utf-8", "gb18030"):
            try:
                html = raw.decode(enc)
                break
            except UnicodeDecodeError:
                html = raw.decode("utf-8", errors="replace")
        m = re.search(r"<title>(.*?)</title>", html, re.S)
        print("Title:", m.group(1).strip() if m else "?")
        links = re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S)
        rel = []
        for h, t in links:
            tc = re.sub(r"<[^>]+>", "", t).strip()
            tc = re.sub(r"\s+", " ", tc)
            if any(y in tc for y in ["2026", "2025", "2019"]) and any(k in tc for k in ["真题", "试题", "答案", "高考", "语文", "数学", "英语", "物理", "化学"]):
                rel.append((tc[:60], urljoin(u, h)))
        print("Matched links:", len(rel))
        for tc, fu in rel[:12]:
            print(" ", tc, "->", fu)
    except Exception as e:
        print("ERR:", e)
