# playlistjockey/spotify/connect.py

"""Function responsible for connecting to Spotify's API."""

import os

import spotipy


def connect_spotify(client_id, client_secret, redirect_uri):
    """Connects to Spotify's API using Spotipy."""
    os.environ["SPOTIPY_CLIENT_ID"] = client_id
    os.environ["SPOTIPY_CLIENT_SECRET"] = client_secret
    os.environ["SPOTIPY_REDIRECT_URI"] = redirect_uri

    scopes = "playlist-modify-private,\
              playlist-modify-public,\
              playlist-read-private,\
              playlist-read-collaborative"

    auth_manager = spotipy.oauth2.SpotifyOAuth(scope=scopes)
    sp = spotipy.Spotify(auth_manager=auth_manager)

    return sp
