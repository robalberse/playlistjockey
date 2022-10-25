from dj_spotify import DJ_Spotify

dj = DJ_Spotify(username='robalberse',
                client_id = 'bc1e42f17d454600919b6538902d5457',
                client_secret = '4f49f9b0cc8c40888084d2482dd92e3f')

# %% Single Sort
sorted_playlist = dj.sort_playlist("Alberse Party",
                                   2)

# %% Weekly Resorting
dj.sort_certain_playlists({'Alberse Party': 3,
                           'Covered Up': 3,
                           'Funkytown': 2,
                           'Groove': 1,
                           'Head Bangers': 3,
                           'Landfill Indie': 3,
                           'Miami': 2,
                           'Middle School': 1,
                           'Millennia': 1,
                           "Poppin' Off": 2,
                           "Riffin'": 3,
                           'Songs for Literally Any Situation': 1,
                           'Halloween gRaveyard': 3,
                           'This Is Robby Alberse': 2,
                           'Fall Into Fall': 2,
                           'Fireside Chat': 2,
                           'Halloween gRaveyard': 3,
                           "Trick 'r Treat": 2,
                           '80s + Modern Mix': 1,
                           '80s Metal + Modern Mix': 1,
                           '90s Mix': 1,
                           'Childhood': 1,
                           'Adolescence': 1,
                           'Best Coast': 3,
                           'Coastal Country': 2})

# %% Self-updating Playlists

dj.combine_playlists({'Groove': 'robalberse',
                      'Millennia': 'robalberse',
                      '90s Mix': 'robalberse'},
                     'Blender',
                     energy_filter=False,
                     duration_h=10,
                     sort_mode=1)

dj.combine_playlists({'37i9dQZF1DX0AMssoUKCz7': 'spotify', # Tropical House
                      '37i9dQZF1DXa8NOEUWPn9W': 'spotify', # Housewerk
                      '37i9dQZF1DXacX3REVaOqV': 'spotify'}, # House Supreme
                     'Homework',
                     energy_filter=True,
                     duration_h=8,
                     sort_mode=3)

dj.combine_playlists({"Party Hits": 'spotify',
                      'Beach Week 2022': 'robalberse',
                      'Beach Week 2021': '1269432053',
                      'Beach Week 2020': '1269432053',
                      # No 2019??
                      'Beach CD 2018': '1236623712',
                      'Beach CD 2017': '1236623712',
                      'Beach CD': '1236623712'},
                     'Beach Week 2023 Preview',
                     energy_filter=False,
                     duration_h=4,
                     sort_mode=2)

dj.combine_playlists({'37i9dQZF1DWUPRADzDnbMq': 'spotify', # Gulf & Western
                      '37i9dQZF1DXcSzYlwgjiSi': 'spotify', # Party Cove
                      '37i9dQZF1DX9fZ7amiNVu6': 'spotify'}, # Feel Good Summer
                     'On the Lake',
                     duration_h=8,
                     energy_filter=False,
                     sort_mode=3)

dj.combine_playlists({'37i9dQZF1DWUWC0NIJDJKL': 'spotify', # Indie Sunshine
                      '37i9dQZF1DX1BzILRveYHb': 'spotify', # Sunny Day
                      'Soak Up the Sun': 'spotify',
                      '37i9dQZF1DWYzpSJHStHHx': 'spotify'}, # Surf Rock Sunshine
                     'On the Beach',
                     duration_h=8,
                     energy_filter=False,
                     sort_mode=3)

dj.combine_playlists({'37i9dQZF1DXbtuVQL4zoey': 'spotify', # Sunny Beats
                      '37i9dQZF1DWSvfPiFfb8Mi': 'spotify', # Poolside Disco
                      '37i9dQZF1DWZSdcRHMl2tT': 'spotify', # Poolside Lounge
                      '37i9dQZF1DX0AMssoUKCz7': 'spotify'}, # Tropical House
                     'Summer Lounge',
                     duration_h=10,
                     energy_filter=False,
                     sort_mode=3)

dj.combine_playlists({'6x6pplPez6ImGWPvsvxCaI': 'tbw2zvqzlnu714tgyeghry318'},
                     'Halloween 2022 - Kasey',
                     duration_h=10,
                     energy_filter=False,
                     sort_mode=3)
