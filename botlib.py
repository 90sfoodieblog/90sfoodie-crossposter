#!/usr/bin/env python3
"""botlib — shared helpers for the 90s Foodie bot team (stdlib only)."""
import hashlib
import hmac
import json
import os
import random
import string
import time
import urllib.error
import urllib.parse
import urllib.request
from base64 import b64encode
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}
ARCHIVE_API = "https://90sfoodie.substack.com/api/v1/archive?sort=new&limit=10&offset=0"

SITE_SNACKS_URL = "https://90sfoodie.com/data/snacks.json"
_archive_cache = None


def archive_link_for(post_url):
    """Return the 90sfoodie.com archive URL for a Substack post, or None.

    Matches the post URL against the 'substack' field of the site's
    snacks.json (the single source of truth). Never raises — if the
    site is unreachable or the post has no archive entry yet, the
    caller just posts the Substack link as before.
    """
    global _archive_cache
    try:
        if _archive_cache is None:
            req = urllib.request.Request(SITE_SNACKS_URL, headers=UA)
            with urllib.request.urlopen(req, timeout=20) as r:
                _archive_cache = json.loads(r.read().decode())
        target = (post_url or "").rstrip("/")
        for s in _archive_cache:
            if (s.get("substack") or "").rstrip("/") == target and s.get("slug"):
                return f"https://90sfoodie.com/archive/{s['slug']}.html"
    except Exception as e:
        print(f"archive lookup failed: {e}")
    return None


BLOG_HOME = "https://90sfoodie.substack.com"
SITE_HOME = "https://90sfoodie.com"


def _promo_text(text):
    """Guarantee dual promotion (Dee, 2026-10-14): every bot post carries
    the blog link AND the website link.
    - Text already mentioning 90sfoodie.com: unchanged.
    - Contains a Substack post URL: append that post's archive-page link.
    - Otherwise: append the blog + archive home links.
    Appends only when the result fits the 280-char budget."""
    if "90sfoodie.com" in text:
        return text
    import re
    m = re.search(r"https://90sfoodie\.substack\.com/p/[^\s\"'<>]+", text)
    if m:
        arch = archive_link_for(m.group(0))
        if arch:
            for suffix in (f"\n\n\U0001F4E6 In the archive: {arch}",
                           f"\n\U0001F4E6 {arch}"):
                if len(text) + len(suffix) <= 280:
                    return text + suffix
        return text
    suffix = f"\n\n\U0001F4D6 {BLOG_HOME}\n\U0001F4E6 {SITE_HOME}"
    if len(text) + len(suffix) <= 280:
        return text + suffix
    return text


def _promo_html(body):
    """HTML twin of _promo_text for Tumblr bodies (no length cap)."""
    if "90sfoodie.com" in body:
        return body
    import re
    m = re.search(r"https://90sfoodie\.substack\.com/p/[^\s\"'<>]+", body)
    if m:
        arch = archive_link_for(m.group(0))
        if arch:
            return body + (f'\n<p>\U0001F4E6 In the archive: '
                           f'<a href="{arch}">this snack in the 90s Foodie archive</a></p>')
    return body + (f'\n<p>\U0001F4D6 <a href="{BLOG_HOME}">The 90s Foodie blog</a>'
                   f' &middot; \U0001F4E6 <a href="{SITE_HOME}">The snack archive</a></p>')



def http_json(url, data=None, headers=None, method=None, timeout=30):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    if body:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _with_retries(fn, tries=4, base_delay=5, label="request"):
    """Retry flaky network calls with exponential backoff."""
    last = None
    for i in range(tries):
        try:
            return fn()
        except Exception as e:
            last = e
            print(f"{label}: attempt {i+1}/{tries} failed "
                  f"({type(e).__name__}: {str(e)[:100]})")
            if i < tries - 1:
                time.sleep(base_delay * (2 ** i))
    raise last


def http_form(url, params, headers=None):
    body = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=body, headers=headers or {})
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def http_get_json(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def load_state(name):
    path = os.path.join(REPO_ROOT, name)
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(name, state):
    path = os.path.join(REPO_ROOT, name)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def _bsky_session():
    handle = os.environ.get("BLUESKY_HANDLE")
    password = os.environ.get("BLUESKY_APP_PASSWORD")
    if not handle or not password:
        return None
    sess = _with_retries(
        lambda: http_json(
            "https://bsky.social/xrpc/com.atproto.server.createSession",
            {"identifier": handle, "password": password},
            timeout=60,
        ),
        label="Bluesky session",
    )
    return sess


def post_bluesky_text(text):
    """Post arbitrary text to Bluesky. Returns (uri, cid) or None if skipped."""
    text = _promo_text(text)
    sess = _bsky_session()
    if not sess:
        print("Bluesky: secrets missing, skipped")
        return None
    if len(text) > 280:
        text = text[:277] + "..."
    record = {
        "repo": sess["did"],
        "collection": "app.bsky.feed.post",
        "record": {
            "$type": "app.bsky.feed.post",
            "text": text,
            "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        },
    }
    res = _with_retries(
        lambda: http_json(
            "https://bsky.social/xrpc/com.atproto.repo.createRecord",
            record,
            {"Authorization": f"Bearer {sess['accessJwt']}"},
            timeout=60,
        ),
        tries=3,
        label="Bluesky post",
    )
    print(f"Bluesky: posted '{text[:60]}'")
    return res.get("uri"), res.get("cid")


def post_bluesky(title, link):
    text = f"{title}\n\n{link}"
    arch = archive_link_for(link)
    if arch:
        text += f"\n\n\U0001F4E6 In the archive: {arch}"
    sess = _bsky_session()
    if not sess:
        print("Bluesky: secrets missing, skipped")
        return False
    if len(text) > 280:
        # The story link always wins: drop the archive line first.
        text = f"{title}\n\n{link}"
        if len(text) > 280:
            text = title[: 277 - len(link)] + "...\n\n" + link
    record = {
        "repo": sess["did"],
        "collection": "app.bsky.feed.post",
        "record": {
            "$type": "app.bsky.feed.post",
            "text": text,
            "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "embed": {
                "$type": "app.bsky.embed.external",
                "external": {"uri": link, "title": title, "description": "The 90s Foodie"},
            },
        },
    }
    _with_retries(
        lambda: http_json(
            "https://bsky.social/xrpc/com.atproto.repo.createRecord",
            record,
            {"Authorization": f"Bearer {sess['accessJwt']}"},
            timeout=60,
        ),
        tries=3,
        label="Bluesky post",
    )
    print(f"Bluesky: posted '{title}'")
    return True


def post_bluesky_thread(texts):
    """Post a reply-chain thread. texts[0] is the root post."""
    if texts and not any("90sfoodie.com" in x for x in texts):
        enriched = _promo_text(texts[-1])
        if "90sfoodie.com" in enriched:
            texts = texts[:-1] + [enriched]
        else:
            texts = texts + [f"\U0001F4D6 Blog: {BLOG_HOME}\n\U0001F4E6 Archive: {SITE_HOME}"]
    sess = _bsky_session()
    if not sess:
        print("Bluesky: secrets missing, skipped")
        return False
    auth = {"Authorization": f"Bearer {sess['accessJwt']}"}
    root_ref = parent_ref = None
    for i, text in enumerate(texts):
        if len(text) > 280:
            text = text[:277] + "..."
        rec = {
            "$type": "app.bsky.feed.post",
            "text": text,
            "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        if parent_ref:
            rec["reply"] = {"root": root_ref, "parent": parent_ref}
        res = _with_retries(
            lambda: http_json(
                "https://bsky.social/xrpc/com.atproto.repo.createRecord",
                {"repo": sess["did"], "collection": "app.bsky.feed.post",
                 "record": rec},
                auth,
                timeout=60,
            ),
            tries=3,
            label=f"Bluesky thread post {i+1}",
        )
        ref = {"uri": res["uri"], "cid": res["cid"]}
        if root_ref is None:
            root_ref = ref
        parent_ref = ref
        time.sleep(2)
    print(f"Bluesky: posted thread of {len(texts)}")
    return True


def _oauth1_header(url, params, consumer_key, consumer_secret, token, token_secret,
                 method="POST"):
    oauth = {
        "oauth_consumer_key": consumer_key,
        "oauth_token": token,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_nonce": "".join(random.choices(string.ascii_letters + string.digits, k=32)),
        "oauth_version": "1.0",
    }
    all_params = {**params, **oauth}
    base = "&".join(
        f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(str(v), safe='')}"
        for k, v in sorted(all_params.items())
    )
    sig_base = "&".join(urllib.parse.quote(p, safe="") for p in (method, url, base))
    key = f"{urllib.parse.quote(consumer_secret, safe='')}&{urllib.parse.quote(token_secret, safe='')}"
    sig = b64encode(hmac.new(key.encode(), sig_base.encode(), hashlib.sha1).digest()).decode()
    oauth["oauth_signature"] = sig
    return "OAuth " + ", ".join(
        f'{k}="{urllib.parse.quote(str(v), safe="")}"' for k, v in sorted(oauth.items())
    )


def _rfc3986_body(params):
    """Encode a POST body with RFC 3986 (%20 for space), matching the
    OAuth signature encoding. urllib.parse.urlencode uses '+' for
    spaces, which breaks signature verification on strict providers."""
    return "&".join(
        f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(str(v), safe='')}"
        for k, v in sorted(params.items())
    ).encode()


def _tumblr_creds():
    ck = os.environ.get("TUMBLR_CONSUMER_KEY")
    cs = os.environ.get("TUMBLR_CONSUMER_SECRET")
    tok = os.environ.get("TUMBLR_OAUTH_TOKEN")
    ts = os.environ.get("TUMBLR_OAUTH_SECRET")
    blog = os.environ.get("TUMBLR_BLOG")
    if not all([ck, cs, tok, ts, blog]):
        return None
    return ck, cs, tok, ts, blog


def post_tumblr_html(title, body_html):
    creds = _tumblr_creds()
    if not creds:
        print("Tumblr: secrets missing, skipped")
        return False
    ck, cs, tok, ts, blog = creds
    body_html = _promo_html(body_html)
    url = f"https://api.tumblr.com/v2/blog/{blog}/post"
    params = {"type": "text", "title": title, "body": body_html}
    auth = _oauth1_header(url, params, ck, cs, tok, ts, method="POST")
    body = _rfc3986_body(params)
    req = urllib.request.Request(url, data=body, headers={"Authorization": auth})
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    def do_post():
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            try:
                detail = e.read().decode()[:500]
            except Exception:
                detail = ""
            print(f"Tumblr: HTTP {e.code} — {detail}")
            raise
    _with_retries(do_post, tries=3, label="Tumblr post")
    print(f"Tumblr: posted '{title}'")
    return True


def post_tumblr(title, link):
    arch = archive_link_for(link)
    extra = (
        f'\n<p>\U0001F4E6 In the archive: <a href="{arch}">this snack in the 90s Foodie archive</a></p>'
        if arch else ""
    )
    return post_tumblr_html(
        title, f'<p><a href="{link}">{title}</a></p>\n<p>The 90s Foodie</p>{extra}'
    )


def fetch_archive_posts(limit=10):
    """Fetch latest Substack posts via the archive JSON API (needs WARP on the runner)."""
    url = f"https://90sfoodie.substack.com/api/v1/archive?sort=new&limit={limit}&offset=0"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
    posts = []
    for p in data:
        url_ = (p.get("canonical_url") or "").strip()
        title = (p.get("title") or "").strip()
        if url_ and title:
            posts.append({
                "url": url_,
                "title": title,
                "subtitle": (p.get("subtitle") or "").strip(),
                "description": (p.get("description") or "").strip(),
                "image": (p.get("cover_image") or "").strip(),
                "body_html": p.get("body_html") or "",
                "post_date": p.get("post_date") or "",
            })
    return posts


def strip_html(html):
    import re
    text = re.sub(r"<[^>]+>", " ", html)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    return " ".join(text.split())
