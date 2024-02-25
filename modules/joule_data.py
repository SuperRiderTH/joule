# This file is for storing variables that will be used everywhere.

MajorVersion    = 1
MinorVersion    = 17
PatchVersion    = 0

Version         = f"{MajorVersion}.{MinorVersion}.{PatchVersion}"

AllowMuse       = False

# Verbosity of the debug output.
Debug           = 2

GameDataFile        = None
GameDataFileType    = "NONE"

GameData        = {}
GameDataOutput  = {}
GameSource      = ""
GameSourceFull  = ""

GameDataLocation = ""

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

# Seconds is the time in seconds at each tick,
# SecondsList is every changed whole second in ticks.
Seconds             = []
SecondsList         = []

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