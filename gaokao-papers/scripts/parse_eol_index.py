import re
import urllib.request
from urllib.parse import urljoin

BASE_URL = "https://gaokao.eol.cn/e_html/gk/gkst/index.shtml"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        raw = r.read()
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")

html = fetch(BASE_URL)
links = re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S | re.I)

year_pages = []
exam_links = []
for href, text in links:
    t = re.sub(r"<[^>]+>", "", text)
    t = re.sub(r"\s+", " ", t).strip()
    full_u = urljoin(BASE_URL, href)
    if "gkst/" in full_u and full_u.endswith(".shtml") and full_u != BASE_URL:
        if (t, full_u) not in year_pages:
            year_pages.append((t, full_u))
    elif any(k in t for k in ["语文", "数学", "英语", "物理", "化学", "生物", "政治", "历史", "地理", "技术", "真题", "答案", "解析", "卷"]) and not href.startswith("#"):
        exam_links.append((t, full_u))

print("=== Year Index Pages Found on eol.cn ===")
for t, u in year_pages:
    print(f"  {t} -> {u}")

print(f"\n=== Direct Exam Links on Current Page ({len(exam_links)}) ===")
non_zong = [(t, u) for t, u in exam_links if "文综" not in t and "理综" not in t]
zong = [(t, u) for t, u in exam_links if "文综" in t or "理综" in t]
print(f"Non-zong: {len(non_zong)}, Zong (filtered out): {len(zong)}")
for t, u in non_zong[:50]:
    print(f"  {t} -> {u}")
