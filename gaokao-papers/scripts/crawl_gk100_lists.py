import json
import re
import urllib.request
from urllib.parse import urljoin

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

CATS = {
    "4001": "语文",
    "4002": "数学",
    "4003": "英语",
    "4004": "史政地",
    "4005": "物化生",
}

def fetch(u):
    req = urllib.request.Request(u, headers=HEADERS)
    return urllib.request.urlopen(req, timeout=12).read().decode("utf-8", errors="replace")

results = []
seen = set()

for cid, cname in CATS.items():
    cat_cnt = 0
    y26_cnt = 0
    y19_cnt = 0
    for page in range(1, 25):
        u = f"https://www.gk100.com/zhenti/list_{cid}.htm" if page == 1 else f"https://www.gk100.com/zhenti/list_{cid}.htm?p={page}"
        try:
            html = fetch(u)
        except Exception:
            break
        links = re.findall(r'<a[^>]+href=["\'](/read_\d+\.htm)["\'][^>]*>(.*?)</a>', html, re.S)
        page_added = 0
        for href, txt in links:
            t = re.sub(r"<[^>]+>", "", txt)
            t = re.sub(r"\s+", " ", t).strip()
            if not t or "高考" not in t:
                continue
            if any(bad in t for bad in ["文综", "理综", "一模", "二模", "三模", "期中", "期末", "月考", "联考", "适应性", "模拟", "志愿", "分数线", "招生"]):
                # wait: 2025/2026 official multi-province papers sometimes say "八省联考"? Skip 联考 unless 2025/2026 official 黑吉辽/陕晋宁青
                if not any(k in t for k in ["黑吉辽", "陕晋", "晋陕"]):
                    continue
            ym = re.search(r"(20(?:1[89]|2[0-6]))", t)
            if not ym:
                continue
            year = int(ym.group(1))
            if year <= 2019 and not any(p in t for p in ["上海", "浙江", "江苏"]):
                continue
            if any(k in t for k in ["全国甲", "全国乙", "全国I", "全国II", "全国III", "全国一文", "全国一理", "全国二文", "全国二理", "全国三文", "全国三理", "文科数学", "理科数学"]):
                if year < 2024:
                    continue
            fu = urljoin("https://www.gk100.com", href)
            if fu not in seen:
                seen.add(fu)
                results.append({"year": year, "cat": cname, "title": t, "url": fu, "source": "gk100.com"})
                page_added += 1
                cat_cnt += 1
                if year == 2026:
                    y26_cnt += 1
                if year == 2019:
                    y19_cnt += 1
        if page_added == 0 and page > 2:
            break
    print(f"cat {cname} ({cid}): total={cat_cnt} | 2026={y26_cnt} | 2019={y19_cnt}")

out_p = r"e:\反重力\p1\gaokao-papers\inventory\gk100_catalog_non_zong.json"
with open(out_p, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("Saved", out_p, "total=", len(results))
