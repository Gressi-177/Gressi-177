"""Render the last year of contributions as a terminal heatmap SVG.

Run: GITHUB_TOKEN=... python3 scripts/build_contrib.py --user Gressi-177 --out dist/contrib.svg
Self-check: python3 scripts/build_contrib.py --selftest
"""
import argparse
import json
import os
import urllib.request
from datetime import date
from pathlib import Path

from term import BLUE, DIM, FG, GREEN, LH, YELLOW, command, output, svg, window

W = 900
X = 24
CELL, GAP = 12, 3
LEVELS = {"NONE": "#161b22", "FIRST_QUARTILE": "#0e4429", "SECOND_QUARTILE": "#006d32", "THIRD_QUARTILE": "#26a641", "FOURTH_QUARTILE": "#39d353"}

QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}"""


def fetch(user, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if "errors" in body or not body.get("data", {}).get("user"):
        raise SystemExit(f"GitHub API error: {body.get('errors') or 'user not found'}")
    return body["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def streaks(counts):
    """(longest, current) runs of days with >0 contributions. Today at 0 does not break the current streak."""
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    tail = counts[:-1] if counts and counts[-1] == 0 else counts
    current = 0
    for c in reversed(tail):
        if not c:
            break
        current += 1
    return longest, current


def render(cal, user):
    weeks = cal["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    counts = [d["contributionCount"] for d in days]
    longest, current = streaks(counts)
    best = max(days, key=lambda d: d["contributionCount"])

    y = 70
    line, t = command(X, y, f"git log --author={user} --since=1.year | heatmap", 0.4)
    parts = [line]
    gx, gy = X + 36, y + 34
    t += 0.3
    for label, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        parts.append(output(X, gy + row * (CELL + GAP) + 10, [(label, DIM)], t))
    last_month = None
    for i, w in enumerate(weeks):
        x = gx + i * (CELL + GAP)
        first = w["contributionDays"][0]["date"]
        month = date.fromisoformat(first).strftime("%b")
        cells = []
        for d in w["contributionDays"]:
            r = date.fromisoformat(d["date"]).isoweekday() % 7  # Sunday = row 0
            cells.append(
                f'<rect x="{x}" y="{gy + r * (CELL + GAP)}" width="{CELL}" height="{CELL}" rx="2" fill="{LEVELS.get(d["contributionLevel"], LEVELS["NONE"])}">'
                f'<title>{d["date"]}: {d["contributionCount"]}</title></rect>'
            )
        at = t + i * 0.025
        parts.append(f'<g><animate attributeName="opacity" values="0;1" keyTimes="0;1" dur="{at:.2f}s" calcMode="discrete" fill="freeze"/>{"".join(cells)}</g>')
        if month != last_month and i < len(weeks) - 2:
            parts.append(output(x, gy - 8, [(month, DIM)], at))
            last_month = month
    t += len(weeks) * 0.025 + 0.3
    y = gy + 7 * (CELL + GAP) + 32
    parts.append(output(X, y, [
        (f"{cal['totalContributions']:,}", GREEN), (" contributions", FG), ("  .  ", DIM),
        ("longest streak ", FG), (f"{longest}d", YELLOW), ("  .  ", DIM),
        ("current streak ", FG), (f"{current}d", YELLOW), ("  .  ", DIM),
        ("best day ", FG), (f"{best['date']} ({best['contributionCount']})", BLUE),
    ], t))
    h = y + LH
    label = f"{user}: {cal['totalContributions']} contributions in the last year, longest streak {longest} days, current streak {current} days."
    return svg(W, h, window(W, h, "heatmap - last 12 months", "".join(parts)), label)


def selftest():
    assert streaks([]) == (0, 0)
    assert streaks([1, 1, 0, 1, 1, 1, 0]) == (3, 3)  # today 0 keeps yesterday's streak
    assert streaks([1, 1, 0, 0, 1]) == (2, 1)
    assert streaks([0, 0, 0]) == (0, 0)
    assert streaks([2, 0, 0, 3, 0, 0]) == (1, 0)
    days = [{"date": f"2026-01-{d:02d}", "contributionCount": d % 3, "contributionLevel": "FIRST_QUARTILE"} for d in range(4, 18)]
    cal = {"totalContributions": 9, "weeks": [{"contributionDays": days[:7]}, {"contributionDays": days[7:]}]}
    import xml.dom.minidom
    xml.dom.minidom.parseString(render(cal, "x"))
    print("selftest ok")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--user")
    p.add_argument("--out", default="dist/contrib.svg")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    if a.selftest:
        selftest()
    else:
        token = os.environ.get("GITHUB_TOKEN") or exit("GITHUB_TOKEN is required")
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(fetch(a.user, token), a.user))
        print(f"wrote {out}")
