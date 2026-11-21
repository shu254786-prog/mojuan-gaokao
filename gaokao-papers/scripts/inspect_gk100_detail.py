import re
import urllib.request

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

for u in [
    "https://www.gk100.com/read_102035355.htm",
    "https://www.gk100.com/read_24762791.htm",
]:
    html = urllib.request.urlopen(urllib.request.Request(u, headers=HEADERS), timeout=15).read().decode("utf-8", errors="replace")
    print(f"=== {u} (len={len(html)}) ===")
    # find links or article text
    m = re.search(r'<div[^>]*class=["\'][^"\']*read[^"\']*["\'][^>]*>(.*?)<div[^>]*class=["\'][^"\']*page', html, re.S)
    if not m:
        # dump paragraphs
        ps = re.findall(r'<p[^>]*>(.*?)</p>', html, re.S)
        clean_ps = [re.sub(r"<[^>]+>", "", p).strip() for p in ps]
        clean_ps = [p for p in clean_ps if len(p) > 8]
        print("  paragraphs:", len(clean_ps))
        for p in clean_ps[:15]:
            print("   ", p[:120])
        links = re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S)
        rlinks = [(re.sub(r"<[^>]+>", "", t).strip(), h) for h, t in links if "read_" in h or "gk100" in h]
        print("  internal links:", rlinks[:15])
