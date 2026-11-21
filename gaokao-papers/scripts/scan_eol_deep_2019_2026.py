import json
import re
import urllib.request
from urllib.parse import urljoin

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
CHANNELS = [("yw","语文"),("sx","数学"),("yy","英语"),("wl","物理"),("hx","化学"),("sw","生物"),("zz","政治"),("ls","历史"),("dl","地理")]

def fetch(u):
    req = urllib.request.Request(u, headers=HEADERS)
    raw = urllib.request.urlopen(req, timeout=12).read()
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")

found = []
seen = set()

for code, subj in CHANNELS:
    y19 = 0
    y26 = 0
    for p in range(0, 22):
        suffix = "index.shtml" if p == 0 else f"index_{p}.shtml"
        u = f"https://gaokao.eol.cn/shiti/{code}/{suffix}"
        try:
            html = fetch(u)
        except Exception:
            break
        for href, txt in re.findall(r'<a\b[^>]*href=["\']([^"\']*t20(?:1[89]|2[0-6])\d{4}_\d+\.shtml)["\'][^>]*>(.*?)</a>', html, re.S):
            t = re.sub(r"<[^>]+>", "", txt)
            t = re.sub(r"\s+", " ", t).strip()
            if not t or t == "详细":
                continue
            if any(b in t for b in ["文综", "理综", "文科数学", "理科数学", "模", "适应性", "月考", "期中", "期末", "评析", "点评", "作文"]):
                continue
            if "2019" in t and any(r in t for r in ["上海", "浙江", "江苏"]):
                fu = urljoin(u, href)
                if fu not in seen:
                    seen.add(fu)
                    found.append({"year": 2019, "subject": subj, "title": t, "url": fu})
                    y19 += 1
            elif "2026" in t and "高考" in t:
                fu = urljoin(u, href)
                if fu not in seen:
                    seen.add(fu)
                    found.append({"year": 2026, "subject": subj, "title": t, "url": fu})
                    y26 += 1
    print(f"{subj}: 2019(沪浙苏)={y19}, 2026={y26}")

out_p = r"e:\反重力\p1\gaokao-papers\inventory\eol_2019_2026_extra.json"
with open(out_p, "w", encoding="utf-8") as f:
    json.dump(found, f, ensure_ascii=False, indent=2)
print("Total extra 2019+2026 found:", len(found))
