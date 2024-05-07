# This file has common functions for Band related games.

import joule_data
import joule_band

from joule_system import *

import math
import datetime

# This function is basically copied from my implementation in CARV,
# with some minor modifications to function in this context.
def format_location( note_location:int, display_time=False ):
        
    time_signature_locations = get_data_indexes("trackNotesMeta", "meta", "time_signature_num")

    location_amount = len(time_signature_locations)

    for test in range(location_amount):

        location_index = ( location_amount - 1 ) - test

        if note_location >= time_signature_locations[location_index]:

            location_base = time_signature_locations[location_index]
            location_offset = note_location - location_base

            location_num = get_meta("time_signature_num", joule_band.time_signature_time[location_index])
            location_denom = get_meta("time_signature_denom", joule_band.time_signature_time[location_index])

            divisor_factor = (location_denom / 4)
            divisor = ( joule_data.TicksPerBeat / divisor_factor ) * location_num

            time_1 = (location_offset / divisor) + joule_band.time_signature_measure[location_index]
            time_2 = (location_offset % divisor ) / ( joule_data.TicksPerBeat / (location_denom / 4) )

            time_1 = math.floor(time_1)
            time_2 = math.floor(time_2)

            time_string = str(time_1 + 1)+ '.' + str(time_2 + 1)

            if display_time == True:
                time_string = time_string + str(time_2 + 1) + f" | {format_seconds(note_location)}"

            return ( time_string )

    return "Error.Error"
pass


# Creates a list of the current time in seconds at every tick.
def generate_seconds():

    if get_meta("TotalLength") == None:
        joule_print("generate_seconds: File has not been initialized for seconds generation!")
        return False

    time_base = 0
    current_tempo = 500000
    last_second = -1
    seconds_list = []

    for test in range( get_meta("TotalLength") + 1):

        tempo_check = get_meta("tempo", test)

        if tempo_check != None:
            current_tempo = tempo_check

        seconds = ( current_tempo / 1000000.0 ) / joule_data.TicksPerBeat

        seconds_final = seconds + time_base
        time_base = seconds_final

        joule_data.Seconds.append(seconds_final)

        if last_second < math.floor(seconds_final):
            last_second = math.floor(seconds_final)
            seconds_list.append(test)
            #joule_print(f"{test} : {seconds_final}")

    joule_data.SecondsList = seconds_list
    return True

pass


# Return the ticks in a seconds based format,
# similar to how REAPER displays the time.
def format_seconds( note_location:int ):

    if get_meta("TotalLength") == None:
        joule_print("format_seconds: File has not been initialized for seconds generation!")
        return "SecondsError"

    raw_time = joule_data.Seconds[note_location]

    if raw_time == None:
        joule_print(note_location)
        return "SecondsError"

    time_string = f"{ datetime.timedelta(seconds=raw_time) }"
    time_string_1 = time_string.split(".")[0]

    # Remove leading hour if it is 0.
    if time_string_1.startswith("0"):
        time_string_1 = time_string_1[2:]

    # Remove leading double digit minute if it is 0.
    if time_string_1.startswith("0"):
        time_string_1 = time_string_1[1:]

    time_string_2 = time_string.split(".")[1][0:3]
    return time_string_1 + "." +time_string_2

pass

def process_time_signature( ticks:int, numerator:int, denominator:int ):

    #joule_print(f"Found {numerator}/{denominator} at {ticks}.")

    joule_band.trackNotesMeta["meta","time_signature_num",ticks] = numerator
    joule_band.trackNotesMeta["meta","time_signature_denom",ticks] = denominator

    # We need to manually keep track of time signature changes
    # since we do not have an easy way to do that here.
    joule_band.time_signature_time.append(ticks)

    tempPosition = ticks - joule_band.time_signature_last_position

    ticks_per_measure = ( joule_data.TicksPerBeat / joule_band.last_time_signature_denom ) * joule_band.last_time_signature_num

    tempPosition = (tempPosition / ticks_per_measure) / 4

    joule_band.time_signature_last_measure     = joule_band.time_signature_last_measure + tempPosition
    joule_band.time_signature_last_position    = ticks
    joule_band.last_time_signature_num         = numerator
    joule_band.last_time_signature_denom       = denominator

    joule_band.time_signature_measure.append( joule_band.time_signature_last_measure )
    
pass

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


# The get_note_* functions function faster by bypassing the
# KeyError exception on access instead of manually checking.
def get_note_on(part:str, note:str, time:int):

    try:
        _tempData = joule_data.GameData["trackNotesOn"][part,note,time]
    except KeyError:
        return False
    else:
        return _tempData
    pass

pass

def get_note_off(part:str, note:str, time:int):

    try:
        _tempData = joule_data.GameData["trackNotesOff"][part,note,time]
    except KeyError:
        return False
    else:
        return _tempData
    pass

pass
