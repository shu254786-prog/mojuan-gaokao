import re
import urllib.request

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch(u):
    req = urllib.request.Request(u, headers=HEADERS)
    raw = urllib.request.urlopen(req, timeout=15).read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("gb18030", errors="replace")

for u in [
    "https://gaokao.eol.cn/shiti/sx/202506/t20250607_2673303.shtml",
    "https://gaokao.eol.cn/shiti/hx/202606/t20260608_2742578.shtml",
    "https://gaokao.eol.cn/shiti/yy/202506/t20250612_2674288.shtml",
]:
    print(f"=== ARTICLE {u} ===")
    try:
        html = fetch(u)
        idx = html.find('class="article"')
        if idx == -1:
            idx = html.find("class='article'")
        if idx != -1:
            chunk = html[idx:idx + 12000]
            imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', chunk)
            txt = re.sub(r"<[^>]+>", "\n", chunk)
            txt = re.sub(r"\n+", "\n", txt).strip()
            print(f"  imgs={len(imgs)} {imgs[:6]}")
            print(f"  text preview:\n{txt[:450]}")
        else:
            print("  No class=article")
    except Exception as e:
        print(f"  ERR: {e}")

print("\n=== SUBJECT CHANNELS ===")
for code, name in [("yw","语文"),("sx","数学"),("yy","英语"),("wl","物理"),("hx","化学"),("sw","生物"),("zz","政治"),("ls","历史"),("dl","地理"),("zhenti","真题")]:
    u = f"https://gaokao.eol.cn/shiti/{code}/"
    try:
        html = fetch(u)
        titles = re.findall(r'href=["\']([^"\']*t20\d{6}_\d+\.shtml)["\'][^>]*>(.*?)</a>', html, re.S)
        clean = [(re.sub(r"<[^>]+>", "", t).strip(), h) for h, t in titles if "详细" not in t]
        # also check pagination count like index_1.shtml or createPageHTML
        p_m = re.search(r'createPageHTML\((\d+),', html)
        total_pages = p_m.group(1) if p_m else "?"
        print(f"  {name} ({code}): pages={total_pages}, links_on_p1={len(clean)}, sample={clean[:2]}")
    except Exception as e:
        print(f"  {name} ({code}): ERR {e}")
