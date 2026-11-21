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

# 1. Check all 2026 links across the 9 subject channels (page 1 & page 2)
CHANNELS = [("yw","语文"),("sx","数学"),("yy","英语"),("wl","物理"),("hx","化学"),("sw","生物"),("zz","政治"),("ls","历史"),("dl","地理")]
print("=== Checking live 2026 papers on eol.cn/shiti/<subj>/ ===")
found_2026 = {}
for code, subj in CHANNELS:
    items = {}
    for suffix in ["index.shtml", "index_1.shtml", "index_2.shtml"]:
        u = f"https://gaokao.eol.cn/shiti/{code}/{suffix}"
        try:
            html = fetch(u)
            for href, txt in re.findall(r'<a\b[^>]*href=["\']([^"\']*t2026[^"\']*\.shtml)["\'][^>]*>(.*?)</a>', html, re.S):
                t = re.sub(r"<[^>]+>", "", txt)
                t = re.sub(r"\s+", " ", t).strip()
                if not t or t == "详细":
                    continue
                if "文综" in t or "理综" in t:
                    continue
                full_u = urljoin(u, href)
                items[full_u] = t
        except Exception:
            pass
    found_2026[subj] = items
    print(f"  {subj}: {len(items)} papers -> {list(items.values())[:6]}")

# 2. Parse 2025st..2021st..2018st index pages
YEAR_PAGES = {
    "2025": "https://gaokao.eol.cn/e_html/gk/gkst/2025st.shtml",
    "2024": "https://gaokao.eol.cn/e_html/gk/gkst/2024st.shtml",
    "2023": "https://gaokao.eol.cn/e_html/gk/gkst/2023st.shtml",
    "2022": "https://www.eol.cn/e_html/gk/gkst/2022st.shtml",
    "2021": "https://www.eol.cn/e_html/gk/gkst/2021st.shtml",
    "2020": "https://www.eol.cn/e_html/gk/gkst/2020st.shtml",
    "2018": "https://www.eol.cn/e_html/gk/gkst/2018st.shtml",
}

print("\n=== Checking eol.cn Year Index Tables (excluding 文综/理综) ===")
summary = {}
for y, url in YEAR_PAGES.items():
    html = fetch(url)
    # Extract all test blocks or links
    links = re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S | re.I)
    paper_links = []
    for href, txt in links:
        href = href.strip()
        if not href or href.startswith("#") or "gkst/" in href:
            continue
        if "/shiti/" in href or "t20" in href:
            t = re.sub(r"<[^>]+>", "", txt).strip()
            paper_links.append((t, urljoin(url, href)))
    print(f"  {y}: raw exam links={len(paper_links)}")
    summary[y] = paper_links

with open(r"e:\反重力\p1\gaokao-papers\inventory\eol_2026_probe.json", "w", encoding="utf-8") as f:
    json.dump({"2026": found_2026}, f, ensure_ascii=False, indent=2)
