import re
import urllib.request
from urllib.parse import urljoin

PAGES = {
    "2026": "https://gaokao.eol.cn/e_html/gk/gkst/index.shtml",
    "2025": "https://gaokao.eol.cn/e_html/gk/gkst/2025st.shtml",
    "2024": "https://gaokao.eol.cn/e_html/gk/gkst/2024st.shtml",
    "2023": "https://gaokao.eol.cn/e_html/gk/gkst/2023st.shtml",
    "2022": "https://www.eol.cn/e_html/gk/gkst/2022st.shtml",
    "2021": "https://www.eol.cn/e_html/gk/gkst/2021st.shtml",
    "2020": "https://www.eol.cn/e_html/gk/gkst/2020st.shtml",
    "2018": "https://www.eol.cn/e_html/gk/gkst/2018st.shtml",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

for year, url in PAGES.items():
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        raw = urllib.request.urlopen(req, timeout=15).read()
        try:
            html = raw.decode("utf-8")
        except UnicodeDecodeError:
            html = raw.decode("gb18030", errors="replace")
        # find all external or .shtml/.html/.pdf links that aren't index/empty/#
        all_links = re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S | re.I)
        valid = []
        for href, txt in all_links:
            href = href.strip()
            if not href or href.startswith("#") or href.startswith("javascript"):
                continue
            if any(x in href for x in ["eol.cn/gaokao", "gaokao.eol.cn/", ".shtml", ".html", ".pdf"]) and "gkst/" not in href:
                t = re.sub(r"<[^>]+>", "", txt).strip()
                valid.append((t, urljoin(url, href)))
        print(f"{year} ({url}): len={len(html)}, valid_article_links={len(valid)}")
        for t, u in valid[:6]:
            print(f"    [{t}] -> {u}")
    except Exception as e:
        print(f"{year}: ERR {e}")
