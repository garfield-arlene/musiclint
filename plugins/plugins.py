#!/usr/bin/env python3

from plugins.queryDiscogs import queryDiscogs
from plugins.queryMusicBrainz import queryMusicBrainz

def chooseDBPlugin(argument):
    switcher = {
        "discogs": queryDiscogs,
        "musicbrainz": queryMusicBrainz
     }
    # Get the function from switcher dictionary
    func = switcher.get(argument, lambda: "Invalid plugin")
    # print("Query: " + func())
    return func


if __name__ == "__main__":
    print("\nChoose a plugin from the following list.\n\tdiscogs\n\tmusicbrainz\n\n")
    plugin = input("Enter the plugin name: ")
    chooseDBPlugin(plugin)
    print("\n")
