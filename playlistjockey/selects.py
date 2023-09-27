import pandas as pd
import random

from playlistjockey import filters


def random_select_song(donor_df):
    try:
        next_song_index = random.choice(list(donor_df.index))
    except:
        next_song_index = None
    return next_song_index


def dj_select_song(donor_df, recipient_df):
    # Filter for songs with differeing artists, and compatible keys and bpms
    donor_df = filters.artist_filter(donor_df, recipient_df)
    donor_df = filters.key_filter(donor_df, recipient_df)
    donor_df = filters.bpm_filter(donor_df, recipient_df)
    donor_df = filters.plus_minus_1_filter(donor_df, recipient_df, "energy")

    # Select a random compatible song as the next song
    next_song_index = random_select_song(donor_df)

    return next_song_index


def basic_select_song(donor_df, recipient_df):
    # Filter for differing artists
    donor_df = filters.artist_filter(donor_df, recipient_df)

    # In different dfs, filter for compatible keys, bpms, energy, danceability, and artist similarity
    key_df = filters.key_filter(donor_df, recipient_df)
    bpm_df = filters.bpm_filter(donor_df, recipient_df)
    energy_df = filters.plus_minus_1_filter(donor_df, recipient_df, "energy")
    dance_df = filters.plus_minus_1_filter(donor_df, recipient_df, "danceability")

    # Combine the compatible dfs, and randomly select the next song
    donor_df = pd.concat([key_df, bpm_df, energy_df, dance_df])
    next_song_index = random_select_song(donor_df)

    return next_song_index


def party_select_song(donor_df, recipient_df):
    # Filter for songs with differeing artists, and compatible keys and bpms
    donor_df = filters.artist_filter(donor_df, recipient_df)
    donor_df = filters.key_filter(donor_df, recipient_df)
    donor_df = filters.bpm_filter(donor_df, recipient_df)

    # In different dfs, filter for compatible energy, dance, and similarity values
    energy_df = filters.plus_minus_1_filter(donor_df, recipient_df, "energy")
    dance_df = filters.plus_minus_1_filter(donor_df, recipient_df, "danceability")

    # Combine the compatible song dfs, and select the song with the highest energy and danceability
    donor_df = pd.concat([energy_df, dance_df])
    donor_df.sort_values(by=["energy", "danceability"], ascending=False, inplace=True)
    next_song_index = donor_df.head(1).index[0]

    return next_song_index


def setlist_select_song(donor_df, recipient_df):
    # Filter for songs with compatible energy and popularity
    donor_df = filters.plus_minus_1_filter(donor_df, recipient_df, "energy")
    donor_df = filters.plus_minus_1_filter(donor_df, recipient_df, "popularity")

    # Select the song wiht the lowest energy and popularity
    donor_df.sort_values(by=["energy", "danceability"], inplace=True)
    next_song_index = donor_df.head(1).index[0]

    return next_song_index