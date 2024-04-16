#!/usr/bin/env python3

from enum import Enum
import sys
import json
import os
import shutil

# Module loading.
tempDirectory = os.path.join(sys.path[0], "modules")
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


# Imports
# ========================================

try:
    from mido import MidiFile
except ImportError:
    pass
else:
    joule_data.IncludeMIDI = True
pass

try:
    from reaper_python import *
    RPR_ShowConsoleMsg("")
except ImportError:
    pass
else:
    joule_data.IncludeREAPER = True
pass


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
    elif joule_data.IncludeREAPER:
        joule_data.GameDataFileType = "REAPER"
    else:
        joule_data.GameDataFileType = "BINARY"
    pass

    # Assume that the game is Rock Band 3 if none is provided.
    # ========================================

    if gameSource == False:
        joule_data.GameSource = joule_data.GameSourceDefault
        if joule_data.GameDataFileType != "REAPER":
            joule_print(f"No Game Source provided, assuming {joule_data.GameSourceList[joule_data.GameSourceDefault]}...")
    else:
        joule_data.GameSource = gameSource
    pass

    
    if joule_data.GameSource in joule_data.GameSourceList:
        joule_data.GameSourceFull = joule_data.GameSourceList[joule_data.GameSource]
    else:
        joule_print("Invalid Game Source provided, Joule can not continue.")
        quit()


    joule_print(f"Game Source: {joule_data.GameSourceFull}")
    output_add("info",f"Joule Version: {joule_data.Version}")
    output_add("info",f"Source: {joule_data.GameSourceFull}")
    output_add("debug_1",f"GameSource: {joule_data.GameSource}")


    fileType = joule_data.GameDataFileType

    # Open the file for reading.
    # ========================================
    try:
        if fileType == "MIDI" or fileType == "CHART":

            # Chart reading in theory can work without MIDI,
            # but the bpm2tempo function needs to be recreated.
            if not joule_data.IncludeMIDI:
                joule_print("Mido is not loaded, unable to proceed.")
                return

            if fileType == "MIDI":
                joule_data.GameDataFile = MidiFile(gameDataLocation, clip=True)
            elif fileType == "CHART":
                _temp = open(gameDataLocation, mode="r")
                joule_data.GameDataFile = _temp.readlines()
            pass

        elif fileType == "BINARY":
            joule_data.GameDataFile = open(gameDataLocation, mode="rb")
        elif fileType == "REAPER":

            # Get REAPER metadata.
            rpr_enum = RPR_EnumProjects(-1, "", 512)

            # Rewrite the location to where the project file is.
            gameDataLocation = rpr_enum[2]
            joule_data.GameDataLocation = gameDataLocation

            # Grab the name for the output.
            file_name_split = gameDataLocation.split('\\')
            file_name = file_name_split[len(file_name_split) - 1]
            file_name = file_name.split(".")[0]

            joule_print(f"Running inside of REAPER, reading {file_name}...")

        pass
    except OSError:
        joule_print(f"Unable to read: {gameDataLocation}")
        return False
    pass


    # Game specific checks
    # ========================================

    # Check for a song.ini, use their information if it exists.
    if joule_data.GameSource in joule_data.GameSourceHasSongINI:
        gameDataDirectory = os.path.dirname(gameDataLocation)
        #joule_print(gameDataDirectory)

        try:
            _temp = open(gameDataDirectory + "/song.ini", mode="r")
            _tempLines = _temp.readlines()

            joule_print("Found song.ini, parsing information...")

            for line in _tempLines:
                lineGroups = line_groups(line)

                if lineGroups != None:

                    keyCheck = lineGroups[0].strip().lower()

                    if "multiplier" in keyCheck and "note" in keyCheck:
                        write_meta("NoteOverdrive", int(lineGroups[1].strip()))
                        joule_print("Found Multiplier Note.")

                    if "whammy" in keyCheck and "cutoff" in keyCheck:
                        write_meta("WhammyCutoff", float(lineGroups[1].strip()))
                        joule_print("Found Whammy Cutoff.")

        except OSError:
            joule_print("No song.ini found.")
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
        joule_print ("Invalid game specified!")
        return False
    pass

    if not ignoreChecks and joule_data.AllowMuse:
        muse_run()

    # Output to json since we are done.
    # ========================================

    with open(gameDataLocation + ".json", "w") as write:
        json.dump(joule_data.GameDataOutput, write, indent=4)

    if joule_data.GameDataFileType == "REAPER":
        _tempOutputLocation = os.path.join(sys.path[0], "output")

        if not os.path.exists(_tempOutputLocation):
            os.makedirs(_tempOutputLocation)

        shutil.copyfile(gameDataLocation + ".json", os.path.join(_tempOutputLocation, "output.json"))

    return initTest
pass


if __name__ == "__main__":
    joule_print ("")
    joule_print ("Joule Version: " + joule_data.Version)
    joule_print ("========================================")
    
    
    # Argument checking.
    # ========================================

    argSource = False

    if joule_data.IncludeREAPER:
        argLocation = "REAPER"
    else:
        if len(sys.argv) < 2 or len(sys.argv) > 3:
            joule_print ("Invalid number of arguments!")
            quit()
        pass

        argLocation = sys.argv[1]

        if len(sys.argv) > 2:
            argSource = sys.argv[2]
        pass
    pass

    joule_run(argLocation, argSource)

    joule_print ("========================================")
    joule_print("Done.")

