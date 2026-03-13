# `tidal-utils`

a set of programs to automate Tidal (and previously Spotify) stuff

all the programs require `python` but no extra dependencies

to run the programs you need to [setup a Spotify app](https://developer.spotify.com/documentation/web-api/concepts/apps) with the following config:
- `app name`: whatever you like
- `app description`: whatever you like
- `redirect uri`: `http://127.0.0.1:6969`
- `which API/SDKs are you planning to use?`: `Web API`

similarly for Tidal:
- `app name`: whatever you like
- `platform preset`: none
- `redirect uri`: `http://127.0.0.1:6969`
- `scopes`: `collection.read`, `playlists.read`, `playlists.write`

once the app is setup you'll have a `client_id` and `client_secret`, needed to obtain an `access_token` and a `refresh_token` via the authentication flow.

when you run a program for the first time pass your `S_CI` (for Spotify, or `T_CI` for Tidal) and `S_CS` (for Spotify, or `T_CS` for Tidal) as environment variables together with any other variable needed by the specific program. the program will open the default browser and ask for your Spotify (or Tidal) credentials and permission to give the calling app the requested grants. if successfully authenticated the program will print the `refresh_token` `S_RT` (for Spotify, or `T_RT` for Tidal) before proceeding to the rest of the tasks.

save the `S_RT` (for Spotify, or `T_RT` for Tidal) and pass it as environment variable to the following executions of any program to bypass the browser step.

## `friday.py` (Spotify)

given a `S_PI` (playlist ID) and a cut-off `DATE`:
- builds a set of distinct artists from the users' liked songs
- looks for albums from those artists that have been released after the cut-off `DATE`, i.e. new music from them
- clears the playlist associated with `S_PI` and adds all the tracks from the new releases found

I personally run this program [every friday morning CET](.github/workflows/friday.yml) to get a fresh batch of new music released during the week from artists I like.

to find out the `S_PI` of the playlist you want to use just copy its share link and get the route parameter:
```
https://open.spotify.com/playlist/<playlist_id>?<query_params>
```

environment variables needed:
- `S_CI`: Spotify client ID
- `S_CS`: Spotify client secret
- `S_RT`: Spotify refresh token
- `S_PI`: Spotify playlist ID

example:

```shell
# first run of the program
$ S_CI=<client_id> S_CS=<client_secret> S_PI=<playlist_id> DATE=2025-07-04 ./friday.py

server up, getting albums released after 2025-07-04
refresh_token: <refresh_token_from_the_auth_flow>
[...]

# following runs of the program
$ S_CI=<client_id> S_CS=<client_secret> S_RT=<refresh_token_from_first_run> S_PI=<playlist_id> DATE=2025-07-04 ./friday.py
```

## `tidal.py`

expects 3 playlists to be provided for singles, EPs and albums respectively.

given `T_PI_SINGLES`, `T_PI_EPS`, `T_PI_ALBUMS` (playlist IDs) and a cut-off `DATE`:
- builds a set of distinct artists from the user's liked songs
- looks for singles, EPs, and albums from those artists released after the cut-off `DATE`
- clears the 3 playlists and adds tracks from new releases to their respective playlist

to find out the playlist IDs copy the share link from each TIDAL playlist:
```
https://tidal.com/browse/playlist/<playlist_id>
```

environment variables needed:
- `T_CI`: TIDAL client ID
- `T_CS`: TIDAL client secret
- `T_RT`: TIDAL refresh token
- `T_UI`: TIDAL user ID
- `T_PI_SINGLES`: singles playlist ID
- `T_PI_EPS`: EPs playlist ID
- `T_PI_ALBUMS`: albums playlist ID

example:

```shell
# first run - will open browser for auth
$ T_CI=<client_id> T_CS=<client_secret> T_UI=<user_id> T_PI_SINGLES=<singles_id> T_PI_EPS=<eps_id> T_PI_ALBUMS=<albums_id> DATE=2025-07-04 ./tidal.py

server up, getting albums released after 2025-07-04
refresh_token: <refresh_token_from_the_auth_flow>
[...]

# following runs
$ T_CI=<client_id> T_CS=<client_secret> T_RT=<refresh_token> T_UI=<user_id> T_PI_SINGLES=<singles_id> T_PI_EPS=<eps_id> T_PI_ALBUMS=<albums_id> DATE=2025-07-04 ./tidal.py
```
