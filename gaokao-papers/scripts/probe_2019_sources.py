import re
import urllib.request
from urllib.parse import urljoin

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

URLS = [
    "https://edu.sina.com.cn/gaokao/2019-06-08/doc-ihvhiews3384260.shtml",
    "https://gaokao.eol.cn/e_html/gk/gkst/sytj/js2019.shtml",
    "https://gaokao.eol.cn/e_html/gk/gkst/sytj/zj2019.shtml",
    "https://gaokao.eol.cn/e_html/gk/gkst/sytj/sh2019.shtml",
]

for u in URLS:
    print(f"=== {u} ===")
    try:
        raw = urllib.request.urlopen(urllib.request.Request(u, headers=HEADERS), timeout=15).read()
        for enc in ("utf-8", "gb18030"):
            try:
                html = raw.decode(enc); break
            except UnicodeDecodeError:
                html = raw.decode("utf-8", errors="replace")
        links = re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S)
        matched = []
        for href, txt in links:
            t = re.sub(r"<[^>]+>", "", txt).strip()
            t = re.sub(r"\s+", " ", t)
            if any(p in t for p in ["上海", "浙江", "江苏"]) and any(s in t for s in ["语文", "数学", "英语", "物理", "化学", "生物", "政治", "历史", "地理", "技术", "试题", "真题", "答案"]):
                if "文综" not in t and "理综" not in t:
                    matched.append((t, urljoin(u, href)))
        print(f"  OK len={len(html)}, matched={len(matched)}")
        for t, fu in matched[:25]:
            print(f"    {t} -> {fu}")
    except Exception as e:
        print(f"  ERR: {e}")
