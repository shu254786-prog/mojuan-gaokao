import glob
import json
import os
import re
import shutil

from latex_normalizer import (
    extract_braced,
    extract_bracketed,
    load_phyunit_map,
    normalize_math_text,
    parse_cmd_args,
    replace_cmd,
    skip_ws,
)

COLLECTED = r"e:\反重力\p1\gaokao-papers\collected"
BANK_ROOT = r"e:\反重力\p1\gaokao-papers\bank"
PAPERS_DIR = os.path.join(BANK_ROOT, "papers")
ASSETS_DIR = os.path.join(BANK_ROOT, "assets")
ENRICHMENT_DIR = r"e:\反重力\p1\gaokao-papers\enrichment"

PHY_MAP = load_phyunit_map()

MATH_REGION_MAP = {
    "national_paper_1": "新课标全国Ⅰ卷",
    "national_paper_2": "新课标全国Ⅱ卷",
    "new_gaokao_paper_1": "新高考全国Ⅰ卷",
    "new_gaokao_paper_2": "新高考全国Ⅱ卷",
    "beijing": "北京卷",
    "shanghai": "上海卷",
    "shanghai_spring": "上海春季卷",
    "tianjin": "天津卷",
    "zhejiang": "浙江卷",
    "jiangsu": "江苏卷",
}


def safe_slug(s):
    return re.sub(r'[\\/:*?"<>|\s]+', "_", s).strip("_")


def copy_asset(src_file, year, subj_slug, paper_slug):
    if not src_file or not os.path.isfile(src_file):
        return None
    rel_dir = os.path.join("assets", str(year), subj_slug, paper_slug)
    abs_dir = os.path.join(BANK_ROOT, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)
    fname = os.path.basename(src_file)
    dst = os.path.join(abs_dir, fname)
    if not os.path.isfile(dst):
        shutil.copy2(src_file, dst)
    return f"{rel_dir.replace(os.sep, '/')}/{fname}"


def resolve_math_fig(ref_path, tex_dir):
    """Resolve img_repaint/.../*.tex or img/.../*.png to local PNG file."""
    fname = os.path.basename(ref_path.strip()).replace(".tex", ".png")
    cand = os.path.join(tex_dir, "img", fname)
    if os.path.isfile(cand):
        return cand
    return None


def resolve_phys_fig(ref_path, tex_dir):
    """Resolve figs/02.png or \\includesvg{figs/07a} to local image file."""
    p = ref_path.strip()
    m = re.search(r"\\includesvg(?:\[[^\]]*\])?\{([^}]+)\}", p)
    if m:
        p = m.group(1).strip()
    p_os = p.replace("/", os.sep)
    for ext in ("", ".svg", ".png", ".jpg", ".jpeg"):
        cand = os.path.join(tex_dir, p_os + ext)
        if os.path.isfile(cand):
            return cand
    return None


def split_multi_methods(sol_text):
    """Split a solution string into structured methods if 【法一】/方法一 markers exist at line/item starts."""
    if not sol_text:
        return []
    # Match only when marker starts a line/paragraph (optionally preceded by (1)/(2) item prefix)
    markers = list(
        re.finditer(
            r"(?:^|\n)\s*(?:（[0-9]+）\s*)?(【(?:法|方法|解法)[一二三四五六]】|(?:方法|解法)[一二三四五六][:：])",
            sol_text,
        )
    )
    # Also check inline 【法一】 / 【法二】 at paragraph boundaries when not preceded by 同/见/按
    if len(markers) <= 1:
        inline_markers = list(re.finditer(r"(?<![同见按用由如（(])(【法[一二三四五六]】)", sol_text))
        if len(inline_markers) > len(markers):
            markers = inline_markers

    if len(markers) <= 1:
        cleaned = re.sub(r"^【法一】\s*", "", sol_text).strip()
        if not cleaned:
            return []
        return [{"id": "method_1", "label": "标准解析", "tier": "standard", "content_md": cleaned}]

    methods = []
    prefix = sol_text[: markers[0].start()].strip()
    seen_labels = {}
    for idx, m in enumerate(markers):
        start = m.end()
        end = markers[idx + 1].start() if idx + 1 < len(markers) else len(sol_text)
        body = sol_text[start:end].strip()
        if idx == 0 and prefix:
            body = prefix + "\n\n" + body
        raw_label = m.group(1).strip("【】：:")
        # Check if previous line/capture had a sub-part marker like （1）
        full_hit = m.group(0).strip()
        sub_m = re.match(r"（(\d+)）", full_hit)
        label = f"第({sub_m.group(1)})问·{raw_label}" if sub_m else raw_label
        if label in seen_labels:
            seen_labels[label] += 1
            label = f"{label}（续{seen_labels[label]}）"
        else:
            seen_labels[label] = 1
        methods.append({
            "id": f"method_{idx + 1}",
            "label": label,
            "tier": "standard" if idx == 0 else "alternative",
            "content_md": body,
        })
    return methods


TIER_ORDER = {"intuition": 0, "standard": 1, "fast": 2, "alternative": 3, "advanced": 4}


def apply_enrichment(paper):
    """Merge curated multi-tier pedagogical enrichment from enrichment/<paper_id>.json if present."""
    ep = os.path.join(ENRICHMENT_DIR, f"{paper['id']}.json")
    enr = {}
    if os.path.isfile(ep):
        enr = json.load(open(ep, encoding="utf-8"))

    multi_cnt = 0
    enr_cnt = 0
    for q in paper.get("questions", []):
        qe = enr.get(q["qid"])
        if qe:
            enr_cnt += 1
            if qe.get("topics") and not q.get("topics"):
                q["topics"] = qe["topics"]
            if qe.get("pitfall"):
                q["pitfall"] = qe["pitfall"]
            if qe.get("takeaway"):
                q["takeaway"] = qe["takeaway"]
            if qe.get("methods"):
                # Keep original standard solution unless explicitly replaced
                base_methods = list(q.get("solution_methods", []))
                if qe.get("replace_standard"):
                    merged = list(qe["methods"])
                else:
                    merged = base_methods + list(qe["methods"])
                # Ensure unique IDs and pedagogical tier ordering: intuition -> standard -> fast -> alternative -> advanced
                merged.sort(key=lambda m: TIER_ORDER.get(m.get("tier", "alternative"), 3))
                for i, m in enumerate(merged, 1):
                    if not m.get("id") or any(x is not m and x.get("id") == m.get("id") for x in merged):
                        m["id"] = f"method_{i}"
                q["solution_methods"] = merged
            q["is_enriched"] = True

        q["has_multi_method"] = len(q.get("solution_methods", [])) > 1
        if q["has_multi_method"]:
            multi_cnt += 1

    paper["multi_method_count"] = multi_cnt
    paper["enriched_count"] = enr_cnt
    return paper


def extract_math_figures_and_clean(text, tex_dir, year, paper_slug, collected_figs):
    """Extract math figure commands, copy PNGs, and replace with clean Markdown image tags."""
    def _add_fig(ref_str):
        src = resolve_math_fig(ref_str, tex_dir)
        asset_rel = copy_asset(src, year, "math", paper_slug) if src else None
        if asset_rel:
            if asset_rel not in collected_figs:
                collected_figs.append(asset_rel)
            return f"\n\n![题目配图]({asset_rel})\n\n"
        return ""

    # Handle \examfiguregroup{...}{...} and \examstatpanels{...}{...}
    text = replace_cmd(text, r"\\examfiguregroup\b", 2, True, lambda opt, args: args[1])
    text = replace_cmd(text, r"\\examstatpanels\b", 2, False, lambda opt, args: args[0] + "\n" + args[1])
    text = replace_cmd(text, r"\\solutionfigure\b", 1, False, lambda opt, args: args[0])
    text = replace_cmd(text, r"\\texfigure\b", 1, True, lambda opt, args: _add_fig(args[0]))
    text = replace_cmd(text, r"\\bitmapfigure\b", 1, True, lambda opt, args: _add_fig(args[0]))
    text = replace_cmd(text, r"\\texinclude\b", 1, True, lambda opt, args: _add_fig(args[0]))
    text = replace_cmd(text, r"\\bitmapinclude\b", 1, True, lambda opt, args: _add_fig(args[0]))
    text = replace_cmd(text, r"\\choicetexfigure\b", 1, True, lambda opt, args: _add_fig(args[0]))
    text = replace_cmd(text, r"\\includegraphics\b", 1, True, lambda opt, args: _add_fig(args[0]))
    return text


def parse_math_paper(tex_path, year, paper_key):
    raw = open(tex_path, encoding="utf-8", errors="replace").read()
    tex_dir = os.path.dirname(tex_path)
    paper_slug = safe_slug(paper_key)
    region_name = MATH_REGION_MAP.get(paper_key, paper_key)

    # Track \section{...} positions
    sections = [(m.start(), m.group(1).strip()) for m in re.finditer(r"\\section\{([^}]+)\}", raw)]

    def get_section(pos):
        sec = "综合"
        for s_pos, s_name in sections:
            if s_pos < pos:
                sec = s_name
        return sec

    # Extract top-level \begin{problem}...\end{problem} spans (allowing nested answer/solution inside!)
    prob_pat = re.compile(r"\\begin\{problem\}(.*?)\\end\{problem\}", re.S)
    prob_matches = list(prob_pat.finditer(raw))

    questions = []
    q_num = 0
    for idx, pm in enumerate(prob_matches):
        q_num += 1
        sec = get_section(pm.start())
        prob_raw = pm.group(1).strip()
        ans_raw = ""
        sol_raw = ""

        # Check nested \begin{answer} / \begin{solution} inside problem
        m_na = re.search(r"\\begin\{answer\}(.*?)\\end\{answer\}", prob_raw, re.S)
        if m_na:
            ans_raw = m_na.group(1).strip()
            prob_raw = (prob_raw[:m_na.start()] + prob_raw[m_na.end():]).strip()
        m_ns = re.search(r"\\begin\{solution\}(.*?)\\end\{solution\}", prob_raw, re.S)
        if m_ns:
            sol_raw = m_ns.group(1).strip()
            prob_raw = (prob_raw[:m_ns.start()] + prob_raw[m_ns.end():]).strip()

        # Also check trailing \begin{answer} / \answer{...} / \begin{solution} between this problem and next problem
        next_start = prob_matches[idx + 1].start() if idx + 1 < len(prob_matches) else len(raw)
        tail = raw[pm.end():next_start]
        if not ans_raw:
            m_ta = re.search(r"\\begin\{answer\}(.*?)\\end\{answer\}", tail, re.S)
            if m_ta:
                ans_raw = m_ta.group(1).strip()
            else:
                for _, _, _, args in parse_cmd_args(tail, r"\\answer\b", n_args=1, has_opt=False):
                    ans_raw = args[0].strip()
                    break
        if not sol_raw:
            m_ts = re.search(r"\\begin\{solution\}(.*?)\\end\{solution\}", tail, re.S)
            if m_ts:
                sol_raw = m_ts.group(1).strip()

        # Extract \choices {A}{B}{C}{D} (up to 4 braced args)
        choices = []
        stem_raw = prob_raw
        m_ch = re.search(r"\\choices\b", prob_raw)
        if m_ch:
            stem_raw = prob_raw[: m_ch.start()].strip()
            cur = m_ch.end()
            keys = ["A", "B", "C", "D", "E", "F"]
            for k in keys:
                cur_ws = skip_ws(prob_raw, cur)
                if cur_ws < len(prob_raw) and prob_raw[cur_ws] == "{":
                    val, cur = extract_braced(prob_raw, cur_ws)
                    c_figs = []
                    val_clean = extract_math_figures_and_clean(val, tex_dir, year, paper_slug, c_figs)
                    val_norm = normalize_math_text(val_clean, PHY_MAP)
                    choices.append({
                        "key": k,
                        "text_md": "" if c_figs and not re.sub(r"!\[.*?\]\([^)]+\)", "", val_norm).strip() else val_norm,
                        "image": c_figs[0] if c_figs else None,
                    })
                else:
                    break

        stem_figs = []
        stem_clean = extract_math_figures_and_clean(stem_raw, tex_dir, year, paper_slug, stem_figs)
        stem_md = normalize_math_text(stem_clean, PHY_MAP)

        sol_figs = []
        sol_clean = extract_math_figures_and_clean(sol_raw, tex_dir, year, paper_slug, sol_figs)
        sol_md = normalize_math_text(sol_clean, PHY_MAP)
        methods = split_multi_methods(sol_md)

        ans_norm = normalize_math_text(ans_raw, PHY_MAP)
        # Determine question type
        if choices:
            if not ans_raw.strip() and sol_raw:
                m_sol_ans = re.search(r"(?:故答案为|故选|答案(?:为|是))[:：]?\s*([A-F]+)", sol_raw)
                if m_sol_ans:
                    ans_raw = m_sol_ans.group(1).strip()
                    ans_norm = ans_raw
            ans_letters = re.findall(r"[A-F]", ans_raw.upper())
            if "多选" in sec or len(ans_letters) > 1:
                qtype = "multiple_choice"
            else:
                qtype = "single_choice"
            ans_obj = {"raw": ans_norm, "choices": ans_letters}
        elif "填空" in sec or (r"\fillinblank" in prob_raw and "解答" not in sec):
            qtype = "fill_blank"
            ans_obj = {"raw": ans_norm}
        else:
            qtype = "open_ended"
            ans_obj = {"raw": ans_norm}

        questions.append({
            "qid": f"{year}-math-{paper_slug}-q{q_num:02d}",
            "number": q_num,
            "section": sec,
            "type": qtype,
            "score": None,
            "difficulty": None,
            "topics": [],
            "stem_md": stem_md,
            "figures": stem_figs,
            "choices": choices,
            "answer": ans_obj,
            "solution_methods": methods,
            "solution_figures": sol_figs,
            "has_multi_method": len(methods) > 1,
        })

    return {
        "id": f"{year}-math-{paper_slug}",
        "year": year,
        "subject": "数学",
        "region": region_name,
        "region_key": paper_key,
        "format_tier": "structured_latex",
        "question_count": len(questions),
        "source": "Gaokao-Math-Problems-Compilation",
        "questions": questions,
    }


def parse_physics_paper(tex_path, year, region_name):
    raw = open(tex_path, encoding="utf-8", errors="replace").read()
    tex_dir = os.path.dirname(tex_path)
    paper_slug = safe_slug(region_name)

    # Split top-level \item blocks using metadata markers %% number:
    # Find each \item followed shortly by %% number:
    item_starts = [m.start() for m in re.finditer(r"\\item\s*\r?\n\s*%%\s*number:", raw)]
    questions = []
    for idx, st in enumerate(item_starts):
        en = item_starts[idx + 1] if idx + 1 < len(item_starts) else len(raw)
        blk = raw[st:en]
        # Strip trailing \end{enumerate} \end{document}
        blk = re.sub(r"\\end\{enumerate\}\s*\\end\{document\}\s*$", "", blk, flags=re.S)

        def _meta(key):
            m = re.search(rf"%%\s*{key}:\s*(.+)", blk)
            return m.group(1).strip() if m else ""

        qnum = int(_meta("number") or (idx + 1))
        qtype_cn = _meta("type")
        chapter = _meta("chapter")
        point = _meta("point")
        score_s = _meta("score")
        degree_s = _meta("degree")

        # Extract body between %% body: and %% answer:
        m_body = re.search(r"%%\s*body:\s*(.*?)(?=%%\s*answer:)", blk, re.S)
        body_raw = m_body.group(1).strip() if m_body else ""
        m_memo = re.search(r"%%\s*memo:\s*(.*)", blk, re.S)
        memo_raw = m_memo.group(1).strip() if m_memo else ""

        # Extract \memoanswer{...}
        sol_raw = ""
        for _, _, _, args in parse_cmd_args(memo_raw, r"\\memoanswer\b", n_args=1, has_opt=False):
            sol_raw = args[0]
            break

        # Extract \jdanswer{...} if present
        jd_ans = ""
        m_ans_sec = re.search(r"%%\s*answer:\s*(.*?)(?=%%\s*memo:|$)", blk, re.S)
        ans_sec = m_ans_sec.group(1).strip() if m_ans_sec else ""
        for _, _, _, args in parse_cmd_args(ans_sec, r"\\jdanswer\b", n_args=1, has_opt=False):
            jd_ans = args[0]
            break

        # Extract choices: if single/multiple choice paper item, extract top-level choices;
        # if composite/experiment (综合题/实验题) or multiple embedded choice blocks, render embedded choices inline!
        choices = []
        choice_ans = ""
        choice_count_map = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
        all_ch_matches = list(re.finditer(r"\\(two|three|four|five|six)choices\b", body_raw))
        is_composite = ("综合" in qtype_cn or "实验" in qtype_cn or len(all_ch_matches) > 1)

        if len(all_ch_matches) == 1 and not is_composite:
            m_ch = all_ch_matches[0]
            n_ch = choice_count_map[m_ch.group(1)]
            for start, end, opt, args in parse_cmd_args(body_raw[m_ch.start():], r"\\(?:two|three|four|five|six)choices\b", n_args=n_ch, has_opt=True):
                m_ca = re.search(r"answer\s*=\s*([A-F]+)", opt)
                if m_ca:
                    choice_ans = m_ca.group(1).strip()
                is_pic = "ispicture=true" in opt.replace(" ", "")
                keys = ["A", "B", "C", "D", "E", "F"]
                for ci, val in enumerate(args):
                    if is_pic:
                        src = resolve_phys_fig(val, tex_dir)
                        arel = copy_asset(src, year, "physics", paper_slug) if src else None
                        choices.append({"key": keys[ci], "text_md": "", "image": arel})
                    else:
                        c_figs = []
                        v_clean = _replace_phys_pics(val, tex_dir, year, paper_slug, c_figs)
                        choices.append({
                            "key": keys[ci],
                            "text_md": normalize_math_text(v_clean, PHY_MAP),
                            "image": c_figs[0] if c_figs else None,
                        })
                body_raw = body_raw[:m_ch.start()] + body_raw[m_ch.start() + end:]
                break
        elif all_ch_matches:
            # Render all embedded \...choices inline inside stem_md
            for kw, n_ch in choice_count_map.items():
                def _repl_inline_ch(opt, args):
                    is_pic = "ispicture=true" in opt.replace(" ", "")
                    keys = ["A", "B", "C", "D", "E", "F"]
                    rendered = []
                    for ci, val in enumerate(args):
                        if is_pic:
                            src = resolve_phys_fig(val, tex_dir)
                            arel = copy_asset(src, year, "physics", paper_slug) if src else None
                            rendered.append(f"({keys[ci]}) ![选项{keys[ci]}]({arel})" if arel else f"({keys[ci]})")
                        else:
                            rendered.append(f"({keys[ci]}) {val.strip()}")
                    return "\n\n" + "  ".join(rendered) + "\n\n"
                body_raw = replace_cmd(body_raw, rf"\\{kw}choices\b", n_ch, True, _repl_inline_ch)

        # Extract inline \xzanswer{C} and \tkanswer{...}
        xz_match = re.search(r"\\xzanswer\{([^}]*)\}", body_raw)
        if xz_match and not choice_ans:
            choice_ans = xz_match.group(1).strip()
        body_raw = re.sub(r"\\xzanswer\{[^}]*\}", "（  ）", body_raw)

        tk_answers = []
        def _repl_tk(opt, args):
            tk_answers.append(normalize_math_text(args[0], PHY_MAP))
            return " ______ "
        body_raw = replace_cmd(body_raw, r"\\tkanswer\b", 1, True, _repl_tk)

        # Extract pictures in body and solution
        stem_figs = []
        body_clean = _replace_phys_pics(body_raw, tex_dir, year, paper_slug, stem_figs)
        stem_md = normalize_math_text(body_clean, PHY_MAP)

        sol_figs = []
        sol_raw = replace_cmd(sol_raw, r"\\tkanswer\b", 1, True, lambda opt, args: args[0])
        sol_clean = _replace_phys_pics(sol_raw, tex_dir, year, paper_slug, sol_figs)
        sol_md = normalize_math_text(sol_clean, PHY_MAP)
        methods = split_multi_methods(sol_md)

        # Fallback answer from %% answer: comment if jd_ans/tk_answers missing
        comment_ans = _meta("answer")

        # Type & answer normalization
        if choices:
            ans_letters = re.findall(r"[A-F]", (choice_ans or comment_ans).upper())
            qtype = "multiple_choice" if ("多选" in qtype_cn or len(ans_letters) > 1) else "single_choice"
            ans_obj = {"raw": choice_ans or comment_ans, "choices": ans_letters}
        elif tk_answers or "填空" in qtype_cn or "实验" in qtype_cn:
            qtype = "fill_blank"
            raw_a = normalize_math_text(jd_ans or comment_ans, PHY_MAP) if (jd_ans or comment_ans) else "；".join(tk_answers)
            ans_obj = {"raw": raw_a, "sub_answers": tk_answers}
        else:
            qtype = "open_ended"
            ans_obj = {"raw": normalize_math_text(jd_ans or ans_sec or comment_ans, PHY_MAP)}

        topics = [t.strip() for t in [chapter, point] if t and t != "无"]

        questions.append({
            "qid": f"{year}-physics-{paper_slug}-q{qnum:02d}",
            "number": qnum,
            "section": qtype_cn or "物理试题",
            "type": qtype,
            "score": int(score_s) if score_s.isdigit() else None,
            "difficulty": int(degree_s) if degree_s.isdigit() else None,
            "topics": topics,
            "stem_md": stem_md,
            "figures": stem_figs,
            "choices": choices,
            "answer": ans_obj,
            "solution_methods": methods,
            "solution_figures": sol_figs,
            "has_multi_method": len(methods) > 1,
        })

    return {
        "id": f"{year}-physics-{paper_slug}",
        "year": year,
        "subject": "物理",
        "region": region_name if region_name.endswith("卷") else f"{region_name}卷",
        "region_key": region_name,
        "format_tier": "structured_latex",
        "question_count": len(questions),
        "source": "gaokao-physics-archive",
        "questions": questions,
    }


def _replace_phys_pics(text, tex_dir, year, paper_slug, collected_figs):
    pic_counts = {"one": 1, "two": 2, "three": 3, "four": 4}
    for prefix, cnt in pic_counts.items():
        def _repl(opt, args):
            md_imgs = []
            for a in args:
                src = resolve_phys_fig(a, tex_dir)
                arel = copy_asset(src, year, "physics", paper_slug) if src else None
                if arel:
                    if arel not in collected_figs:
                        collected_figs.append(arel)
                    md_imgs.append(f"![物理配图]({arel})")
            return "\n\n" + " ".join(md_imgs) + "\n\n" if md_imgs else ""
        text = replace_cmd(text, rf"\\{prefix}picture\b", cnt, True, _repl)

    def _repl_inc(opt, args):
        src = resolve_phys_fig(args[0], tex_dir)
        arel = copy_asset(src, year, "physics", paper_slug) if src else None
        if arel:
            if arel not in collected_figs:
                collected_figs.append(arel)
            return f"\n\n![物理配图]({arel})\n\n"
        return ""
    text = replace_cmd(text, r"\\(?:includegraphics|includesvg)\b", 1, True, _repl_inc)
    return text


def parse_gzywtk_chinese(meta_path):
    meta = json.load(open(meta_path, encoding="utf-8"))
    txt_path = os.path.join(os.path.dirname(meta_path), "content.txt")
    txt = open(txt_path, encoding="utf-8").read()
    year = meta["year"]
    region = meta["region"]
    paper_slug = safe_slug(f"{region}_{os.path.basename(os.path.dirname(meta_path))}")

    blocks = [b.strip() for b in txt.split("\n---\n") if b.strip()]
    questions = []
    for idx, blk in enumerate(blocks, 1):
        lines = blk.splitlines()
        title_line = lines[0].lstrip("# ").strip() if lines else f"第{idx}部分"
        body = "\n".join(lines[1:]).strip()
        # Separate answer if Reference Answer exists
        m_ans = re.search(r"\n(参考答案|答案：|解析：)(.*)$", body, re.S)
        ans_raw = ""
        if m_ans:
            ans_raw = (m_ans.group(1) + m_ans.group(2)).strip()
            body = body[: m_ans.start()].strip()
        questions.append({
            "qid": f"{year}-chinese-{paper_slug}-q{idx:02d}",
            "number": idx,
            "section": title_line,
            "type": "open_ended",
            "score": None,
            "difficulty": None,
            "topics": [],
            "stem_md": body,
            "figures": [],
            "choices": [],
            "answer": {"raw": ans_raw},
            "solution_methods": [{"id": "method_1", "label": "参考解析", "tier": "standard", "content_md": ans_raw}] if ans_raw else [],
            "solution_figures": [],
            "has_multi_method": False,
        })

    return {
        "id": f"{year}-chinese-{paper_slug}",
        "year": year,
        "subject": "语文",
        "region": region,
        "region_key": region,
        "format_tier": "structured_text",
        "question_count": len(questions),
        "source": "gzywtk.com",
        "questions": questions,
    }


def main():
    os.makedirs(PAPERS_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)

    index_entries = []
    stats = {"math_papers": 0, "math_q": 0, "phys_papers": 0, "phys_q": 0, "chi_papers": 0, "chi_q": 0, "web_packs": 0, "pdfs": 0}

    # 1. Parse 54 Math LaTeX papers
    for fp in sorted(glob.glob(os.path.join(COLLECTED, "*", "数学", "*", "latex", "*.tex"))):
        parts = fp.split(os.sep)
        year = int(parts[-5])
        paper_key = parts[-3]
        paper = apply_enrichment(parse_math_paper(fp, year, paper_key))
        out_p = os.path.join(PAPERS_DIR, f"{paper['id']}.json")
        json.dump(paper, open(out_p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        stats["math_papers"] += 1
        stats["math_q"] += paper["question_count"]
        index_entries.append({
            "id": paper["id"], "year": year, "subject": "数学", "region": paper["region"],
            "format_tier": "structured_latex", "question_count": paper["question_count"],
            "multi_method_count": paper.get("multi_method_count", 0),
            "enriched_count": paper.get("enriched_count", 0),
            "paper_file": f"papers/{paper['id']}.json",
        })

    # 2. Parse 123 Physics LaTeX papers
    for fp in sorted(glob.glob(os.path.join(COLLECTED, "*", "物理", "*", "latex", "*.tex"))):
        parts = fp.split(os.sep)
        year = int(parts[-5])
        region = parts[-3]
        paper = apply_enrichment(parse_physics_paper(fp, year, region))
        out_p = os.path.join(PAPERS_DIR, f"{paper['id']}.json")
        json.dump(paper, open(out_p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        stats["phys_papers"] += 1
        stats["phys_q"] += paper["question_count"]
        index_entries.append({
            "id": paper["id"], "year": year, "subject": "物理", "region": paper["region"],
            "format_tier": "structured_latex", "question_count": paper["question_count"],
            "multi_method_count": paper.get("multi_method_count", 0),
            "enriched_count": paper.get("enriched_count", 0),
            "paper_file": f"papers/{paper['id']}.json",
        })

    # 3. Parse 15 gzywtk Chinese structured papers
    for mp in sorted(glob.glob(os.path.join(COLLECTED, "*", "语文", "*", "gzywtk", "*", "meta.json"))):
        paper = apply_enrichment(parse_gzywtk_chinese(mp))
        out_p = os.path.join(PAPERS_DIR, f"{paper['id']}.json")
        json.dump(paper, open(out_p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        stats["chi_papers"] += 1
        stats["chi_q"] += paper["question_count"]
        index_entries.append({
            "id": paper["id"], "year": paper["year"], "subject": "语文", "region": paper["region"],
            "format_tier": "structured_text", "question_count": paper["question_count"],
            "multi_method_count": paper.get("multi_method_count", 0),
            "enriched_count": paper.get("enriched_count", 0),
            "paper_file": f"papers/{paper['id']}.json",
        })

    # 4. Index all web image/text packs + PDFs
    for root, dirs, files in os.walk(COLLECTED):
        if "meta.json" in files and f"{os.sep}gzywtk{os.sep}" not in root:
            mp = os.path.join(root, "meta.json")
            m = json.load(open(mp, encoding="utf-8"))
            rel_dir = os.path.relpath(root, COLLECTED).replace(os.sep, "/")
            stats["web_packs"] += 1
            index_entries.append({
                "id": f"{m.get('year')}-{m.get('subject')}-{safe_slug(m.get('region',''))}-{os.path.basename(root)}",
                "year": m.get("year"),
                "subject": m.get("subject"),
                "region": m.get("region"),
                "title": m.get("title", ""),
                "format_tier": "page_images",
                "image_count": len(m.get("saved_images", [])),
                "text_length": m.get("text_length", 0),
                "collected_dir": f"../collected/{rel_dir}",
                "source": m.get("source", ""),
            })
        elif os.path.basename(root) == "_pdf_originals":
            parts = root.split(os.sep)
            year = int(parts[-3])
            subj = parts[-2]
            for pf in sorted(files):
                if pf.endswith(".pdf"):
                    stats["pdfs"] += 1
                    index_entries.append({
                        "id": f"pdf-{year}-{subj}-{safe_slug(pf[:-4])}",
                        "year": year,
                        "subject": subj,
                        "region": pf[:-4],
                        "format_tier": "pdf_original",
                        "pdf_path": f"../collected/{year}/{subj}/_pdf_originals/{pf}",
                    })

    index_entries.sort(key=lambda x: (-int(x.get("year") or 0), str(x.get("subject")), str(x.get("region"))))
    json.dump({"stats": stats, "total_entries": len(index_entries), "items": index_entries},
              open(os.path.join(BANK_ROOT, "index.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("BANK BUILD COMPLETE:", stats, "| total index entries:", len(index_entries))


if __name__ == "__main__":
    main()
