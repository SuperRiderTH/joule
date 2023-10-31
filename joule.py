#!/usr/bin/env python3

from enum import Enum
import sys
import json
import os

from mido import MidiFile

# Module loading.
tempDirectory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules")
sys.path.insert(1,tempDirectory)

import joule_data

# For simplicity, game specific functions are moved into their own files.
from joule_system import *
from joule_band import *
from joule_band_rbn import *
from joule_muse import *

__version__ = joule_data.Version

gameDataLocation    = ""
ignoreChecks        = False


# Functions
# ========================================

def joule_init(gameDataLocation:str, gameSource:str = False):
    global ignoreChecks
    ignoreChecks = True
    return joule_run(gameDataLocation, gameSource)
pass

def joule_run(gameDataLocation:str, gameSource:str = False):

    global ignoreChecks

    joule_data.GameData.clear()
    joule_data.GameDataOutput.clear()
    joule_data.Tracks.clear()
    joule_data.TracksFound.clear()

    joule_data.GameDataOutput  = {"issues_critical":{},"issues_major":{},"issues_minor":{},}
    joule_data.GameDataLocation = gameDataLocation

    if joule_data.Debug > 0:
        for i in range(joule_data.Debug):
            joule_data.GameDataOutput.update( { f"debug_{i+1}":{}, } )


    # Set the file type that we are reading.
    # ========================================
    
    if gameDataLocation.endswith(".mid") or gameDataLocation.endswith(".midi"):
        joule_data.GameDataFileType = "MIDI"
    elif gameDataLocation.endswith(".chart"):
        joule_data.GameDataFileType = "CHART"
    else:
        joule_data.GameDataFileType = "BINARY"
    pass

    if gameSource == False:
        if joule_data.GameDataFileType == "MIDI":
            print("No Game Source provided, assuming Rock Band 3...")
            joule_data.GameSource   = "rb3"
        else:
            print("No Game Source provided, Joule can not continue.")
            return False
        pass
    else:
        joule_data.GameSource   = gameSource
    pass

    

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
        return False
    pass

    
    joule_data.GameSourceFull = joule_data.GameSourceList[joule_data.GameSource]

    print(f"Game Source: {joule_data.GameSourceFull}")
    output_add("debug_1",f"Version: {joule_data.Version}")
    output_add("debug_1",f"GameSource: {joule_data.GameSourceFull}")

    # Game specific checks
    # ========================================

    # Check for a song.ini, use their information if it exists.
    if joule_data.GameSource in joule_data.GameSourceHasSongINI:
        gameDataDirectory = os.path.dirname(gameDataLocation)
        #print(gameDataDirectory)

        try:
            _temp = open(gameDataDirectory + "/song.ini", mode="r")
            _tempLines = _temp.readlines()

            print("Found song.ini, parsing information...")

            for line in _tempLines:
                lineGroups = line_groups(line)

                if lineGroups != None:

                    keyCheck = lineGroups[0].strip().lower()

                    if "multiplier" in keyCheck and "note" in keyCheck:
                        write_meta("NoteOverdrive", int(lineGroups[1].strip()))
                        print("Found Multiplier Note.")

                    if "whammy" in keyCheck and "cutoff" in keyCheck:
                        write_meta("WhammyCutoff", float(lineGroups[1].strip()))
                        print("Found Whammy Cutoff.")

        except OSError:
            print("No song.ini found.")
        pass
    pass
    
    if joule_data.GameSource in joule_data.GameSourceRBLike:
        
        joule_data.GameDataOutput.update( { "events":{}, "lyrics":{} } )
        
        initTest = initialize_band()

        if initTest != False:
            process_lyrics()
            process_events()
        
            if ignoreChecks == False:
            
                for part in joule_data.TracksFound:

                    if part in ( "PART DRUMS", "PART DRUMS_2X"):
                        rbn_drums_limbs(part)
                        rbn_drums_fills(part)
                    pass

                    if part in ( "PART GUITAR", "PART BASS", "PART RHYTHM"):
                        rbn_guitar_chords(part)
                        rbn_hopos(part)
                        validate_sustains(part)
                    pass

                    if part in ( "PART VOCALS", "HARM1", "HARM2", "HARM3"):
                        
                        if part == "PART VOCALS":
                            tow_check()
                        pass
                    
                        rbn_vocals_lyrics(part)
                        validate_spacing_vocals(part)
                        
                    pass

                    if part == "PART KEYS":
                        
                        rbn_hopos(part)
                        
                        for diff in joule_data_rockband.diff_array:
                            rbn_broken_chords(part,diff)
                        pass

                        validate_sustains(part)

                    pass

                    if part.startswith("PART REAL_KEYS"):
                        rbn_keys_real_chords(part)
                        validate_sustains(part, True)
                        pass
                    pass

                validate_instrument_phrases()
                
            pass
        pass
    elif joule_data.GameSource == "ch" or joule_data.GameSource == "ghwtde":
        
        joule_data.GameData["sections"] = {}
        joule_data.GameDataOutput.update( { "events":{}, "lyrics":{} } )
        
        GuitarTracks = [
                "PART GUITAR",
                "PART BASS",
                "PART RHYTHM",
                "Single",
                "DoubleGuitar",
                "DoubleBass",
                "DoubleRhythm",
            ]
        
        initTest = initialize_band()
        
        if initTest != False:
            process_lyrics()
            process_events()

            if ignoreChecks == False:
                for part in joule_data.TracksFound:

                    if part in ( "PART DRUMS", "PART DRUMS_2X", "Drums"):
                        rbn_drums_limbs(part)
                        rbn_drums_fills(part)
                    pass

                    if part in GuitarTracks:
                        rbn_guitar_chords(part)
                        rbn_hopos(part)
                        validate_sustains(part)
                    pass

                    if part in ( "PART VOCALS", "HARM1", "HARM2", "HARM3"):
                        
                        if part == "PART VOCALS":
                            tow_check()
                        pass
                    
                        rbn_vocals_lyrics(part)
                        validate_spacing_vocals(part)
                        
                    pass

                    if part in ( "PART KEYS", "Keyboard" ):
                        
                        rbn_hopos(part)
                        
                        for diff in joule_data_rockband.diff_array:
                            rbn_broken_chords(part,diff)
                        pass

                        validate_sustains(part)

                    pass

                    if part.startswith("PART REAL_KEYS"):
                        rbn_keys_real_chords(part)
                        validate_sustains(part, True)
                        pass
                    pass

                validate_instrument_phrases()
            pass
        pass
    else:
        print ("Invalid game specified!")
        return False
    pass

    if not ignoreChecks and joule_data.AllowMuse:
        muse_run()

    # Output to json since we are done.
    # ========================================
    
    with open(gameDataLocation+".json", "w") as write:
        json.dump(joule_data.GameDataOutput, write, indent=4)

    return initTest
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
    
    argSource = False
    
    if joule_data.GameDataFileType == "MIDI":
        if len(sys.argv) == 2:
            print("No Game Source provided, assuming Rock Band 3...")
            argSource = "rb3"
        else:
            argSource = sys.argv[2]
        pass
    else:
        if len(sys.argv) < 3:
            print("No Game Source provided, Joule can not continue.")
        else:
            argSource = sys.argv[2]
        pass
    pass
  
    if argSource != False:
        joule_run(argLocation, argSource)

    print ("========================================")
    print("Done.")

