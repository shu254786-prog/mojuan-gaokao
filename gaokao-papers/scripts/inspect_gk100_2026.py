import re
import urllib.request

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch(u):
    req = urllib.request.Request(u, headers=HEADERS)
    raw = urllib.request.urlopen(req, timeout=12).read()
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")

print("=== Checking 2019 eol.cn URL variants ===")
for u in [
    "https://www.eol.cn/e_html/gk/2019st/index.shtml",
    "https://gaokao.eol.cn/e_html/gk/2019st/index.shtml",
    "https://www.eol.cn/html/g/gkst/2019.shtml",
    "https://www.eol.cn/e_html/gk/gkst/2019/index.shtml",
]:
    try:
        h = fetch(u)
        print("OK", u, len(h))
    except Exception as e:
        print("ERR", u, e)

print("\n=== Inspecting gk100 2026 pagination & content ===")
for u in [
    "https://www.gk100.com/read_142044965.htm",
    "https://www.gk100.com/read_142954944.htm",
]:
    h = fetch(u)
    m = re.search(r"page_num:\s*(\d+)", h)
    pnum = int(m.group(1)) if m else 1
    print(f"{u} -> page_num={pnum}")
    for p in range(1, min(pnum + 1, 4)):
        pu = u if p == 1 else f"{u}?page={p}"
        ph = h if p == 1 else fetch(pu)
        imgs = [i for i in re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', ph) if "article/" in i]
        print(f"  page {p}: article imgs={len(imgs)} {imgs[:3]}")
