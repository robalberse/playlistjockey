# dj_spotify
## Algorithmically sort your playlists like a DJ.

### Setup
In order to utilize this package, you will first need to create a Spotify developer account:
  1. Visit https://developer.spotify.com/ and **create a free account**
  2. Once in My Dashbaord, click on **Create an App**
  3. Provide a name and description 
  4. Once on the Overiew page for your app, **save your Client ID and Client Secret**

You will also need your Spotify username. You can navigate to find your username through the desktop or mobile applications:
  Desktop: Click on your profile in the top-right of the page, select Account, your username will be under the Account Overview section
  Mobile: Got to Settings, click Account, your username will be displayed at the top of the page

### Methodology

This package sorts the songs in your Spotify playlists by applying two essential DJ strategies: mixing in key, and beat matching.

**Mixing in key** refers to playing songs with compatable keys together. Songs with compatable keys will sound similar to one-another, making
the transition from one song to another more seamless. **Beat matching** refers to playing songs that play at similar speeds, and syncing
their beats together. Spotify's Automix feature is adequate at aligning songs in transition, further making the change from one song to another
more smooth.
