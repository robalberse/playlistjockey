import random
import spotipy
import pandas as pd

def connect_spotify(client_id:str, client_secret:str, spotify_user:str):
    '''
    Connect to the Spotify API. Create an application to recieve proper
    authentication from https://developer.spotify.com/

    Parameters
    ----------
    client_id : str
        Your unique client ID.
    client_secret : str
        Your unique client secret.
    spotify_user : str
        Your Spotify user ID.

    Returns
    -------
    Generates global sp and USER_ID variables for other functions.

    '''
    global SP
    global USER_ID
    USER_ID = spotify_user
    token = spotipy.util.prompt_for_user_token(USER_ID,
                                        scope='playlist-modify-private,\
                                               playlist-modify-public',
                                        client_id=client_id, client_secret=client_secret,
                                        redirect_uri='https://localhost:8000')
    if token:
        SP = spotipy.Spotify(auth=token, requests_timeout=10)

def show_tracks(results, results_array):
    '''
    Helper function to ensure all song IDs are identified from a playlist. This
    bypasses the 100 song API limit.

    '''
    for i, item in enumerate(results['items']):
        try:
            track = item['track']
            results_array.append(track['id'])
        except TypeError:
            pass

def show_playlists(results, results_array):
    '''
    Helper function to ensure all public playlists are identified from a user.
    If a playlist is set to public, but still cannot be read in, make sure
    it is also added to your profile.

    '''
    for i, item in enumerate(results['items']):
        results_array.append(item)

def get_playlist_id(playlist_name:str, other_user:str=None):
    '''
    Ease of use playlist - return the ID of a playlist given its name and
    owner.

    Parameters
    ----------
    playlist_name : str
        Name of selected playlist, case-sensative.
    other_user : str, optional
        If you do not own the playlist, you must also specify the owner's
        username. The default is None.

    Raises
    ------
    ValueError
        Error raised when no match is found.

    Returns
    -------
    playlist_id : str
        Unique Spotify playlist ID of identified playlist.

    '''
    user_playlists = []
    if other_user is None:
        playlists = SP.user_playlists(USER_ID)
    else:
        playlists = SP.user_playlists(other_user)
    show_playlists(playlists, user_playlists)
    while playlists['next']:
        playlists = SP.next(playlists)
        show_playlists(playlists, user_playlists)
    identified_playlist = list(filter(lambda p: p['name'] in playlist_name, user_playlists))
    try:
        return identified_playlist[0]['id']
    except IndexError:
        raise ValueError('Playlist not found')

def get_song_features(song_id:str):
    '''
    Extract song data.

    Parameters
    ----------
    song_id : str
        Spotify song ID.

    Raises
    ------
    ValueError
        Error raised when an invalid ID is inputted.

    Returns
    -------
    song_features : dict
        Song data detailing basic information.

    '''
    try:
        basic_info = SP.track(song_id)
        audio_info = SP.audio_features(song_id)
    except:
        raise ValueError('Invalid song ID')
    track_id = basic_info['id']
    title = basic_info['name']
    artists = []
    artist_ids = []
    for i in basic_info['artists']:
        artists.append(i['name'])
        artist_ids.append(i['id'])
    genres = []
    for i in artist_ids:
        for j in SP.artist(i)['genres']:
            genres.append(j)
    release_year = int(pd.to_datetime(basic_info['album']['release_date']).year)
    duration_s = basic_info['duration_ms']/1000
    pop_energy = round((audio_info[0]['energy']*50+\
                        audio_info[0]['danceability']*50+\
                        basic_info['popularity'])/200, 2)
    bpm = audio_info[0]['tempo']
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
    key = int(camelot_key[:len(camelot_key)-1])-1
    mode = mode_dict[(camelot_key[-1])]
    song_features = {'track_id':track_id,
                      'title':title,
                      'artists':artists,
                      'genres':genres,
                      'release_year':release_year,
                      'duration_s':duration_s,
                      'pop_energy':pop_energy,
                      'bpm':bpm,
                      'key':key,
                      'mode':mode}
    return song_features

def get_playlist_features(playlist_id:str):
    '''
    Return the features of each song from a given playlist.

    Parameters
    ----------
    playlist_id : str
        Unique Spotify playlist ID.

    Raises
    ------
    ValueError
        Error raised when an invalid playlist ID is inputted.

    Returns
    -------
    track_features_df : DataFrame
        Features of each track in a DataFrame.

    '''
    try:
        playlist = SP.playlist(playlist_id)['tracks']
    except:
        raise ValueError('Invalid playlist ID')
    song_ids = []
    show_tracks(playlist, song_ids)
    while playlist['next']:
        playlist = SP.next(playlist)
        show_tracks(playlist, song_ids)
    track_features = []
    for i in song_ids:
        track_features.append(get_song_features(i))
    track_features_df = pd.DataFrame(track_features)
    return track_features_df

def artist_filter(donor_df:pd.DataFrame, recipient_df:pd.DataFrame,
                  previous_songs:int=3):
    '''
    Because artists will typically stick to similar keys for their songs, this
    function ensures the same artist will not be over-played.

    Parameters
    ----------
    donor_df : pd.DataFrame
        Songs available to be chosen as the next song.
    recipient_df : pd.DataFrame
        Current list and order of songs for the updated playlist.
    previous_songs : int, optional
        The number of previous tracks to collect artist names.
        The default is 3.

    Returns
    -------
    new_donor_df : pd.DataFrame
        List of selectable next songs that do not contain the recent artists
        from the recipient list.

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

def key_wrap(key_value:int):
    '''
    Allow key values to wrap backwards from 0 to 11, or forwards from 11 to 0.

    Parameters
    ----------
    key_value : int
        Key value from the most recently picked song.

    Returns
    -------
    prev_song_key_lower : int
        Lower acceptable key value.
    prev_song_key_upper : int
        Higher acceptable key value.

    '''
    if key_value-1 == -1:
        prev_song_key_lower = 11
    else:
        prev_song_key_lower = key_value-1
    if key_value+1 == 12:
        prev_song_key_upper = 0
    else:
        prev_song_key_upper = key_value+1
    return prev_song_key_lower, prev_song_key_upper

def key_filter(donor_df:pd.DataFrame, recipient_df:pd.DataFrame):
    '''
    Filter donor_df for songs with compatable keys to the previously added song
    to the recipient_df.

    Parameters
    ----------
    donor_df : pd.DataFrame
        Songs available to be chosen as the next song.
    recipient_df : pd.DataFrame
        Current list and order of songs for the updated playlist.

    Returns
    -------
    key_df : pd.DataFrame
        List of selectable next songs that have compatable keys to the most
        recent song from the recipient list.

    '''
    prev_key = recipient_df.iloc[-1]['key']
    prev_mode = recipient_df.iloc[-1]['mode']
    ideal_keys_1 = donor_df[donor_df.key==prev_key]
    lower_key, upper_key = key_wrap(prev_key)
    ideal_keys_2 = donor_df[(donor_df['mode']==prev_mode) &
                            ((donor_df['key']==lower_key) |
                             (donor_df['key']==upper_key))]
    key_df = pd.concat([ideal_keys_1, ideal_keys_2])
    return key_df

def bpm_filter(donor_df:pd.DataFrame, recipient_df:pd.DataFrame):
    '''
    Filter donor_df for songs with similar BPM values to the previously added
    song to the recipient_df.

    Parameters
    ----------
    donor_df : pd.DataFrame
        Songs available to be chosen as the next song.
    recipient_df : pd.DataFrame
        Current list and order of songs for the updated playlist.

    Returns
    -------
    key_df : pd.DataFrame
        List of selectable next songs that have similar BPM values to the most
        recent song from the recipient list.

    '''
    prev_bpm = recipient_df.iloc[-1]['bpm']
    bpm_df = donor_df[(donor_df.bpm>=prev_bpm*0.9) &
                      (donor_df.bpm<=prev_bpm*1.1)]
    return bpm_df

def random_select_song(donor_df:pd.DataFrame):
    '''
    Select a random song ID from a playlist DataFrame.

    Parameters
    ----------
    donor_df : pd.DataFrame
        Songs available to be chosen as the next song.

    Returns
    -------
    next_song_index : pd.index
        DataFrame index of randomly selected song.

    '''
    next_song_index = random.choice(list(donor_df.index))
    return next_song_index

def move_song(donor_df:pd.DataFrame, next_song_index:int,
              recipient_df:pd.DataFrame, select_type:str='random'):
    '''
    Move a song from the donor_df to the recipient_df given its index.

    Parameters
    ----------
    donor_df : pd.DataFrame
        Songs available to be chosen as the next song.
    next_song_index : int
        Index of chosen song to be moved.
    recipient_df : pd.DataFrame
        Current list and order of songs for the updated playlist.
    select_type : str, optional
        Identifies how the song was chosen. The default is 'random'.

    Returns
    -------
    new_donor_df : pd.DataFrame
        Updated donor DataFrame.
    new_recipient_df : pd.DataFrame
        Updated recipient DataFrame.

    '''
    donor_df.at[next_song_index, 'select_type'] = select_type
    new_recipient_df = pd.concat([recipient_df,
                                  donor_df.loc[[next_song_index]]])
    new_donor_df = donor_df.drop(next_song_index)
    return new_donor_df, new_recipient_df

def dj_select_song(donor_df:pd.DataFrame, recipient_df:pd.DataFrame,
                   opt_output:bool=False):
    '''
    Choses the next song by finding songs with compatable keys and similar
    BPM values.

    Parameters
    ----------
    donor_df : pd.DataFrame
        Songs available to be chosen as the next song.
    recipient_df : pd.DataFrame
        Current list and order of songs for the updated playlist.
    opt_output : bool, optional
        Only output list of compatable songs, not select one at random.
        The default is False.

    Returns
    -------
    new_donor_df : pd.DataFrame
        Updated donor DataFrame.
    new_recipient_df : pd.DataFrame
        Updated recipient DataFrame.

    '''
    prev_artists = artist_filter(donor_df, recipient_df)
    ideal_bpms = bpm_filter(prev_artists, recipient_df)
    dj_pool = key_filter(ideal_bpms, recipient_df)
    if opt_output is True:
        return dj_pool
    else:
        try:
            dj_index = random_select_song(dj_pool)
            new_donor_df, new_recipient_df = move_song(donor_df,
                                                       dj_index,
                                                       recipient_df,
                                                       'dj')
        except:
            pass
        return new_donor_df, new_recipient_df

def opt_dj_select_song(donor_df:pd.DataFrame, recipient_df:pd.DataFrame):
    '''
    Similar to dj_select_song, but instead of choosing a compatable song at
    random, the song with the most compatable DJ songs next is chosen.

    Parameters
    ----------
    donor_df : pd.DataFrame
        Songs available to be chosen as the next song.
    recipient_df : pd.DataFrame
        Current list and order of songs for the updated playlist.

    Returns
    -------
    new_donor_df : pd.DataFrame
        Updated donor DataFrame.
    new_recipient_df : pd.DataFrame
        Updated recipient DataFrame.

    '''
    dj_pool = dj_select_song(donor_df, recipient_df, True)
    for i in list(dj_pool.index):
        drill_song = dj_pool.loc[[i]]
        dj_pool.at[i, 'drill_depth'] = len(dj_select_song(donor_df,
                                                          drill_song,
                                                          True))
    try:
        dj_pool = dj_pool.sort_values(by=['drill_depth'], ascending=False)
        dj_index = dj_pool.index[0]
        new_donor_df, new_recipient_df = move_song(donor_df,
                                                   dj_index,
                                                   recipient_df,
                                                   'opt_dj')
    except:
        pass
    return new_donor_df, new_recipient_df

def key_select_song(donor_df:pd.DataFrame, recipient_df:pd.DataFrame):
    '''
    Select the next song only by its key.

    Parameters
    ----------
    donor_df : pd.DataFrame
        Songs available to be chosen as the next song.
    recipient_df : pd.DataFrame
        Current list and order of songs for the updated playlist.

    Returns
    -------
    new_donor_df : pd.DataFrame
        Updated donor DataFrame.
    new_recipient_df : pd.DataFrame
        Updated recipient DataFrame.

    '''
    prev_artists = artist_filter(donor_df, recipient_df)
    key_pool = key_filter(prev_artists, recipient_df)
    try:
        key_index = random_select_song(key_pool)
        new_donor_df, new_recipient_df = move_song(donor_df,
                                                   key_index,
                                                   recipient_df,
                                                   'key')
    except:
        pass
    return new_donor_df, new_recipient_df

def bpm_select_song(donor_df:pd.DataFrame, recipient_df:pd.DataFrame):
    '''
    Select the next song only by its BPM value.

    Parameters
    ----------
    donor_df : pd.DataFrame
        Songs available to be chosen as the next song.
    recipient_df : pd.DataFrame
        Current list and order of songs for the updated playlist.

    Returns
    -------
    new_donor_df : pd.DataFrame
        Updated donor DataFrame.
    new_recipient_df : pd.DataFrame
        Updated recipient DataFrame.

    '''
    prev_artists = artist_filter(donor_df, recipient_df)
    bpm_pool = bpm_filter(prev_artists, recipient_df)
    try:
        bpm_index = random_select_song(bpm_pool)
        new_donor_df, new_recipient_df = move_song(donor_df,
                                                   bpm_index,
                                                   recipient_df,
                                                   'bpm')
    except:
        pass
    return new_donor_df, new_recipient_df

def dj_playlist_sort(donor_playlist:str):
    '''
    Main function - sort the entire donor_playlist like a DJ.

    Parameters
    ----------
    donor_playlist : str or pd.DataFrame
        Playlist to be sorted. Can be playlist ID of a Spotify playlist, or a
        playlist DataFrame that has been passed through the
        get_playlist_features function.

    Returns
    -------
    recipient_df : pd.DataFrame
        Sorted playlist with new 'select_type' column detailing how each song
        was selected.

    '''
    if isinstance(donor_playlist) == str:
        donor_df = get_playlist_features(donor_playlist)
    else:
        donor_df = donor_playlist
    recipient_df = pd.DataFrame(columns=donor_df.columns)
    song_1_index = random_select_song(donor_df)
    # Begin by selecting a random song
    donor_df, recipient_df = move_song(donor_df, song_1_index, recipient_df)
    while len(donor_df)!=0:
        current_song_count = len(recipient_df)
        while True:
            # Identify ideal DJ songs
            donor_df, recipient_df = opt_dj_select_song(donor_df, recipient_df)
            if len(recipient_df) != current_song_count:
                break
            # Identify songs with compatable keys
            donor_df, recipient_df = key_select_song(donor_df, recipient_df)
            if len(recipient_df) != current_song_count:
                break
            # Identify songs with similar BPM values
            donor_df, recipient_df = bpm_select_song(donor_df, recipient_df)
            if len(recipient_df) != current_song_count:
                break
            # If there are no good matches, select a random song
            rand_song_index = random_select_song(donor_df)
            donor_df, recipient_df = move_song(donor_df,
                                               rand_song_index,
                                               recipient_df)
            if len(donor_df)!=0:
                break
    return recipient_df

def push_to_spotify(playlist_id:str, playlist_df:pd.DataFrame):
    '''
    Overwrite a Spotify playlist with its new song order.

    Parameters
    ----------
    playlist_id : str
        Unique Spotify playlist ID.
    playlist_df : pd.DataFrame
        Playlist DataFrame in updated song order.

    Returns
    -------
    recipient_df : pd.DataFrame
        Sorted playlist with new 'select_type' column detailing how each song
        was selected.

    '''
    if len(playlist_df) <= 100:
        SP.playlist_replace_items(playlist_id, playlist_df['track_id'])
    elif len(playlist_df) > 100:
        song_pool_temp = playlist_df
        SP.playlist_replace_items(playlist_id, song_pool_temp['track_id'].head(100))
        song_pool_temp = song_pool_temp.tail(len(song_pool_temp)-100)
        while len(song_pool_temp) > 0:
            if len(song_pool_temp) > 100:
                SP.user_playlist_add_tracks(USER_ID,
                                            playlist_id,
                                            song_pool_temp['track_id'].head(100))
                song_pool_temp = song_pool_temp.tail(len(song_pool_temp)-100)
            else:
                songs_left = len(song_pool_temp)
                SP.user_playlist_add_tracks(USER_ID,
                                            playlist_id,
                                            song_pool_temp['track_id'].head(songs_left))
                break
    playlist_desc = SP.playlist(playlist_id)['description'].replace('&#x2F;', '/')
    desc_keep = playlist_desc.split('[', 1)[0]
    desc_new = desc_keep + '[Sorted by dj_spotify. Play in order, turn on '\
                            'automix and crossfader.]'
    SP.playlist_change_details(playlist_id=playlist_id, description=desc_new)
    return playlist_df
