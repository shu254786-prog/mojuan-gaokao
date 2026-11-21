import re
import urllib.request

h = urllib.request.urlopen(urllib.request.Request("https://www.eol.cn/e_html/gk/gkst/2019.shtml", headers={"User-Agent": "Mozilla/5.0"}), timeout=15).read().decode("utf-8", errors="replace")
# Remove comments and inspect
h_nc = re.sub(r"<!--.*?-->", "", h, flags=re.S)
print("No-comment len:", len(h_nc))
links = re.findall(r'<a[^>]+href=["\']([^"\']*t2019[^"\']*\.shtml)["\'][^>]*>(.*?)</a>', h_nc, re.S)
print("2019 links in non-comment HTML:", len(links))
for u, t in links[:20]:
    print(" ", re.sub(r"<[^>]+>", "", t).strip(), "->", u)
# also check inside comments just in case!
links_all = re.findall(r'href=["\']([^"\']*t2019[^"\']*\.shtml)["\']', h)
print("2019 links in ALL HTML:", len(links_all))
