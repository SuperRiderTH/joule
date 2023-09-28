import joule_data
import math

from joule_system import *
import joule_band

import datetime


def format_location( note_location:int, display_time=False ):
            
    # This function is basically copied from my implementation in CARV,
    # with some minor modifications to function in this context.
        
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

def generate_seconds():

    if get_meta("TotalLength") == None:
        print("File has not been initialized for seconds generation!")
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
            #print(f"{test} : {seconds_final}")

    output_add("debug_1",f"TotalLength: {get_meta('TotalLength')} | {format_seconds(get_meta('TotalLength'))}")
    joule_data.SecondsList = seconds_list
    return True

pass

def format_seconds( note_location:int ):

    # Return the ticks in a seconds based format,
    # similar to how REAPER displays the time.

    raw_time = joule_data.Seconds[note_location]

    if raw_time == None:
        print(note_location)
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