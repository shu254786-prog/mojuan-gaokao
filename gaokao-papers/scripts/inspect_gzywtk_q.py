import re
import urllib.request

h = urllib.request.urlopen(urllib.request.Request("https://www.gzywtk.com/tmshow/32149.html", headers={"User-Agent": "Mozilla/5.0"}), timeout=10).read().decode("utf-8", errors="replace")
body = h[h.find("<body"):]
body = re.sub(r"<script.*?</script>|<style.*?</style>", "", body, flags=re.S | re.I)
txt = re.sub(r"<br\s*/?>|</p>|</div>|</li>", "\n", body, flags=re.I)
txt = re.sub(r"<[^>]+>", "", txt)
lines = [l.strip() for l in txt.splitlines() if l.strip()]
print("Total lines:", len(lines))
for l in lines[20:65]:
    print(" ", l[:100])
