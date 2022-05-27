# dj_spotify
Algorithmically sort your playlists like a DJ.

### Setup
In order to utilize this package, you will first need to create a Spotify developer account:
  1. Visit https://developer.spotify.com/ and **create a free account**
  2. Once in My Dashboard, click on **Create an App**
  3. Provide a name and description 
  4. Once on the Overview page for your app, **save your Client ID and Client Secret**

You will also need your Spotify username. You can navigate to find your username through the desktop or mobile applications:
  - Desktop: Click on your profile in the top-right of the page, select Account, your username will be under the Account Overview section
  - Mobile: Got to Settings, click Account, your username will be displayed at the top of the page

Required packages:
  - [pandas](https://pandas.pydata.org/) 
    'pip install pandas'
  - [spotipy](https://spotipy.readthedocs.io/en/2.19.0/) 
    'pip install spotipy'

### Methodology

This package sorts the songs in your Spotify playlists by applying three essential DJ strategies: harmonic mixing, beat matching, and energy levels.
  - **Harmonic mixing:** playing songs with compatible keys together
  - **Beat matching:** playing songs with similar speeds and syncing their beats together
  - **Energy levels:** playing songs with identical intensity 

After picking a random song to begin, the dj_spotify algorithm then identifies other songs from your playlist that meet all or most of the above criteria. It then selects the next song by identifying which applicable song will lead to the most future matches. The algorithm repeats this process until all songs are sorted.
