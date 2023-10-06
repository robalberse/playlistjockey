# playlistjockey/main.py

"""Main module containing the key functions of playlistjockey.

The module contains the following classes and functions:

- `sort_playlist(playlist_df, mix)`: Sorts the songs in a playlist df using a specified mixing algorithm.
- `Spotify(client_id, client_secret, redirect_uri)`: Class used for pulling and pushing playlists to and from Spotify.
    - `get_playlist_features(self, playlist_id, genres=False)`: Pull in all required features of songs in a given playlist.
    - `update_playlist(self, playlist_id, playlist_df)`: Overwrites the songs and order of the given playlist ID, using the songs in the given playlist DataFrame.
- `Tidal(spotify)`: Class used for pulling and pushing playlists to and from Tidal.
    - `get_playlist_features(self, playlist_id, genres=False)`: Pull in all required features of songs in a given playlist.
    - `update_playlist(self, playlist_id, playlist_df)`: Overwrites the songs and order of the given playlist ID, using the songs in the given playlist DataFrame.
"""

import pandas as pd
import numpy as np
import html
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA

from playlistjockey import utils, mixes
from playlistjockey.spotify import connect as sp_connect, extract as sp_extract
from playlistjockey.tidal import connect as td_connect, extract as td_extract


def sort_playlist(playlist_df, mix):
    """Sorts the songs in a playlist df using a specified mixing algorithm.

    Args:
        playlist_df (pd.DataFrame): DataFrame containing songs with required columns.
        mix (str): String identifying which mixing algorithm you would like to use to sort the playlist. Options so far include "dj", "party", "setlist", and "genre".

    Returns:
        df (pd.DataFrame): DataFrame with the updated sorting of songs.
    """
    if mix == "dj":
        mix_algorhythm = mixes.dj_mix
    elif mix == "party":
        mix_algorhythm = mixes.party_mix
    elif mix == "setlist":
        mix_algorhythm = mixes.setlist_mix
    elif mix == "genre":
        mix_algorhythm = mixes.genre_mix

    df = mix_algorhythm(playlist_df)

    return df


class Spotify:
    """Class used for pulling and pushing playlists to and from Spotify.

    Args:
        client_id (str): Your Client ID generated from your Spotify application.
        client_secret (str): Your Client Secret ID generated from your Spotify application.
        redirect_uri (str): Your Redirect URI set from your Spotify application.

    Attributes:
        sp (spotipy.client.Spotify object): Spotify API client used to connect to your account.
    """

    def __init__(self, client_id, client_secret, redirect_uri):
        self.sp = sp_connect.connect_spotify(client_id, client_secret, redirect_uri)

    def get_playlist_features(self, playlist_id, genres=False):
        """Pull in all required features of songs in a given playlist.

        Args:
            playlist_id (str): Unique Spotify playlist ID or shared link. This can be acquired by selecting a playlist and selecting the "copy link to playlist" option under share.

        Returns:
            playlist_df (pd.DataFrame): DataFrame of all tracks and their features in the inputted playlist. To be used as input into the sort_playlist function.
        """
        # Get playlist object
        playlist = self.sp.playlist(playlist_id)
        playlist_tracks = playlist["tracks"]

        # First, get all song IDs for feature extraction
        song_ids = []
        utils.show_tracks(playlist_tracks, song_ids)
        while playlist_tracks["next"]:
            playlist_tracks = self.sp.next(playlist_tracks)
            utils.show_tracks(playlist_tracks, song_ids)

        # Now iterate through each song to get required features
        feature_store = []
        for i in song_ids:
            utils.progress_bar(
                len(feature_store) + 1,
                len(song_ids),
                prefix="Loading songs from {}:".format(playlist["name"]),
            )
            feature_store.append(sp_extract.get_track_features(self.sp, i, genres))
        playlist_df = pd.DataFrame(feature_store)

        if genres:
            # Explode and scale genres
            dummies = playlist_df["genres"].explode().str.get_dummies()
            dummies = dummies.groupby(level=0).sum()
            dummies = MinMaxScaler().fit_transform(dummies)

            # Apply PCA to identify similar song groupings
            pca = PCA(n_components=1)
            log_pca = pca.fit_transform(dummies)
            pca_feature_importance = np.around(MinMaxScaler().fit_transform(log_pca), 3)

            # Add into df
            playlist_df["artist_similarity"] = pca_feature_importance
            playlist_df["artist_similarity"] = playlist_df["artist_similarity"].apply(
                lambda x: round(x * 10)
            )

        return playlist_df

    def update_playlist(self, playlist_id, playlist_df):
        """Overwrites the songs and order of the given playlist ID, using the songs in the given playlist DataFrame.

        Args:
            playlist_id (str): Unique Spotify playlist ID or shared link. This can be acquired by selecting a playlist and selecting the "copy link to playlist" option under share.
            playlist_df (pd.DataFrame): DataFrame containing the new tracks and order the playlist will be in. This is intended to be the returned DataFrame from the sort_playlist function.

        """
        if len(playlist_df) <= 100:
            self.sp.playlist_replace_items(playlist_id, playlist_df["track_id"])
        elif len(playlist_df) > 100:
            song_pool_temp = playlist_df
            self.sp.playlist_replace_items(
                playlist_id, song_pool_temp["track_id"].head(100)
            )
            song_pool_temp = song_pool_temp.tail(len(song_pool_temp) - 100)
            while len(song_pool_temp) > 0:
                if len(song_pool_temp) > 100:
                    self.sp.user_playlist_add_tracks(
                        self.sp.user, playlist_id, song_pool_temp["track_id"].head(100)
                    )
                    song_pool_temp = song_pool_temp.tail(len(song_pool_temp) - 100)
                else:
                    songs_left = len(song_pool_temp)
                    self.sp.user_playlist_add_tracks(
                        self.sp.user,
                        playlist_id,
                        song_pool_temp["track_id"].head(songs_left),
                    )
                    break
        playlist_desc = html.unescape(self.sp.playlist(playlist_id)["description"])
        desc_keep = playlist_desc.split("(", 1)[0]
        desc_new = desc_keep + " (Mixed by playlistjockey)"
        self.sp.playlist_change_details(playlist_id=playlist_id, description=desc_new)


class Tidal:
    """Class used for pulling and pushing playlists to and from Tidal.

    Args:
        spotify (playlistjockey.main.Spotify object): Spotify object by calling the playlistjockey.Spotify class.

    Attributes:
        sp (spotipy.client.Spotify object): Spotify API client used to connect to your account.
        td (tidalapi.session.Session object): Tidal API client used to connect to your account.
    """

    def __init__(self, spotify):
        self.sp = spotify.sp
        self.td = td_connect.connect()

    def get_playlist_features(self, playlist_id, genres=False):
        """Pull in all required features of songs in a given playlist.

        Args:
            playlist_id (str): Unique Tidal playlist ID. This can be acquired by selecting a playlist, selecting the "copy link to playlist" option under share, and removing everything before the final forward slash. Example playlist ID format: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'.

        Returns:
            playlist_df (pd.DataFrame): DataFrame of all tracks and their features in the inputted playlist. To be used as input into the sort_playlist function.
        """
        # Pull in the playlist tracks
        playlist = self.td.playlist(playlist_id)
        tracks = playlist.tracks()

        # Now iterate through each song to get required features
        feature_store = []
        for i in tracks:
            utils.progress_bar(
                len(feature_store) + 1,
                len(tracks),
                prefix="Loading songs from {}:".format(playlist.name),
            )
            feature_store.append(
                td_extract.get_song_features(self.sp, self.td, i.id, genres)
            )

        playlist_df = pd.DataFrame(feature_store)

        if genres:
            # Explode and scale genres
            dummies = playlist_df["genres"].explode().str.get_dummies()
            dummies = dummies.groupby(level=0).sum()
            dummies = MinMaxScaler().fit_transform(dummies)

            # Apply PCA to identify similar song groupings
            pca = PCA(n_components=1)
            log_pca = pca.fit_transform(dummies)
            pca_feature_importance = np.around(MinMaxScaler().fit_transform(log_pca), 3)

            # Add into df
            playlist_df["artist_similarity"] = pca_feature_importance
            playlist_df["artist_similarity"] = playlist_df["artist_similarity"].apply(
                lambda x: round(x * 10)
            )

        return playlist_df

    def update_playlist(self, playlist_id, playlist_df):
        """Overwrites the songs and order of the given playlist ID, using the songs in the given playlist DataFrame.

        Args:
            playlist_id (str): Unique Tidal playlist ID. This can be acquired by selecting a playlist, selecting the "copy link to playlist" option under share, and removing everything before the final forward slash. Example playlist ID format: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'.
            playlist_df (pd.DataFrame): DataFrame containing the new tracks and order the playlist will be in. This is intended to be the returned DataFrame from the sort_playlist function.

        """
        # Get playlist object
        playlist = self.td.playlist(playlist_id)

        # Remove previous order
        try:
            playlist.remove_by_indices(range(0, len(playlist.tracks())))
        except:
            pass

        # Refresh playlist object
        playlist = self.td.playlist(playlist_id)

        # Add new song order 100 songs at a time
        q = len(playlist_df) // 100
        rem = len(playlist_df) % 100
        playlist_df = playlist_df[playlist_df["track_id"].notna()]
        playlist_df["track_id"] = playlist_df["track_id"].astype(int)

        for i in range(q):
            playlist.add(list(playlist_df["track_id"].head(100)))
            playlist_df = playlist_df.tail(len(playlist_df) - 100)

        playlist.add(list(playlist_df["track_id"].head(rem)))

        # Update playlist description
        description = html.unescape(playlist.description)
        if description.find("(Mixed by playlistjockey.com)") == -1:
            description = description + " (Mixed by playlistjockey.com)"
        playlist.edit(description=description)
