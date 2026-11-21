import re
import urllib.request

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=HEADERS), timeout=12).read().decode("utf-8", errors="replace")

# Check gk100 article actual body
for u in ["https://www.gk100.com/read_142044965.htm", "https://www.gk100.com/read_35811218.htm"]:
    h = fetch(u)
    # find the main article div
    idx = h.find("2026年")
    # strip tags from a broad body slice
    m = re.search(r'<div[^>]*class=["\'][^"\']*(?:detail|article|content|main|left)[^"\']*["\'][^>]*>(.*?)微信扫码', h, re.S)
    chunk = m.group(1) if m else h
    imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', chunk)
    txt = re.sub(r"<[^>]+>", "\n", chunk)
    txt = re.sub(r"\n+", "\n", txt).strip()
    print(f"=== {u} ===")
    print("  imgs:", [i for i in imgs if "qr" not in i and "icp" not in i][:10])
    print("  text len:", len(txt), "preview:\n", txt[:600])

# Check all 2026 links on https://gaokao.eol.cn/shiti/
shiti_h = fetch("https://gaokao.eol.cn/shiti/")
print("\n=== Live test on gaokao.eol.cn/shiti/ 2026 links ===")
for href, txt in re.findall(r'<a[^>]+href=["\']([^"\']*2026[^"\']*\.shtml)["\'][^>]*>(.*?)</a>', shiti_h, re.S):
    t = re.sub(r"<[^>]+>", "", txt).strip()
    if t and t != "详细":
        print(" ", t, "->", href)
