#!/usr/bin/env python3

import os
import json
import urllib.request
from friday import DEBUG, API, get_access_token, request


client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
refresh_token = os.getenv("REFRESH_TOKEN")


def get_tracks(url, access_token):
    resp = request(url, access_token)
    return [{
        "title": s["track"]["name"],
        "isrc": s["track"]["external_ids"]["isrc"],
        "duration": s["track"]["duration_ms"]
    } for s in resp["items"]], resp["next"]


def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f: return json.load(f)
    else: return []

def dump_json(data, file):
    with open(file, "w")as f: json.dump(data, f)


if __name__ == "__main__":
    access_token = get_access_token(refresh_token)

    tracks = load_json("tracks.json");
    if not tracks:
        url = f"{API}/me/tracks?offset=0&limit=50"
        while (url):
            batch, url = get_tracks(url, access_token)
            tracks.extend(batch)
            if DEBUG: print(f"{len(batch)=}, {len(tracks)=}, {url=}")

        dump_json(tracks, "tracks.json")

    print(f"liked songs: {len(tracks)}")

