"""Build the static terminal SVGs in assets/: header, section headings, footer.

Run: python3 scripts/build_assets.py   (edit the text below, rerun, commit)
"""
from pathlib import Path

from term import BLUE, DIM, FG, GREEN, LH, YELLOW, command, cursor, output, prompt_width, svg, window

W = 900
X = 24
OUT = Path(__file__).resolve().parent.parent / "assets"

# 5x7 bitmap glyphs, only the letters the name needs
GLYPHS = {
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
}


def pixel_text(text, x, y, step, start, sweep=0.012):
    """Big pixel letters that light up column by column from `start`."""
    cols, cx = [], 0
    for ch in text:
        if ch == " ":
            cx += 3
            continue
        for c in range(5):
            cols.append((cx + c, [r for r in range(7) if GLYPHS[ch][r][c] == "1"]))
        cx += 6
    out = []
    for i, (c, rows) in enumerate(cols):
        rects = "".join(f'<rect x="{x + c * step}" y="{y + r * step}" width="{step - 1}" height="{step - 1}"/>' for r in rows)
        at = start + i * sweep
        out.append(f'<g><animate attributeName="opacity" values="0;1" keyTimes="0;1" dur="{at:.2f}s" calcMode="discrete" fill="freeze"/>{rects}</g>')
    return f'<g fill="{GREEN}" filter="url(#glow)">{"".join(out)}</g>', start + len(cols) * sweep


GLOW = (
    '<defs><filter id="glow" x="-10%" y="-10%" width="120%" height="120%">'
    '<feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
    "</filter></defs>"
)


def header():
    parts, y = [], 70
    line, t = command(X, y, 'figlet -f pixel "doan tran"', 0.4)
    parts.append(line)
    name, t = pixel_text("DOAN TRAN", X + 4, y + 16, 11, t + 0.2)
    parts.append(name)
    y += 16 + 7 * 11 + 34
    stack = ["TypeScript", "React", "Next.js", "Node.js", "NestJS", "MongoDB", "PostgreSQL", "Docker"]
    stack_out = [p for s in stack for p in ((s, BLUE), ("  .  ", DIM))][:-1]
    script = [
        ("whoami", [("Doan Tran", GREEN), (" - fullstack developer, frontend background, Vietnam", FG)]),
        ("cat stack.txt", stack_out),
        ("cat status.txt", [("open to fullstack roles", GREEN)]),
    ]
    for cmd, out in script:
        line, t = command(X, y, cmd, t + 0.5)
        parts += [line, output(X, y + LH, out, t + 0.25)]
        t += 0.25
        y += LH * 2
    parts.append(command(X, y, "", t + 0.4)[0])
    parts.append(cursor(X + prompt_width(), y, t + 0.4))
    h = y + 30
    label = "Doan Tran, fullstack developer with a frontend background, based in Vietnam. Stack: " + ", ".join(stack) + ". Open to fullstack roles."
    return svg(W, h, GLOW + window(W, h, "doan@vietnam: ~ - zsh", "".join(parts)), label)


def heading(cmd, comment):
    h = 44
    line, t = command(16, 28, cmd, 0.3, cps=24)
    body = (
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="8" fill="#0d1117" stroke="#30363d"/>{line}'
        f'<text x="{W - 16}" y="28" fill="{DIM}" text-anchor="end"># {comment}</text>'
    )
    return svg(W, h, body, f"{comment}: $ {cmd}")


HEADINGS = {
    "h-activity": ("git log --since=1.year", "activity"),
}

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    files = {"header": header(), **{k: heading(*v) for k, v in HEADINGS.items()}}
    for name, content in files.items():
        (OUT / f"{name}.svg").write_text(content)
        print(f"assets/{name}.svg  {len(content)} bytes")
