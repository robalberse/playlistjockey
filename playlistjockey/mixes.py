# playlistjockey/mixes.py

"""Module containing mixing algorithms.

The module contains the following classes and functions:

- `dj_mix(donor_df)`: Mixing algorithm that sorts a playlist like a DJ: utilizing compatible keys, bpms, and energy features.
- `party_mix(donor_df)`: Mixing algorithm that puts the most party appropriate songs in the middle of the playlist.
- `setlist_mix(donor_df)`: Mixing algorithm that puts the most energetic and popular songs at the beginning and end of the playlist.
- `genre_mix(donor_df)`: Mixing algorithm that sorts a playlist by grouping genres together.
"""

import pandas as pd

from playlistjockey import selects, utils


def dj_mix(donor_df):
    """Mixing algorithm that sorts a playlist like a DJ: utilizing compatible keys, bpms, and energy features."""
    # Establish the recipient df that will be the playlist's new order
    recipient_df = pd.DataFrame(columns=donor_df.columns)

    # Begin by randomly selecting the first song
    song_1_index = selects.random_select_song(donor_df)
    donor_df, recipient_df = utils.move_song(
        donor_df, recipient_df, song_1_index, "random"
    )

    # Define the order in which to select songs
    select_order = [
        [selects.dj_select_song, "dj"],
        [selects.basic_select_song, "basic"],
        [selects.random_select_song, "random"],
    ]

    # Fill the rest of the playlist
    while len(donor_df) != 0:
        for select, select_type in select_order:
            if select_type == "random":
                next_song_index = select(donor_df)
            else:
                next_song_index = select(donor_df, recipient_df)
            if next_song_index:
                break

        donor_df, recipient_df = utils.move_song(
            donor_df, recipient_df, next_song_index, select_type
        )

    return recipient_df


def party_mix(donor_df):
    """Mixing algorithm that puts the most party appropriate songs in the middle of the playlist. This allows your playlist to compliment the typical flow of a party: starting at a
    low level of energy, building to a peak at the halfway point, then gradually lowering the energy back down."""
    # Establish two recipient DataFrames
    rec_front_half = pd.DataFrame(columns=donor_df.columns)
    rec_back_half = rec_front_half.copy()

    # Sort the donor_df by energy and danceability
    donor_df.sort_values(by=["energy", "danceability"], ascending=False, inplace=True)

    # Grab the most hype song to establish the end of the first half of the playlist
    peak_index = donor_df.head(1).index[0]
    donor_df, rec_front_half = utils.move_song(
        donor_df, rec_front_half, peak_index, "peak"
    )

    # Get a compatible song, use it to start the first song in the second half
    song_index = None
    while song_index is None:
        song_index = selects.party_select_song(donor_df, rec_front_half)
        if song_index:
            select_type = "party"
            break
        song_index = selects.dj_select_song(donor_df, rec_front_half)
        if song_index:
            select_type = "dj"
            break
        song_index = selects.basic_select_song(donor_df, rec_front_half)
        if song_index:
            select_type = "basic"
            break
    donor_df, rec_back_half = utils.move_song(
        donor_df, rec_back_half, song_index, select_type
    )

    # Now fill the remainder of the songs into the two halves
    select_order = [
        [selects.party_select_song, "party"],
        [selects.dj_select_song, "dj"],
        [selects.basic_select_song, "basic"],
        [selects.random_select_song, "random"],
    ]

    i = 3
    while len(donor_df) != 0:
        # Alternate between adding songs to the front and back half of the playlist
        recipient_df = rec_front_half
        if (i % 2) == 0:
            recipient_df = rec_back_half

        for select, select_type in select_order:
            if select_type == "random":
                next_song_index = select(donor_df)
            else:
                next_song_index = select(donor_df, recipient_df)
            if next_song_index:
                break

        donor_df, recipient_df = utils.move_song(
            donor_df, recipient_df, next_song_index, select_type
        )

        # Ensure updates are correctly overwritten
        if (i % 2) == 0:
            rec_back_half = recipient_df
        else:
            rec_front_half = recipient_df

        i += 1

    # Flip the front half df, then add both halves together
    rec_front_half = rec_front_half.iloc[::-1]
    recipient_df = pd.concat([rec_front_half, rec_back_half])

    # Calculate a moving average to observe the behavior of the energy levels
    recipient_df["ma_energy"] = (
        recipient_df["energy"].rolling(len(recipient_df) // 10).mean()
    )

    return recipient_df


def setlist_mix(donor_df):
    """Mixing algorithm that puts the most energetic and popular songs at the beginning and end of the playlist. This allows your playlist to compliment the typical flow of a concert:
    Starting with high levels of energy, saving the least energetic song for the midpoint, then building the energy back up for the grand finale."""
    # Establish two recipient DataFrames
    rec_front_half = pd.DataFrame(columns=donor_df.columns)
    rec_back_half = rec_front_half.copy()

    # Sort the donor_df by energy and popularity
    donor_df.sort_values(by=["energy", "popularity"], inplace=True)

    # Grab the least energetic song to establish the end of the first half of the playlist
    peak_index = donor_df.head(1).index[0]
    donor_df, rec_front_half = utils.move_song(
        donor_df, rec_front_half, peak_index, "floor"
    )

    # Get a compatible song, use it to start the first song in the second half
    song_index = None
    while song_index is None:
        song_index = selects.setlist_select_song(donor_df, rec_front_half)
        if song_index:
            select_type = "setlist"
            break
        song_index = selects.dj_select_song(donor_df, rec_front_half)
        if song_index:
            select_type = "dj"
            break
        song_index = selects.basic_select_song(donor_df, rec_front_half)
        if song_index:
            select_type = "basic"
            break
    donor_df, rec_back_half = utils.move_song(
        donor_df, rec_back_half, song_index, select_type
    )

    # Now fill the remainder of the songs into the two halves
    select_order = [
        [selects.setlist_select_song, "setlist"],
        [selects.dj_select_song, "dj"],
        [selects.basic_select_song, "basic"],
        [selects.random_select_song, "random"],
    ]

    i = 3
    while len(donor_df) != 0:
        # Alternate between adding songs to the front and back half of the playlist
        recipient_df = rec_front_half
        if (i % 2) == 0:
            recipient_df = rec_back_half

        for select, select_type in select_order:
            if select_type == "random":
                next_song_index = select(donor_df)
            else:
                next_song_index = select(donor_df, recipient_df)
            if next_song_index:
                break

        donor_df, recipient_df = utils.move_song(
            donor_df, recipient_df, next_song_index, select_type
        )

        # Ensure updates are correctly overwritten
        if (i % 2) == 0:
            rec_back_half = recipient_df
        else:
            rec_front_half = recipient_df

        i += 1

    # Flip the front half df, then add both halves together
    rec_front_half = rec_front_half.iloc[::-1]
    recipient_df = pd.concat([rec_front_half, rec_back_half])

    # Calculate a moving average to observe the behavior of the energy levels
    recipient_df["ma_energy"] = (
        recipient_df["energy"].rolling(len(recipient_df) // 10).mean()
    )

    return recipient_df


def genre_mix(donor_df):
    """Mixing algorithm that sorts a playlist by grouping genres together."""

    # Ensure the artist_similarity variable is present
    if "artist_similarity" not in donor_df:
        raise KeyError(
            '"artist_similarity" column not in data. Set genres=True in get_playlist_features function.'
        )

    # Establish the recipient df that will be the playlist's new order
    recipient_df = pd.DataFrame(columns=donor_df.columns)

    # Begin by randomly selecting the first song
    song_1_index = selects.random_select_song(donor_df)
    donor_df, recipient_df = utils.move_song(
        donor_df, recipient_df, song_1_index, "random"
    )

    # Define the order in which to select songs
    select_order = [
        [selects.genre_select_song, "genre"],
        [selects.basic_select_song, "basic"],
        [selects.random_select_song, "random"],
    ]

    # Fill the rest of the playlist
    while len(donor_df) != 0:
        for select, select_type in select_order:
            if select_type == "random":
                next_song_index = select(donor_df)
            else:
                next_song_index = select(donor_df, recipient_df)
            if next_song_index:
                break

        donor_df, recipient_df = utils.move_song(
            donor_df, recipient_df, next_song_index, select_type
        )

    return recipient_df
