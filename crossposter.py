#!/usr/bin/env python3
"""
90s Foodie cross-poster — free bot, runs on GitHub Actions.
Polls the Substack RSS feed and auto-shares new posts to
Bluesky, Threads, and Tumblr. Configure via GitHub Secrets;
any platform without secrets configured is skipped.
Secrets:
  BLUESKY_HANDLE, BLUESKY_APP_PASSWORD
  THREADS_USER_ID, THREADS_ACCESS_TOKEN
  TUMBLR_CONSUMER_KEY, TUMBLR_CONSUMER_SECRET,
  TUMBLR_OAUTH_TOKEN, TUMBLR_OAUTH_SECRET, TUMBLR_BLOG
  INSTAGRAM_USER_ID, INSTAGRAM_ACCESS_TOKEN
    (Instagram requires a Business/Creator account linked to a
     Facebook Page; skipped automatically if not configured)
NOTE: Quora has no public write API, so it cannot be automated.
"""
import hashlib
import hmac
import json
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from base64 import b64encode
from datetime import datetime, timezone

FEED_URL = "https://90sfoodie.substack.com/feed"
ARCHIVE_API = "https://90sfoodie.substack.com/api/v1/archive?sort=new&limit=10&offset=0"
# (name, url, kind) — tried in order until one returns posts.
FEED_SOURCES = [
    ("codetabs", "https://api.codetabs.com/v1/proxy?quest=" + urllib.parse.quote(FEED_URL, safe=""), "rss"),
    ("corsproxy", "https://corsproxy.io/?url=" + urllib.parse.quote(FEED_URL, safe=""), "rss"),
    ("archive-api", ARCHIVE_API, "api"),
    ("rss-direct", FEED_URL, "rss"),
]
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posted.json")
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}


def http_json(url, data=None, headers=None, method=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    if body:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def http_form(url, params, headers=None):
    body = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=body, headers=headers or {})
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def feed_image(it):
    for tag in ("{http://search.yahoo.com/mrss/}content", "enclosure"):
        el = it.find(tag)
        if el is not None and el.get("url"):
            return el.get("url")
    return ""


def fetch_rss(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        root = ET.fromstring(r.read())
    items = []
    for it in root.iter("item"):
        guid = (it.findtext("guid") or "").strip()
        link = (it.findtext("link") or "").strip()
        title = (it.findtext("title") or "").strip()
        if guid and title:
            items.append({"guid": guid, "link": link or guid, "title": title,
                          "image": feed_image(it)})
    return items


def fetch_api(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
    items = []
    for p in data:
        url_ = (p.get("canonical_url") or "").strip()
        title = (p.get("title") or "").strip()
        if url_ and title:
            items.append({"guid": url_, "link": url_, "title": title,
                          "image": (p.get("cover_image") or "").strip()})
    return items


def fetch_feed():
    """Try each feed source in order until one returns posts."""
    for name, url, kind in FEED_SOURCES:
        try:
            items = fetch_api(url) if kind == "api" else fetch_rss(url)
            if items:
                print(f"Feed source OK: {name} ({len(items)} posts)")
                return items
            print(f"Feed source {name}: no posts")
        except Exception as e:
            print(f"Feed source {name} failed: {e}")
    print("All feed sources failed")
    return []


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def post_bluesky(title, link):
    handle = os.environ.get("BLUESKY_HANDLE")
    password = os.environ.get("BLUESKY_APP_PASSWORD")
    if not handle or not password:
        print("Bluesky: secrets missing, skipped")
        return False
    sess = http_json(
        "https://bsky.social/xrpc/com.atproto.server.createSession",
        {"identifier": handle, "password": password},
    )
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
    http_json(
        "https://bsky.social/xrpc/com.atproto.repo.createRecord",
        record,
        {"Authorization": f"Bearer {sess['accessJwt']}"},
    )
    print(f"Bluesky: posted '{title}'")
    return True


def post_threads(title, link):
    user_id = os.environ.get("THREADS_USER_ID")
    token = os.environ.get("THREADS_ACCESS_TOKEN")
    if not user_id or not token:
        print("Threads: secrets missing, skipped")
        return False
    text = f"{title}\n\n{link}"
    create = http_form(
        f"https://graph.threads.net/v1.0/{user_id}/threads",
        {"media_type": "TEXT", "text": text, "access_token": token},
    )
    time.sleep(20)  # allow media container processing
    http_form(
        f"https://graph.threads.net/v1.0/{user_id}/threads_publish",
        {"creation_id": create["id"], "access_token": token},
    )
    print(f"Threads: posted '{title}'")
    return True


def _oauth1_header(url, params, consumer_key, consumer_secret, token, token_secret):
    """Minimal OAuth 1.0a HMAC-SHA1 signing (stdlib only)."""
    import random
    import string

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
    sig_base = "&".join(
        urllib.parse.quote(p, safe="") for p in ("POST", url, base)
    )
    key = f"{urllib.parse.quote(consumer_secret, safe='')}&{urllib.parse.quote(token_secret, safe='')}"
    sig = b64encode(hmac.new(key.encode(), sig_base.encode(), hashlib.sha1).digest()).decode()
    oauth["oauth_signature"] = sig
    return "OAuth " + ", ".join(
        f'{k}="{urllib.parse.quote(str(v), safe="")}"' for k, v in sorted(oauth.items())
    )


def post_instagram(title, link, image):
    user_id = os.environ.get("INSTAGRAM_USER_ID")
    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
    if not user_id or not token:
        print("Instagram: secrets missing, skipped")
        return False
    if not image:
        print("Instagram: no image in feed item, skipped")
        return False
    caption = f"{title}\n\nRead more at the link in bio — 90sfoodie.substack.com"
    container = http_form(
        f"https://graph.facebook.com/v21.0/{user_id}/media",
        {"image_url": image, "caption": caption, "access_token": token},
    )
    time.sleep(20)
    http_form(
        f"https://graph.facebook.com/v21.0/{user_id}/media_publish",
        {"creation_id": container["id"], "access_token": token},
    )
    print(f"Instagram: posted '{title}'")
    return True


def post_tumblr(title, link):
    ck = os.environ.get("TUMBLR_CONSUMER_KEY")
    cs = os.environ.get("TUMBLR_CONSUMER_SECRET")
    tok = os.environ.get("TUMBLR_OAUTH_TOKEN")
    ts = os.environ.get("TUMBLR_OAUTH_SECRET")
    blog = os.environ.get("TUMBLR_BLOG")
    if not all([ck, cs, tok, ts, blog]):
        print("Tumblr: secrets missing, skipped")
        return False
    url = f"https://api.tumblr.com/v2/blog/{blog}/post"
    params = {"type": "text", "title": title, "body": f'<p><a href="{link}">{title}</a></p>\n<p>The 90s Foodie</p>'}
    auth = _oauth1_header(url, params, ck, cs, tok, ts)
    body = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=body, headers={"Authorization": auth})
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=30) as r:
        json.loads(r.read().decode())
    print(f"Tumblr: posted '{title}'")
    return True


def main():
    state = load_state()
    try:
        items = fetch_feed()
    except Exception as e:
        print(f"Feed fetch failed: {e}")
        return
    new_items = [it for it in items if it["guid"] not in state]
    if not new_items:
        print("No new posts.")
        return
    for it in new_items:
        ok = True
        for poster in (post_bluesky, post_threads, post_tumblr):
            try:
                poster(it["title"], it["link"])
            except Exception as e:
                print(f"{poster.__name__} failed: {e}")
                ok = False
        try:
            post_instagram(it["title"], it["link"], it.get("image", ""))
        except Exception as e:
            print(f"post_instagram failed: {e}")
        if ok:
            state[it["guid"]] = True
    save_state(state)


if __name__ == "__main__":
    main()
