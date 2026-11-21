import glob
import re

math_files = glob.glob(r"e:\反重力\p1\gaokao-papers\collected\*\数学\*\latex\*.tex")
phys_files = glob.glob(r"e:\反重力\p1\gaokao-papers\collected\*\物理\*\latex\*.tex")

def scan_cmds(files, label):
    envs = set()
    cmds = set()
    for fp in files:
        txt = open(fp, encoding="utf-8", errors="replace").read()
        envs.update(re.findall(r"\\begin\{([^}]+)\}", txt))
        cmds.update(re.findall(r"(\\[A-Za-z]+)", txt))
    print(f"=== {label}: {len(files)} files ===")
    print("  envs:", sorted(envs))
    # filter out standard katex commands to see custom/unusual ones
    common = {
        r"\frac", r"\dfrac", r"\tfrac", r"\sqrt", r"\left", r"\right", r"\cdot", r"\times",
        r"\le", r"\ge", r"\leq", r"\geq", r"\neq", r"\ne", r"\approx", r"\equiv",
        r"\in", r"\notin", r"\subset", r"\subseteq", r"\cup", r"\cap", r"\emptyset",
        r"\sin", r"\cos", r"\tan", r"\cot", r"\ln", r"\log", r"\lg", r"\exp", r"\lim", r"\max", r"\min",
        r"\pi", r"\alpha", r"\beta", r"\gamma", r"\theta", r"\lambda", r"\mu", r"\phi", r"\omega", r"\Delta", r"\Omega", r"\Sigma",
        r"\vec", r"\overrightarrow", r"\overline", r"\bar", r"\hat", r"\tilde", r"\dot",
        r"\text", r"\mathrm", r"\mathbf", r"\mathbb", r"\mathcal", r"\boldsymbol",
        r"\sum", r"\prod", r"\int", r"\infty", r"\partial", r"\nabla", r"\pm", r"\mp",
        r"\quad", r"\qquad", r"\,", r"\;", r"\!", r"\circ", r"\degree", r"\angle", r"\triangle", r"\perp", r"\parallel", r"\sim", r"\cong",
        r"\cdots", r"\ldots", r"\vdots", r"\ddots", r"\forall", r"\exists",
        r"\lvert", r"\rvert", r"\lVert", r"\rVert", r"\mid", r"\not", r"\complement",
        r"\begin", r"\end", r"\item", r"\hline", r"\section", r"\chapter", r"\subsection", r"\label", r"\ref",
    }
    unusual = sorted(c for c in cmds if c not in common and not c.startswith(r"\U"))
    print(f"  non-U unusual cmds ({len(unusual)}):", unusual[:120])
    if len(unusual) > 120:
        print("   more:", unusual[120:240])

scan_cmds(math_files, "MATH")
scan_cmds(phys_files, "PHYSICS")
