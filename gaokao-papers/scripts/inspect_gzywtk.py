import re
import urllib.request

h = urllib.request.urlopen(urllib.request.Request("https://www.gzywtk.com/sjshow/3057.html", headers={"User-Agent": "Mozilla/5.0"}), timeout=12).read().decode("utf-8", errors="replace")
idx = h.find('class="sjshowul"')
print(h[idx:idx+1800] if idx != -1 else "not found")
