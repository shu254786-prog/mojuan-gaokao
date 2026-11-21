import os
import re
import urllib.request
from urllib.parse import urljoin

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

AD_IMAGE_SUBSTRINGS = [
    "gongju.jpg", "qj326.jpg", "kkfsx", "2023zytb", "jlq.jpg", "dlxy.jpg",
    "tszy.jpg", "gkrs.jpg", "header_log", "jnc", "left.png", "eol.png",
    "gkcx_", "ewm", "qrcode", "logo", "wx.jpg", "app.jpg", "banner",
]

def fetch(u):
    req = urllib.request.Request(u, headers=HEADERS)
    raw = urllib.request.urlopen(req, timeout=15).read()
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")

def extract_eol_article(url):
    html = fetch(url)
    m_cnt = re.search(r'var\s+_PAGE_COUNT\s*=\s*"(\d+)"', html)
    page_count = int(m_cnt.group(1)) if m_cnt else 1
    m_name = re.search(r'var\s+_PAGE_NAME\s*=\s*"([^"]+)"', html)
    page_name = m_name.group(1) if m_name else None

    all_pages_html = [html]
    if page_count > 1 and page_name:
        base_dir = url.rsplit("/", 1)[0]
        for idx in range(1, page_count):
            sub_u = f"{base_dir}/{page_name}_{idx}.shtml"
            try:
                all_pages_html.append(fetch(sub_u))
            except Exception as e:
                print(f"  warn subpage {sub_u}: {e}")

    exam_imgs = []
    texts = []
    for phtml in all_pages_html:
        m = re.search(r'<div class="article">(.*?)<div class="mzsm', phtml, re.S)
        chunk = m.group(1) if m else phtml
        chunk_nc = re.sub(r"<!--.*?-->", "", chunk, flags=re.S)
        chunk_nc = re.sub(r"<script.*?</script>", "", chunk_nc, flags=re.S | re.I)
        chunk_nc = re.sub(r"<style.*?</style>", "", chunk_nc, flags=re.S | re.I)

        for src in re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', chunk_nc, re.I):
            src = src.strip()
            if not src or "+" in src:
                continue
            full_src = urljoin(url, src)
            if any(bad in full_src.lower() for bad in AD_IMAGE_SUBSTRINGS):
                continue
            if full_src not in exam_imgs:
                exam_imgs.append(full_src)

        txt = re.sub(r"<br\s*/?>", "\n", chunk_nc, flags=re.I)
        txt = re.sub(r"</p>|</div>|</li>", "\n", txt, flags=re.I)
        txt = re.sub(r"<[^>]+>", "", txt)
        lines = [l.strip() for l in txt.splitlines()]
        lines = [l for l in lines if l and not l.startswith("温馨提示：") and "点击此处" not in l and "掌上高考" not in l]
        if lines:
            texts.append("\n".join(lines))

    return page_count, exam_imgs, "\n\n".join(texts)

for u in [
    "https://gaokao.eol.cn/shiti/sx/202506/t20250607_2673303.shtml",
    "https://gaokao.eol.cn/shiti/hx/202506/t20250612_2674322.shtml",
    "https://gaokao.eol.cn/shiti/yw/202406/t20240613_2616374.shtml",
]:
    cnt, imgs, txt = extract_eol_article(u)
    print(f"=== {u} ===")
    print(f"  pages={cnt}, exam_imgs={len(imgs)} -> {imgs[:4]} ... {imgs[-2:]}")
    print(f"  text_len={len(txt)}, preview={txt[:200]!r}")
