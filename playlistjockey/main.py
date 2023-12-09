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


def _get_mix(mix):
    """Helper function to define which mixing technique to use."""
    if mix == "dj":
        mix_algorhythm = mixes.dj_mix
    elif mix == "party":
        mix_algorhythm = mixes.party_mix
    elif mix == "setlist":
        mix_algorhythm = mixes.setlist_mix
    elif mix == "genre":
        mix_algorhythm = mixes.genre_mix

    return mix_algorhythm


def sort_playlist(playlist_df, mix, first_track=None):
    """Sorts the songs in a playlist df using a specified mixing algorithm.

    Args:
        playlist_df (pd.DataFrame): DataFrame containing songs with required columns.
        mix (str): String identifying which mixing algorithm you would like to use to sort the playlist. Options so far include "dj", "party", "setlist", and "genre".

    Returns:
        df (pd.DataFrame): DataFrame with the updated sorting of songs.
    """
    # Establish a copy of playlist_df
    df = playlist_df.copy()

    # Identify which mix algorhythm to utilize
    mix_algorhythm = _get_mix(mix)

    # Apply the mix and return
    df = mix_algorhythm(df, first_track)

    return df


def optimal_sort_playlist(playlist_df, mix, n=None):
    """Sort the songs in a playlist df many times using a specified mixing algorithm to find an optimal order.

    Args:
        playlist_df (pd.DataFrame): DataFrame containing songs with required columns.
        mix (str): String identifying which mixing algorithm you would like to use to sort the playlist. Options so far include "dj", "party", "setlist", and "genre".
        n (int): Specifies how many sorting iterations you want to run. Default is the number of songs in the supplied playlist_df.

    Returns:
        df (pd.DataFrame): DataFrame with the updated sorting of songs.
    """
    # Call the mix algorhythm once to get the best select type
    _get_mix(mix)(playlist_df)
    best_select = _get_mix(mix).select_order[0][1]

    # If not explicitly inputted, set iterations to song count
    if not n:
        n = len(playlist_df)

    # Sort the playlist n times, caputring how many best and random selects are made
    mix_store = []
    for i in range(n):
        utils.progress_bar(
            i + 1,
            n,
            prefix="Running iterations of {} algorhythm:".format(mix),
        )
        df = sort_playlist(playlist_df, mix)
        n_best = len(df[df["select_type"] == best_select])
        n_random = len(df[df["select_type"] == "random"])
        mix_peformance = {
            "n_best": n_best,
            "n_random": n_random,
            "diff": n_best - n_random,
            "df": df,
        }
        mix_store.append(mix_peformance)
    results = pd.DataFrame(mix_store)

    # Sort the results to get the optimal song order
    results = results.sort_values(by="diff", ascending=False)

    # Grab the best sorted df and return
    best_sort = results.head(1)
    sorted_df = best_sort["df"].item()
    print(
        "\nMixing optimized, found iteration with {} {} and {} random song transitions.".format(
            best_sort["n_best"].item(), best_select, best_sort["n_random"].item()
        )
    )

    return sorted_df


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
            playlist_id (str): Unique Tidal playlist ID or shared link. This can be acquired by selecting the "copy link to playlist" option under share.

        Returns:
            playlist_df (pd.DataFrame): DataFrame of all tracks and their features in the inputted playlist. To be used as input into the sort_playlist function.
        """
        # If playlist_id is a shared link, strip out the playlist id
        if playlist_id[:6] == "https:":
            playlist_id = playlist_id.split("/")[5]

        # Pull in the playlist tracks
        playlist = self.td.playlist(playlist_id)
        media = playlist.tracks()

        # If there are videos, pull them in instead using the items func
        if playlist.num_videos > 0:
            # Add media 100 items at a time
            q = len(media) // 100
            media = []

            offset = 0
            for i in range(q + 1):
                media.extend(playlist.items(offset=offset))
                offset += 100

        # Now iterate through each song to get required features
        feature_store = []
        for i in media:
            utils.progress_bar(
                len(feature_store) + 1,
                len(media),
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
        # If playlist_id is a shared link, strip out the playlist id
        if playlist_id[:6] == "https:":
            playlist_id = playlist_id.split("/")[5]

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

        if rem > 0:
            playlist.add(list(playlist_df["track_id"].head(rem)))

        # Update playlist description
        description = html.unescape(playlist.description)
        if description.find("(Mixed by playlistjockey.com)") == -1:
            description = description + " (Mixed by playlistjockey.com)"
        playlist.edit(description=description)
