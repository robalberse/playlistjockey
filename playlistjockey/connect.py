import os

import spotipy


def connect_spotify(client_id, client_secret):
    os.environ["SPOTIPY_CLIENT_ID"] = client_id
    os.environ["SPOTIPY_CLIENT_SECRET"] = client_secret

    scopes = "playlist-modify-private,\
              playlist-modify-public,\
              playlist-read-private,\
              playlist-read-collaborative"

    auth_manager = spotipy.oauth2.SpotifyClientCredentials()
    sp = spotipy.Spotify(auth_manager=auth_manager)

    return sp
