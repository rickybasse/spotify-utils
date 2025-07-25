#!/usr/bin/env python3

import base64
import concurrent.futures
import http.server
import json
import os
import pickle
import random
import time
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timedelta

DEBUG = os.getenv("DEBUG", 0)
OAUTH_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
OAUTH_TOKEN_URL = "https://accounts.spotify.com/api/token"
API = "https://api.spotify.com/v1"
IGNORE = {
    # don't get me wrong I love classical music as much as any other genre
    # but there is so much music being released every week associated with
    # these artists that just pollutes the output, hence filtering them out
    "2QOIawHpSlOwXDvSqQ9YJR", # Antonio Vivaldi
    "6uRJnvQ3f8whVnmeoecv5Z", # Berlin Philharmoniker
    "1Uff91EOsvd99rtAupatMP", # Claude Debussy
    "459INk8vcC0ebEef82WjIK", # Erik Satie
    "7y97mc3bZRFXzT2szRM4L4", # Frédéric Chopin
    "5aIqB5nVVvmFsvSdExz408", # Johann Sebastian Bach
    "62TD7509VQIxUe4WpwO0s3", # Johann Pachelbel
    "2wOqMjp9TyABvtHdOSOTUS", # Ludwig van Beethoven
    "4NJhFmfw43RLBLjQvxDuRS", # Wolfgang Amadeus Mozart
    "39FC9x5PaTNYHp5hwlaY4q", # Niccolò Paganini
}

date = os.getenv("DATE", (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
refresh_token = os.getenv("REFRESH_TOKEN")
playlist_id = os.getenv("PLAYLIST_ID")


class AuthHandler(http.server.BaseHTTPRequestHandler):
    """ accepts the redirect from Spotify and parses the auth code """
    def do_GET(self):
        self.server.auth_code = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)['code'][0]
        self.send_response(200)
        self.end_headers()
    def log_message(self, format, *args): pass

def get_access_token(refresh_token=None):
    """ handles the authentication flow, if `refresh_token` is not provided it requires interaction with browser """
    if refresh_token:
        print(f"refresh_token provided, getting albums released after {date}")
        data = urllib.parse.urlencode({ "refresh_token": refresh_token, "grant_type": "refresh_token" }).encode()
        req = urllib.request.Request(OAUTH_TOKEN_URL, data=data)
        req.add_header("Authorization", f"Basic {base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()}")
        with urllib.request.urlopen(req) as f:
            return json.loads(f.read().decode())["access_token"]

    server = http.server.HTTPServer(("127.0.0.1", 6969), AuthHandler)
    print(f"server up, getting albums released after {date}")
    response_type = "code"
    redirect_uri = "http://127.0.0.1:6969"
    scope = "user-library-read playlist-read-private playlist-modify-private"
    state = random.random()
    webbrowser.open(f"{OAUTH_AUTHORIZE_URL}?{response_type=}&{client_id=}&{scope=}&{redirect_uri=}&{state=}".replace("'", ""))
    server.handle_request()

    data = urllib.parse.urlencode({ "redirect_uri": redirect_uri, "code": server.auth_code, "grant_type": "authorization_code" }).encode()
    req = urllib.request.Request(OAUTH_TOKEN_URL, data=data)
    req.add_header("Authorization", f"Basic {base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()}")
    with urllib.request.urlopen(req) as f:
        resp = json.loads(f.read().decode())
        print(f"refresh_token: {resp['refresh_token']}")
        return resp["access_token"]


def load_pickle(file):
    if os.path.exists(file):
        print(f"> found `{file}`")
        with open(file, "rb") as f: return pickle.load(f)
    else: return set()

def dump_pickle(data, file): 
    with open(file, "wb") as f: pickle.dump(data, f)


def request(url, data=None):
    req = urllib.request.Request(url, data)
    req.add_header("Authorization", f"Bearer {access_token}")
    try:
        with urllib.request.urlopen(req) as f: return json.loads(f.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("retry-after:", int(e.headers.get("Retry-After"))/60/60, "h")
            raise

def get_artists(url):
    """ returns only the first artist in the artists list """
    resp = request(url)
    return {song["track"]["artists"][0]["id"] for song in resp["items"]}, resp["next"]

def get_albums(url):
    resp = request(url)
    return [(album["id"], album["release_date"], album["name"], album["artists"]) for album in resp["items"]]

def get_tracks(url):
    resp = request(url)
    return [song["uri"] for album in resp["albums"] for song in album["tracks"]["items"]]


if __name__ == "__main__":
    access_token = get_access_token(refresh_token)

    # get artists from liked tracks
    artists = load_pickle("artists.pkl")
    if not artists:
        # TODO: check if tracks are ordered, so we can save the last processed track and just get the newer ones
        url = f"{API}/me/tracks?offset=0&limit=50"
        while (url):
            batch, url = get_artists(url)
            artists.update(batch)
            if DEBUG: print(f"{len(batch)=}, {len(artists)=}, {url=}")

        dump_pickle(artists, "artists.pkl")

    print(f"liked artists: {len(artists)}")
    artists -= IGNORE
    print(f"liked artist - ignored: {len(artists)}")

    # get new albums from those artists
    albums = load_pickle("albums.pkl")
    if not albums:
        for artist in artists:
            url = f"{API}/artists/{artist}/albums?offset=0&limit=50&include_groups=album,single"
            new_albums = [a for a in get_albums(url) if a[1] >= date]
            albums.update({a[0] for a in new_albums})
            if DEBUG: [print(f"* {len(albums)=} ~ {a[2]}: {[(art['name'], art['id']) for art in a[3]]}") for a in new_albums]

        dump_pickle(albums, "albums.pkl")

    print(f"new albums: {len(albums)}")

    # get tracks from new albums
    tracks = []
    albums_l = list(albums)
    for chunk in [albums_l[i:i+20] for i in range(0, len(albums_l), 20)]:
        url = f"{API}/albums?ids={",".join(list(chunk))}"
        tracks.extend(get_tracks(url))

    print(f"new tracks: {len(tracks)}")

    # clear the `friday` playlist
    data = json.dumps({"uris": []}).encode()
    url = f"{API}/playlists/{playlist_id}/tracks"
    req = urllib.request.Request(url, data, method="PUT")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {access_token}")
    urllib.request.urlopen(req)

    print("cleaned playlist")

    # add tracks from new albums to `friday` playlist
    for chunk in [tracks[i:i+100] for i in range(0, len(tracks), 100)]:
        data = json.dumps({ "uris": chunk }).encode()
        url = f"{API}/playlists/{playlist_id}/tracks"
        req = urllib.request.Request(url, data)
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {access_token}")
        with urllib.request.urlopen(req) as f:
             resp = json.loads(f.read().decode())

    print("fresh tracks ready to be listened to!")

