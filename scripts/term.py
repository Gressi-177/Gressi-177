"""Shared terminal-style SVG helpers. Stdlib only.

Animations are SMIL that start at t=0 and encode their delay in keyTimes, so a
renderer without SMIL shows the finished frame instead of a blank image.
"""
from itertools import count
from xml.sax.saxutils import escape

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SIZE = 14
CW = SIZE * 0.6  # monospace advance width
LH = 24  # line height

BG, BAR, BORDER = "#0d1117", "#161b22", "#30363d"
FG, DIM = "#c9d1d9", "#8b949e"
GREEN, BLUE, YELLOW, RED = "#3fb950", "#58a6ff", "#d29922", "#f85149"
PROMPT = [("doan", GREEN), ("@", DIM), ("vietnam", BLUE), (":", DIM), ("~", YELLOW), ("$ ", FG)]

_ids = count()


def svg(w, h, body, label):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{escape(label)}" font-family="{FONT}" font-size="{SIZE}">'
        f"<title>{escape(label)}</title>{body}</svg>\n"
    )


def window(w, h, title, body):
    dots = "".join(f'<circle cx="{20 + i * 20}" cy="18" r="6" fill="{c}"/>' for i, c in enumerate((RED, YELLOW, GREEN)))
    return (
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>'
        f'<path d="M0.5 36V10.5a10 10 0 0 1 10-10h{w - 21}a10 10 0 0 1 10 10V36z" fill="{BAR}"/>'
        f'<line x1="0" y1="36" x2="{w}" y2="36" stroke="{BORDER}"/>{dots}'
        f'<text x="{w / 2}" y="23" fill="{DIM}" text-anchor="middle">{escape(title)}</text>{body}'
    )


def appear(at):
    """Child element: hidden until `at` seconds, then visible for good."""
    if at <= 0:
        return ""
    return f'<animate attributeName="opacity" values="0;1" keyTimes="0;1" dur="{at:.2f}s" calcMode="discrete" fill="freeze"/>'


def spans(parts):
    return "".join(f'<tspan fill="{c}">{escape(t)}</tspan>' for t, c in parts)


def typed(x, y, parts, start, cps=30, prefix=()):
    """Draw `prefix` instantly at `start`, then type `parts` char by char. Returns (svg, end_time)."""
    pre = sum(len(t) for t, _ in prefix)
    n = sum(len(t) for t, _ in parts)
    end = start + n / cps
    cid = f"t{next(_ids)}"
    full = (pre + n) * CW + CW
    times = [0] + [start + i / cps for i in range(1, n + 1)]
    widths = [pre * CW] + [(pre + i) * CW for i in range(1, n)] + [full]
    anim = ""
    if n:
        keys = ";".join(f"{t / end:.4f}" for t in times)
        vals = ";".join(f"{v:.1f}" for v in widths)
        anim = f'<animate attributeName="width" values="{vals}" keyTimes="{keys}" dur="{end:.2f}s" calcMode="discrete" fill="freeze"/>'
    out = (
        f'<clipPath id="{cid}"><rect x="{x}" y="{y - LH + 6}" width="{full:.1f}" height="{LH}">{anim}</rect></clipPath>'
        f'<text x="{x}" y="{y}" clip-path="url(#{cid})" xml:space="preserve">{appear(start)}{spans(list(prefix) + list(parts))}</text>'
    )
    return out, end


def command(x, y, cmd, start, cps=30):
    return typed(x, y, [(cmd, FG)], start, cps, prefix=PROMPT)


def output(x, y, parts, at):
    return f'<text x="{x}" y="{y}" xml:space="preserve">{appear(at)}{spans(parts)}</text>'


def cursor(x, y, at):
    return (
        f'<g>{appear(at)}<rect x="{x}" y="{y - SIZE + 2}" width="{CW:.1f}" height="{SIZE + 2}" fill="{GREEN}">'
        f'<animate attributeName="opacity" values="1;0" dur="1s" calcMode="discrete" repeatCount="indefinite"/></rect></g>'
    )


def prompt_width():
    return sum(len(t) for t, _ in PROMPT) * CW
