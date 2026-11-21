import concurrent.futures
import json
import os
import re
import urllib.request
from urllib.parse import urljoin

OUT_ROOT = r"e:\反重力\p1\gaokao-papers\collected"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
AD_SUBS = ["gongju.jpg", "qj326.jpg", "kkfsx", "2023zytb", "jlq.jpg", "dlxy.jpg", "tszy.jpg", "gkrs.jpg", "header_log", "jnc", "left.png", "eol.png", "gkcx_", "ewm", "qrcode", "logo", "wx.jpg", "app.jpg", "banner", "static-gkcx", "e_include", "index/2018", "/skin/"]

def fetch_bytes(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=HEADERS), timeout=15).read()

def decode_html(raw):
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")

def safe_name(s):
    return re.sub(r'[\\/:*?"<>|\r\n]+', "_", s).strip() or "unknown"

def detect_subj(t):
    for s in ["语文", "数学", "英语", "物理", "化学", "生物", "政治", "历史", "地理", "技术"]:
        if s in t:
            return s
    return "汇总"

def detect_reg(t):
    for r in ["上海", "浙江", "江苏"]:
        if r in t:
            return r + "卷"
    return "未知"

def download_eol_item(url, title, subj):
    region = detect_reg(title)
    m_id = re.search(r"(t\d+_\d+)", url)
    slug = m_id.group(1) if m_id else str(abs(hash(url)) % 1000000)
    tdir = os.path.join(OUT_ROOT, "2019", safe_name(subj), safe_name(region), "eol", f"真题_{slug}")
    if os.path.isfile(os.path.join(tdir, "meta.json")):
        return "skip"
    h0 = decode_html(fetch_bytes(url))
    m_cnt = re.search(r'var\s+_PAGE_COUNT\s*=\s*"(\d+)"', h0)
    pcnt = int(m_cnt.group(1)) if m_cnt else 1
    m_nm = re.search(r'var\s+_PAGE_NAME\s*=\s*"([^"]+)"', h0)
    pnm = m_nm.group(1) if m_nm else None
    pages = [h0]
    if pcnt > 1 and pnm:
        bdir = url.rsplit("/", 1)[0]
        for idx in range(1, min(pcnt, 30)):
            try:
                pages.append(decode_html(fetch_bytes(f"{bdir}/{pnm}_{idx}.shtml")))
            except Exception:
                pass
    imgs, texts = [], []
    for ph in pages:
        m = re.search(r'<div class="article">(.*?)<div class="(?:mzsm|pagemore|perpage|gjcon)', ph, re.S)
        chunk = m.group(1) if m else ph
        chunk = re.sub(r"<!--.*?-->|<script.*?</script>|<style.*?</style>", "", chunk, flags=re.S | re.I)
        for s in re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', chunk, re.I):
            fu = urljoin(url, s.strip())
            if not any(b in fu.lower() for b in AD_SUBS) and fu not in imgs:
                imgs.append(fu)
        txt = re.sub(r"<br\s*/?>|</p>|</div>|</li>", "\n", chunk, flags=re.I)
        txt = re.sub(r"<[^>]+>", "", txt)
        lines = [l.strip() for l in txt.splitlines() if l.strip() and "var _PAGE" not in l]
        if lines:
            texts.append("\n".join(lines))
    os.makedirs(tdir, exist_ok=True)
    simgs = []
    for i, iu in enumerate(imgs, 1):
        try:
            b = fetch_bytes(iu)
            if len(b) > 2000:
                ext = os.path.splitext(iu.split("?")[0])[1].lower()
                if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
                    ext = ".jpg"
                fn = f"page_{i:02d}{ext}"
                open(os.path.join(tdir, fn), "wb").write(b)
                simgs.append(fn)
        except Exception:
            pass
    ft = "\n\n".join(texts)
    if ft:
        open(os.path.join(tdir, "content.txt"), "w", encoding="utf-8").write(ft)
    open(os.path.join(tdir, "meta.json"), "w", encoding="utf-8").write(json.dumps({
        "year": 2019, "region": region, "subject": subj, "title": title,
        "source_url": url, "saved_images": simgs, "text_length": len(ft), "source": "eol.cn"
    }, ensure_ascii=False, indent=2))
    return f"ok(imgs={len(simgs)},txt={len(ft)})"

def main():
    # 1. Download eol 2019 extra items
    extra = json.load(open(r"e:\反重力\p1\gaokao-papers\inventory\eol_2019_2026_extra.json", encoding="utf-8"))
    for it in extra:
        res = download_eol_item(it["url"], it["title"], it["subject"])
        print("eol2019:", it["subject"], it["title"], "->", res)

    # 2. Extract 555edu 2019 上海/浙江/江苏 links from 172287.html
    h55 = decode_html(fetch_bytes("https://www.555edu.com/gaokaozixun/jiaoyuyaowen/2019-06-05/172287.html"))
    urls_555 = []
    for prov in ["上海", "浙江", "江苏"]:
        idx = h55.find(prov)
        if idx != -1:
            seg = h55[idx:idx+2500]
            # cut at next </tr> or table row end
            tr_end = seg.find("</tr>")
            if tr_end != -1:
                seg = seg[:tr_end]
            for u, t in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', seg, re.S):
                fu = urljoin("https://www.555edu.com/", u)
                if "555edu.com" in fu and fu.endswith(".html") and fu not in [x[0] for x in urls_555]:
                    urls_555.append((fu, prov + "卷"))

    print(f"Found {len(urls_555)} 555edu 2019 links for 上海/浙江/江苏")
    for fu, reg in urls_555:
        try:
            h = decode_html(fetch_bytes(fu))
            mt = re.search(r"<title>(.*?)</title>", h, re.S)
            title = mt.group(1).split("_")[0].strip() if mt else fu
            if any(b in title for b in ["文综", "理综", "作文"]):
                continue
            subj = detect_subj(title)
            slug = os.path.basename(fu).replace(".html", "")
            tdir = os.path.join(OUT_ROOT, "2019", safe_name(subj), reg, "555edu", f"555_{slug}")
            if os.path.isfile(os.path.join(tdir, "meta.json")):
                continue
            # extract between <h1 and 相关阅读/上一篇/免责
            s_i = h.find("<h1")
            if s_i == -1: s_i = 0
            e_i = len(h)
            for mk in ["上一篇", "相关文章", "相关阅读", "版权声明"]:
                mi = h.find(mk, s_i)
                if mi != -1 and mi < e_i:
                    e_i = mi
            chunk = h[s_i:e_i]
            chunk = re.sub(r"<script.*?</script>|<style.*?</style>", "", chunk, flags=re.S | re.I)
            imgs = []
            for s in re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', chunk, re.I):
                iu = urljoin(fu, s.strip())
                if not any(b in iu.lower() for b in AD_SUBS) and ("upload" in iu or "d/" in iu or "2019" in iu):
                    if iu not in imgs:
                        imgs.append(iu)
            txt = re.sub(r"<br\s*/?>|</p>|</div>|</li>", "\n", chunk, flags=re.I)
            txt = re.sub(r"<[^>]+>", "", txt)
            lines = [l.strip() for l in txt.splitlines() if l.strip()]
            ft = "\n".join(lines)
            if len(imgs) == 0 and len(ft) < 300:
                continue
            os.makedirs(tdir, exist_ok=True)
            simgs = []
            for i, iu in enumerate(imgs, 1):
                try:
                    b = fetch_bytes(iu)
                    if len(b) > 2000:
                        ext = os.path.splitext(iu.split("?")[0])[1].lower()
                        if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
                            ext = ".jpg"
                        fn = f"page_{i:02d}{ext}"
                        open(os.path.join(tdir, fn), "wb").write(b)
                        simgs.append(fn)
                except Exception:
                    pass
            open(os.path.join(tdir, "content.txt"), "w", encoding="utf-8").write(ft)
            open(os.path.join(tdir, "meta.json"), "w", encoding="utf-8").write(json.dumps({
                "year": 2019, "region": reg, "subject": subj, "title": title,
                "source_url": fu, "saved_images": simgs, "text_length": len(ft), "source": "555edu.com"
            }, ensure_ascii=False, indent=2))
            print(f"555edu 2019: {reg} {subj} -> ok(imgs={len(simgs)}, txt={len(ft)})")
        except Exception as e:
            print(f"555edu err {fu}: {e}")

if __name__ == "__main__":
    main()
