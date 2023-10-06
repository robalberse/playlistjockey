# playlistjockey/tidal/extract.py

"""Functions responsible for identify Tidal songs in Spotify, and extracting required features from tracks."""

from playlistjockey import utils


def get_spotify_id(sp, isrc, title, artist):
    """Identifies the same Tidal song in Spotify, so that its features can be extracted."""
    queries = [
        "isrc:" + isrc,
        "track:{}, artist:{}".format(title, artist),
        "track:{}, artist:{}".format(
            utils.clean_title(title), utils.clean_artist(artist)
        ),
        "track:" + title,
        "track:" + utils.clean_title(title),
    ]
    query_no = 0
    result = None

    while query_no != 5:
        results = sp.search(queries[query_no])["tracks"]["items"]
        # Break if no results are returned
        if len(results) != 0:
            # Go through the results, looking for a matching ISRC
            for i in results:
                if i["external_ids"]["isrc"] is None:
                    pass
                elif i["external_ids"]["isrc"] == isrc:
                    result = i["id"]
                    break
        if result:
            break
        else:
            query_no += 1

    if not result:
        query_no = 0
        while query_no != 5:
            results = sp.search(queries[query_no])["tracks"]["items"]
            # Break if no results are returned
            if len(results) != 0:
                # Go through the results, looking for a matching title and artist
                for i in results:
                    result_title = i["name"]
                    result_artist = i["artists"][0]["name"]
                    if utils.text_similarity(
                        title, result_title
                    ) and utils.text_similarity(artist, result_artist):
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


def get_song_features(sp, td, td_track_id, genres=False):
    """Acquires all necessary song features for the mixing algorithms to consider."""
    # Pull in Tidal track object
    td_track = td.track(td_track_id)

    # Extract basic features
    isrc = td_track.isrc
    title = td_track.name
    artist = td_track.artist.name

    # Pull in all artists
    artists = []
    for i in td_track.artists:
        artists.append(i.name)

    # Pull in Spotify track object
    sp_track_id = get_spotify_id(sp, isrc, title, artist)
    audio_info = sp.audio_features(sp_track_id)[0]

    # Pull in song key information and remaining features
    camelot = utils.spotify_key_to_camelot(audio_info["key"], audio_info["mode"])

    song_features = {
        "track_id": td_track_id,
        "sp_track_id": sp_track_id,
        "title": title,
        "artists": artists,
        "duration_s": round(td_track.duration, 1),
        "key": camelot,
        "bpm": round(audio_info["tempo"]),
        "energy": round(audio_info["energy"] * 10),
        "danceability": round(audio_info["danceability"] * 10),
        "popularity": round(td_track.popularity / 10),
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
