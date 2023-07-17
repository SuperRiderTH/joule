#!/usr/bin/env python3


from enum import Enum
import sys
import json

from mido import MidiFile

# Module loading.
tempDirectory = (str(sys.path[0]) + "/modules")
sys.path.insert(1,tempDirectory)

import joule_data

# For simplicity, game specific functions are moved into their own files.
from joule_band import *
from joule_band_rbn import *

__version__ = joule_data.Version


# Variables
# ========================================

class FileType(Enum):
    MIDI = 1
    BINARY = 2
    TEXT = 3

gameDataLocation    = ""
gameDataFileType    = None



# Functions
# ========================================


def main():

    # Argument checking.
    # ========================================

    if len(sys.argv) < 2:
        print ("Invalid number of arguments!")
        return False
    pass
    
    gameDataLocation    = sys.argv[1]

    if joule_data.Debug > 0:
        for i in range(joule_data.Debug):
            joule_data.GameDataOutput.update( { f"debug_{i+1}":{}, } )
    
    global gameDataFileType

    # Set the file type that we are reading.
    # ========================================
    
    if gameDataLocation.endswith(".mid") or gameDataLocation.endswith(".midi"):
        gameDataFileType = FileType.MIDI
    elif gameDataLocation.endswith(".chart"):
        gameDataFileType = FileType.TEXT
    else:
        gameDataFileType = FileType.BINARY
    pass


    # Assume that the game is Rock Band 3 if none is provided.
    # ========================================

    if len(sys.argv) == 2 and gameDataFileType == FileType.MIDI:
        print("No Game Source provided, assuming Rock Band 3...")
        joule_data.GameSource = "rb3"
    else:
        joule_data.GameSource = sys.argv[2]
    pass


    if joule_data.GameSource in joule_data.GameSourceList:
        joule_data.GameSourceFull = joule_data.GameSourceList[joule_data.GameSource]


    # Open the file for reading.
    # ========================================
    try:
        if gameDataFileType == FileType.MIDI:
            joule_data.gameDataFile = MidiFile(gameDataLocation)
        elif gameDataFileType == FileType.TEXT:
            joule_data.gameDataFile = open(gameDataLocation, mode="r")
        elif gameDataFileType == FileType.BINARY:
            joule_data.gameDataFile = open(gameDataLocation, mode="rb")
        pass
    except OSError:
        print("Unable to read", gameDataLocation)
    pass

    
    joule_data.GameSourceFull = joule_data.GameSourceList[joule_data.GameSource]

    print(f"Game Source: {joule_data.GameSourceFull}")
    output_add("debug_1",f"Version: {joule_data.Version}")
    output_add("debug_1",f"GameSource: {joule_data.GameSourceFull}")

    # Game specific checks
    # ========================================
    
    if joule_data.GameSource in joule_data.GameSourceRBLike:
        
        joule_data.GameDataOutput.update( { "events":{}, "lyrics":{} } )
        initialize_band()
        process_lyrics()
        process_events()

        for part in joule_data.TracksFound:

            if part == "PART DRUMS" or part == "PART DRUMS_2X":
                rbn_drums_limbs(part)
                rbn_drums_fills(part)
            pass

            if part == "PART GUITAR" or part == "PART BASS" or part == "PART RHYTHM":
                rbn_guitar_chords(part)
            pass

            if part == "PART VOCALS" or part == "HARM1" or part == "HARM2" or part == "HARM3":
                rbn_vocals_lyrics(part)
            pass

            if part == "PART KEYS":
                for diff in joule_data_rockband.diff_array:
                    rbn_broken_chords(part,diff)
                pass
            pass

            if part.startswith("PART REAL_KEYS"):
                rbn_keys_real_chords(part)
                pass
            pass

            validate_spacing(part)
        
        validate_overdrive()

    elif joule_data.GameSource == "ch":

        joule_data.GameDataOutput.update( { "events":{}, "lyrics":{} } )
        print("TODO")

    else:
        print ("Invalid game specified!")
        return False
    pass

    # Output to json since we are done.
    # ========================================
    
    with open(gameDataLocation+".json", "w") as write:
        json.dump(joule_data.GameDataOutput, write, indent=4)

    return True
pass


if __name__ == "__main__":
    print ("")
    print ("Version: " + joule_data.Version)
    print ("========================================")

    main()

    print ("========================================")
    print("Done.")

