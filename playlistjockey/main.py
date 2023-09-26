import pandas as pd
import html

from playlistjockey import connect, utils, extract, mixes


class PlaylistJockey:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.sp = connect.connect_spotify(client_id, client_secret, redirect_uri)

    def get_playlist_features(self, playlist_id):
        # Get playlist object
        playlist = self.sp.playlist(playlist_id)["tracks"]

        # First, get all song IDs for feature extraction
        song_ids = []
        utils.show_tracks(playlist, song_ids)
        while playlist["next"]:
            playlist = self.sp.next(playlist)
            utils.show_tracks(playlist, song_ids)

        # Now iterate through each song to get required features
        feature_store = []
        for i in song_ids:
            feature_store.append(extract.get_track_features(self.sp, i))
        playlist_df = pd.DataFrame(feature_store)

        return playlist_df

    def sort_playlist(self, playlist_df, mix):
        if mix == "dj":
            mix_algorhythm = mixes.dj_mix

        df = mix_algorhythm(playlist_df)

        return df

    def push_playlist(self, playlist_id, playlist_df):
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
        desc_new = desc_keep + "(Mixed by playlistjockey)"
        self.sp.playlist_change_details(playlist_id=playlist_id, description=desc_new)
