"""
This file contains all the information that DrumBeats VR uses.
"""

from joule_data_rockband import *

# Any part in this list will be processed.
notesname_instruments_array = {
    "PART DRUMS": "DRUMS",  # This is currently incorrect, as DrumBeats does not currently have MIDI tracks.
}

notes_pads = [
    "china",
    "cymbal_right",
    "cymbal_left",
    "tom_high",
    "tom_mid",
    "tom_low",
    "bell",
    "ride",
    "hat_open",
    "hat_closed",
    "snare",
]
notes_kick = [
    "kick",
]
notes_drum = notes_pads + notes_kick
ghost_velocity = 19

diff_highest = "x"

diff_array = {
    "x": "Extreme",
    "h": "Hard",
    "m": "Medium",
    "e": "Easy",
}

# Internal names for these notes.
notename_array = {
    "DRUMS": {
        81: "china",
        79: "cymbal_right",
        77: "cymbal_left",
        71: "tom_high",
        69: "tom_mid",
        65: "tom_low",
        61: "bell",
        60: "ride",
        55: "hat_open",
        51: "hat_closed",
        38: "snare",
        36: "kick",
        35: "golden",
    },
}
