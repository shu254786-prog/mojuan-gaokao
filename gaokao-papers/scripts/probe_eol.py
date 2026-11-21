import re
import urllib.request

URLS = [
    "https://gaokao.eol.cn/e_html/gk/gkst/index.shtml",
    "https://www.eol.cn/e_html/gk/2025st/index.shtml",
    "https://www.eol.cn/e_html/gk/2024st/index.shtml",
]

for url in URLS:
    print(f"=== Probing {url} ===")
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            # try utf-8 or gb18030
            try:
                html = raw.decode("utf-8")
            except UnicodeDecodeError:
                html = raw.decode("gb18030", errors="replace")
        print(f"OK len={len(html)}")
        # save sample for inspection
        links = re.findall(r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S)
        clean_links = []
        for u, t in links:
            t_clean = re.sub(r"<[^>]+>", "", t).strip()
            t_clean = re.sub(r"\s+", " ", t_clean)
            if any(k in t_clean or k in u for k in ["2026", "2025", "2024", "2023", "2022", "2021", "2020", "2019", "2018", "真题", "卷", "数学", "语文", "英语", "物理", "化学", "生物", "历史", "政治", "地理"]):
                clean_links.append((t_clean, u))
        print(f"Matched links: {len(clean_links)}")
        for t_clean, u in clean_links[:35]:
            print(f"  {t_clean[:50]} -> {u}")
    except Exception as e:
        print(f"ERR: {e}")
