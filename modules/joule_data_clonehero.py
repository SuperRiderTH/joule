'''
This file contains all the information that Clone Hero uses.
'''

# TODO: all of it.

from joule_data_rockband import *

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

notes_pads = ['red','yellow','blue','green',]
notes_kick = ['kick','kick_2x',]
notes_drum = notes_pads + notes_kick

notes_lane = ['open','green','red','yellow','blue','orange',]
