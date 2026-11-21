import concurrent.futures
import json
import os
import re
import urllib.request
from urllib.parse import urljoin

OUT_ROOT = r"e:\反重力\p1\gaokao-papers\collected"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=HEADERS), timeout=15).read().decode("utf-8", errors="replace")

def safe_name(s):
    return re.sub(r'[\\/:*?"<>|\r\n]+', "_", s).strip() or "unknown"

def detect_region(title):
    for r in [
        "全国I卷", "全国II卷", "全国一卷", "全国二卷", "新课标全国Ⅰ卷", "新课标全国Ⅱ卷",
        "新课标I卷", "新课标II卷", "新高考I卷", "新高考II卷",
        "北京", "上海", "天津", "浙江", "江苏", "山东", "海南", "广东", "福建",
        "湖北", "湖南", "河北", "辽宁", "重庆",
    ]:
        if r in title:
            return r + ("卷" if not r.endswith("卷") else "")
    return "全国通用"

def is_eligible(year, title):
    if year < 2018 or year > 2026:
        return False
    if any(b in title for b in ["全国甲", "全国乙", "全国III", "全国Ⅲ", "全国三", "大纲", "模拟", "一模", "二模", "三模", "联考", "检测", "期中", "期末"]):
        return False
    if year <= 2019 and not any(p in title for p in ["上海", "浙江", "江苏"]):
        return False
    if year < 2020 and any(p in title for p in ["全国I", "全国II", "全国一", "全国二", "北京", "天津"]):
        return False
    if year < 2024 and any(k in title for k in ["全国卷I", "全国卷II", "全国I卷", "全国II卷", "全国一卷", "全国二卷"]) and "新" not in title:
        return False
    return True

def extract_q(qurl):
    h = fetch(qurl)
    body = h[h.find("<body"):] if "<body" in h else h
    body = re.sub(r"<script.*?</script>|<style.*?</style>", "", body, flags=re.S | re.I)
    txt = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h\d>", "\n", body, flags=re.I)
    txt = re.sub(r"<[^>]+>", "", txt)
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    start = 0
    for i, l in enumerate(lines):
        if "试题内容：" in l:
            start = i + 1
            break
    end = len(lines)
    for i in range(start, len(lines)):
        if "本试题由一苇轩" in lines[i] or "收藏本题" in lines[i]:
            end = i
            break
    q_text = "\n".join(lines[start:end])
    # Extract answer block after 试题答案：
    ans_lines = []
    ans_start = -1
    for i, l in enumerate(lines):
        if "试题答案：" in l:
            ans_start = i + 1
            break
    if ans_start != -1:
        for i in range(ans_start, len(lines)):
            if any(stop in lines[i] for stop in ["您可能感兴趣", "相关试题", "报告题目内容", "版权所有"]):
                break
            ans_lines.append(lines[i])
    return q_text + ("\n\n参考答案：\n" + "\n".join(ans_lines) if ans_lines else "")

def main():
    papers = []
    seen = set()
    for page in range(1, 6):
        u = "https://www.gzywtk.com/shijuan/gkzt-list.aspx" if page == 1 else f"https://www.gzywtk.com/shijuan/gkzt-list.aspx?page={page}"
        try:
            h = fetch(u)
        except Exception:
            break
        added = 0
        for href, txt in re.findall(r'<a[^>]+href=["\'](/sjshow/\d+\.html)["\'][^>]*>(.*?)</a>', h, re.S):
            t = re.sub(r"<[^>]+>", "", txt).strip()
            ym = re.search(r"(20(?:1[89]|2[0-6]))", t)
            if not ym:
                continue
            y = int(ym.group(1))
            if not is_eligible(y, t):
                continue
            fu = urljoin("https://www.gzywtk.com", href)
            if fu not in seen:
                seen.add(fu)
                papers.append((y, t, fu))
                added += 1
        if added == 0 and page > 1:
            break

    print(f"Found {len(papers)} eligible Chinese papers on gzywtk.com", flush=True)
    ok = 0
    for y, title, url in papers:
        slug = os.path.basename(url).replace(".html", "")
        reg = detect_region(title)
        tdir = os.path.join(OUT_ROOT, str(y), "语文", safe_name(reg), "gzywtk", f"gzywtk_{slug}")
        if os.path.isfile(os.path.join(tdir, "meta.json")):
            continue
        try:
            ph = fetch(url)
            q_links = re.findall(r'href=["\'](/tmshow/\d+\.html)["\'][^>]*>(.*?)</a>', ph, re.S)
            sections = []
            for qh, qt in q_links:
                qtitle = re.sub(r"<[^>]+>", "", qt).strip()
                qtxt = extract_q(urljoin("https://www.gzywtk.com", qh))
                sections.append(f"## {qtitle}\n\n{qtxt}")
            full_text = f"# {title}\n\n" + "\n\n---\n\n".join(sections)
            os.makedirs(tdir, exist_ok=True)
            open(os.path.join(tdir, "content.txt"), "w", encoding="utf-8").write(full_text)
            open(os.path.join(tdir, "meta.json"), "w", encoding="utf-8").write(json.dumps({
                "year": y, "region": reg, "subject": "语文", "title": title,
                "source_url": url, "question_count": len(q_links),
                "saved_images": [], "text_length": len(full_text), "source": "gzywtk.com"
            }, ensure_ascii=False, indent=2))
            ok += 1
            print(f"gzywtk ok: {y} {reg} {title[:30]} (q={len(q_links)}, len={len(full_text)})", flush=True)
        except Exception as e:
            print(f"gzywtk err {url}: {e}", flush=True)
    print("GZYWTK DONE, ok=", ok, flush=True)

if __name__ == "__main__":
    main()
