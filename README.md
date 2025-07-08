# `spotify-utils`

a set of programs to automate spotify stuff

all the programs require `python` but no extra dependencies

to run the programs you need to [setup a spotify app](https://developer.spotify.com/documentation/web-api/concepts/apps) with the following config:
- `app name`: whatever you like
- `app description`: whatever you like
- `redirect uri`: `http://127.0.0.1:6969` **(important)**
- `which API/SDKs are you planning to use?`: `Web API`

once the app is setup you'll have a `client_id` and `client_secret`, needed to obtain an `access_token` and a `refresh_token` via the authentication flow.

when you run a program for the first time pass your `CLIENT_ID` and `CLIENT_SECRET` as environment variables together with any other variable needed by the specific program. the program will open the default browser and ask for your spotify credentials and permission to give the calling app the requested grants. if successfully authenticated the program will print the `refresh_token` before proceeding to the rest of the tasks.

save the `refresh_token` and pass it as environment variable to the following executions of any program to bypass the browser step.

## `friday.py`

given a `PLAYLIST_ID` and a cut-off `DATE`:
- builds a set of distinct artists from the users' liked songs
- looks for albums from those artists that have been released after the cut-off `DATE`, i.e. new music from them
- clears the playlist associated with `PLAYLIST_ID` and adds all the tracks from the new releases found

I personally run this program every friday morning CET to get a fresh batch of new music released during the week from artists I like.

to find out the `PLAYLIST_ID` of the playlist you want to use just copy its share link and get the route parameter:
```
https://open.spotify.com/playlist/<playlist_id>?<query_params>
```

example:

```shell
# first run of the program
$ CLIENT_ID=<client_id> CLIENT_SECRET=<client_secret> PLAYLIST_ID=<playlist_id> DATE=2025-07-04 ./friday.py

server up, getting albums released after 2025-07-04
refresh_token: <refresh_token_from_the_auth_flow>
[...]

# following runs of the program
$ CLIENT_ID=<client_id> CLIENT_SECRET=<client_secret> REFRESH_TOKEN=<refresh_token_from_first_run> PLAYLIST_ID=<playlist_id> DATE=2025-07-04 ./friday.py
```

