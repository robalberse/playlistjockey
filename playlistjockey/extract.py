import pandas as pd
from playlistjockey import utils


def get_track_features(sp, song_id):
    # Get basic and audio objects for the given track
    basic_info = sp.track(song_id)
    audio_info = sp.audio_features(song_id)

    # Iterate and capture artists and their genres
    artists = []
    artist_ids = []
    genres = []
    for i in basic_info["artists"]:
        artists.append(i["name"])
        artist_ids.append(i["id"])
        genres.append(sp.artist(i["id"])["genres"])
        for j in sp.artist_related_artists(i['id'])['artists']:
            genres.append(j['genres'])
    genres = [i for sublist in genres for i in sublist] # flatten genres
    genres = list(set(genres)) # remove duplicates

    # Convert Spotify's key information to camelot
    camelot = utils.spotify_key_to_camelot(audio_info[0]["key"], audio_info[0]["mode"])

    # Package all features into a dict
    song_features = {
        "track_id": basic_info["id"],
        "title": basic_info["name"],
        "artists": artists,
        "album": basic_info["album"]["name"],
        "genres": genres,
        "release_year": int(pd.to_datetime(basic_info["album"]["release_date"]).year),
        "duration_s": round(basic_info["duration_ms"] / 1000, 1),
        "key": camelot,
        "bpm": round(audio_info[0]["tempo"]),
        "energy": round(audio_info[0]["energy"] * 10),
        "danceability": round(audio_info[0]["danceability"] * 10),
        "popularity": round(basic_info["popularity"]/10),
    }

    return song_features
