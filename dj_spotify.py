import random
import sys
import html
import warnings
import spotipy
import pandas as pd
warnings.filterwarnings('ignore')

def connect_spotify(client_id:str, client_secret:str, spotify_user:str):
    '''
    Connect to the Spotify API. Create an application to receive proper
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
    Global SP and USER_ID variables for other functions.

    '''
    global SP
    global USER_ID
    USER_ID = spotify_user
    token = spotipy.util.prompt_for_user_token(USER_ID,
                                               scope='playlist-modify-private,\
                                               playlist-modify-public',
                                               client_id=client_id,
                                               client_secret=client_secret,
                                               redirect_uri='https://localhost:8000')
    if token:
        SP = spotipy.Spotify(auth=token, requests_timeout=10)

def show_tracks(results, results_array):
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
    Ease of use function - return the ID of a playlist given its name and
    owner.

    Parameters
    ----------
    playlist_name : str
        Name of selected playlist, case-sensitive.
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
    Extract required data from an individual song.

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
        Song data detailing basic information needed for algorithm.

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
    pop_energy = round((audio_info[0]['energy']*100+\
                        audio_info[0]['danceability']*100+\
                        basic_info['popularity'])/300, 2)
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
    key = int(camelot_key[:len(camelot_key)-1])
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
        sys.stdout.write('\rLoaded {}/{} songs     '.format(len(track_features)+1,
                                                            len(song_ids)))
        sys.stdout.flush()
        track_features.append(get_song_features(i))
    track_features_df = pd.DataFrame(track_features)
    return track_features_df

def artist_filter(donor_df:pd.DataFrame, recipient_df:pd.DataFrame,
                  previous_songs:int=5):
    '''
    Because artists typically stick to similar keys for their songs on a
    particular album, this function ensures the same artist will not be
    over-played while sorting a playlist.

    Parameters
    ----------
    donor_df : pd.DataFrame
        Songs available to be chosen as the next song.
    recipient_df : pd.DataFrame
        Current list and order of songs for the updated playlist.
    previous_songs : int, optional
        The number of previous tracks to collect artist names.
        The default is 5.

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
    Allow key values to wrap backwards from 1 to 12, or forwards from 12 to 1.

    Parameters
    ----------
    key_value : int
        A song's key value, ranging from 1 to 12.

    Returns
    -------
    prev_song_key_lower : int
        Lower acceptable key value.
    prev_song_key_upper : int
        Higher acceptable key value.

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

def key_filter(donor_df:pd.DataFrame, recipient_df:pd.DataFrame):
    '''
    Filter donor_df for songs with compatable keys to the previously added song
    from the recipient_df. Each key and mode combination has 4 compatable key
    and mode combinations:
        - The previous key and mode
        - The previous key, but alternative mode
        - The previous key+1 and the previous mode
        - the previous key-1 and the previous mode

    Songs with similar keys will sound similar to each other, making the
    transitions between them smoother.

    Parameters
    ----------
    donor_df : pd.DataFrame
        Songs available to be chosen as the next song.
    recipient_df : pd.DataFrame
        Current list and order of songs for the updated playlist.

    Returns
    -------
    key_df : pd.DataFrame
        List of selectable next songs that have compatible keys to the most
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
    song from the recipient_df. BPM values are considered compatible if they
    are ±10% of the previously selected song's BPM. Additionally, the previous
    song's BPM value can be doubled or halved beforehand. Thus, each BPM has 3
    compatible BPM value ranges:
        - [90%, 110%]
        - [180%, 220%]
        - [45%, 55%]

    Songs with similar BPM values will be similar in speed, making the
    transitions between them smoother.

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
    bpm_df_1 = donor_df[(donor_df.bpm>=prev_bpm*0.9) &
                        (donor_df.bpm<=prev_bpm*1.1)]
    bpm_df_2 = donor_df[(donor_df.bpm>=prev_bpm*1.8) &
                        (donor_df.bpm<=prev_bpm*2.2)]
    bpm_df_3 = donor_df[(donor_df.bpm>=prev_bpm*0.45) &
                        (donor_df.bpm<=prev_bpm*0.55)]
    bpm_df = pd.concat([bpm_df_1, bpm_df_2, bpm_df_3])
    return bpm_df

def energy_filter(donor_df:pd.DataFrame, recipient_df:pd.DataFrame):
    '''
    Filter donor_df for songs with similar energy values to the previously
    added song from the recipient_df. "Energy" for this algorithm is a
    combination of a song's energy, danceability, and popularity from Spotify's
    own metrics. Songs with compatible energy levels come from a single range
    of values of ±0.1 the previous song's energy level.

    Songs with similar energy levels will be similar in intensity, making the
    transitions between them smoother.

    Parameters
    ----------
    donor_df : pd.DataFrame
        Songs available to be chosen as the next song.
    recipient_df : pd.DataFrame
        Current list and order of songs for the updated playlist.

    Returns
    -------
    energy_df : pd.DataFrame
        List of selectable next songs that have similar energy levels to the
        most recent song from the recipient list.

    '''
    prev_energy = recipient_df.iloc[-1]['pop_energy']
    energy_df = donor_df[(donor_df.pop_energy>=prev_energy-0.1) &
                         (donor_df.pop_energy<=prev_energy+0.1)]
    return energy_df

def random_select_song(donor_df:pd.DataFrame):
    '''
    Select a random song ID from a playlist DataFrame. Should a song have no
    compatible DJ, key, BPM, or energy matches, a random song will be selected
    to progress the algorithm.

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
                   opt_output:bool=False, consider_energy:bool=True):
    '''
    Choses the next song by finding songs with compatible keys, BPM, and energy
    values. If multiple songs identified, choose the song with the most future
    good matches.

    Parameters
    ----------
    donor_df : pd.DataFrame
        Songs available to be chosen as the next song.
    recipient_df : pd.DataFrame
        Current list and order of songs for the updated playlist.
    opt_output : bool, optional
        Only output list of compatible songs for opt_select_song function.
        The default is False.

    Returns
    -------
    dj_index : int
        Index of selected song to be added to the recipient_df.

    '''
    prev_artists = artist_filter(donor_df, recipient_df)
    ideal_bpms = bpm_filter(prev_artists, recipient_df)
    if consider_energy is True:
        ideal_energy = energy_filter(ideal_bpms, recipient_df)
    else:
        ideal_energy = ideal_bpms
    dj_pool = key_filter(ideal_energy, recipient_df)
    if opt_output is True:
        output = dj_pool
    else:
        dj_index = opt_select_song(donor_df, recipient_df, dj_pool)
        output = dj_index
    return output

def opt_select_song(donor_df:pd.DataFrame, recipient_df:pd.DataFrame,
                    pool_df:pd.DataFrame):
    '''
    Given a song's list of compatible songs, identify how many future good
    matches each compatible song has. The song with the highest future matches
    will be selected, and its index returned.

    Parameters
    ----------
    donor_df : pd.DataFrame
        Songs available to be chosen as the next song.
    recipient_df : pd.DataFrame
        Current list and order of songs for the updated playlist.
    pool_df : pd.DataFrame
        DataFrame containing compatible songs from dj_select_song 

    Returns
    -------
    dj_index : int
        Index of selected song to be added to the recipient_df.

    '''
    for i in list(pool_df.index):
        drill_song = pool_df.loc[[i]]
        pool_df.loc[i, 'drill_depth'] = len(dj_select_song(donor_df,
                                                           drill_song,
                                                           True))
    try:
        dj_pool = pool_df.sort_values(by=['drill_depth'], ascending=False)
        dj_index = dj_pool.index[0]
    except KeyError or IndexError:
        dj_index = None
    return dj_index

def key_select_song(donor_df:pd.DataFrame, recipient_df:pd.DataFrame):
    '''
    Select the next song only by its key. If there are no suitable DJ matches,
    mixing in key is the next best alternative.

    Parameters
    ----------
    donor_df : pd.DataFrame
        Songs available to be chosen as the next song.
    recipient_df : pd.DataFrame
        Current list and order of songs for the updated playlist.

    Returns
    -------
    key_index : int
        Index of selected song to be added to the recipient_df.

    '''
    prev_artists = artist_filter(donor_df, recipient_df)
    key_pool = key_filter(prev_artists, recipient_df)
    key_index = opt_select_song(donor_df, recipient_df, key_pool)
    return key_index

def bpm_select_song(donor_df:pd.DataFrame, recipient_df:pd.DataFrame):
    '''
    Select the next song only by its BPM value. If there no DJ or key matches,
    keeping the speed consistent is the next best alternative.

    Parameters
    ----------
    donor_df : pd.DataFrame
        Songs available to be chosen as the next song.
    recipient_df : pd.DataFrame
        Current list and order of songs for the updated playlist.

    Returns
    -------
    bpm_index : int
        Index of selected song to be added to the recipient_df.

    '''
    prev_artists = artist_filter(donor_df, recipient_df)
    bpm_pool = bpm_filter(prev_artists, recipient_df)
    bpm_index = opt_select_song(donor_df, recipient_df, bpm_pool)
    return bpm_index

def energy_select_song(donor_df:pd.DataFrame, recipient_df:pd.DataFrame):
    '''
    Select the next song only by its energy level. If there no DJ, key, or BPM
    matches, keeping the energy consistent is the next best alternative.

    Parameters
    ----------
    donor_df : pd.DataFrame
        Songs available to be chosen as the next song.
    recipient_df : pd.DataFrame
        Current list and order of songs for the updated playlist.

    Returns
    -------
    energy_index : int
        Index of selected song to be added to the recipient_df.

    '''
    prev_artists = artist_filter(donor_df, recipient_df)
    energy_pool = energy_filter(prev_artists, recipient_df)
    energy_index = opt_select_song(donor_df, recipient_df, energy_pool)
    return energy_index

def dj_playlist_sort(donor_playlist:str, playlist_name:str='Updating'):
    '''
    Main function - sort the entire donor_playlist like a DJ. The logic is as
    follows:
        1. Select a random song to serve as the first song
        2. While all songs have yet to be sorted:
            -- Begin Loop -- Try to select next song on...
            a. All DJ mixing strategies
            b. Key and BPM values
            c. Only key values
            d. Only BPM values
            e. Only energy levels
            f. If no compatible songs are available, select a random song to
               progress
            g. Move selected song to recipient_df
            -- Restart Loop --
        3. Return sorted order of songs

    Parameters
    ----------
    donor_playlist : str or pd.DataFrame
        Playlist to be sorted. Can be the case-sensitive name of one of your
        Spotify playlists, or a playlist DataFrame that has been previously
        passed through the get_playlist_features function.

    Returns
    -------
    recipient_df : pd.DataFrame
        Sorted playlist with new 'select_type' column detailing how each song
        was selected.

    '''
    if isinstance(donor_playlist, str) is True:
        donor_df = get_playlist_features(get_playlist_id(donor_playlist))
    else:
        donor_df = donor_playlist
    donor_len = len(donor_df)
    recipient_df = pd.DataFrame(columns=donor_df.columns)
    # Begin by selecting a random song
    song_1_index = random_select_song(donor_df)
    donor_df, recipient_df = move_song(donor_df, song_1_index, recipient_df)
    while len(donor_df)!=0:
        while True:
            # Identify an ideal DJ song
            next_index = dj_select_song(donor_df, recipient_df)
            if next_index is not None:
                select_type = 'dj_energy'
                break
            # Consider DJ matches without considering energy
            next_index = dj_select_song(donor_df, recipient_df,
                                        consider_energy=False)
            if next_index is not None:
                select_type = 'dj'
                break
            # Identify an ideal harmonic song
            next_index = key_select_song(donor_df, recipient_df)
            if next_index is not None:
                select_type = 'key'
                break
            # Identify an ideal BPM song
            next_index = bpm_select_song(donor_df, recipient_df)
            if next_index is not None:
                select_type = 'bpm'
                break
            # Identify an ideal energy song
            next_index = energy_select_song(donor_df, recipient_df)
            if next_index is not None:
                select_type = 'energy'
                break
            # If there are no good matches, select a random song
            next_index = random_select_song(donor_df)
            if next_index is not None:
                select_type = 'random'
                break
        donor_df, recipient_df = move_song(donor_df, next_index,
                                           recipient_df, select_type)
        sys.stdout.write('\rSorted {}/{} songs     '.format(len(recipient_df),
                                                            donor_len))
        sys.stdout.flush()
    return recipient_df

def push_to_spotify(playlist_id:str, playlist_df:pd.DataFrame):
    '''
    Overwrite a Spotify playlist with its new song order. You are only
    permitted to overwrite the order of your own playlists.

    Parameters
    ----------
    playlist_id : str
        Unique Spotify playlist ID.
    playlist_df : pd.DataFrame
        Playlist DataFrame of updated song order.

    Returns
    -------
    None. Updated order is immediately applied in Spotify.

    '''
    if len(playlist_df) <= 100:
        SP.playlist_replace_items(playlist_id, playlist_df['track_id'])
    elif len(playlist_df) > 100:
        song_pool_temp = playlist_df
        SP.playlist_replace_items(playlist_id,
                                  song_pool_temp['track_id'].head(100))
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
    playlist_desc = html.unescape(SP.playlist(playlist_id)['description'])
    desc_keep = playlist_desc.split('[', 1)[0]
    desc_new = desc_keep + '[Sorted by dj_spotify]'
    SP.playlist_change_details(playlist_id=playlist_id, description=desc_new)

def sort_all_playlists():
    '''
    Sort all public playlists listed on your Spotify profile. To keep the order
    of your playlists fresh, it is advised to resort your playlists at least on
    a weekly basis.

    Returns
    -------
    None.

    '''
    user_playlists = []
    playlists = SP.user_playlists(USER_ID)
    show_playlists(playlists, user_playlists)
    while playlists['next']:
        playlists = SP.next(playlists)
        show_playlists(playlists, user_playlists)
    playlist_names = []
    for playlist in user_playlists:
        playlist_names.append(playlist['name'])
    for i in playlist_names:
        print('\rUpdating songs from {}...'.format(i))
        push_to_spotify(get_playlist_id(i), dj_playlist_sort(i, i))

def combine_playlists(donor_playlists:list, recipient_playlist:str,
                      duration_h:int=4, energy_filter:bool=False):
    '''
    Combine other playlists into a single playlist. This function is useful for
    extracting playlists created by others into your own. Helping keep you
    up to date on your favorite playlists while simultaneously sorting them.

    Again, you can only overwrite the order of your own playlist. However, you
    can pull songs from any public playlist, given the playlist's name and
    owner's username. You can identify the username of any user by selecting
    "Copy Link to Profile" and extracting the string or numbers in between the
    '/user/' and '?' of the resulting link.

    The resulting playlist will automatically be passed through the
    push_to_spotify function.

    Parameters
    ----------
    donor_playlists : list
        Nested lists of Spotify playlist names, and their owner's usernames.
        If their username is a string, make sure it's inputted as such.
    recipient_playlist : str
        Name of the recipient playlist you own.
    duration_h : int, optional
        Number of hours you would like the resulting playlist to be. The number
        of songs chosen from each playlist will be proportionate to the number
        of donor playlists. Input a very large number if you want all songs to
        be included. The default is 4.
    energy_filter : bool, optional
        Should a reasonable duration_h value be used, setting this to True will
        ensure the selected songs from each playlist are the most energetic
        one's available. The default is False.

    Returns
    -------
    None.

    '''
    if duration_h is not False:
        seconds_per_playlist = duration_h*3600/len(donor_playlists)
    playlist_pool = pd.DataFrame()
    for playlist_name, playlist_owner in donor_playlists:
        print('\nLoading {}...'.format(playlist_name))
        try:
            playlist_songs = get_playlist_features(get_playlist_id(playlist_name,
                                                                   playlist_owner))
        except ValueError:
            playlist_songs = get_playlist_features(playlist_name)
        if energy_filter is True:
            playlist_songs = playlist_songs.sort_values(by=['pop_energy'],
                                                        ascending=False)
        else:
            playlist_songs = playlist_songs.sample(frac=1)
        if duration_h is False:
            playlist_pool = pd.concat([playlist_pool, playlist_songs])
        else:
            playlist_pool_small = pd.DataFrame(columns=playlist_songs.columns)
            while sum(playlist_pool_small.duration_s)<seconds_per_playlist and\
                  len(playlist_songs)!=0:
                playlist_songs, playlist_pool_small = move_song(playlist_songs,
                                                                playlist_songs.index[0],
                                                                playlist_pool_small)
        playlist_pool = pd.concat([playlist_pool, playlist_pool_small])
    recipient_df = playlist_pool.drop_duplicates(subset=['track_id']).reset_index(drop=True)
    print('\nSorted {}...'.format(recipient_playlist))
    push_to_spotify(get_playlist_id(recipient_playlist),
                    dj_playlist_sort(recipient_df))
