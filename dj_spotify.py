# -*- coding: utf-8 -*-

''' Module for sorting a Spotify playlist like a DJ. '''

import sys
import random
import warnings
import html
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA

warnings.filterwarnings('ignore')

class DJ_Spotify:

    def __init__(self, username:str, client_id:str, client_secret:str):
        self.user = username
        self.client_id = client_id
        self.client_secret = client_secret
        self.sp = self._connect()

    def _connect(self):
        '''
        Used in the initialization of the class to create an API session.

        '''
        auth_mgmt = SpotifyOAuth(client_id=self.client_id,
                                 client_secret=self.client_secret,
                                 redirect_uri='https://localhost:8000',
                                 scope='playlist-modify-private,\
                                        playlist-read-private,\
                                        playlist-modify-public,\
                                        playlist-read-collaborative')
        session = spotipy.Spotify(auth_manager=auth_mgmt,
                                  requests_timeout=10)
        if session:
            return session

    def show_tracks(self, results, results_array):
        '''
        Helper function to ensure all song IDs are identified from a playlist,
        bypassing the 100-song limit.

        '''
        for i, item in enumerate(results['items']):
            try:
                track = item['track']
                results_array.append(track['id'])
            except TypeError:
                pass

    def show_playlists(self, results, results_array):
        '''
        Helper function to ensure all public playlists are identified from a
        user. If a playlist is set to public, but still cannot be read in, make
        sure it is also added to your profile.

        '''
        for i, item in enumerate(results['items']):
            results_array.append(item)

    def get_playlist_id(self, playlist_name:str, other_user:str=None):
        '''
        Helper function to return the ID of a playlist given its name and
        owner.

        '''
        user_playlists = []
        if other_user is None:
            playlists = self.sp.user_playlists(self.user)
        else:
            playlists = self.sp.user_playlists(other_user)
        self.show_playlists(playlists, user_playlists)
        while playlists['next']:
            playlists = self.sp.next(playlists)
            self.show_playlists(playlists, user_playlists)
        identified_playlist = list(filter(lambda p: p['name'] in playlist_name,
                                          user_playlists))
        try:
            return identified_playlist[0]['id']
        except IndexError:
            raise ValueError('Playlist not found')

    def get_song_features(self, song_id:str):
        '''
        Extract required data from an individual song.

        '''
        try:
            basic_info = self.sp.track(song_id)
            audio_info = self.sp.audio_features(song_id)
        except:
            warnings.warn('Invalid song ID {}. Song will be skipped.'.format(song_id))
        artists = []
        artist_ids = []
        for i in basic_info['artists']:
            artists.append(i['name'])
            artist_ids.append(i['id'])
        genres = []
        for i in artist_ids:
            for j in self.sp.artist(i)['genres']:
                genres.append(j)
        pred_key = audio_info[0]['key']
        pred_mode = audio_info[0]['mode']
        camelot_dict = {(0,1):'8B',
                		(1,1):'3B',
                		(2,1):'10B',
                		(3,1):'5B',
                		(4,1):'12B',
                		(5,1):'7B',
                		(6,1):'2B',
                		(7,1):'9B',
                		(8,1):'4B',
                		(9,1):'11B',
                		(10,1):'6B',
                		(11,1):'1B',
                		(0,0):'5A',
                		(1,0):'12A',
                		(2,0):'7A',
                		(3,0):'2A',
                		(4,0):'9A',
                		(5,0):'4A',
                		(6,0):'11A',
                		(7,0):'6A',
                		(8,0):'1A',
                		(9,0):'8A',
                		(10,0):'3A',
                		(11,0):'10A'}
        mode_dict = {'A':0,
                     'B':1}
        camelot_key = camelot_dict[(pred_key, pred_mode)]
        key = int(camelot_key[:len(camelot_key)-1])
        mode = mode_dict[(camelot_key[-1])]
        song_features = {'track_id':basic_info['id'],
                         'title':basic_info['name'],
                         'artists':artists,
                         'album':basic_info['album']['name'],
                         'genres':genres,
                         'release_year':int(pd.to_datetime(basic_info['album']['release_date']).year),
                         'duration_s':basic_info['duration_ms']/1000,
                         'energy':audio_info[0]['energy'],
                         'bpm':audio_info[0]['tempo'],
                         'key':key,
                         'mode':mode}
        return song_features

    def get_playlist_features(self, playlist_id:str):
        '''
        Return the features of each song from a given playlist.

        '''
        try:
            playlist = self.sp.playlist(playlist_id)['tracks']
        except:
            raise ValueError('Invalid playlist ID')
        song_ids = []
        self.show_tracks(playlist, song_ids)
        while playlist['next']:
            playlist = self.sp.next(playlist)
            self.show_tracks(playlist, song_ids)
        track_features = []
        for i in song_ids:
            sys.stdout.write('\rLoaded {}/{} songs     '.format(len(track_features)+1,
                                                                len(song_ids)))
            sys.stdout.flush()
            try:
                track_features.append(self.get_song_features(i))
            except TypeError:
                pass
        track_features_df = pd.DataFrame(track_features)
        dummies = track_features_df['genres'].explode().str.get_dummies()\
            .sum(level=0).add_prefix('genre_')
        dummies_scaled = MinMaxScaler().fit_transform(dummies)
        pca = PCA(n_components=1)
        log_pca = pca.fit_transform(dummies_scaled)
        pca_feature_importance = np.around(MinMaxScaler().fit_transform(log_pca),
                                           3)
        track_features_df.insert(loc=7,
                                 column='genre_scalar',
                                 value=pca_feature_importance)
        return track_features_df

    def artist_filter(self, donor_df:pd.DataFrame, recipient_df:pd.DataFrame,
                      previous_songs:int=5):
        '''
        Because artists typically stick to similar keys for their songs on a
        particular album, this function ensures the same artist will not be
        over-played while sorting a playlist.

        '''
        previous_artists = []
        for i in range(1, previous_songs+1):
            try:
                previous_artists = previous_artists+recipient_df['artists'].iloc[-i]
            except:
                pass
        new_donor_df = donor_df[(~donor_df.apply(lambda x:\
                                                  any(i in previous_artists for i in x['artists']),
                                                  axis=1))]
        return new_donor_df

    def key_wrap(self, key_value:int):
        '''
        Allow key values to wrap backwards from 1 to 12, or forwards from 12 to
        1.

        '''
        if key_value-1 == 0:
            prev_song_key_lower = 12
        else:
            prev_song_key_lower = key_value-1
        if key_value+1 == 13:
            prev_song_key_upper = 1
        else:
            prev_song_key_upper = key_value+1
        return prev_song_key_lower, prev_song_key_upper

    def key_filter(self, donor_df:pd.DataFrame, recipient_df:pd.DataFrame):
        '''
        Filter donor_df for songs with compatable keys to the previously added
        song from the recipient_df. Each key and mode combination has 4
        compatable key and mode combinations:
            - The previous key and mode
            - The previous key, but alternative mode
            - The previous key+1 and the previous mode
            - the previous key-1 and the previous mode

        Songs with similar keys will share similar sonic qualities with each
        other, making the transitions between them smoother.

        '''
        prev_key = recipient_df.iloc[-1]['key']
        prev_mode = recipient_df.iloc[-1]['mode']
        ideal_keys_1 = donor_df[donor_df.key==prev_key]
        lower_key, upper_key = self.key_wrap(prev_key)
        ideal_keys_2 = donor_df[(donor_df['mode']==prev_mode) &
                                ((donor_df['key']==lower_key) |
                                 (donor_df['key']==upper_key))]
        key_df = pd.concat([ideal_keys_1, ideal_keys_2])
        return key_df

    def bpm_filter(self, donor_df:pd.DataFrame, recipient_df:pd.DataFrame):
        '''
        Filter donor_df for songs with similar BPM values to the previously
        added song from the recipient_df. BPM values are considered compatible
        if they are ±10% of the previously selected song's BPM. Additionally,
        the previous song's BPM value can be doubled or halved beforehand.
        Thus, each BPM has 3 compatible BPM value ranges:
            - [90%, 110%]
            - [180%, 220%]
            - [45%, 55%]

        Songs with similar BPM values will be similar in speed, making the
        transitions between them smoother.

        '''
        prev_bpm = recipient_df.iloc[-1]['bpm']
        bpm_df_1 = donor_df[(donor_df.bpm>=prev_bpm*0.9) &
                            (donor_df.bpm<=prev_bpm*1.1)]
        bpm_df_2 = donor_df[(donor_df.bpm>=prev_bpm*1.8) &
                            (donor_df.bpm<=prev_bpm*2.2)]
        bpm_df_3 = donor_df[(donor_df.bpm>=prev_bpm*0.45) &
                            (donor_df.bpm<=prev_bpm*0.55)]
        bpm_df = pd.concat([bpm_df_1, bpm_df_2, bpm_df_3])
        return bpm_df

    def energy_filter(self, donor_df:pd.DataFrame, recipient_df:pd.DataFrame):
        '''
        Filter donor_df for songs with similar energy values to the previously
        added song from the recipient_df. "Energy" for this algorithm is a
        metric collected from Spotify's own song data. Songs with compatible
        energy levels come from a single range of values of ±0.1 the previous
        song's energy level.

        Songs with similar energy levels will be similar in intensity, making
        the transitions between them smoother.

        '''
        prev_energy = recipient_df.iloc[-1]['energy']
        energy_df = donor_df[(donor_df.energy>=prev_energy-0.1) &
                             (donor_df.energy<=prev_energy+0.1)]
        return energy_df

    def genre_filter(self, donor_df:pd.DataFrame, recipient_df:pd.DataFrame):
        '''
        Filter donor_df for songs with similar artist genres to the previously
        added song from the recipient_df. Genre values are quantified for each
        individual playlist on a scale of [0,1] by implementing principal
        component analysis on the genres listed for particular artist(s).

        Songs with similar genres will be similar in form, style, or subject
        matter; making transitions between them smoother.

        '''
        prev_genre = recipient_df.iloc[-1]['genre_scalar']
        genre_df = donor_df[(donor_df.genre_scalar>=prev_genre-0.1) &
                             (donor_df.genre_scalar<=prev_genre+0.1)]
        return genre_df

    def random_select_song(self, donor_df:pd.DataFrame):
        '''
        Select a random song ID from a playlist DataFrame. Should a song have
        no compatible matches, a random song will be selected to progress the
        algorithm.

        '''
        try:
            next_song_index = random.choice(list(donor_df.index))
        except IndexError:
            next_song_index = None
        return next_song_index

    def move_song(self, donor_df:pd.DataFrame, next_song_index:int,
                  recipient_df:pd.DataFrame, select_type:str='random'):
        '''
        Move a song from the donor_df to the recipient_df given its index.

        '''
        donor_df.at[next_song_index, 'select_type'] = select_type
        new_recipient_df = pd.concat([recipient_df,
                                      donor_df.loc[[next_song_index]]])
        new_donor_df = donor_df.drop(next_song_index)
        return new_donor_df, new_recipient_df

    def dj_select_song(self, donor_df:pd.DataFrame, recipient_df:pd.DataFrame,
                       opt_output:bool=False, opt_select:bool=True):
        '''
        Chooses the next song by finding songs with compatible key, BPM, energy,
        and genre scale values. If multiple songs are identified, choose the
        song with the most future good matches.

        '''
        prev_artists = self.artist_filter(donor_df, recipient_df)
        ideal_bpms = self.bpm_filter(prev_artists, recipient_df)
        ideal_energy = self.energy_filter(ideal_bpms, recipient_df)
        ideal_genre = self.genre_filter(ideal_energy, recipient_df)
        dj_pool = self.key_filter(ideal_genre, recipient_df)
        if opt_output is True:
            output = dj_pool
        elif opt_select is True:
            dj_index = self.opt_select_song(donor_df, dj_pool)
            output = dj_index
        else:
            dj_index = self.random_select_song(dj_pool)
            output = dj_index
        return output

    def opt_select_song(self, donor_df:pd.DataFrame, pool_df:pd.DataFrame):
        '''
        Given a song's list of compatible songs, identify how many future good
        matches each compatible song has. The song with the highest future
        matches will be selected, and its index returned.

        '''
        for i in list(pool_df.index):
            drill_song = pool_df.loc[[i]]
            pool_df.loc[i, 'drill_depth'] = len(self.dj_select_song(donor_df,
                                                                    drill_song,
                                                                    True))
        try:
            dj_pool = pool_df.sort_values(by=['drill_depth'], ascending=False)
            dj_index = dj_pool.index[0]
        except KeyError or IndexError:
            dj_index = None
        return dj_index

    def three_select_song(self, donor_df:pd.DataFrame, recipient_df:pd.DataFrame,
                          opt_select:bool=True):
        '''
        Select the next song by identifying songs that share similar key and
        BPM values. Additionally, songs must also have similar energy or
        genre values.

        '''
        prev_artists = self.artist_filter(donor_df, recipient_df)
        # Compatible key, BPM, and energy
        ideal_key = self.key_filter(prev_artists, recipient_df)
        ideal_bpm = self.bpm_filter(ideal_key, recipient_df)
        key_bpm_eng = self.energy_filter(ideal_bpm, recipient_df)
        # Compatible key, BPM, and genre
        ideal_key = self.key_filter(prev_artists, recipient_df)
        ideal_bpm = self.bpm_filter(ideal_key, recipient_df)
        key_bpm_gen = self.genre_filter(ideal_bpm, recipient_df)
        three_pool = pd.concat([key_bpm_eng, key_bpm_gen])
        three_pool = three_pool.drop_duplicates(subset=['track_id'])
        if opt_select is True:
            three_index = self.opt_select_song(donor_df, three_pool)
        else:
            three_index = self.random_select_song(three_pool)
        return three_index

    def two_select_song(self, donor_df:pd.DataFrame, recipient_df:pd.DataFrame,
                        opt_select:bool=True):
        '''
        Select the next song by identifying songs that share similar key and
        BPM values.

        '''
        prev_artists = self.artist_filter(donor_df, recipient_df)
        # Compatilbe key and BPM
        ideal_key = self.key_filter(prev_artists, recipient_df)
        two_pool = self.bpm_filter(ideal_key, recipient_df)
        if opt_select is True:
            two_index = self.opt_select_song(donor_df, two_pool)
        else:
            two_index = self.random_select_song(two_pool)
        return two_index

    def key_select_song(self, donor_df:pd.DataFrame, recipient_df:pd.DataFrame,
                        opt_select:bool=True):
        '''
        Select the next song only by its key. If there are no suitable matches,
        mixing in key is the next best alternative.

        '''
        prev_artists = self.artist_filter(donor_df, recipient_df)
        key_pool = self.key_filter(prev_artists, recipient_df)
        if opt_select is True:
            key_index = self.opt_select_song(donor_df, key_pool)
        else:
            key_index = self.random_select_song(key_pool)
        return key_index

    def bpm_select_song(self, donor_df:pd.DataFrame, recipient_df:pd.DataFrame,
                        opt_select:bool=True):
        '''
        Select the next song only by its BPM value.

        '''
        prev_artists = self.artist_filter(donor_df, recipient_df)
        bpm_pool = self.bpm_filter(prev_artists, recipient_df)
        if opt_select is True:
            bpm_index = self.opt_select_song(donor_df, bpm_pool)
        else:
            bpm_index = self.random_select_song(bpm_pool)
        return bpm_index

    def energy_select_song(self, donor_df:pd.DataFrame, recipient_df:pd.DataFrame,
                           opt_select:bool=True):
        '''
        Select the next song only by its energy level.

        '''
        prev_artists = self.artist_filter(donor_df, recipient_df)
        energy_pool = self.energy_filter(prev_artists, recipient_df)
        if opt_select is True:
            energy_index = self.opt_select_song(donor_df, energy_pool)
        else:
            energy_index = self.random_select_song(energy_pool)
        return energy_index

    def genre_select_song(self, donor_df:pd.DataFrame, recipient_df:pd.DataFrame,
                          opt_select:bool=True):
        '''
        Select the next song only by its genre scalar value.

        '''
        prev_artists = self.artist_filter(donor_df, recipient_df)
        genre_pool = self.genre_filter(prev_artists, recipient_df)
        if opt_select is True:
            genre_index = self.opt_select_song(donor_df, genre_pool)
        else:
            genre_index = self.random_select_song(genre_pool)
        return genre_index

    def playlist_sort_level_3(self, donor_playlist:str):
        '''
        Sort a playlist like a DJ: placing songs with compatible keys, BPM,
        energy levels, and genres next to each other. This is the most optimal
        sorting function as it will seek to maximize the amount of compatible
        transitions.

        '''
        if isinstance(donor_playlist, str) is True:
            donor_df = self.get_playlist_features(self.get_playlist_id(donor_playlist))
        else:
            donor_df = donor_playlist
        donor_len = len(donor_df)
        recipient_df = pd.DataFrame(columns=donor_df.columns)
        # Begin by selecting a random song
        song_1_index = self.random_select_song(donor_df)
        donor_df, recipient_df = self.move_song(donor_df, song_1_index,
                                                recipient_df)
        while len(donor_df)!=0:
            while True:
                # Identify an ideal DJ song
                next_index = self.dj_select_song(donor_df, recipient_df,
                                                 opt_select=True)
                if next_index is not None:
                    select_type = 'dj_optimal'
                    break
                # Identify an ideal key, bpm and (energy or genre) song
                next_index = self.three_select_song(donor_df, recipient_df,
                                                    opt_select=True)
                if next_index is not None:
                    select_type = 'dj_3'
                    break
                # Identify an ideal key & bpm song
                next_index = self.two_select_song(donor_df, recipient_df,
                                                  opt_select=True)
                if next_index is not None:
                    select_type = 'dj_2'
                    break
                # Identify an ideal harmonic song
                next_index = self.key_select_song(donor_df, recipient_df,
                                                  opt_select=True)
                if next_index is not None:
                    select_type = 'key'
                    break
                # Identify an ideal BPM song
                next_index = self.bpm_select_song(donor_df, recipient_df,
                                                  opt_select=True)
                if next_index is not None:
                    select_type = 'bpm'
                    break
                # Identify an ideal energy song
                next_index = self.energy_select_song(donor_df, recipient_df,
                                                     opt_select=True)
                if next_index is not None:
                    select_type = 'energy'
                    break
                # Identify an ideal genre song
                next_index = self.genre_select_song(donor_df, recipient_df,
                                                    opt_select=True)
                if next_index is not None:
                    select_type = 'genre'
                    break
                # If there are no good matches, select a random song
                next_index = self.random_select_song(donor_df)
                if next_index is not None:
                    select_type = 'random'
                    break
            donor_df, recipient_df = self.move_song(donor_df, next_index,
                                                    recipient_df, select_type)
            sys.stdout.write('\rSorted {}/{} songs     '.format(len(recipient_df),
                                                                    donor_len))
            sys.stdout.flush()
        return recipient_df

    def playlist_sort_level_2(self, donor_playlist:str):
        '''
        Sort a playlist like a DJ: placing songs with compatible keys, BPM,
        energy levels, and genres next to each other. This is a less optimal
        sorting function as it will produce sorted playlists with more
        variability.

        '''
        if isinstance(donor_playlist, str) is True:
            donor_df = self.get_playlist_features(self.get_playlist_id(donor_playlist))
        else:
            donor_df = donor_playlist
        donor_len = len(donor_df)
        recipient_df = pd.DataFrame(columns=donor_df.columns)
        # Begin by selecting a random song
        song_1_index = self.random_select_song(donor_df)
        donor_df, recipient_df = self.move_song(donor_df, song_1_index,
                                                recipient_df)
        while len(donor_df)!=0:
            while True:
                # Identify an ideal DJ song
                next_index = self.dj_select_song(donor_df, recipient_df,
                                                 opt_select=False)
                if next_index is not None:
                    select_type = 'dj_optimal'
                    break
                # Identify an ideal key, bpm and (energy or genre) song
                next_index = self.three_select_song(donor_df, recipient_df,
                                                    opt_select=False)
                if next_index is not None:
                    select_type = 'dj_3'
                    break
                # Identify an ideal key & bpm song
                next_index = self.two_select_song(donor_df, recipient_df,
                                                  opt_select=False)
                if next_index is not None:
                    select_type = 'dj_2'
                    break
                # Identify an ideal harmonic song
                next_index = self.key_select_song(donor_df, recipient_df,
                                                  opt_select=False)
                if next_index is not None:
                    select_type = 'key'
                    break
                # Identify an ideal BPM song
                next_index = self.bpm_select_song(donor_df, recipient_df,
                                                  opt_select=False)
                if next_index is not None:
                    select_type = 'bpm'
                    break
                # Identify an ideal energy song
                next_index = self.energy_select_song(donor_df, recipient_df,
                                                     opt_select=False)
                if next_index is not None:
                    select_type = 'energy'
                    break
                # Identify an ideal genre song
                next_index = self.genre_select_song(donor_df, recipient_df,
                                                    opt_select=False)
                if next_index is not None:
                    select_type = 'genre'
                    break
                # If there are no good matches, select a random song
                next_index = self.random_select_song(donor_df)
                if next_index is not None:
                    select_type = 'random'
                    break
            donor_df, recipient_df = self.move_song(donor_df, next_index,
                                                    recipient_df, select_type)
            sys.stdout.write('\rSorted {}/{} songs     '.format(len(recipient_df),
                                                                    donor_len))
            sys.stdout.flush()
        return recipient_df

    def playlist_sort_level_1(self, donor_playlist:str):
        '''
        Sort your playlist with more variety. This function still sorts your
        playlist using key, BPM, energy level, and genre; but in an
        imperfect way to allow for more variety in the order.

        '''
        if isinstance(donor_playlist, str) is True:
            donor_df = self.get_playlist_features(self.get_playlist_id(donor_playlist))
        else:
            donor_df = donor_playlist
        donor_len = len(donor_df)
        recipient_df = pd.DataFrame(columns=donor_df.columns)
        # Begin by selecting a random song
        song_1_index = self.random_select_song(donor_df)
        donor_df, recipient_df = self.move_song(donor_df, song_1_index,
                                                recipient_df)
        while len(donor_df)!=0:
            while True:
                # Identify songs that meet at least 3 criteria
                next_index = self.three_select_song(donor_df, recipient_df,
                                                    opt_select=False)
                if next_index is not None:
                    select_type = 'dj_3'
                    break
                # Identify songs that meet at least 2 criteria
                next_index = self.two_select_song(donor_df, recipient_df,
                                                  opt_select=False)
                if next_index is not None:
                    select_type = 'dj_2'
                    break
                # Identify an ideal harmonic song
                next_index = self.key_select_song(donor_df, recipient_df,
                                                  opt_select=False)
                if next_index is not None:
                    select_type = 'key'
                    break
                # Identify an ideal BPM song
                next_index = self.bpm_select_song(donor_df, recipient_df,
                                                  opt_select=False)
                if next_index is not None:
                    select_type = 'bpm'
                    break
                # Identify an ideal energy song
                next_index = self.energy_select_song(donor_df, recipient_df,
                                                     opt_select=False)
                if next_index is not None:
                    select_type = 'energy'
                    break
                # If there are no good matches, select a random song
                next_index = self.random_select_song(donor_df)
                if next_index is not None:
                    select_type = 'random'
                    break
            donor_df, recipient_df = self.move_song(donor_df, next_index,
                                                    recipient_df, select_type)
            sys.stdout.write('\rSorted {}/{} songs     '.format(len(recipient_df),
                                                                donor_len))
            sys.stdout.flush()
        return recipient_df

    def push_to_spotify(self, playlist_id:str, playlist_df:pd.DataFrame):
        '''
        Overwrite a Spotify playlist with its new song order. You are only
        permitted to overwrite your own playlists.

        '''
        if len(playlist_df) <= 100:
            self.sp.playlist_replace_items(playlist_id, playlist_df['track_id'])
        elif len(playlist_df) > 100:
            song_pool_temp = playlist_df
            self.sp.playlist_replace_items(playlist_id,
                                      song_pool_temp['track_id'].head(100))
            song_pool_temp = song_pool_temp.tail(len(song_pool_temp)-100)
            while len(song_pool_temp) > 0:
                if len(song_pool_temp) > 100:
                    self.sp.user_playlist_add_tracks(self.user,
                                                playlist_id,
                                                song_pool_temp['track_id'].head(100))
                    song_pool_temp = song_pool_temp.tail(len(song_pool_temp)-100)
                else:
                    songs_left = len(song_pool_temp)
                    self.sp.user_playlist_add_tracks(self.user,
                                                playlist_id,
                                                song_pool_temp['track_id'].head(songs_left))
                    break
        playlist_desc = html.unescape(self.sp.playlist(playlist_id)['description'])
        desc_keep = playlist_desc.split('[', 1)[0]
        desc_new = desc_keep + '[Sorted by dj_spotify]'
        self.sp.playlist_change_details(playlist_id=playlist_id, description=desc_new)

    def sort_playlist(self, donor_playlist_name:str, sort_mode:int=3):
        '''
        Main function: identify a playlist you own and determine how you would
        like for it to be sorted. The playlist will be sorted and automatically
        updated in Spotify

        '''
        self.sp = self._connect()
        playlist_id = self.get_playlist_id(donor_playlist_name)
        print('Sorting {}...'.format(donor_playlist_name))
        donor_df = self.get_playlist_features(playlist_id)
        if sort_mode == 3:
            playlist_sorted = self.playlist_sort_level_3(donor_df)
        elif sort_mode == 2:
            playlist_sorted = self.playlist_sort_level_2(donor_df)
        else:
            playlist_sorted = self.playlist_sort_level_1(donor_df)
        self.push_to_spotify(playlist_id, playlist_sorted)
        return playlist_sorted
        print('\nDone.')

    def sort_certain_playlists(self, donor_playlists:dict):
        '''
        Sort a list of public playlists listed on your Spotify profile. To keep
        the order of your playlists fresh, it is advised to re-sort your
        playlists at least on a weekly basis.

        '''
        for playlist in donor_playlists:
            print('\rSorting songs from {}...'.format(playlist))
            self.sp = self._connect()
            if donor_playlists.get(playlist) == 3:
                playlist_sorted = self.playlist_sort_level_3(playlist)
            elif donor_playlists.get(playlist) == 2:
                playlist_sorted = self.playlist_sort_level_2(playlist)
            else:
                playlist_sorted = self.playlist_sort_level_1(playlist)
            self.push_to_spotify(playlist_id=self.get_playlist_id(playlist),
                                 playlist_df=playlist_sorted)
        print('\rAll playlists sorted.')

    def combine_playlists(self, donor_playlists:list, recipient_playlist:str,
                          duration_h:int=4, energy_filter:bool=False,
                          sort_mode:int=3):
        '''
        Combine other playlists into a single playlist. This function is useful
        for extracting playlists created by others into your own. Helping keep
        you up to date on your favorite playlists while simultaneously sorting
        them.

        Again, you can only overwrite the order of your own playlists. However,
        you can pull songs from any public playlist, given the playlist's name
        and owner's username. You can identify the username of any user by
        selecting "Copy Link to Profile" and extracting the string or numbers
        in between the '/user/' and '?' of the resulting link.

        The resulting playlist will automatically be passed through the
        push_to_spotify function.

        '''
        if duration_h is not False:
            seconds_per_playlist = duration_h*3600/len(donor_playlists)
        playlist_pool = pd.DataFrame()
        for playlist in donor_playlists:
            print('\nLoading {}...'.format(playlist))
            playlist_owner = donor_playlists.get(playlist)
            self.sp = self._connect()
            try:
                playlist_songs = self.get_playlist_features(\
                                    self.get_playlist_id(playlist, playlist_owner))
            except ValueError:
                playlist_songs = self.get_playlist_features(playlist)
            if energy_filter is True:
                playlist_songs = playlist_songs.sort_values(by=['energy'],
                                                            ascending=False)
            else:
                playlist_songs = playlist_songs.sample(frac=1)
            if duration_h is False:
                playlist_pool = pd.concat([playlist_pool, playlist_songs])
            else:
                playlist_pool_small = pd.DataFrame(columns=playlist_songs.columns)
                while sum(playlist_pool_small.duration_s)<seconds_per_playlist and\
                      len(playlist_songs)!=0:
                    playlist_songs, playlist_pool_small = self.move_song(playlist_songs,
                                                                         playlist_songs.index[0],
                                                                         playlist_pool_small)
            playlist_pool = pd.concat([playlist_pool, playlist_pool_small])
        recipient_df = playlist_pool.drop_duplicates(subset=['track_id']).reset_index(drop=True)
        print('\nSorting {}...'.format(recipient_playlist))
        if sort_mode == 3:
            playlist_sorted = self.playlist_sort_level_3(recipient_df)
        elif sort_mode == 2:
            playlist_sorted = self.playlist_sort_level_2(recipient_df)
        else:
            playlist_sorted = self.playlist_sort_level_1(recipient_df)
        print('\nPlaylists combined.')
        self.push_to_spotify(self.get_playlist_id(recipient_playlist),
                             playlist_sorted)
        return playlist_sorted
