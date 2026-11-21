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

# 1. Inspect gk100.com 2026 hub pages
hubs = [
    "https://www.gk100.com/read_102035355.htm",
    "https://www.gk100.com/read_40858516.htm",
]
gk100_links = {}
for h in hubs:
    html = fetch(h)
    for href, txt in re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S):
        t = re.sub(r"<[^>]+>", "", txt).strip()
        if "2026" in t and "read_" in href and "文综" not in t and "理综" not in t:
            gk100_links[urljoin(h, href)] = t

print(f"=== gk100 2026 hub extracted {len(gk100_links)} links ===")
for u, t in list(gk100_links.items())[:25]:
    print(f"  {t} -> {u}")

# 2. Check eol.cn/shiti/<subj>/ pages (depth 1..15) for 2019 and 2025/2026 missing papers
CHANNELS = [("yw","语文"),("sx","数学"),("yy","英语"),("wl","物理"),("hx","化学"),("sw","生物"),("zz","政治"),("ls","历史"),("dl","地理")]
eol_channel_items = []
for code, subj in CHANNELS:
    cnt_2025 = 0
    cnt_2024 = 0
    for p in range(0, 8):
        suffix = "index.shtml" if p == 0 else f"index_{p}.shtml"
        u = f"https://gaokao.eol.cn/shiti/{code}/{suffix}"
        try:
            html = fetch(u)
        except Exception:
            break
        for href, txt in re.findall(r'<a\b[^>]*href=["\']([^"\']*t202\d{5}_\d+\.shtml)["\'][^>]*>(.*?)</a>', html, re.S):
            t = re.sub(r"<[^>]+>", "", txt)
            t = re.sub(r"\s+", " ", t).strip()
            if not t or t == "详细":
                continue
            if "文综" in t or "理综" in t or "模" in t or "联考" in t or "一模" in t or "二模" in t or "适应性" in t or "月考" in t or "期中" in t or "期末" in t:
                continue
            if "高考" in t and any(y in t for y in ["2026", "2025", "2024", "2023", "2022", "2021", "2020", "2019", "2018"]):
                fu = urljoin(u, href)
                eol_channel_items.append({"subject": subj, "title": t, "url": fu})
                if "2025" in t:
                    cnt_2025 += 1
                if "2024" in t:
                    cnt_2024 += 1
    print(f"  eol channel {subj}: found 2025={cnt_2025}, 2024={cnt_2024}")

with open(r"e:\反重力\p1\gaokao-papers\inventory\gk100_and_eol_channels.json", "w", encoding="utf-8") as f:
    json.dump({"gk100_2026": gk100_links, "eol_channel_gaokao": eol_channel_items}, f, ensure_ascii=False, indent=2)
print("Saved inventory/gk100_and_eol_channels.json, eol_channel total:", len(eol_channel_items))
