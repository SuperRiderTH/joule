# This file is for storing variables that will be used everywhere.

MajorVersion = 2
MinorVersion = 2
PatchVersion = 1

Version = f"{MajorVersion}.{MinorVersion}.{PatchVersion}"

IncludeMIDI = False
IncludeREAPER = False

AllowMuse = False

# Verbosity of the debug output.
Debug = 2

GameDataFile = None
GameDataFileType = "NONE"

OutputNextToSource = True
OutputToOutputDir = False

GameData = {}
GameDataOutput = {}
GameSource = ""
GameSourceFull = ""
GameSourceDefault = "rb3"

GameDataLocation = ""

GameSourceList = {
    "rb3": "Rock Band 3",
    "rb2": "Rock Band 2",
    "lego": "Lego Rock Band",
    "beatles": "The Beatles: Rock Band",
    "ps": "Phase Shift",
    "ch": "Clone Hero",
    "yarg": "Yet Another Rhythm Game",
    "ghwtde": "Guitar Hero World Tour: Definitive Edition",
    "dbvr": "DrumBeats VR",
}

# Band Specific variables.
Tracks = []
TracksFound = []
TicksPerBeat = 0

# Combine all data into a singular track.
MonoTrack = False

# Seconds is the time in seconds at each tick,
# SecondsList is every changed whole second in ticks.
Seconds = []
SecondsList = []

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
