import joule_data
import math

from joule_system import *
import joule_band



def format_location( note_location:int ):
            
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

            return ( str(time_1 + 1)+ '.' + str(time_2 + 1) )

    return "Error.Error"
pass

