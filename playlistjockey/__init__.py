# playlistjockey/__init__.py

"""Modules exported by this package:

- `Spotify`: class used to connect and extract songs from Spotify's API
- `Tidal`: class used to connect and extract songs from Tidal's API
- `sort_playlist`: function used to call mixing algorithms
"""

from .main import Spotify, Tidal, sort_playlist
