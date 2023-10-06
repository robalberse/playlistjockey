# playlistjockey/filters.py

"""Provide the filters used by the various mixing algorithms to identify compatible songs.

The module contains the following functions:

- `artist_filter(donor_df, recipient_df)`: Filter the donor_df for artists that have been recently played.
- `key_filter(donor_df, recipient_df)`: Filters donor_df for songs that have compatible keys with the last song in recipient_df.
- `bpm_filter(donor_df, recipient_df)`: Filters donor_df for songs within 10% difference in tempo from the last song in recipient_df, half and double time included.
- `plus_minus_1_filter(donor_df, recipient_df, column)`: Filters donor_df for 1 value difference in inputted quantitative column from the last song in recipient_df.
- `equal_filter(donor_df, recipient_df, column)`: Filters donor_df for the same value in inputted quantitative column from the last song in recipient_df.
"""

import pandas as pd

from collections import Counter


def artist_filter(donor_df, recipient_df):
    """Filter the donor_df for artists that have been recently played. This ensures the same artists aren't being played consecutively."""
    # Calculate max artist count to song percentage
    donor_artists = [i for j in donor_df["artists"] for i in j]
    recipient_artists = [i for j in recipient_df["artists"] for i in j]
    artist_counts = dict(Counter(donor_artists + recipient_artists))
    max_artist_count = max(artist_counts.values())

    song_count = len(donor_df) + len(recipient_df)
    max_artist_count_ratio = round(max_artist_count / song_count, 1)

    prev_songs = int((1 - max_artist_count_ratio) * 5)

    # Capture recently played artists
    prev_artists = []
    for i in range(1, prev_songs + 1):
        try:
            prev_artists += recipient_df["artists"].iloc[-i]
        except:
            pass

    # Filter out donor_df for songs without those artists
    donor_df = donor_df[
        (
            ~donor_df.apply(
                lambda x: any(i in prev_artists for i in x["artists"]), axis=1
            )
        )
    ]

    return donor_df


def key_filter(donor_df, recipient_df):
    """Filters donor_df for songs that have compatible keys with the last song in recipient_df."""
    prev_camelot = recipient_df.iloc[-1]["key"]

    key_mix_dict = {
        "1A": ["1A", "1B", "2A", "12A"],
        "1B": ["1B", "1A", "2B", "12B"],
        "2A": ["2A", "2B", "3A", "1A"],
        "2B": ["2B", "2A", "3B", "1B"],
        "3A": ["3A", "3B", "4A", "2A"],
        "3B": ["3B", "3A", "4B", "2B"],
        "4A": ["4A", "4B", "5A", "3A"],
        "4B": ["4B", "4A", "5B", "3B"],
        "5A": ["5A", "5B", "6A", "4A"],
        "5B": ["5B", "5A", "6B", "4B"],
        "6A": ["6A", "6B", "7A", "5A"],
        "6B": ["6B", "6A", "7B", "5B"],
        "7A": ["7A", "7B", "8A", "6A"],
        "7B": ["7B", "7A", "8B", "6B"],
        "8A": ["8A", "8B", "9A", "7A"],
        "8B": ["8B", "8A", "9B", "7B"],
        "9A": ["9A", "9B", "10A", "8A"],
        "9B": ["9B", "9A", "10B", "8B"],
        "10A": ["10A", "10B", "11A", "9A"],
        "10B": ["10B", "10A", "11B", "9B"],
        "11A": ["11A", "11B", "12A", "10A"],
        "11B": ["11B", "11A", "12B", "10B"],
        "12A": ["12A", "12B", "1A", "11A"],
        "12B": ["12B", "12A", "1B", "11B"],
    }

    donor_df = donor_df[donor_df["key"].isin(key_mix_dict[prev_camelot])]

    return donor_df


def bpm_filter(donor_df, recipient_df):
    """Filters donor_df for songs within 10% difference in tempo from the last song in recipient_df, half and double time included."""
    prev_bpm = recipient_df.iloc[-1]["bpm"]

    # Songs +- 10% speed
    donor_df_1 = donor_df[
        (donor_df["bpm"] >= prev_bpm * 0.9) & (donor_df["bpm"] <= prev_bpm * 1.1)
    ]
    # Songs +- 10% at double time
    donor_df_2 = donor_df[
        (donor_df["bpm"] >= prev_bpm * 1.8) & (donor_df["bpm"] <= prev_bpm * 2.2)
    ]
    # Songs +- 10% at half time
    donor_df_3 = donor_df[
        (donor_df["bpm"] >= prev_bpm * 0.45) & (donor_df["bpm"] <= prev_bpm * 0.55)
    ]

    donor_df = pd.concat([donor_df_1, donor_df_2, donor_df_3])

    return donor_df


def plus_minus_1_filter(donor_df, recipient_df, column):
    """Filters donor_df for 1 value difference in inputted quantitative column from the last song in recipient_df."""
    prev_value = recipient_df.iloc[-1][column]

    donor_df = donor_df[
        (donor_df[column] >= prev_value - 1) & (donor_df[column] <= prev_value + 1)
    ]

    return donor_df


def equal_filter(donor_df, recipient_df, column):
    """Filters donor_df for the same value in inputted quantitative column from the last song in recipient_df."""
    prev_value = recipient_df.iloc[-1][column]

    donor_df = donor_df[donor_df["column"] == prev_value]

    return donor_df
