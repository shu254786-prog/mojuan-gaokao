import concurrent.futures
import json
import os
import re
import threading
import urllib.request
from urllib.parse import urljoin

OUT_ROOT = r"e:\反重力\p1\gaokao-papers\collected"
CAT_PATH = r"e:\反重力\p1\gaokao-papers\inventory\6617_catalog_non_zong.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

BAD_IMG_SUBS = ["qr", "icp", "logo", "static", "avatar", "banner", "label_sm", "5596cb39128a6e3a", "d31cb2360aea9217"]
LOCK = threading.Lock()
COUNTERS = {"ok": 0, "skip": 0, "err": 0, "imgs": 0}

def safe_name(s):
    return re.sub(r'[\\/:*?"<>|\r\n]+', "_", s).strip() or "unknown"

def fetch_bytes(u, timeout=15):
    req = urllib.request.Request(u, headers=HEADERS)
    return urllib.request.urlopen(req, timeout=timeout).read()

def detect_subject(title):
    for s in ["语文", "数学", "英语", "物理", "化学", "生物", "政治", "历史", "地理", "技术"]:
        if s in title:
            return s
    return "全科九科汇总"

def detect_region(title):
    for r in [
        "新高考一卷", "新高考二卷", "新高考1卷", "新高考2卷", "全国一卷", "全国二卷",
        "北京", "上海", "天津", "浙江", "江苏", "山东", "海南", "广东", "福建",
        "湖北", "湖南", "河北", "辽宁", "重庆", "安徽", "江西", "广西", "贵州",
        "甘肃", "吉林", "黑龙江", "黑吉辽蒙", "黑吉辽", "河南", "四川", "云南",
        "陕西", "山西", "内蒙古", "青海", "宁夏", "陕晋宁青", "晋陕青宁",
    ]:
        if r in title:
            return r
    return "全国汇总"

def is_eligible(year, title):
    if year < 2018:
        return False
    if any(b in title for b in ["文综", "理综", "文科数学", "理科数学", "一模", "二模", "三模", "期中", "期末", "月考", "适应性", "分数线", "志愿", "招生", "作文出炉", "作文题目"]):
        return False
    if year <= 2019 and not any(p in title for p in ["上海", "浙江", "江苏"]):
        return False
    batch3 = ["河北", "辽宁", "福建", "湖北", "湖南", "广东", "重庆"]
    batch4 = ["吉林", "黑龙江", "安徽", "江西", "广西", "贵州", "甘肃"]
    batch5 = ["山西", "内蒙古", "河南", "四川", "云南", "陕西", "青海", "宁夏"]
    if year < 2021 and any(p in title for p in batch3):
        return False
    if year < 2024 and any(p in title for p in batch4):
        return False
    if year < 2025 and any(p in title for p in batch5):
        return False
    return True

def crawl_catalog():
    items = []
    seen = set()
    for p in range(1, 21):
        u = "https://www.6617.com/list_2003.html" if p == 1 else f"https://www.6617.com/list_2003.html?p={p}"
        try:
            html = fetch_bytes(u).decode("utf-8", errors="replace")
        except Exception:
            break
        for href, txt in re.findall(r'<a[^>]+href=["\']([^"\']*p_\d+\.html)["\'][^>]*>(.*?)</a>', html, re.S):
            t = re.sub(r"<[^>]+>", "", txt)
            t = re.sub(r"\s+", " ", t).strip()
            ym = re.search(r"(20(?:1[89]|2[0-6]))", t)
            if not ym:
                continue
            y = int(ym.group(1))
            if not is_eligible(y, t):
                continue
            fu = urljoin("https://www.6617.com/", href)
            if fu not in seen:
                seen.add(fu)
                items.append({"year": y, "title": t, "url": fu, "source": "6617.com"})
    with open(CAT_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"Crawled 6617 list_2003: {len(items)} eligible items", flush=True)
    return items

def process_item(item):
    year = str(item["year"])
    title = item["title"]
    url = item["url"]
    subj = detect_subject(title)
    region = detect_region(title)
    m_id = re.search(r"p_(\d+)\.html", url)
    slug = m_id.group(1) if m_id else str(abs(hash(url)) % 1000000)

    target_dir = os.path.join(OUT_ROOT, year, safe_name(subj), safe_name(region), "6617", f"6617_{slug}")
    meta_path = os.path.join(target_dir, "meta.json")
    if os.path.isfile(meta_path):
        with LOCK:
            COUNTERS["skip"] += 1
        return

    try:
        html = fetch_bytes(url).decode("utf-8", errors="replace")
        start_idx = html.find("<h1")
        if start_idx == -1:
            start_idx = 0
        # cut before related articles
        end_idx = len(html)
        for marker in ["相关推荐", "猜你喜欢", "上一篇", "免责声明", "icp"]:
            mi = html.find(marker, start_idx)
            if mi != -1 and mi < end_idx:
                end_idx = mi
        chunk = html[start_idx:end_idx]
        chunk = re.sub(r"<script.*?</script>", "", chunk, flags=re.S | re.I)
        chunk = re.sub(r"<style.*?</style>", "", chunk, flags=re.S | re.I)

        imgs = []
        for src in re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', chunk, re.I):
            full_s = urljoin(url, src.strip())
            if any(b in full_s.lower() for b in BAD_IMG_SUBS):
                continue
            if ("6617.com/article/" in full_s or "p1.6617.com" in full_s) and full_s not in imgs:
                imgs.append(full_s)

        txt = re.sub(r"<br\s*/?>", "\n", chunk, flags=re.I)
        txt = re.sub(r"</p>|</div>|</li>|</h\d>", "\n", txt, flags=re.I)
        txt = re.sub(r"<[^>]+>", "", txt)
        lines = [l.strip() for l in txt.splitlines() if l.strip()]
        full_text = "\n".join(lines)

        if len(imgs) == 0 and len(full_text) < 1000:
            with LOCK:
                COUNTERS["skip"] += 1
            return

        os.makedirs(target_dir, exist_ok=True)
        saved_imgs = []
        for i, iu in enumerate(imgs, 1):
            ext = os.path.splitext(iu.split("?")[0])[1].lower()
            if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
                ext = ".jpg"
            iname = f"page_{i:02d}{ext}"
            try:
                b = fetch_bytes(iu, timeout=15)
                if len(b) > 3000:
                    with open(os.path.join(target_dir, iname), "wb") as f:
                        f.write(b)
                    saved_imgs.append(iname)
            except Exception:
                pass

        if full_text:
            with open(os.path.join(target_dir, "content.txt"), "w", encoding="utf-8") as f:
                f.write(full_text)

        meta = {
            "year": item["year"],
            "region": region,
            "subject": subj,
            "title": title,
            "source_url": url,
            "saved_images": saved_imgs,
            "text_length": len(full_text),
            "source": "6617.com",
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        with LOCK:
            COUNTERS["ok"] += 1
            COUNTERS["imgs"] += len(saved_imgs)
            if COUNTERS["ok"] % 25 == 0:
                print(f"6617 progress: ok={COUNTERS['ok']}, skip={COUNTERS['skip']}, err={COUNTERS['err']}, imgs={COUNTERS['imgs']}", flush=True)
    except Exception:
        with LOCK:
            COUNTERS["err"] += 1

def main():
    items = crawl_catalog()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        ex.map(process_item, items)
    print("6617 DONE:", COUNTERS, flush=True)

if __name__ == "__main__":
    main()
