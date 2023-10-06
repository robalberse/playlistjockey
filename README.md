# ![playlistjockey](docs/images/banner_v1.png)
Unlock innovative ways to experience playlists.

Currently supporting:

![Spotify](docs/images/spotify.jpg) ![Tidal](docs/images/tidal.jpg)

With the following mixing algorithms:

:control_knobs: `"dj"`: songs with compatible keys, speeds, and energy levels are placed next to each other<br>
:tada: `"party"`: build the energy levels to a peak at the halfway point, then gradually calm things down<br>
:guitar: `"setlist"`: kick off with some of the most popular songs, saving lower-energy songs for the halfway point, then build back up to the finale<br>
:musical_note: `"genre"`: group and smoothly transition through the various genres in your playlist

### Description
Since the inception of music players, we've always had 3 methods of playback: shuffle, repeat, and repeat once. Frankly, we can do better.

`playlistjockey` unlocks a variety of new ways you can sort and experience your playlists. Select a playlist from your streaming platform of choice, choose a mixing algorithm, and upon reviewing
your playlist's new track order, immediately update and listen to your enhanced playlist. DJs can utilize this package to instantly prepare setlists in Tidal.

Happy mixing!

### Setup
To utilize this module, you will first need to create a Spotify developer account:
  1. Visit https://developer.spotify.com/ and create a free account (Spotify Premium is not required)
  2. Once in your dashboard, click on Create App, and provide a name and description
  3. On the overview page for your app, go to settings
  4. Save your client ID and client secret, and create a redirect URI

Install the package:
```
pip install playlistjockey
```

### Usage
Import the package:
```python
import playlistjockey as pj
```
Initialize the Spotify object, and if you use another streaming service, initialize it as well:
```python
sp = pj.Spotify('<Client ID>', '<Client Secret>', '<Redirect URI>')

td = pj.Tidal(sp)
```
The following will need to be done when first initializing these streaming platform objects:
  * __Spotify__: Return the callback link automatically opened by your browser into the input prompted by your IDE
  * __Tidal__: Your browser will automatically open a window prompting you to log into your Tidal account

> [!NOTE]
> If you experience any connection-related errors, try reinitializing your streaming platform objects.

Once the connections to your streaming platforms are established, you can pull in one of your playlists:
```python
playlist_id = 'https://open.spotify.com/playlist/7kIvZ3p234OPRRgibzNoQS?si=9d743a7caec143b9'

playlist_df = sp.get_playlist_features(playist_id)
``` 

Next, utilize a `playlistjockey` sorting algorithm to mix your playlist:
```python
sorted_df = pj.sort_playlist(playlist_df, "dj")
```

Preview the new track order, and rerun as many times as you'd like. Once you're ready, push it back to update your playlist:
```python
sp.update_playlist(playlist_id, sorted_df)
```

### Playback
When experiencing a playlist that has been sorted by `playlistjockey`, enable to following suggested playback settings:
  - **Turn off shuffle** to ensure songs are played in the order in which they were sorted in
  - Maximize the **Crossfade** value for dance and pop playlists, or set to around 4 seconds for rock or other genres
  - If you're using Spotify's mobile app, enable **Gapless Playback** to minimize quiet moments while a playlist is playing

