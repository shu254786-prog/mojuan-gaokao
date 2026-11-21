import re
import urllib.request

url = "https://gaokao.eol.cn/e_html/gk/gkst/index.shtml"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", errors="replace")

with open(r"e:\反重力\p1\gaokao-papers\scripts\_eol_index_sample.html", "w", encoding="utf-8") as f:
    f.write(html)

m = re.search(r'<title>(.*?)</title>', html, re.S)
print("Title:", m.group(1) if m else "N/A")

idx = html.find('id="st1"')
if idx == -1:
    idx = html.find("全国一卷")
print("Snippet around 全国一卷 / st1:")
print(html[max(0, idx - 100):idx + 1500])
