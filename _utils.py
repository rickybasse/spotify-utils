#!/usr/bin/env python3

import json, os, pickle, time, urllib.error, urllib.request

DEBUG = os.getenv("DEBUG", 0)
API = "https://api.spotify.com/v1"

load_pickle = lambda f: (print(f"> found `{f}`"), pickle.load(open(f, "rb")))[1] if os.path.exists(f) else set()
dump_pickle = lambda d, f: pickle.dump(d, open(f, "wb"))
dump_json = lambda d, f: json.dump(d, open(f, "w"))

def request(url, access_token, data=None, method="GET"):
    if DEBUG: print(f"{method} {url}")
    req = urllib.request.Request(url, data, method=method)
    req.add_header("Authorization", f"Bearer {access_token}")
    if data: req.add_header("Content-Type", "application/vnd.api+json")
    try:
        with urllib.request.urlopen(req) as f:
            if DEBUG: print(f"status={f.status}")
            if f.status == 204: return None
            body = f.read().decode()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        if DEBUG: print(f"error={e.code}")
        if e.code == 429:
            r = int(e.headers.get("Retry-After", 1))
            if DEBUG: print(f"rate-limit: {r}s")
            time.sleep(r)
            if DEBUG: print(f"retry {method} {url}")
            return request(url, access_token, data, method)
        raise
