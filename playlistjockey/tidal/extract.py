from playlistjockey import utils


def get_spotify_id(sp, isrc, title, artist):
    queries = [
        "isrc:" + isrc,
        "track:{}, artist:{}".format(title, artist),
        "track:{}, artist:{}".format(
            utils.clean_title(title), utils.clean_artist(artist)
        ),
    ]
    query_no = 0
    result = None

    while query_no != 3:
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
        title = utils.clean_title(title)
        artist = utils.clean_artist(artist)
        while query_no != 3:
            results = sp.search(queries[query_no])["tracks"]["items"]
            # Break if no results are returned
            if len(results) != 0:
                # Go through the results, looking for a matching title and artist
                for i in results:
                    result_title = utils.clean_title(i["name"])
                    result_artist = utils.clean_artist(i["artists"][0]["name"])
                    if utils.text_similarity(
                        title, result_title
                    ) and utils.text_similarity(artist, result_artist):
                        result = i["id"]
                        break
            if result:
                break
            else:
                query_no += 1

    return result


def get_song_features(sp, td, td_track_id):
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
    sp_track = sp.audio_features(sp_track_id)[0]

    # Pull in song key information and remaining features
    camelot = utils.spotify_key_to_camelot(sp_track["key"], sp_track["mode"])

    song_features = {
        "track_id": td_track_id,
        "sp_track_id": sp_track_id,
        "title": title,
        "artists": artists,
        "duration_s": round(td_track.duration, 1),
        "key": camelot,
        "bpm": round(sp_track["tempo"]),
        "energy": round(sp_track["energy"] * 10),
        "danceability": round(sp_track["danceability"] * 10),
        "popularity": round(td_track.popularity / 10),
    }

    return song_features
