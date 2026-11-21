import concurrent.futures
import json
import os
import re
import threading
import urllib.request
from urllib.parse import urljoin

CHAN_PATH = r"e:\反重力\p1\gaokao-papers\inventory\gk100_and_eol_channels.json"
COLLECTED_ROOT = r"e:\反重力\p1\gaokao-papers\collected"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

AD_IMAGE_SUBSTRINGS = [
    "gongju.jpg", "qj326.jpg", "kkfsx", "2023zytb", "jlq.jpg", "dlxy.jpg",
    "tszy.jpg", "gkrs.jpg", "header_log", "jnc", "left.png", "eol.png",
    "gkcx_", "ewm", "qrcode", "logo", "wx.jpg", "app.jpg", "banner",
    "static-gkcx", "e_include", "index/2018",
]

LOCK = threading.Lock()
COUNTERS = {"ok": 0, "skip": 0, "err": 0, "imgs": 0}

def safe_name(s):
    return re.sub(r'[\\/:*?"<>|\r\n]+', "_", s).strip() or "unknown"

def fetch_bytes(u, timeout=15):
    req = urllib.request.Request(u, headers=HEADERS)
    return urllib.request.urlopen(req, timeout=timeout).read()

def decode_html(raw):
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")

def detect_year(title, url):
    m = re.search(r"(20(?:1[89]|2[0-6]))", title)
    if m:
        return int(m.group(1))
    m2 = re.search(r"/(20(?:1[89]|2[0-6]))\d{2}/", url)
    return int(m2.group(1)) if m2 else None

def detect_region(title):
    for r in [
        "新高考全国I卷", "新高考全国II卷", "新高考全国一卷", "新高考全国二卷",
        "新课标I卷", "新课标II卷", "新课标一卷", "新课标二卷",
        "全国I卷", "全国II卷", "全国一卷", "全国二卷",
        "北京", "上海", "天津", "浙江", "江苏", "山东", "海南", "广东", "福建",
        "湖北", "湖南", "河北", "辽宁", "重庆", "安徽", "江西", "广西", "贵州",
        "甘肃", "吉林", "黑龙江", "黑吉辽蒙", "黑吉辽", "河南", "四川", "云南",
        "陕西", "山西", "内蒙古", "青海", "宁夏", "陕晋宁青", "晋陕青宁",
    ]:
        if r in title:
            return r + ("卷" if not r.endswith("卷") else "")
    return "全国通用"

def is_eligible(year, title):
    if not year or year < 2018:
        return False
    bad = [
        "文综", "理综", "文科综合", "理科综合", "文科数学", "理科数学", "文数", "理数",
        "全国甲", "全国乙", "全国III", "全国Ⅲ", "全国三", "评析", "点评", "作文题", "微写作",
        "一模", "二模", "三模", "模考", "适应性", "月考", "期中", "期末", "新疆", "西藏",
    ]
    if any(b in title for b in bad):
        return False
    if year <= 2019:
        return any(p in title for p in ["上海", "浙江", "江苏"])
    if year < 2024 and any(k in title for k in ["全国卷I", "全国卷II", "全国I卷", "全国II卷", "全国一卷", "全国二卷"]) and "新高考" not in title and "新课标" not in title:
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

def extract_article_body(phtml):
    m = re.search(r'<div class="article">(.*?)<div class="mzsm', phtml, re.S)
    if not m:
        m = re.search(r'<div class="TRS_Editor">(.*?)<div class="(?:page|mzsm|shengming|gjcon)', phtml, re.S)
    if not m:
        m = re.search(r'<div class="article">(.*?)<div class="pagemore"', phtml, re.S)
    chunk = m.group(1) if m else ""
    if not chunk:
        return [], ""
    for cut_marker in ['<div class="pagemore"', '<div class="perpage"', '<div class="gjcon"', '往期回顾']:
        idx = chunk.find(cut_marker)
        if idx != -1:
            chunk = chunk[:idx]
    chunk = re.sub(r"<!--.*?-->", "", chunk, flags=re.S)
    chunk = re.sub(r"<script.*?</script>", "", chunk, flags=re.S | re.I)
    chunk = re.sub(r"<style.*?</style>", "", chunk, flags=re.S | re.I)
    imgs = [s.strip() for s in re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', chunk, re.I) if s.strip() and "+" not in s]
    txt = re.sub(r"<br\s*/?>", "\n", chunk, flags=re.I)
    txt = re.sub(r"</p>|</div>|</li>|</tr>", "\n", txt, flags=re.I)
    txt = re.sub(r"<[^>]+>", "", txt)
    lines = [l.strip() for l in txt.splitlines()]
    lines = [l for l in lines if l and not l.startswith("温馨提示：") and "点击此处" not in l and "掌上高考" not in l and not l.startswith("var _PAGE_")]
    return imgs, "\n".join(lines)

def collect_existing_slugs():
    slugs = set()
    for r, d, f in os.walk(COLLECTED_ROOT):
        if "meta.json" in f:
            base = os.path.basename(r)
            m = re.search(r"(t\d+_\d+)", base)
            if m:
                slugs.add(m.group(1))
    return slugs

EXISTING_SLUGS = collect_existing_slugs()

def process_item(item):
    url = item["url"]
    title = item["title"]
    subj = item["subject"]
    year = detect_year(title, url)
    if not is_eligible(year, title):
        with LOCK:
            COUNTERS["skip"] += 1
        return
    m_id = re.search(r"(t\d+_\d+)", url)
    slug = m_id.group(1) if m_id else str(abs(hash(url)) % 1000000)
    if slug in EXISTING_SLUGS:
        with LOCK:
            COUNTERS["skip"] += 1
        return

    region = detect_region(title)
    kind = "答案解析" if ("答案" in title or "解析" in title) and "试题" not in title and "真题" not in title else "试题及答案"
    target_dir = os.path.join(COLLECTED_ROOT, str(year), safe_name(subj), safe_name(region), "eol", f"{kind}_{slug}")
    meta_path = os.path.join(target_dir, "meta.json")
    if os.path.isfile(meta_path):
        with LOCK:
            COUNTERS["skip"] += 1
        return

    try:
        html0 = decode_html(fetch_bytes(url))
        m_cnt = re.search(r'var\s+_PAGE_COUNT\s*=\s*"(\d+)"', html0)
        page_count = int(m_cnt.group(1)) if m_cnt else 1
        m_name = re.search(r'var\s+_PAGE_NAME\s*=\s*"([^"]+)"', html0)
        page_name = m_name.group(1) if m_name else None

        pages_html = [html0]
        if page_count > 1 and page_name:
            base_dir = url.rsplit("/", 1)[0]
            for idx in range(1, min(page_count, 50)):
                sub_u = f"{base_dir}/{page_name}_{idx}.shtml"
                try:
                    pages_html.append(decode_html(fetch_bytes(sub_u)))
                except Exception:
                    pass

        all_imgs, all_texts = [], []
        for phtml in pages_html:
            imgs, txt = extract_article_body(phtml)
            for s in imgs:
                full_s = urljoin(url, s)
                if not any(bad in full_s.lower() for bad in AD_IMAGE_SUBSTRINGS) and full_s not in all_imgs:
                    all_imgs.append(full_s)
            if txt:
                all_texts.append(txt)

        os.makedirs(target_dir, exist_ok=True)
        saved_imgs = []
        for i, iu in enumerate(all_imgs, 1):
            ext = os.path.splitext(iu.split("?")[0])[1].lower()
            if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
                ext = ".jpg"
            iname = f"page_{i:02d}{ext}"
            try:
                b = fetch_bytes(iu, timeout=15)
                if len(b) > 2000:
                    with open(os.path.join(target_dir, iname), "wb") as f:
                        f.write(b)
                    saved_imgs.append(iname)
            except Exception:
                pass

        full_text = "\n\n".join(all_texts)
        if full_text:
            with open(os.path.join(target_dir, "content.txt"), "w", encoding="utf-8") as f:
                f.write(full_text)

        meta = {
            "year": year,
            "region": region,
            "subject": subj,
            "kind": kind,
            "title": title,
            "source_url": url,
            "page_count": page_count,
            "saved_images": saved_imgs,
            "text_length": len(full_text),
            "source": "eol.cn-channel",
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        with LOCK:
            COUNTERS["ok"] += 1
            COUNTERS["imgs"] += len(saved_imgs)
            done = COUNTERS["ok"] + COUNTERS["skip"] + COUNTERS["err"]
            if done % 50 == 0:
                print(f"Channel Progress: done={done}, ok={COUNTERS['ok']}, skip={COUNTERS['skip']}, err={COUNTERS['err']}, imgs={COUNTERS['imgs']}", flush=True)
    except Exception:
        with LOCK:
            COUNTERS["err"] += 1

def main():
    raw = json.load(open(CHAN_PATH, encoding="utf-8"))
    items = raw.get("eol_channel_gaokao", [])
    print(f"Loaded {len(items)} channel items (existing slugs={len(EXISTING_SLUGS)})", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        ex.map(process_item, items)
    print("CHANNEL DONE:", COUNTERS, flush=True)

if __name__ == "__main__":
    main()
