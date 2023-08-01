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

gameDataLocation    = ""


# Functions
# ========================================


def joule_run(gameDataLocation:str, gameSource:str):

    if joule_data.Debug > 0:
        for i in range(joule_data.Debug):
            joule_data.GameDataOutput.update( { f"debug_{i+1}":{}, } )

    joule_data.GameSource   = gameSource

    if joule_data.GameSource in joule_data.GameSourceList:
        joule_data.GameSourceFull = joule_data.GameSourceList[joule_data.GameSource]


    fileType = joule_data.GameDataFileType

    # Open the file for reading.
    # ========================================
    try:
        if fileType == "MIDI":
            joule_data.GameDataFile = MidiFile(gameDataLocation)
        elif fileType == "CHART":
            _temp = open(gameDataLocation, mode="r")
            joule_data.GameDataFile = _temp.readlines()
        elif fileType == "BINARY":
            joule_data.GameDataFile = open(gameDataLocation, mode="rb")
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
                rbn_hopos(part)
            pass

            if part == "PART VOCALS" or part == "HARM1" or part == "HARM2" or part == "HARM3":
                
                if part == "PART VOCALS":
                    tow_check()
                pass
            
                rbn_vocals_lyrics(part)
                
            pass

            if part == "PART KEYS":
                
                rbn_hopos(part)
                
                for diff in joule_data_rockband.diff_array:
                    rbn_broken_chords(part,diff)
                pass
            pass

            if part.startswith("PART REAL_KEYS"):
                rbn_keys_real_chords(part)
                pass
            pass

            validate_spacing(part)
        
        validate_instrument_phrases()

    elif joule_data.GameSource == "ch":

        joule_data.GameDataOutput.update( { "events":{}, "lyrics":{} } )
        
        initialize_band()

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
    
    
    # Argument checking.
    # ========================================

    if len(sys.argv) < 2:
        print ("Invalid number of arguments!")
        quit()
    pass

    argLocation = sys.argv[1]
  
    # Set the file type that we are reading.
    # ========================================
    
    if argLocation.endswith(".mid") or argLocation.endswith(".midi"):
        joule_data.GameDataFileType = "MIDI"
    elif argLocation.endswith(".chart"):
        joule_data.GameDataFileType = "CHART"
    else:
        joule_data.GameDataFileType = "BINARY"
    pass


    # Assume that the game is Rock Band 3 if none is provided.
    # ========================================
  
    if len(sys.argv) == 2 and joule_data.GameDataFileType == "MIDI":
        print("No Game Source provided, assuming Rock Band 3...")
        argSource = "rb3"
    else:
        argSource = sys.argv[2]
    pass

    joule_run(argLocation, argSource)

    print ("========================================")
    print("Done.")

