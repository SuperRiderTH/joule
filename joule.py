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

    joule_data.GameDataOutput.update( { "info":{} } )
    joule_data.GameDataOutput.update( { "issues_critical":{}, "issues_major":{}, "issues_minor":{} } )
    joule_data.GameDataOutput.update( { "events":{}, "lyrics":{} } )
    joule_data.GameDataOutput.update( { "check_results":{} } )

    joule_data.GameDataLocation = gameDataLocation

    if joule_data.Debug > 0:
        for i in range(joule_data.Debug):
            joule_data.GameDataOutput.update( { f"debug_{i+1}":{}, } )


    # Set the file type that we are reading.
    # ========================================
    
    _location = gameDataLocation.lower()
    
    if _location.endswith(".mid") or _location.endswith(".midi"):
        joule_data.GameDataFileType = "MIDI"
    elif _location.endswith(".chart"):
        joule_data.GameDataFileType = "CHART"
    else:
        joule_data.GameDataFileType = "BINARY"
    pass

    # Assume that the game is Rock Band 3 if none is provided.
    # ========================================

    if gameSource == False:
        if joule_data.GameDataFileType == "MIDI":
            print("No Game Source provided, assuming Rock Band 3...")
            joule_data.GameSource = "rb3"
        else:
            print("No Game Source provided, Joule can not continue.")
            return False
        pass
    else:
        joule_data.GameSource = gameSource
    pass

    
    if joule_data.GameSource in joule_data.GameSourceList:
        joule_data.GameSourceFull = joule_data.GameSourceList[joule_data.GameSource]
    else:
        print("Invalid Game Source provided, Joule can not continue.")
        quit()


    fileType = joule_data.GameDataFileType

    # Open the file for reading.
    # ========================================
    try:
        if fileType == "MIDI":
            joule_data.GameDataFile = MidiFile(gameDataLocation, clip=True)
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


    print(f"Game Source: {joule_data.GameSourceFull}")
    output_add("info",f"Joule Version: {joule_data.Version}")
    output_add("info",f"Source: {joule_data.GameSourceFull}")
    output_add("debug_1",f"GameSource: {joule_data.GameSource}")

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
        
        initTest = initialize_band()

        if initTest != False:
            process_lyrics()
            process_events()
        
            if ignoreChecks == False:
            
                for part in joule_data.TracksFound:

                    if part in ( "PART DRUMS", "PART DRUMS_2X"):
                        rbn_drums_limbs(part)
                        rbn_drums_fills(part)
                        tow_check(part)
                    pass

                    if part in ( "PART GUITAR", "PART BASS", "PART RHYTHM"):
                        rbn_guitar_chords(part)
                        rbn_broken_chords(part)
                        rbn_hopos(part)
                        validate_sustains(part)
                        tow_check(part)
                    pass

                    if part in ( "PART VOCALS", "HARM1", "HARM2", "HARM3"):
                        
                        if part == "PART VOCALS":
                            tow_check(part)
                        pass
                    
                        rbn_vocals_lyrics(part)
                        validate_spacing_vocals(part)
                        
                    pass

                    if part == "PART KEYS":
                        
                        rbn_hopos(part)
                        rbn_broken_chords(part)
                        validate_sustains(part)

                    pass

                    if part.startswith("PART REAL_KEYS"):
                        rbn_keys_real_chords(part)
                        rbn_keys_real_shifts(part)
                        validate_sustains(part, True)
                        pass
                    pass

                validate_instrument_phrases()
                
            pass
        pass
    elif joule_data.GameSource == "ch" or joule_data.GameSource == "ghwtde":
        
        joule_data.GameData["sections"] = {}
        
        GuitarTracks = [
                "PART GUITAR",
                "PART BASS",
                "PART RHYTHM",
                "Single",
                "DoubleGuitar",
                "DoubleBass",
                "DoubleRhythm",
                "LeadRival1",
                "LeadRival2",
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
                        rbn_keys_real_shifts(part)
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

    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print ("Invalid number of arguments!")
        quit()
    pass

    argLocation = sys.argv[1]
    argSource = False

    if len(sys.argv) > 2:
        argSource = sys.argv[2]

    joule_run(argLocation, argSource)

    print ("========================================")
    print("Done.")

