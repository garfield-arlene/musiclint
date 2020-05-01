#!/usr/bin/python3

from plugins.queryDiscogs import queryDiscogs

# def queryDiscogs():
#     return "discogs"

def queryMusicBrainz():
    return "musicbrainz"

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
