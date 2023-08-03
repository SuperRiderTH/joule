'''
This file contains all the information that Clone Hero uses.
'''

from joule_data_yarg import *

brokenChordsAllowed     = True
lowerHOPOsAllowed       = True

# Any part in this list will be processed.
notesname_instruments_array = {
    "PART DRUMS": "DRUMS",
    "PART DRUMS_2X": "DRUMS",
    #"PART TRUE_DRUMS": "TRUEDRUMS"

    "PART GUITAR": "5LANES",
    "PART RHYTHM": "5LANES",
    "PART BASS": "5LANES",
    "PART KEYS": "5LANES",
    
    "Single": "5LANES",
    "DoubleGuitar": "5LANES",
    "DoubleBass": "5LANES",
    "DoubleRhythm": "5LANES",
    "Keyboard": "5LANES",

    "PART REAL_KEYS_X": "PROKEYS",
    "PART REAL_KEYS_H": "PROKEYS",
    "PART REAL_KEYS_M": "PROKEYS",
    "PART REAL_KEYS_E": "PROKEYS",

    "PART VOCALS" : "VOCALS",
    "HARM1": "VOCALS",
    "HARM2": "VOCALS",
    "HARM3": "VOCALS",
    }

notes_pads = ['red','yellow','blue','green','orange',]
notes_kick = ['kick','kick_2x',]
notes_drum = notes_pads + notes_kick

notes_lane = ['open','green','red','yellow','blue','orange',]

notename_chart_notes = {
    "5LANES" :
    {
        0 : "green", 
        1 : "red",
        2 : "yellow", 
        3 : "blue",
        4 : "orange",
        7 : "open",
        5 : "hopo",
        6 : "tap",
    },
    "DRUMS" :
    {
        0 : "kick",
        1 : "red",
        2 : "yellow",
        3 : "blue",
        4 : "orange",
        5 : "green",
        32 : "kick_2x",
        
        34 : "accent_red",
        35 : "accent_yellow",
        36 : "accent_blue",
        37 : "accent_orange",
        38 : "accent_green",
        
        40 : "ghost_red",
        41 : "ghost_yellow",
        42 : "ghost_blue",
        43 : "ghost_orange",
        44 : "ghost_green",
        
        66 : "cymbal_yellow",
        67 : "cymbal_blue",
        68 : "cymbal_green",
    },
}

# We are using Rock Band style naming for consistency.
notename_chart_phrase = {
    "5LANES" :
    {
        0 : "phrase_p1", 
        1 : "phrase_p2",
        2 : "overdrive", 
    },
    "DRUMS" :
    {
        2 : "overdrive",
        64 : "fill_kick",
        65 : "roll_single",
        66 : "roll_swell",
    }
}

