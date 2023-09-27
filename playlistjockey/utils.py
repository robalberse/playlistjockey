import pandas as pd
import re
from difflib import SequenceMatcher as sm


def show_tracks(results, results_array):
    for i, item in enumerate(results["items"]):
        try:
            track = item["track"]
            results_array.append(track["id"])
        except TypeError:
            pass


def show_playlists(results, results_array):
    for i, item in enumerate(results["items"]):
        results_array.append(item)


def spotify_key_to_camelot(spotify_key, spotify_mode):
    camelot_dict = {
        (0, 1): "8B",
        (1, 1): "3B",
        (2, 1): "10B",
        (3, 1): "5B",
        (4, 1): "12B",
        (5, 1): "7B",
        (6, 1): "2B",
        (7, 1): "9B",
        (8, 1): "4B",
        (9, 1): "11B",
        (10, 1): "6B",
        (11, 1): "1B",
        (0, 0): "5A",
        (1, 0): "12A",
        (2, 0): "7A",
        (3, 0): "2A",
        (4, 0): "9A",
        (5, 0): "4A",
        (6, 0): "11A",
        (7, 0): "6A",
        (8, 0): "1A",
        (9, 0): "8A",
        (10, 0): "3A",
        (11, 0): "10A",
    }

    camelot_key = camelot_dict[(spotify_key, spotify_mode)]
    return camelot_key


def key_wrap(self, key):
    lower = key - 1
    if lower == 0:
        lower = 12

    upper = key + 1
    if upper == 13:
        upper = 1

    return lower, upper


def move_song(donor_df, recipient_df, next_song_index, select_type=None):
    if select_type:
        donor_df.at[next_song_index, "select_type"] = select_type
    recipient_df = pd.concat([recipient_df, donor_df.loc[[next_song_index]]])
    donor_df = donor_df.drop(next_song_index)

    return donor_df, recipient_df


def clean_title(string):
    return re.split("[-:&/.•[(]+", string)[0].strip()


def clean_artist(string):
    string = string.replace("The ", "").strip()
    string = clean_title(string)

    return string


def text_similarity(str_a, str_b):
    similarity = sm(None, str_a, str_b).ratio()
    if similarity >= 0.8:
        return True
    else:
        return False
