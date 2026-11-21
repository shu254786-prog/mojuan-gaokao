import json
import re
import urllib.request
from urllib.parse import urljoin

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

YEAR_PAGES = {
    2025: "https://gaokao.eol.cn/e_html/gk/gkst/2025st.shtml",
    2024: "https://gaokao.eol.cn/e_html/gk/gkst/2024st.shtml",
    2023: "https://gaokao.eol.cn/e_html/gk/gkst/2023st.shtml",
    2022: "https://www.eol.cn/e_html/gk/gkst/2022st.shtml",
    2021: "https://www.eol.cn/e_html/gk/gkst/2021st.shtml",
    2020: "https://www.eol.cn/e_html/gk/gkst/2020st.shtml",
    2019: "https://www.eol.cn/e_html/gk/gkst/2019.shtml",
    2018: "https://www.eol.cn/e_html/gk/gkst/2018st.shtml",
}

VALID_SUBJECTS = ["语文", "数学", "英语", "物理", "化学", "生物", "政治", "历史", "地理", "技术"]

def fetch(u):
    req = urllib.request.Request(u, headers=HEADERS)
    raw = urllib.request.urlopen(req, timeout=15).read()
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")

def normalize_subject(raw_subj):
    # First line before spaces/newlines
    s = re.split(r"[\r\n]+", raw_subj.strip())[0].strip()
    if any(k in s for k in ["综合", "文综", "理综", "（文）", "（理）", "(文)", "(理)", "文数", "理数", "作文"]):
        return None
    for vs in VALID_SUBJECTS:
        if s == vs or s.startswith(vs):
            return vs
    return None

def is_old_zong_region(year, region_name):
    r = region_name.strip()
    if not r or "作文" in r:
        return True
    # Old national papers
    if any(k in r for k in ["全国甲", "全国乙", "全国卷I", "全国卷Ⅱ", "全国卷Ⅲ", "全国卷1", "全国卷2", "全国卷3", "全国III", "全国Ⅲ", "全国三"]):
        return True
    if ("全国I" in r or "全国II" in r or "全国卷" in r or "全国一" in r or "全国二" in r) and "新高考" not in r and "新课标" not in r:
        # 2024+ 全国一卷/二卷 are 新课标 without 文理综
        if year < 2024:
            return True
    if year <= 2019 and any(k in r for k in ["北京", "天津"]):
        return True
    batch3_2021 = ["河北", "辽宁", "福建", "湖北", "湖南", "广东", "重庆"]
    batch4_2024 = ["吉林", "黑龙江", "安徽", "江西", "广西", "贵州", "甘肃"]
    batch5_2025 = ["山西", "内蒙古", "河南", "四川", "云南", "陕西", "青海", "宁夏"]
    other_old = ["新疆", "西藏"]
    if year < 2021 and any(p in r for p in batch3_2021):
        return True
    if year < 2024 and any(p in r for p in batch4_2024):
        return True
    if year < 2025 and any(p in r for p in batch5_2025):
        return True
    if any(p in r for p in other_old):
        return True
    return False

catalog = []
seen_urls = set()

for year, url in sorted(YEAR_PAGES.items(), reverse=True):
    html = fetch(url)
    blocks = re.split(r'<div\s+class=["\']test["\'][^>]*>', html)
    if len(blocks) <= 1:
        blocks = re.split(r'<div\s+class=["\'](?:box|con|area|st)[^"\']*["\'][^>]*>', html)
    year_cnt = 0
    for blk in blocks[1:]:
        rm = re.search(r'<div\s+class=["\']head-fl[^"\']*["\'][^>]*>\s*<span>(.*?)</span>', blk, re.S)
        if not rm:
            rm = re.search(r'<(?:h2|h3|span|strong)[^>]*>([^<]{2,20}卷[^<]{0,15})</(?:h2|h3|span|strong)>', blk)
        region = re.sub(r"<[^>]+>", "", rm.group(1)).strip() if rm else ""
        if is_old_zong_region(year, region):
            continue
        for li in re.findall(r'<li>(.*?)</li>', blk, re.S):
            sm = re.search(r'<div\s+class=["\']word-xueke["\'][^>]*>(.*?)</div>', li, re.S)
            if not sm:
                sm = re.search(r'<div\s+class=["\']word-xueke["\'][^>]*>([^<]+)', li, re.S)
            if not sm:
                continue
            subj = normalize_subject(re.sub(r"<[^>]+>", "", sm.group(1)))
            if not subj:
                continue
            for href, label in re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', li, re.S):
                href = href.strip()
                if not href or href.startswith("#") or href.startswith("javascript"):
                    continue
                lbl = re.sub(r"<[^>]+>", "", label).strip()
                if lbl not in ("真题", "试题", "答案", "解析", "试题及答案", "听力"):
                    continue
                full_u = urljoin(url, href)
                if "eol.cn" in full_u and (".shtml" in full_u or ".html" in full_u) and "gkst/" not in full_u:
                    key = (year, region, subj, full_u)
                    if key not in seen_urls:
                        seen_urls.add(key)
                        catalog.append({
                            "year": year,
                            "region": region,
                            "subject": subj,
                            "kind": lbl,
                            "url": full_u,
                            "source": "eol.cn",
                        })
                        year_cnt += 1
    print(f"Year {year}: clean non-zong items = {year_cnt}")

out_file = r"e:\反重力\p1\gaokao-papers\inventory\eol_catalog_non_zong.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(catalog, f, ensure_ascii=False, indent=2)
print(f"Total clean items: {len(catalog)}")
