#!/usr/bin/env python3
"""Activity digest — weekly summary of what the whole bot team did.
READ-ONLY: writes activity_digest.md, never posts."""
import os
import urllib.parse
from datetime import datetime, timezone

import botlib

REPO = "90sfoodieblog/90sfoodie-crossposter"


def main():
    token = os.environ.get("GITHUB_TOKEN", "")
    week = datetime.now(timezone.utc).strftime("%Y-W%V")
    lines = [f"# Bot activity digest — week {week}", ""]

    runs_info = []
    if token:
        try:
            url = ("https://api.github.com/repos/" + REPO + "/actions/runs?"
                   + urllib.parse.urlencode({"per_page": 100}))
            data = botlib.http_get_json(url, {"Authorization": f"Bearer {token}",
                                              "Accept": "application/vnd.github+json"})
            by_wf = {}
            for r in data.get("workflow_runs", []):
                w = r.get("name") or "unknown"
                by_wf.setdefault(w, []).append(r.get("conclusion"))
            for w in sorted(by_wf):
                cons = by_wf[w]
                ok = sum(1 for c in cons if c == "success")
                fail = sum(1 for c in cons if c == "failure")
                runs_info.append(f"- **{w}**: {len(cons)} runs, {ok} ok, {fail} failed")
            lines.append("## Workflow runs (last 100)")
            lines.extend(runs_info or ["- no runs found"])
            lines.append("")
        except Exception as e:
            lines.append(f"## Workflow runs\n- GitHub API failed: {e}\n")
    else:
        lines.append("## Workflow runs\n- GITHUB_TOKEN missing, skipped\n")

    # Highlights from other bots' data files
    hist = botlib.load_state("stats_history.json")
    if isinstance(hist, list) and hist:
        last = hist[-1]
        lines.append("## Latest stats")
        lines.append(f"- Bluesky followers: {last.get('bsky_followers', '?')}, "
                     f"Tumblr followers: {last.get('tumblr_followers', '?')}")
        lines.append("")
    try:
        with open("thread_candidates.md") as f:
            tc = f.read()
        n = tc.count("## r/")
        lines.append("## Thread scout")
        lines.append(f"- {n} candidate threads in latest scout")
        lines.append("")
    except OSError:
        pass
    try:
        with open("idea_bank.md") as f:
            ib = f.read()
        n = ib.count("## ")
        lines.append("## Idea bank")
        lines.append(f"- {n} fresh ideas in latest bank")
        lines.append("")
    except OSError:
        pass

    with open("activity_digest.md", "w") as f:
        f.write("\n".join(lines))
    print(f"Digest written for {week}.")


if __name__ == "__main__":
    main()
