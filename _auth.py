#!/usr/bin/env python3

import base64, hashlib, http.server, json, os, random, secrets, urllib.parse, urllib.request, webbrowser

DEBUG = os.getenv("DEBUG", 0)
REDIRECT_IP="127.0.0.1"
REDIRECT_PORT=6969
REDIRECT_URI=f"{REDIRECT_IP}:{REDIRECT_PORT}"

class AuthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if hasattr(self.server, "expected_state") and q.get("state", [None])[0] != self.server.expected_state: raise ValueError("state mismatch")
        self.server.auth_code = q["code"][0]
        self.send_response(200); self.end_headers()
    def log_message(self, *args): pass

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_SCOPE = "user-library-read playlist-read-private playlist-modify-private"

def spotify_access_token(client_id, client_secret, refresh_token=None, scope=SPOTIFY_SCOPE):
    auth_header = f"Basic {base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()}"
    if refresh_token:
        if DEBUG: print("spotify refresh_token provided")
        data = urllib.parse.urlencode({"refresh_token": refresh_token, "grant_type": "refresh_token"}).encode()
        req = urllib.request.Request(SPOTIFY_TOKEN_URL, data=data)
        req.add_header("Authorization", auth_header)
        with urllib.request.urlopen(req) as f: return json.loads(f.read().decode())["access_token"]
    server = http.server.HTTPServer((REDIRECT_IP, REDIRECT_PORT), AuthHandler)
    if DEBUG: print("server up")
    webbrowser.open(f"{SPOTIFY_AUTH_URL}?response_type=code&client_id={client_id}&scope={scope.replace(' ', '%20')}&redirect_uri={redirect_uri}&state={random.random()}")
    server.handle_request()
    data = urllib.parse.urlencode({"redirect_uri": REDIRECT_URI, "code": server.auth_code, "grant_type": "authorization_code"}).encode()
    req = urllib.request.Request(SPOTIFY_TOKEN_URL, data=data)
    req.add_header("Authorization", auth_header)
    with urllib.request.urlopen(req) as f:
        resp = json.loads(f.read().decode())
        print(f"refresh_token={resp['refresh_token']}")
        return resp["access_token"]

TIDAL_AUTH_URL = "https://login.tidal.com/authorize"
TIDAL_TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"
_pkce = lambda: (cv:=base64.urlsafe_b64encode(secrets.token_bytes(64)).decode().rstrip("="), base64.urlsafe_b64encode(hashlib.sha256(cv.encode()).digest()).decode().rstrip("="))

def tidal_access_token(client_id, client_secret=None, refresh_token=None, scope="collection.read collection.write playlists.write"):
    if refresh_token:
        if DEBUG: print("tidal refresh_token provided")
        data = urllib.parse.urlencode({"client_id": client_id, "refresh_token": refresh_token, "grant_type": "refresh_token"}).encode()
        with urllib.request.urlopen(urllib.request.Request(TIDAL_TOKEN_URL, data=data)) as f: return json.loads(f.read().decode())["access_token"]
    server = http.server.HTTPServer((REDIRECT_IP, REDIRECT_PORT), AuthHandler)
    if DEBUG: print("server up")
    code_verifier, code_challenge = _pkce()
    server.expected_state = secrets.token_urlsafe(32)
    webbrowser.open(TIDAL_AUTH_URL + "?"+ urllib.parse.urlencode({
        "response_type": "code", "client_id": client_id, "redirect_uri": REDIRECT_URI,
        "scope": scope, "code_challenge_method": "S256", "code_challenge": code_challenge, "state": server.expected_state
    }))
    server.handle_request()
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code", "client_id": client_id, "code": server.auth_code,
        "redirect_uri": redirect_uri, "code_verifier": code_verifier
    }).encode()
    with urllib.request.urlopen(urllib.request.Request(TIDAL_TOKEN_URL, data=data)) as f:
        resp = json.loads(f.read().decode())
        print(f"refresh_token={resp['refresh_token']}")
        return resp["access_token"]
