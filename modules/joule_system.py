# This is the file for system related tasks that is shared
# between multiple files.
import re
import os
import sys
import base64
import codecs
import joule_data

import joule_data_rockband
import joule_data_clonehero
import joule_data_yarg


def output_add(output_type: str, output: str, unique=False):

    if output_type.startswith("debug"):
        if int(output_type.split("_")[1]) > joule_data.Debug:
            return

    if unique:
        for outputs in joule_data.GameDataOutput[output_type]:
            if output == joule_data.GameDataOutput[output_type][outputs]:
                return

    _index = len(joule_data.GameDataOutput[output_type])
    joule_data.GameDataOutput[output_type][_index] = output


pass

# We have a custom print function, because we need to change where we are outputting to.
try:
    from reaper_python import RPR_ShowConsoleMsg
except ImportError:

    def joule_print(string: str):
        print(string)

        if joule_data.OutputDebugFile == True:
            _tempOutputLocation = os.path.join(sys.path[0], "/joule_log.txt")

            f = open(_tempOutputLocation, "a")
            f.write(str(string) + "\n")
            f.close()
        pass

    pass
else:

    def joule_print(string: str):
        RPR_ShowConsoleMsg(str(string) + "\n")

        if joule_data.OutputDebugFile == True:
            _tempOutputLocation = os.path.join(sys.path[0], "joule_log.txt")

            f = open(_tempOutputLocation, "a")
            f.write(str(string) + "\n")
            f.close()
        pass

    pass
pass


def get_source_data():

    if joule_data.GameSource in joule_data.GameSourceRBLike:
        temp = joule_data_rockband

    if joule_data.GameSource == "ch":
        temp = joule_data_clonehero

    if joule_data.GameSource == "ghwtde":
        temp = joule_data_clonehero

    if joule_data.GameSource == "yarg":
        temp = joule_data_yarg

    return temp


pass


def get_meta(track: str, key: int = 0):
    # get_meta("time_signature_num", 0)

    try:
        _tempData = joule_data.GameData["trackNotesMeta"]["meta", track, key]
    except KeyError:
        return None
    else:
        return _tempData
    pass


pass


def write_meta(track: str, data):
    # This function writes data to the meta section of the Meta dictionary.

    if not "trackNotesMeta" in joule_data.GameData.keys():
        joule_data.GameData["trackNotesMeta"] = {}

    joule_data.GameData["trackNotesMeta"]["meta", track, 0] = data


pass


def write_meta_key(track: str, key: int, data):
    # This function writes data to the meta section of the Meta dictionary.

    if not "trackNotesMeta" in joule_data.GameData.keys():
        joule_data.GameData["trackNotesMeta"] = {}

    joule_data.GameData["trackNotesMeta"]["meta", track, key] = data


pass


def get_data_indexes(type: str, track: str, key: str, strict: bool = False):

    # This function returns a list of all the valid indexes of the data type you
    # are searching for.

    # get_data_indexes("trackNotesOn", 'PART DRUMS', 'x_kick')
    # get_data_indexes("trackNotesOn", 'PART DRUMS', 'x_kick', True)

    _tempData = []

    for _key, _val, _ind in joule_data.GameData[type].keys():
        if strict and _key == track and _val == key:
            _tempData.append(_ind)
        elif _key == track and _val.startswith(key):
            _tempData.append(_ind)
        pass
    pass

    return _tempData


pass


def get_data_indexes_range(type: str, track: str, key: str, time1: int, time2: int):

    _tempData = []
    _tempIndexes = get_data_indexes(type, track, key)

    for _index in _tempIndexes:
        if _index >= time1 and _index <= time2:
            _tempData.append(_index)
        pass
    pass

    return _tempData


pass


def extract_data(type: str, track: str, rename: str = ""):

    # This function extracts the whole track to a separate dictionary,
    # optionally renames the track if provided.

    if rename != "":
        _trackName = rename
    else:
        _trackName = track
    pass

    _tempData = {}

    for entry in joule_data.GameData[type]:
        if entry[0] == track:

            if joule_data.GameData[type][entry[0], entry[1], entry[2]] == True:
                _result = True
            else:
                _result = False

            _tempData[_trackName, entry[1], entry[2]] = _result
        pass
    pass

    return _tempData


pass


def line_groups(inputStr: str):

    test = re.search(r"(?:\ *)([^\s=]+)(?:\s*)(?:={1})(?:\ *)(.+)", inputStr)

    if test != None:
        lineGroups = test.groups()
        return lineGroups
    else:
        return None
    pass


pass


def cleaner_decimal(input):

    _input = str(input)

    if "." in _input:
        return _input.split(".")[0] + "." + _input.split(".")[1][0:2]
    else:
        return _input
    pass


pass


def decode_reaper_text(input):

    output = input

    try:
        output = base64.b64decode(output)

        textType = int(output[1])

        # Catch Sysex.
        if textType != 80:
            textData = output[2:]
        else:
            textData = list(output)
        pass

    except:
        try:
            textData = str.encode(output)
            textType = 1
        except:
            output_add(
                "debug_1",
                f"Joule Error | decode_reaper_text | Failed b64 decode: {output}",
            )
        pass
    pass

    # Do not decode Sysex events.
    if textType != 80:
        try:
            textData = codecs.decode(textData, "utf-8")
            textData = str(textData)
        except:
            output_add(
                "debug_1",
                f"Joule Error | decode_reaper_text | Failed utf-8 decode: {output}, {[textType, textData]}",
            )
        pass
    else:

        # Format the Sysex event in the same way as the MIDI reader.
        if textData[0] == 240:
            textData.pop(0)
            textData.pop()
        pass

        # We need to clamp these numbers to match what Mido reads.
        for index, item in enumerate(textData):
            if item > 127:
                textData[index] = 127
            pass
        pass

    pass

    return [textType, textData]


pass
