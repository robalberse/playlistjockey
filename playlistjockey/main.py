import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA
import numpy as np

from playlistjockey import connect, utils, extract

class PlaylistJockey:
    def __init__(self, client_id, client_secret):
        self.sp = connect.connect_spotify(client_id, client_secret)

    def get_playlist_features(self, playlist_id):
        # Get playlist object
        playlist = self.sp.playlist(playlist_id)['tracks']

        # First, get all song IDs for feature extraction
        song_ids = []
        utils.show_tracks(playlist, song_ids)
        while playlist['next']:
            playlist = self.sp.next(playlist)
            utils.show_tracks(playlist, song_ids)

        # Now iterate through each song to get required features
        feature_store = []
        for i in song_ids:
            feature_store.append(extract.get_track_features(self.sp, i))
        playlist_df = pd.DataFrame(feature_store)

        # Explode and scale genres
        dummies = playlist_df['genres'].explode().str.get_dummies()
        dummies = dummies.sum(level=0).add_prefix('genre_')
        dummies = MinMaxScaler().fit_transform(dummies)

        # Apply PCA to identify similar song groupings
        pca = PCA(n_components=1)
        log_pca = pca.fit_transform(dummies)
        pca_feature_importance = np.around(MinMaxScaler().fit_transform(log_pca), 3)

        # Add into df
        playlist_df['artist_similarity'] = pca_feature_importance
        playlist_df['artist_similarity'] = playlist_df['artist_similarity'].apply(lambda x: round(x*10))

        return playlist_df