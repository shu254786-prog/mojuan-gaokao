import re
import urllib.request

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

for u in [
    "https://gaokao.eol.cn/shiti/hx/202506/t20250612_2674322.shtml",
    "https://gaokao.eol.cn/shiti/yw/202506/t20250612_2674255.shtml",
    "https://gaokao.eol.cn/shiti/sx/202506/t20250607_2673303.shtml",
]:
    html = fetch(u)
    print(f"=== {u} ===")
    m = re.search(r'<div class="article">(.*?)<div class="mzsm', html, re.S)
    chunk = m.group(1) if m else html
    # strip HTML comments
    chunk_no_c = re.sub(r"<!--.*?-->", "", chunk, flags=re.S)
    imgs = [x for x in re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', chunk_no_c) if "/st/" in x or "202" in x]
    txt = re.sub(r"<[^>]+>", "\n", chunk_no_c)
    txt = re.sub(r"\n+", "\n", txt).strip()
    print("  imgs:", len(imgs), imgs[:8])
    print("  text len:", len(txt), "preview:", repr(txt[:500]))
    # check subpage links _1.shtml etc
    subp = re.findall(r't\d+_\d+_\d+\.shtml', html)
    print("  pagination:", sorted(set(subp))[:10])

print("\n=== Check channel pagination hx/ ===")
hx_html = fetch("https://gaokao.eol.cn/shiti/hx/")
m = re.search(r'var\s+countPage\s*=\s*(\d+)', hx_html)
print("countPage:", m.group(1) if m else "not found")
page_snippets = re.findall(r'.{0,60}index_1\.shtml.{0,60}', hx_html)
print("index_1 snippets:", page_snippets[:3])
for p in range(1, 5):
    try:
        u = f"https://gaokao.eol.cn/shiti/hx/index_{p}.shtml"
        h = fetch(u)
        titles = re.findall(r't20\d{6}_\d+\.shtml', h)
        print(f"  index_{p}.shtml: OK len={len(h)}, article_refs={len(set(titles))}")
    except Exception as e:
        print(f"  index_{p}.shtml: ERR {e}")
