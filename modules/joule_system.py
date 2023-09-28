# This is the file for system related tasks that is shared
# between multiple files.
import re
import joule_data

import joule_data_rockband
import joule_data_clonehero
import joule_data_yarg

def output_add( output_type:str, output:str ):

    if output_type.startswith("debug"):
        if int(output_type.split('_')[1]) > joule_data.Debug:
            return

    _index = len(joule_data.GameDataOutput[output_type])
    joule_data.GameDataOutput[output_type][_index] = output
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

    test = re.search("(?:\ *)([^\s=]+)(?:\s*)(?:={1})(?:\ *)(.+)", inputStr)

    if test != None:
        lineGroups = test.groups()
        return lineGroups
    else:
        return None
    pass

pass
