# This file is for storing variables that will be used everywhere.

MajorVersion   = 0
MinorVersion   = 15
PatchVersion   = 1

Version         = f"{MajorVersion}.{MinorVersion}.{PatchVersion}"

# Verbosity of the debug output.
Debug           = 2

gameDataFile    = None

GameData        = {}
GameDataOutput  = {"issues_critical":{},"issues_major":{},"issues_minor":{},}
GameSource      = ""
GameSourceFull  = ""

GameSourceList = {
    "rb3":"Rock Band 3",
    "rb2":"Rock Band 2",
    "lego":"Lego Rock Band",
    "beatles":"The Beatles: Rock Band",
    "ps":"Phase Shift",
    "ch":"Clone Hero",
    "yarg":"Yet Another Rhythm Game",
}

# Band Specific variables.
NoteTime       = 0
TracksFound    = []

GameSourceRBLike = {
    "rb3",
    "rb2",
    "lego",
    "beatles",
    "ps",
    "yarg",
}

BrokenChordsAllowed     = False
LowerHOPOsAllowed       = False
