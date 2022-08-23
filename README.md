# dj_spotify
Algorithmically sort your playlists like a DJ.

### Setup
In order to utilize this module, you will first need to create a Spotify developer account:
  1. Visit https://developer.spotify.com/ and **create a free account**
  2. Once in My Dashboard, click on **Create an App**
  3. Provide a name and description 
  4. Once on the Overview page for your app, **save your Client ID and Client Secret**
  5. Add https://localhost:8000 as a **Redirect URI**

You will also need your Spotify username. You can navigate to find your username through the desktop or mobile applications:
  - Desktop: Click on your profile in the top-right of the page, select Account, your username will be under the Account Overview section
  - Mobile: Got to Settings, click Account, your username will be displayed at the top of the page

Required packages:
  - [pandas](https://pandas.pydata.org/)
  - [numpy](https://numpy.org/)
  - [scikit-learn](https://scikit-learn.org/stable/)
  - [spotipy](https://spotipy.readthedocs.io/en/2.19.0/)

### Playback
When experiencing a playlist that has been sorted by dj_spotify, enable to following suggested Playback settings in Spotify:
  - Set the **Crossfade** value in between 8 and 12 seconds, allowing the ending of one song to blend into the beginning of the next
  - If you're using the mobile app, also enable **Gapless Playback** to ensure no quiet moments occur while a playlist is playing

### Methodology
This package sorts the songs in your Spotify playlists by applying four essential DJ strategies: harmonic mixing, beat matching, energy levels, and genres.
  - **Harmonic mixing:** playing songs with compatible keys together
  - **Beat matching:** playing songs with similar speeds and syncing their beats together
  - **Energy levels:** playing songs with identical intensity 
  - **Genres:** playling songs with identical form, style, or subject matter

After picking a random song to begin, the dj_spotify algorithm then identifies other songs from your playlist that meet all or most of the above criteria. It then selects the next song by identifying which applicable song will lead to the most future matches. The algorithm repeats this process until all songs are sorted.
