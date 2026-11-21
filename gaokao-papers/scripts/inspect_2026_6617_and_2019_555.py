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

# 1. Check 6617.com/p_3222438157.html (2026广东九科全) & list_2003 pagination
h66 = fetch("https://www.6617.com/p_3222438157.html")
links66 = [(re.sub(r"<[^>]+>", "", t).strip(), urljoin("https://www.6617.com/", href)) for href, t in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', h66, re.S) if "p_" in href and "2026" in t]
imgs66 = [i for i in re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', h66) if "article" in i or "upload" in i or "2026" in i or "p1." in i]
txt66 = re.sub(r"<[^>]+>", "\n", h66)
txt66 = re.sub(r"\n+", "\n", txt66)
print(f"=== 6617 2026广东九科全: len={len(h66)}, sublinks={len(links66)}, imgs={len(imgs66)} ===")
for t, u in links66[:15]:
    print("  sublink:", t, "->", u)
print("  imgs:", imgs66[:6])

# Check list_2003 pagination
hl = fetch("https://www.6617.com/list_2003.html")
pl = re.findall(r'list_2003[^"\']*\.html(?:\?p=\d+)?', hl)
print("6617 list_2003 pages:", sorted(set(pl))[:10])

# 2. Check 555edu 2019 (172287.html) for 上海/浙江/江苏
h55 = fetch("https://www.555edu.com/gaokaozixun/jiaoyuyaowen/2019-06-05/172287.html")
# Check table/rows around 上海, 浙江, 江苏
for prov in ["上海", "浙江", "江苏"]:
    idx = h55.find(prov)
    print(f"\n=== 555edu 2019 {prov} (idx={idx}) ===")
    if idx != -1:
        seg = h55[max(0, idx-50):idx+1200]
        ls = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', seg, re.S)
        print(" ", [(re.sub(r"<[^>]+>", "", t).strip(), urljoin("https://www.555edu.com/", u)) for u, t in ls[:12]])

# 3. Check gzywtk 2026全国I卷语文
hg = fetch("https://www.gzywtk.com/sjshow/3057.html")
txtg = re.sub(r"<[^>]+>", "\n", hg)
txtg = re.sub(r"\n+", "\n", txtg)
idxg = txtg.find("现代文阅读")
print("\n=== gzywtk 2026全国I卷语文 preview ===")
print(txtg[max(0, idxg):idxg+400] if idxg != -1 else txtg[:400])
