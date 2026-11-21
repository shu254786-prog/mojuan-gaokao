import re
import urllib.request

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch(u):
    req = urllib.request.Request(u, headers=HEADERS)
    raw = urllib.request.urlopen(req, timeout=15).read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("gb18030", errors="replace")

for u in [
    "https://gaokao.eol.cn/shiti/sx/202506/t20250607_2673303.shtml",
    "https://gaokao.eol.cn/shiti/",
]:
    print(f"=== {u} ===")
    try:
        html = fetch(u)
        m = re.search(r"<title>(.*?)</title>", html, re.S)
        print("Title:", m.group(1).strip() if m else "")
        imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
        print("Imgs:", len(imgs), imgs[:8])
        # check multi-page pagination or article body
        body_m = re.search(r'<div[^>]*class=["\'][^"\']*(?:TRS_Editor|article|content|main)[^"\']*["\'][^>]*>(.*?)</div>', html, re.S)
        if body_m:
            txt = re.sub(r"<[^>]+>", " ", body_m.group(1))
            txt = re.sub(r"\s+", " ", txt).strip()
            print("Body sample:", txt[:400])
        links = re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S)
        rel = [(re.sub(r"<[^>]+>", "", t).strip(), href) for href, t in links if "2026" in t or "2026" in href or "t2025" in href or "t2026" in href]
        print("2026/subpage links:", len(rel), rel[:12])
    except Exception as e:
        print("ERR:", e)
