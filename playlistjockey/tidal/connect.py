import configparser
import pkg_resources
import os

import tidalapi


def first_time_connect():
    # Establish config file
    config = configparser.ConfigParser()
    path = pkg_resources.resource_filename(__name__, "config.ini")
    config.read(path)

    config.add_section("tidal")
    config.set("tidal", "access_token", "")
    config.set("tidal", "refresh_token", "")

    with open(path, "w") as configfile:
        config.write(configfile)


def connect():
    config = configparser.ConfigParser()
    path = pkg_resources.resource_filename(__name__, "config.ini")
    if len(config.read(path)) == 0:
        first_time_connect()
    config.read(path)

    try:
        access_token = config["tidal"]["access_token"]
        refresh_token = config["tidal"]["refresh_token"]
        td = tidalapi.Session()
        td.load_oauth_session(
            token_type="Bearer", access_token=access_token, refresh_token=refresh_token
        )
    except:
        print("Tidal session requires refresh:")
        td = tidalapi.Session()
        td.login_oauth_simple()
        config["tidal"]["access_token"] = td.access_token
        config["tidal"]["refresh_token"] = td.refresh_token
        with open(path, "w") as configfile:
            config.write(configfile)
    return td
