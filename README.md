# playlistjockey
Unlock innovative ways to experience playlists.

Currently supporting:

![Spotify](playlistjockey/docs/spotify.jpg) ![Tidal](playlistjockey/docs/tidal.jpg)

### Description
Since the inception of music players, we've always had 3 methods of playback: shuffle, repeat, and repeat once. Frankly, we can do better.

`playlistjockey` unlocks a variety of new ways you can sort and experience your playlists. Select a playlist from your streaming platform of choice, choose a mixing algorithm, and upon reviewing
your playlist's new track order, immediately update and listen to your refreshed playlist. DJs can utilize this package to instantly prepare setlists stored in Tidal.

Happy mixing!

### Setup
In order to utilize this module, you will first need to create a Spotify developer account:
  1. Visit https://developer.spotify.com/ and create a free account (Spotify Premium is not required)
  2. Once in your dashboard, click on create app, and provide a name and description
  3. On the overview page for your app, go to settings
  4. Save your client ID and client secret, create a redirect URI

Import the package:
```python
import playlistjockey as pj
```
Initialize the Spotify object, and if you use another streaming service, initialize it as well:
```python
sp = pj.Spotify('<Client ID>', '<Client Secret>', '<Redirect URI>')

td = pj.Tidal(sp)
```
The following will need to be done when first initializng these streaming platform objects:
  * __Spotify__: Return the callback link automatically opened by your browser into the input prompted by your IDE
  * __Tidal__: Your browser will automatically open a window prompting you to log into your Tidal account

> [!NOTE]
> These objects are supported by official and unofficial Python API projects. If you experience connection issues, resets and patience are sometimes required.

Once your connections to your streaming platforms are established, you can pull in one of your playlists:
```python
playlist_id = 'https://open.spotify.com/playlist/7kIvZ3p234OPRRgibzNoQS?si=9d743a7caec143b9'

playlist_df = sp.get_playlist_features(playist_id)
``` 

Next, utilize a `playlistjockey` sorting algorithm to mix your playlist:
```python
sorted_df = pj.sort_playlist(playlist_df, 'dj')
```

Preview the new track order, rerun as many times as you'd like. Once you're ready, push it back to update your playlist:
```python
sp.push_playlist(playlist_id, sorted_df)
```


### Playback
When experiencing a playlist that has been sorted by playlistjockey, enable to following suggested Playback settings:
  - **Turn off shuffle** to ensure songs are played in the order in which they were sorted in
  - Maximize the **Crossfade** value for dance and pop playlists, or set to around 4 seconds for rock or other genres
  - If you're using Spotify's mobile app, enable **Gapless Playback** to minimize quiet moments while a playlist is playing

### Methodology
This package sorts the songs in your Spotify playlists by applying four essential DJ strategies: harmonic mixing, beat matching, and energy levels.
  - **Harmonic mixing:** playing songs with compatible keys together
  - **Beat matching:** playing songs with similar speeds and syncing their beats together
  - **Energy levels:** playing songs with identical intensity levels
