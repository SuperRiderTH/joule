# This file is for storing variables that will be used everywhere.

MajorVersion    = 0
MinorVersion    = 21
PatchVersion    = 0

Version         = f"{MajorVersion}.{MinorVersion}.{PatchVersion}"

# Verbosity of the debug output.
Debug           = 2

GameDataFile        = None
GameDataFileType    = "NONE"

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
    "ghwtde":"Guitar Hero World Tour: Definitive Edition"
}

# Band Specific variables.
Tracks              = []
TracksFound         = []
TicksPerBeat        = 0
TicksSustainLimit   = 0

GameSourceRBLike = {
    "rb3",
    "rb2",
    "lego",
    "beatles",
    "ps",
    "yarg",
}

GameSourceHasSongINI = {
    "ps",
    "ch",
    "ghwtde",
}

BrokenChordsAllowed     = False
LowerHOPOsAllowed       = False