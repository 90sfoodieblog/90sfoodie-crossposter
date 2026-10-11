#!/usr/bin/env python3
"""Tumblr OAuth diagnostic — tests whether the stored OAuth credentials
produce valid signatures. READ-ONLY: makes no posts."""
import urllib.parse
import urllib.request

import botlib


def test(name, method, url, params=None):
    creds = botlib._tumblr_creds()
    if not creds:
        print(f"{name}: SKIPPED (secrets missing)")
        return
    ck, cs, tok, ts, blog = creds
    params = params or {}
    auth = botlib._oauth1_header(url, params, ck, cs, tok, ts, method=method)
    if method == "GET":
        if params:
            url = url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"Authorization": auth})
    else:
        body = botlib._rfc3986_body(params)
        req = urllib.request.Request(url, data=body, headers={"Authorization": auth})
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read().decode()
        print(f"{name}: SUCCESS (HTTP {r.status}) — {data[:120]}")
    except Exception as e:
        try:
            detail = e.read().decode()[:200]
        except Exception:
            detail = ""
        print(f"{name}: FAILED ({type(e).__name__}: {e}) | {detail}")


def main():
    _, _, _, _, blog = botlib._tumblr_creds()
    # /user/info strictly requires a valid OAuth signature (unlike /blog/info,
    # which serves public data leniently). This proves whether our signing works.
    test("GET user/info (strict auth)", "GET", "https://api.tumblr.com/v2/user/info")
    test("GET blog/info (lenient)", "GET", f"https://api.tumblr.com/v2/blog/{blog}/info")


if __name__ == "__main__":
    main()
