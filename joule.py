#!/usr/bin/env python3

from enum import Enum
import sys
import json
import os
import configparser

# Module loading.
tempDirectory = os.path.join(sys.path[0], "modules")
sys.path.insert(1, tempDirectory)

import joule_data

# For simplicity, game specific functions are moved into their own files.
from joule_system import *
from joule_band import *
from joule_band_rbn import *
from joule_muse import *

__version__ = joule_data.Version

gameDataLocation = ""
ignoreChecks = False

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


def joule_init(gameDataLocation: str, gameSource: str = False):
    global ignoreChecks
    ignoreChecks = True
    return joule_run(gameDataLocation, gameSource)


pass


def joule_run(gameDataLocation: str, gameSource: str = False):

    global ignoreChecks

    joule_data.GameData.clear()
    joule_data.GameDataOutput.clear()
    joule_data.Tracks.clear()
    joule_data.TracksFound.clear()

    joule_data.GameDataOutput.update({"info": {}, "messages": {}})
    joule_data.GameDataOutput.update(
        {"issues_critical": {}, "issues_major": {}, "issues_minor": {}}
    )
    joule_data.GameDataOutput.update({"events": {}, "lyrics": {}})
    joule_data.GameDataOutput.update({"check_results": {}, "flags": {}})
    joule_data.GameDataOutput.update({"tracks": {}, "tracks_found": {}})

    joule_data.GameDataLocation = gameDataLocation

    joule_data.GameData["sections"] = {}

    # Config file reading
    config = configparser.ConfigParser()
    configLoaded = False

    if os.path.isfile(os.path.join(sys.path[0], "joule_config.ini")):
        try:
            config.read(os.path.join(sys.path[0], "joule_config.ini"))
            configLoaded = True

            joule_data.GameSourceDefault = str(config["Joule"]["GameSourceDefault"])
            joule_data.IgnoreModNotes = config["Joule"].getboolean("IgnoreModNotes")
            joule_data.OutputNextToSource = config["Joule"].getboolean(
                "OutputNextToSource"
            )
            joule_data.OutputToOutputDir = config["Joule"].getboolean(
                "OutputToOutputDir"
            )

            joule_data.AllowMuse = config["Muse"].getboolean("AllowMuse")

            joule_data.Debug = int(config["Debug"]["Level"])
            joule_data.OutputDebugFile = config["Debug"].getboolean("OutputDebugFile")

        except Exception as ex:
            joule_print(f"Configuration Error!\n\n{ex}")
        pass
    else:
        pass
    pass

    if joule_data.Debug > 0:
        for i in range(joule_data.Debug):
            joule_data.GameDataOutput.update(
                {
                    f"debug_{i+1}": {},
                }
            )

    if joule_data.OutputDebugFile == True:
        _tempOutputLocation = os.path.join(sys.path[0], "joule_log.txt")

        # Create the output file, close it for now.
        f = open(_tempOutputLocation, "w")
        f.close()

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
            joule_print(
                f"No Game Source provided, assuming {joule_data.GameSourceList[joule_data.GameSourceDefault]}..."
            )
    else:
        joule_data.GameSource = gameSource
    pass

    if joule_data.GameSource in joule_data.GameSourceList:
        joule_data.GameSourceFull = joule_data.GameSourceList[joule_data.GameSource]
    else:
        joule_print("Invalid Game Source provided, Joule can not continue.")
        quit()

    joule_print(f"Game Source: {joule_data.GameSourceFull}")
    output_add("info", f"Joule Version: {joule_data.Version}")
    output_add("info", f"Source: {joule_data.GameSourceFull}")
    output_add("debug_1", f"GameSource: {joule_data.GameSource}")

    if joule_data.IncludeREAPER:
        _client = "REAPER"
    else:
        _client = "CLI"

    output_add("info", f"Client: {_client}")
    output_add("info", f"Configuration Loaded: {configLoaded}")

    fileType = joule_data.GameDataFileType

    # Open the file for reading.
    # ========================================
    try:
        if fileType == "MIDI":
            if not joule_data.IncludeMIDI:
                joule_print("Mido is not loaded, unable to proceed.")
                return
            else:
                joule_data.GameDataFile = MidiFile(gameDataLocation, clip=True)
            pass
        elif fileType == "CHART":
            _temp = open(gameDataLocation, mode="r")
            joule_data.GameDataFile = _temp.readlines()
        elif fileType == "BINARY":
            joule_data.GameDataFile = open(gameDataLocation, mode="rb")
        elif fileType == "REAPER":

            if not joule_data.IncludeREAPER:
                joule_print("REAPER API failed to load, aborting...")
                return

            # Get REAPER metadata.
            rpr_enum = RPR_EnumProjects(-1, "", 512)

            # Rewrite the location to where the project file is.
            gameDataLocation = rpr_enum[2]
            joule_data.GameDataLocation = gameDataLocation

            # Grab the name for the output.
            file_name_split = gameDataLocation.split("\\")
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
        # joule_print(gameDataDirectory)

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
                    pass

                    if "whammy" in keyCheck and "cutoff" in keyCheck:
                        write_meta("WhammyCutoff", float(lineGroups[1].strip()))
                        joule_print("Found Whammy Cutoff.")
                    pass

                pass
            pass
        except OSError:
            joule_print("No song.ini found.")
        pass
    pass

    initTest = initialize_band()

    if initTest != False:

        check_mod_enhancements()
        process_lyrics()
        process_events()

        if not ignoreChecks:

            DrumsTracks = [
                "PART DRUMS",
                "PART DRUMS_2X",
                "Drums",
            ]

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

            for part in joule_data.TracksFound:

                if part in DrumsTracks:
                    rbn_drums_limbs(part)
                    rbn_drums_fills(part)
                    tow_check(part)
                pass

                if part in GuitarTracks:
                    rbn_guitar_chords(part)
                    rbn_broken_chords(part)
                    rbn_hopos(part)
                    validate_sustains(part)
                    tow_check(part)
                pass

                if part in ("PART VOCALS", "HARM1", "HARM2", "HARM3"):

                    if part == "PART VOCALS":
                        tow_check(part)
                    pass

                    rbn_vocals_lyrics(part)
                    validate_spacing_vocals(part)

                pass

                if part in ("PART KEYS", "Keyboard"):

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

    if not ignoreChecks and joule_data.AllowMuse:
        muse_run()

    for track in joule_data.Tracks:
        output_add("tracks", f"{track}")

    for track in joule_data.TracksFound:
        output_add("tracks_found", f"{track}")

    # Output to json since we are done.
    # ========================================

    if joule_data.OutputNextToSource == True:
        with open(gameDataLocation + ".json", "w") as write:
            json.dump(joule_data.GameDataOutput, write, indent=4)

    # Running from REAPER will always create an output in the folder.
    if joule_data.GameDataFileType == "REAPER" or joule_data.OutputToOutputDir == True:
        _tempOutputLocation = os.path.join(sys.path[0], "output")

        if not os.path.exists(_tempOutputLocation):
            os.makedirs(_tempOutputLocation)

        with open(os.path.join(_tempOutputLocation, "output.json"), "w") as write:
            json.dump(joule_data.GameDataOutput, write, indent=4)

    return initTest


pass


if __name__ == "__main__":
    joule_print("")
    joule_print("Joule Version: " + joule_data.Version)
    joule_print("========================================")

    # Argument checking.
    # ========================================

    argSource = False

    if joule_data.IncludeREAPER:
        argLocation = "REAPER"
    else:
        if len(sys.argv) < 2 or len(sys.argv) > 3:
            joule_print("Invalid number of arguments!")
            quit()
        pass

        argLocation = sys.argv[1]

        if len(sys.argv) > 2:
            argSource = sys.argv[2]
        pass
    pass

    joule_run(argLocation, argSource)

    joule_print("========================================")
    joule_print("Done.")
