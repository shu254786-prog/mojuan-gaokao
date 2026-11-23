import os
import re

PHYUNIT_PATH = r"e:\反重力\p1\gaokao-papers\sources\gaokao-physics-archive\PhyUnit.sty"


def load_phyunit_map(path=PHYUNIT_PATH):
    """Parse \\NewDocumentCommand \\U... definitions directly from PhyUnit.sty."""
    mapping = {}
    if not os.path.isfile(path):
        return mapping
    txt = open(path, encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"\\NewDocumentCommand\s*\\(U[A-Za-z]+)\s*\{\s*O\{([^}]*)\}\s*\}\s*\{", txt):
        cmd = m.group(1)
        default_opt = m.group(2).strip()
        body, _ = extract_braced(txt, m.end() - 1)
        body = body.replace(r"\__phyunit_space:n{#1}", r"\," if default_opt != "a" else "")
        body = body.replace(r"\__phyunit_space:n {#1}", r"\," if default_opt != "a" else "")
        body = body.replace(r"\upmu", r"\mu")
        mapping[cmd] = body.strip()
    return mapping


def extract_braced(text, start_idx):
    """Extract content inside balanced {...} starting at start_idx ('{'). Returns (inner, end_idx_after_close)."""
    if start_idx >= len(text) or text[start_idx] != "{":
        return "", start_idx
    depth = 0
    i = start_idx
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start_idx + 1 : i], i + 1
        i += 1
    return text[start_idx + 1 :], len(text)


def extract_bracketed(text, start_idx):
    """Extract content inside [...] starting at start_idx ('[')."""
    if start_idx >= len(text) or text[start_idx] != "[":
        return "", start_idx
    depth = 0
    i = start_idx
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            i += 2
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return text[start_idx + 1 : i], i + 1
        i += 1
    return text[start_idx + 1 :], len(text)


def skip_ws(text, idx):
    while idx < len(text) and text[idx].isspace():
        idx += 1
    return idx


def parse_cmd_args(text, cmd_pattern, n_args=1, has_opt=True):
    """Yield (match_start, match_end, opt_str, [arg1, ...]) for a LaTeX command."""
    pos = 0
    pat = re.compile(cmd_pattern)
    while True:
        m = pat.search(text, pos)
        if not m:
            break
        cur = m.end()
        opt = ""
        if has_opt:
            cur_ws = skip_ws(text, cur)
            if cur_ws < len(text) and text[cur_ws] == "[":
                opt, cur = extract_bracketed(text, cur_ws)
        args = []
        ok = True
        for _ in range(n_args):
            cur = skip_ws(text, cur)
            if cur < len(text) and text[cur] == "{":
                val, cur = extract_braced(text, cur)
                args.append(val)
            else:
                ok = False
                break
        if ok:
            yield m.start(), cur, opt, args
            pos = cur
        else:
            pos = m.end()


def replace_cmd(text, cmd_pattern, n_args, has_opt, repl_fn):
    """Replace all occurrences of a command using repl_fn(opt, args) -> str."""
    out = []
    last = 0
    for start, end, opt, args in parse_cmd_args(text, cmd_pattern, n_args=n_args, has_opt=has_opt):
        out.append(text[last:start])
        out.append(repl_fn(opt, args))
        last = end
    out.append(text[last:])
    return "".join(out)


def convert_tabular_to_html(tex_body, phy_map=None):
    """Convert tabular or tblr body into clean HTML table."""
    # Remove \hline, \toprule, \midrule, \bottomrule, \cline{...}
    body = re.sub(r"\\(?:hline|toprule|midrule|bottomrule)\b", "", tex_body)
    body = re.sub(r"\\cline\{[^}]*\}", "", body)
    # Handle \SetCell[r=2]{c} or \SetCell[c=2]{c}
    body = re.sub(r"\\SetCell(?:\[[^\]]*\])?\{[^}]*\}", "", body)
    # Split rows by \\
    rows = [r.strip() for r in re.split(r"\\\\", body) if r.strip()]
    if not rows:
        return ""
    html_rows = []
    for r_idx, row in enumerate(rows):
        cells = [c.strip() for c in row.split("&")]
        tag = "th" if r_idx == 0 else "td"
        tds = []
        for cell in cells:
            m_mc = re.match(r"\\multicolumn\{(\d+)\}\{[^}]*\}\{(.*)\}$", cell, re.S)
            if m_mc:
                colspan = m_mc.group(1)
                inner = normalize_math_text(m_mc.group(2).strip(), phy_map=phy_map)
                tds.append(f'<{tag} colspan="{colspan}">{inner}</{tag}>')
            else:
                inner = normalize_math_text(cell, phy_map=phy_map)
                tds.append(f"<{tag}>{inner}</{tag}>")
        html_rows.append("<tr>" + "".join(tds) + "</tr>")
    return '<table class="exam-table">' + "".join(html_rows) + "</table>"


def normalize_math_text(text, phy_map=None):
    """Normalize custom LaTeX macros and environments into KaTeX + clean Markdown/HTML."""
    if not text:
        return ""

    # Strip latex comments (un-escaped %)
    lines = []
    for line in text.splitlines():
        # keep escaped \%
        cleaned = re.sub(r"(?<!\\)%.*$", "", line)
        lines.append(cleaned)
    t = "\n".join(lines)

    # Expand PhyUnit \U... commands (with optional [a])
    if phy_map:
        def _repl_u(m):
            cmd = m.group(1)
            opt = m.group(2) or ""
            val = phy_map.get(cmd)
            if val is None:
                return m.group(0)
            if opt == "a" and val.startswith(r"\,"):
                return val[2:]
            return val
        t = re.sub(r"\\(U[A-Za-z]+)(?:\[([^\]]*)\])?", _repl_u, t)

    # Convert \( ... \) -> $ ... $ and \[ ... \] -> $$ ... $$ (avoid matching \\[4pt] linebreaks)
    t = t.replace(r"\(", "$").replace(r"\)", "$")
    t = re.sub(r"(?<!\\)\\\[", "\n$$\n", t)
    t = re.sub(r"(?<!\\)\\\]", "\n$$\n", t)

    # Custom examdisplay* macros
    t = replace_cmd(t, r"\\examdisplaycases\b", 2, False, lambda opt, args: f"\n$$\n{args[0]}\\begin{{cases}}\n{args[1]}\n\\end{{cases}}\n$$\n")
    t = replace_cmd(t, r"\\examdisplayaligned\b", 1, False, lambda opt, args: f"\n$$\n\\begin{{aligned}}\n{args[0]}\n\\end{{aligned}}\n$$\n")
    t = replace_cmd(t, r"\\examdisplayarray\b", 2, False, lambda opt, args: f"\n$$\n\\begin{{array}}{{{args[0]}}}\n{args[1]}\n\\end{{array}}\n$$\n")

    # Convert custom macros to KaTeX-standard equivalents
    t = replace_cmd(t, r"\\bs\b", 1, False, lambda opt, args: f"\\boldsymbol{{{args[0]}}}")
    t = re.sub(r"\\bs(?![A-Za-z])", r"\\boldsymbol", t)
    t = replace_cmd(t, r"\\odv\b", 2, False, lambda opt, args: f"\\frac{{\\mathrm{{d}}{args[0]}}}{{\\mathrm{{d}}{args[1]}}}")
    t = replace_cmd(t, r"\\odif\b", 1, False, lambda opt, args: f"\\mathrm{{d}}{args[0]}")
    t = replace_cmd(t, r"\\circled\b", 1, False, lambda opt, args: _circled_num(args[0]))
    t = replace_cmd(t, r"\\ccnum\b", 1, False, lambda opt, args: _circled_num(args[0]))
    t = replace_cmd(t, r"\\ronum\b", 1, False, lambda opt, args: _roman_num(args[0]))
    t = replace_cmd(t, r"\\textbf\b", 1, False, lambda opt, args: f"**{args[0]}**")

    t = re.sub(r"\\i(?![A-Za-z])", r"{\\mathrm{i}}", t)
    t = re.sub(r"\\e(?![A-Za-z])", r"{\\mathrm{e}}", t)
    t = re.sub(r"\\R(?![A-Za-z])", r"{\\mathbb{R}}", t)
    t = re.sub(r"\\Z(?![A-Za-z])", r"{\\mathbb{Z}}", t)
    t = re.sub(r"\\N(?![A-Za-z])", r"{\\mathbb{N}}", t)
    t = re.sub(r"\\degree\b", r"^\\circ", t)
    t = re.sub(r"\\fillinblank(?:\{\})?", " ______ ", t)
    t = re.sub(r"\\textasciitilde(?:\{\})?", r"\\sim ", t)
    t = re.sub(r"\\quad\b", " ", t)
    t = re.sub(r"\\qquad\b", "  ", t)
    t = re.sub(r"\\gknewpage\b|\\gkvfill\b|\\gkvfil\b|\\gkhfill\b|\\gkhfil\b|\\FloatBarrier\b|\\centering\b|\\par\b|\\allowbreak\b", "", t)
    t = replace_cmd(t, r"\\FigureLayoutDeclare\b", 3, False, lambda opt, args: "")
    t = re.sub(r"\\ref\{([^}]+)\}", lambda m: _clean_ref(m), t)
    t = t.replace("~", " ")

    # Convert align* -> $$ \begin{aligned} ... \end{aligned} $$
    t = re.sub(r"\\begin\{align\*\}(.*?)\\end\{align\*\}", lambda m: f"\n$$\n\\begin{{aligned}}\n{m.group(1).strip()}\n\\end{{aligned}}\n$$\n", t, flags=re.S)

    # Convert tables (tabular / tblr)
    t = re.sub(r"\\begin\{tabular\}\{[^}]*\}(.*?)\\end\{tabular\}", lambda m: "\n" + convert_tabular_to_html(m.group(1), phy_map=phy_map) + "\n", t, flags=re.S)
    t = re.sub(r"\\begin\{tblr\}\{[^}]*\}(.*?)\\end\{tblr\}", lambda m: "\n" + convert_tabular_to_html(m.group(1), phy_map=phy_map) + "\n", t, flags=re.S)

    # Convert circlelist / steps / enumerate / itemize
    t = _convert_lists(t)

    # Clean center wrapper and stray braces around tables
    t = re.sub(r"\\begin\{center\}|\\end\{center\}", "", t)
    t = re.sub(r"\\begin\{table\}(?:\[[^\]]*\])?|\\end\{table\}", "", t)
    t = re.sub(r"\{\s*(<table class=\"exam-table\">[\s\S]*?</table>)\s*\}", r"\1", t)

    # Replace unescaped multiple underscores (e.g., ______ from \fillinblank / \tkanswer) inside math mode
    def _clean_math_blanks(eq):
        return re.sub(r"(?<!\\)_{2,}", r"\\underline{\\hspace{2.2em}}", eq)

    t = re.sub(r"\$\$([\s\S]*?)\$\$", lambda m: f"$${_clean_math_blanks(m.group(1))}$$", t)
    t = re.sub(r"(?<!\$)\$(?!\$)([^$]+?)(?<!\$)\$(?!\$)", lambda m: f"${_clean_math_blanks(m.group(1))}$", t)

    # Normalize excessive blank lines
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    return t


def _clean_ref(m):
    label = m.group(1).strip()
    m_sub = re.match(r"^20[12]\d.*?\d+([a-dA-D])$", label)
    if m_sub:
        return f"（{m_sub.group(1).lower()}）"
    if re.match(r"^20[12]\d.*?\d+$", label):
        return ""
    return f"[{label}]"


def _circled_num(s):
    nums = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫"
    s = s.strip()
    if s.isdigit() and 1 <= int(s) <= len(nums):
        return nums[int(s) - 1]
    return f"({s})"


def _roman_num(s):
    nums = ("Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ", "Ⅴ", "Ⅵ", "Ⅶ", "Ⅷ", "Ⅸ", "Ⅹ")
    s = s.strip()
    if s.isdigit() and 1 <= int(s) <= len(nums):
        return nums[int(s) - 1]
    return f"({s})"


def _convert_lists(text):
    """Convert circlelist, steps, and enumerate/itemize into clean numbered/bulleted lines, innermost-first."""
    roman = ("i", "ii", "iii", "iv", "v", "vi", "vii", "viii")
    begin_pat = re.compile(r"\\begin\{(circlelist|steps|itemize|enumerate)\}(?:\[[^\]]*\])?")

    while True:
        begins = list(begin_pat.finditer(text))
        if not begins:
            break
        converted = False
        for bm in begins:
            env = bm.group(1)
            em = re.search(rf"\\end\{{{env}\}}", text[bm.end():])
            if not em:
                continue
            inner = text[bm.end() : bm.end() + em.start()]
            if begin_pat.search(inner):
                continue
            depth = 0
            if env == "enumerate":
                depth = len(re.findall(r"\\begin\{enumerate\}", text[:bm.start()])) - len(re.findall(r"\\end\{enumerate\}", text[:bm.start()]))
            parts = re.split(r"\\item\b", inner)
            items = [p.strip() for p in parts[1:] if p.strip()]
            lines = []
            for idx, item in enumerate(items, 1):
                if env in ("circlelist", "steps"):
                    lines.append(f"{_circled_num(str(idx))} {item}")
                elif env == "itemize":
                    lines.append(f"- {item}")
                else:
                    if depth >= 1 and idx <= len(roman):
                        lines.append(f"  （{roman[idx - 1]}）{item}")
                    else:
                        lines.append(f"（{idx}）{item}")
            rendered = "\n" + "\n".join(lines) + "\n"
            text = text[:bm.start()] + rendered + text[bm.end() + em.end():]
            converted = True
            break
        if not converted:
            break
    return text
