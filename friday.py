#!/usr/bin/env python3

import json, os, urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta
from _auth import spotify_access_token
from _utils import DEBUG, API, load_pickle, dump_pickle, request

IGNORE = {
    # don't get me wrong I love classical music as much as any other genre
    # but there is so much music being released every week associated with
    # these artists that just pollutes the output, hence filtering them out
    "2QOIawHpSlOwXDvSqQ9YJR", # Antonio Vivaldi
    "6uRJnvQ3f8whVnmeoecv5Z", # Berlin Philharmoniker
    "1Uff91EOsvd99rtAupatMP", # Claude Debussy
    "1nIUhcKHnK6iyumRyoV68C", # Ennio Morricone
    "459INk8vcC0ebEef82WjIK", # Erik Satie
    "7y97mc3bZRFXzT2szRM4L4", # Frédéric Chopin
    "62TD7509VQIxUe4WpwO0s3", # Johann Pachelbel
    "5aIqB5nVVvmFsvSdExz408", # Johann Sebastian Bach
    "5goS0v24Fc1ydjCKQRwtjM", # Johann Strauss II
    "3dRfiJ2650SZu6GbydcHNb", # John Williams
    "2wOqMjp9TyABvtHdOSOTUS", # Ludwig van Beethoven
    "4NJhFmfw43RLBLjQvxDuRS", # Wolfgang Amadeus Mozart
    "39FC9x5PaTNYHp5hwlaY4q", # Niccolò Paganini
}

date = os.getenv("DATE", (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))
client_id = os.getenv("S_CI")
client_secret = os.getenv("S_CS")
refresh_token = os.getenv("S_RT")
playlist_id = os.getenv("S_PI")

@dataclass(frozen=True)
class Album:
    id: str
    date: str
    name: str
    artists: list
    type: str

def get_artists(url, token):
    r = request(url, token)
    return {s["track"]["artists"][0]["id"] for s in r["items"]}, r["next"]

def get_albums(url, token):
    r = request(url, token)
    return [Album(a["id"], a["release_date"], a["name"], a["artists"], a["album_type"]) for a in r["items"]]

def get_tracks(url, token):
    r = request(url, token)
    return [s["uri"] for a in r["albums"] for s in a["tracks"]["items"]]

if __name__ == "__main__":
    access_token = spotify_access_token(client_id, client_secret, refresh_token)
    print(f"getting albums released after {date}")

    artists = load_pickle("spotify_artists.pkl")
    if not artists:
        url = f"{API}/me/tracks?offset=0&limit=50"
        while url:
            batch, url = get_artists(url, access_token)
            artists.update(batch)
            if DEBUG: print(f"{len(batch)=}, {len(artists)=}, {url=}")
        dump_pickle(artists, "spotify_artists.pkl")

    print(f"liked artists: {len(artists)}")
    artists -= IGNORE
    print(f"liked artist - ignored: {len(artists)}")

    albums = load_pickle("spotify_albums.pkl")
    new_singles, new_albums = [], []
    if not albums:
        for artist in artists:
            url = f"{API}/artists/{artist}/albums?offset=0&limit=50&include_groups=album,single"
            new_releases = [a for a in get_albums(url, access_token) if a.date >= date]
            new_singles.extend([r for r in new_releases if r.type == "single"])
            new_albums.extend([r for r in new_releases if r.type == "album"])
            if DEBUG: [print(f"* {r.type} | {r.name}: {[(art['name'], art['id']) for art in r.artists]}") for r in new_releases]
        albums = dict.fromkeys(r.id for r in [*new_singles, *new_albums])
        dump_pickle(albums, "spotify_albums.pkl")
    print(f"new albums: {len(albums)}")

    tracks = []
    albums_l = list(albums)
    for chunk in [albums_l[i:i+20] for i in range(0, len(albums_l), 20)]:
        url = f"{API}/albums?ids={','.join(chunk)}"
        tracks.extend(get_tracks(url, access_token))
    print(f"new tracks: {len(tracks)}")

    data = json.dumps({"uris": []}).encode()
    req = urllib.request.Request(f"{API}/playlists/{playlist_id}/tracks", data, method="PUT")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {access_token}")
    urllib.request.urlopen(req)
    print("cleaned playlist")

    for chunk in [tracks[i:i+100] for i in range(0, len(tracks), 100)]:
        data = json.dumps({"uris": chunk}).encode()
        req = urllib.request.Request(f"{API}/playlists/{playlist_id}/tracks", data)
        req.add_header("Content-Type", "application/json"); req.add_header("Authorization", f"Bearer {access_token}")
        urllib.request.urlopen(req)
    print("fresh tracks ready to be listened to!")
