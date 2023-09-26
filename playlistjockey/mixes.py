import pandas as pd

from playlistjockey import selects, utils


def dj_mix(donor_df):
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
