import concurrent.futures
import json
import os
import re
import threading
import urllib.request
from urllib.parse import urljoin

CATALOG_PATH = r"e:\反重力\p1\gaokao-papers\inventory\eol_catalog_non_zong.json"
OUT_ROOT = r"e:\反重力\p1\gaokao-papers\collected"
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
    s = re.sub(r'[\\/:*?"<>|\r\n]+', "_", s).strip()
    return s or "unknown"

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

def extract_article_body(phtml):
    # Narrow down to article main body before comments/recommendations
    m = re.search(r'<div class="article">(.*?)<div class="mzsm', phtml, re.S)
    if not m:
        m = re.search(r'<div class="TRS_Editor">(.*?)<div class="(?:page|mzsm|shengming|gjcon)', phtml, re.S)
    if not m:
        m = re.search(r'<div class="article">(.*?)<div class="pagemore"', phtml, re.S)
    chunk = m.group(1) if m else ""
    if not chunk:
        return [], ""
    # Strip trailing recommendation / footer blocks if present
    for cut_marker in ['<div class="pagemore"', '<div class="perpage"', '<div class="gjcon"', '往期回顾']:
        idx = chunk.find(cut_marker)
        if idx != -1:
            chunk = chunk[:idx]
    chunk = re.sub(r"<!--.*?-->", "", chunk, flags=re.S)
    chunk = re.sub(r"<script.*?</script>", "", chunk, flags=re.S | re.I)
    chunk = re.sub(r"<style.*?</style>", "", chunk, flags=re.S | re.I)

    imgs = []
    for src in re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', chunk, re.I):
        src = src.strip()
        if not src or "+" in src:
            continue
        imgs.append(src)

    txt = re.sub(r"<br\s*/?>", "\n", chunk, flags=re.I)
    txt = re.sub(r"</p>|</div>|</li>|</tr>", "\n", txt, flags=re.I)
    txt = re.sub(r"<[^>]+>", "", txt)
    lines = [l.strip() for l in txt.splitlines()]
    lines = [
        l for l in lines
        if l
        and not l.startswith("温馨提示：")
        and "点击此处" not in l
        and "掌上高考" not in l
        and not l.startswith("var _PAGE_")
    ]
    return imgs, "\n".join(lines)

def process_item(item):
    year = str(item["year"])
    subj = safe_name(item["subject"])
    region = safe_name(item["region"])
    kind = safe_name(item["kind"])
    url = item["url"]

    # Unique slug from article id to avoid collisions when multiple links exist
    m_id = re.search(r"(t\d+_\d+)", url)
    slug = m_id.group(1) if m_id else str(abs(hash(url)) % 1000000)
    target_dir = os.path.join(OUT_ROOT, year, subj, region, "eol", f"{kind}_{slug}")
    meta_path = os.path.join(target_dir, "meta.json")
    if os.path.isfile(meta_path):
        with LOCK:
            COUNTERS["skip"] += 1
        return

    try:
        html0 = decode_html(fetch_bytes(url))
        m_title = re.search(r"<title>(.*?)</title>", html0, re.S)
        page_title = re.sub(r"\s+", " ", m_title.group(1)).strip() if m_title else ""
        # Double-check title doesn't sneak in 文综/理综
        if any(bad in page_title for bad in ["文综", "理综", "文科综合", "理科综合", "文科数学", "理科数学"]):
            with LOCK:
                COUNTERS["skip"] += 1
            return

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

        all_imgs = []
        all_texts = []
        for phtml in pages_html:
            imgs, txt = extract_article_body(phtml)
            for s in imgs:
                full_s = urljoin(url, s)
                if any(bad in full_s.lower() for bad in AD_IMAGE_SUBSTRINGS):
                    continue
                if full_s not in all_imgs:
                    all_imgs.append(full_s)
            if txt:
                all_texts.append(txt)

        os.makedirs(target_dir, exist_ok=True)
        saved_imgs = []
        for i, img_u in enumerate(all_imgs, 1):
            ext = os.path.splitext(img_u.split("?")[0])[1].lower()
            if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
                ext = ".jpg"
            img_name = f"page_{i:02d}{ext}"
            try:
                b = fetch_bytes(img_u, timeout=15)
                if len(b) > 2000:  # skip tiny tracking pixels
                    with open(os.path.join(target_dir, img_name), "wb") as f:
                        f.write(b)
                    saved_imgs.append(img_name)
            except Exception:
                pass

        full_text = "\n\n".join(all_texts)
        if full_text:
            with open(os.path.join(target_dir, "content.txt"), "w", encoding="utf-8") as f:
                f.write(full_text)

        meta = {
            "year": item["year"],
            "region": item["region"],
            "subject": item["subject"],
            "kind": item["kind"],
            "title": page_title,
            "source_url": url,
            "page_count": page_count,
            "saved_images": saved_imgs,
            "text_length": len(full_text),
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        with LOCK:
            COUNTERS["ok"] += 1
            COUNTERS["imgs"] += len(saved_imgs)
            done = COUNTERS["ok"] + COUNTERS["skip"] + COUNTERS["err"]
            if done % 50 == 0:
                print(f"Progress: done={done}, ok={COUNTERS['ok']}, skip={COUNTERS['skip']}, err={COUNTERS['err']}, imgs={COUNTERS['imgs']}", flush=True)
    except Exception:
        with LOCK:
            COUNTERS["err"] += 1

def main():
    items = json.load(open(CATALOG_PATH, encoding="utf-8"))
    print(f"Loaded {len(items)} items from {CATALOG_PATH}", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        ex.map(process_item, items)
    print("FINAL:", COUNTERS, flush=True)

if __name__ == "__main__":
    main()
