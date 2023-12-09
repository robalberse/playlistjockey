# playlistjockey/tidal/extract.py

"""Functions responsible for identify Tidal songs in Spotify, and extracting required features from tracks."""

import logging

from playlistjockey import utils


# Supress 404 error messages when a media ID is not a video
logging.disable(logging.ERROR)


def search_by_isrc(sp, isrc):
    # Establish the search query and
    query = "isrc:" + isrc

    # Establish output
    result = None

    # Search via ISRC, look through resulting tracks for a match
    results = sp.search(query)["tracks"]["items"]
    # Break if no results are returned
    if len(results) != 0:
        # Go through the results, looking for a matching ISRC
        for i in results:
            if i["external_ids"]["isrc"] is None:
                pass
            elif i["external_ids"]["isrc"] == isrc:
                result = i["id"]
                break

    return result


def search_by_title_artist(sp, title, artist):
    # Establish possible search queries
    queries = [
        "track:{}, artist:{}".format(title, artist),
        "track:{}, artist:{}".format(
            utils.clean_title(title), utils.clean_artist(artist)
        ),
        "track:" + title,
        "track:" + utils.clean_title(title),
    ]

    # Establish query counter
    query_no = 0

    # Establish output
    result = None

    # Try to find the song in Spotify using the queries, matching on ISRC or song name and artist
    while query_no != 4:
        results = sp.search(queries[query_no])["tracks"]["items"]
        # Break if no results are returned
        if len(results) != 0:
            # Go through the results, looking for a matching title and artist
            for i in results:
                result_title = i["name"]
                result_artist = i["artists"][0]["name"]
                if utils.text_similarity(title, result_title) and utils.text_similarity(
                    artist, result_artist
                ):
                    result = i["id"]
                    break
                elif utils.text_similarity(
                    utils.clean_title(title), utils.clean_title(result_title)
                ) and utils.text_similarity(
                    utils.clean_artist(artist), utils.clean_artist(result_artist)
                ):
                    result = i["id"]
                    break
        if result:
            break
        else:
            query_no += 1

    return result


def get_spotify_id(sp, isrc, title, artist):
    """Identifies the same Tidal song in Spotify, so that its features can be extracted."""
    # Establish the output
    result = None

    # First try to find the song utilizing its ISRC
    if isrc is not None:
        result = search_by_isrc(sp, isrc)

    # If unsuccessful, try searching using its song title and artist text
    if not result:
        result = search_by_title_artist(sp, title, artist)

    return result


def get_song_features(sp, td, td_media_id, genres=False):
    """Acquires all necessary song features for the mixing algorithms to consider."""
    # First see if the media ID belongs to a video
    try:
        td_media = td.video(td_media_id)
        isrc = None

    # If unsuccessful, extract as audio
    except:
        td_media = td.track(td_media_id)
        isrc = td_media.isrc

    # Pull in basic name and artist information
    title = td_media.name
    artist = td_media.artist.name

    # Pull in all artists
    artists = []
    for i in td_media.artists:
        artists.append(i.name)

    # Pull in Spotify track object
    sp_track_id = get_spotify_id(sp, isrc, title, artist)
    audio_info = sp.audio_features(sp_track_id)[0]

    # Pull in song key information and remaining features
    camelot = utils.spotify_key_to_camelot(audio_info["key"], audio_info["mode"])

    song_features = {
        "track_id": td_media.id,
        "sp_track_id": sp_track_id,
        "title": title,
        "artists": artists,
        "duration_s": round(td_media.duration, 1),
        "key": camelot,
        "bpm": round(audio_info["tempo"]),
        "energy": round(audio_info["energy"] * 10),
        "danceability": round(audio_info["danceability"] * 10),
        "popularity": round(td_media.popularity / 10),
    }

    if genres:
        # Get basic Spotify track object
        basic_info = sp.track(sp_track_id)

        # Collect the genres the track's artists, and their related artists
        genres = []
        for i in basic_info["artists"]:
            genres.append(sp.artist(i["id"])["genres"])
            for j in sp.artist_related_artists(i["id"])["artists"]:
                genres.append(j["genres"])
        genres = [i for sublist in genres for i in sublist]  # flatten genres
        genres = list(set(genres))  # remove duplicates

        # Attach to dict
        song_features.update({"genres": genres})

    return song_features
