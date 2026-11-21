import concurrent.futures
import json
import os
import re
import threading
import urllib.request
from urllib.parse import urljoin

CATALOG_PATH = r"e:\反重力\p1\gaokao-papers\inventory\gk100_catalog_non_zong.json"
OUT_ROOT = r"e:\反重力\p1\gaokao-papers\collected"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

BAD_IMG_SUBS = ["qr", "icp.png", "label_sm_", "logo", "static/images", "avatar", "96f566d38f1cfde9"]

LOCK = threading.Lock()
COUNTERS = {"ok": 0, "skip": 0, "err": 0, "imgs": 0}

def safe_name(s):
    return re.sub(r'[\\/:*?"<>|\r\n]+', "_", s).strip() or "unknown"

def detect_subject(title, fallback_cat):
    for s in ["语文", "数学", "英语", "物理", "化学", "生物", "政治", "历史", "地理", "技术"]:
        if s in title:
            return s
    return fallback_cat

def detect_region(title):
    for r in [
        "新高考全国一卷", "新高考全国二卷", "新高考一卷", "新高考二卷", "全国一卷", "全国二卷",
        "新课标一卷", "新课标二卷", "新课标I卷", "新课标II卷",
        "北京", "上海", "天津", "浙江", "江苏", "山东", "海南", "广东", "福建",
        "湖北", "湖南", "河北", "辽宁", "重庆", "安徽", "江西", "广西", "贵州",
        "甘肃", "吉林", "黑龙江", "黑吉辽蒙", "黑吉辽", "河南", "四川", "云南",
        "陕西", "山西", "内蒙古", "青海", "宁夏", "陕晋宁青", "晋陕青宁", "全国"
    ]:
        if r in title:
            return r
    return "全国各省汇总"

def fetch_bytes(u, timeout=15):
    req = urllib.request.Request(u, headers=HEADERS)
    return urllib.request.urlopen(req, timeout=timeout).read()

def process_item(item):
    year = str(item["year"])
    title = item["title"]
    url = item["url"]
    if any(bad in title for bad in ["文综", "理综", "文科数学", "理科数学"]):
        with LOCK:
            COUNTERS["skip"] += 1
        return
    subj = detect_subject(title, item["cat"])
    region = detect_region(title)
    m_id = re.search(r"read_(\d+)\.htm", url)
    slug = m_id.group(1) if m_id else str(abs(hash(url)) % 1000000)

    target_dir = os.path.join(OUT_ROOT, year, safe_name(subj), safe_name(region), "gk100", f"gk100_{slug}")
    meta_path = os.path.join(target_dir, "meta.json")
    if os.path.isfile(meta_path):
        with LOCK:
            COUNTERS["skip"] += 1
        return

    try:
        html = fetch_bytes(url).decode("utf-8", errors="replace")
        # Extract main article section between <h1> or author date and 微信扫码
        start_idx = html.find("<h1")
        if start_idx == -1:
            start_idx = 0
        end_idx = html.find("微信扫码", start_idx)
        if end_idx == -1:
            end_idx = len(html)
        chunk = html[start_idx:end_idx]
        chunk = re.sub(r"<script.*?</script>", "", chunk, flags=re.S | re.I)
        chunk = re.sub(r"<style.*?</style>", "", chunk, flags=re.S | re.I)

        imgs = []
        for src in re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', chunk, re.I):
            full_s = urljoin(url, src.strip())
            if any(b in full_s.lower() for b in BAD_IMG_SUBS):
                continue
            if "gk100.com/article/" in full_s or "p1.gk100.com" in full_s:
                if full_s not in imgs:
                    imgs.append(full_s)

        txt = re.sub(r"<br\s*/?>", "\n", chunk, flags=re.I)
        txt = re.sub(r"</p>|</div>|</li>|</h\d>", "\n", txt, flags=re.I)
        txt = re.sub(r"<[^>]+>", "", txt)
        lines = [l.strip() for l in txt.splitlines()]
        lines = [l for l in lines if l and "report_options" not in l and "@context" not in l]
        full_text = "\n".join(lines)

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
            "source": "gk100.com",
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        with LOCK:
            COUNTERS["ok"] += 1
            COUNTERS["imgs"] += len(saved_imgs)
    except Exception:
        with LOCK:
            COUNTERS["err"] += 1

def main():
    items = json.load(open(CATALOG_PATH, encoding="utf-8"))
    # Download all 2026 items first (plus 2020-2025 unique items)
    items_2026 = [x for x in items if x["year"] == 2026]
    print(f"Downloading {len(items_2026)} 2026 items from gk100.com...", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        ex.map(process_item, items_2026)
    print("2026 DONE:", COUNTERS, flush=True)

if __name__ == "__main__":
    main()
