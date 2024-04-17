# This is the file for system related tasks that is shared
# between multiple files.
import re
import base64
import codecs
import joule_data

import joule_data_rockband
import joule_data_clonehero
import joule_data_yarg

def output_add( output_type:str, output:str, unique=False ):

    if output_type.startswith("debug"):
        if int(output_type.split('_')[1]) > joule_data.Debug:
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
    def joule_print(string:str):
        print(string)
    pass
else:
    def joule_print(string:str):
        RPR_ShowConsoleMsg(str(string) + "\n")
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

def get_meta(track:str, key:int = 0):
# get_meta("time_signature_num", 0)

    try:
        _tempData = joule_data.GameData["trackNotesMeta"]["meta",track,key]
    except KeyError:
        return None
    else:
        return _tempData
    pass

pass

def write_meta(track:str, data):
# This function writes data to the meta section of the Meta dictionary.

    if not "trackNotesMeta" in joule_data.GameData.keys():
        joule_data.GameData["trackNotesMeta"] = {}

    joule_data.GameData["trackNotesMeta"]["meta",track,0] = data

pass

def write_meta_key(track:str, key:int, data):
# This function writes data to the meta section of the Meta dictionary.

    if not "trackNotesMeta" in joule_data.GameData.keys():
        joule_data.GameData["trackNotesMeta"] = {}

    joule_data.GameData["trackNotesMeta"]["meta",track,key] = data

pass


def get_data_indexes(type:str, track:str, key:str, strict:bool = False):

# This function returns a list of all the valid indexes of the data type you
# are searching for.

# get_data_indexes("trackNotesOn", 'PART DRUMS', 'x_kick')
# get_data_indexes("trackNotesOn", 'PART DRUMS', 'x_kick', True)

    _tempData = []

    for _key,_val, _ind in joule_data.GameData[type].keys():
        if strict and _key == track and _val == key:
            _tempData.append(_ind)
        elif _key == track and _val.startswith(key):
            _tempData.append(_ind)
        pass
    pass

    return _tempData

pass

def get_data_indexes_range(type:str, track:str, key:str, time1:int, time2:int):
    
    _tempData = []
    _tempIndexes = get_data_indexes(type, track, key)

    for _index in _tempIndexes:
        if _index >= time1 and _index <= time2:
            _tempData.append(_index)
        pass
    pass

    return _tempData
pass


def line_groups(inputStr:str):

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
        textString = output[2:]
    except:

        try:
            str.encode(output)
            textType = 1
            textString = str.encode(output)
        except:
            joule_print(f"failed b64 decode: {output}")
            pass

    textString = codecs.decode(textString, 'utf-8')
    textString = str(textString)

    return [textType, textString]

# This function is taken straight out of Mido,
# so that we can use it here. It is just a simple calculation, 
# but we should at least say where it came from.
def bpm2tempo(bpm, time_signature=(4, 4)):
    """Convert BPM (beats per minute) to MIDI file tempo (microseconds per
    quarter note).

    Depending on the chosen time signature a bar contains a different number of
    beats. These beats are multiples/fractions of a quarter note, thus the
    returned BPM depend on the time signature. Normal rounding applies.
    """
    return int(round(60 * 1e6 / bpm * time_signature[1] / 4.))