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

TARGETS = [
    ("555_2026", "https://www.555edu.com/gaokaozixun/jiaoyuyaowen/2026-05-07/1253680.html"),
    ("555_2019", "https://www.555edu.com/gaokaozixun/jiaoyuyaowen/2019-06-05/172287.html"),
    ("6617_zt", "https://www.6617.com/list_2003.html"),
    ("gzywtk_gk", "https://www.gzywtk.com/shijuan/gkzt-list.aspx"),
]

for name, u in TARGETS:
    try:
        h = fetch(u)
        links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', h, re.S)
        matched = []
        for href, txt in links:
            t = re.sub(r"<[^>]+>", "", txt)
            t = re.sub(r"\s+", " ", t).strip()
            if any(y in t for y in ["2026", "2025", "2024", "2023", "2022", "2021", "2020", "2019", "2018", "真题", "试题", "试卷", "上海", "浙江", "江苏", "物理", "化学", "生物", "历史", "政治", "地理", "语文", "数学", "英语"]):
                if "文综" not in t and "理综" not in t:
                    matched.append((t[:55], urljoin(u, href)))
        print(f"=== {name} ({u}) | matched={len(matched)} ===")
        for t, fu in matched[:25]:
            print(" ", t, "->", fu)
    except Exception as e:
        print(f"=== {name} ERR: {e} ===")
