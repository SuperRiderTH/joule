"""
This file contains all the information that YARG uses.
"""

from joule_data_rockband import *

brokenChordsAllowed = True
lowerHOPOsAllowed = True

# Any part in this list will be processed.
notesname_instruments_array = {
    "PART DRUMS": "DRUMS",
    "PART DRUMS_2X": "DRUMS",
    # "PART TRUE_DRUMS": "TRUEDRUMS"
    "PART GUITAR": "5LANES",
    "PART RHYTHM": "5LANES",
    "PART BASS": "5LANES",
    "PART KEYS": "5LANES",
    "PART REAL_KEYS_X": "PROKEYS",
    "PART REAL_KEYS_H": "PROKEYS",
    "PART REAL_KEYS_M": "PROKEYS",
    "PART REAL_KEYS_E": "PROKEYS",
    "PART VOCALS": "VOCALS",
    "HARM1": "VOCALS",
    "HARM2": "VOCALS",
    "HARM3": "VOCALS",
}

notes_pads = [
    "red",
    "yellow",
    "blue",
    "green",
]
notes_kick = [
    "kick",
    "kick_2x",
]
notes_drum = notes_pads + notes_kick

notes_lane = [
    "open",
    "green",
    "red",
    "yellow",
    "blue",
    "orange",
]

# Internal names for these notes.
notename_array = {
    "5LANES": {
        127: "trill",
        126: "tremolo",
        124: "bre_5",
        123: "bre_4",
        122: "bre_3",
        121: "bre_2",
        120: "bre_1",
        116: "overdrive",
        106: "tow_p2",
        105: "tow_p1",
        104: "tap",
        103: "solo",
        102: "hopo_x_off",
        101: "hopo_x_on",
        100: "x_orange",
        99: "x_blue",
        98: "x_yellow",
        97: "x_red",
        96: "x_green",
        95: "x_open",
        90: "hopo_h_off",
        89: "hopo_h_on",
        88: "h_orange",
        87: "h_blue",
        86: "h_yellow",
        85: "h_red",
        84: "h_green",
        83: "h_open",
        78: "m_hopo_off",
        77: "m_hopo_on",
        76: "m_orange",
        75: "m_blue",
        74: "m_yellow",
        73: "m_red",
        72: "m_green",
        71: "m_open",
        66: "e_hopo_off",
        65: "e_hopo_on",
        64: "e_orange",
        63: "e_blue",
        62: "e_yellow",
        61: "e_red",
        60: "e_green",
        59: "e_open",
    },
    "DRUMS": {
        127: "roll_swell",
        126: "roll_single",
        124: "fill_green",
        123: "fill_blue",
        122: "fill_yellow",
        121: "fill_red",
        120: "fill_kick",
        116: "overdrive",
        112: "tom_green",
        111: "tom_blue",
        110: "tom_yellow",
        106: "tow_p2",
        105: "tow_p1",
        103: "solo",
        100: "x_green",
        99: "x_blue",
        98: "x_yellow",
        97: "x_red",
        96: "x_kick",
        95: "x_kick_2x",
        88: "h_green",
        87: "h_blue",
        86: "h_yellow",
        85: "h_red",
        84: "h_kick",
        83: "h_kick_2x",
        76: "m_green",
        75: "m_blue",
        74: "m_yellow",
        73: "m_red",
        72: "m_kick",
        71: "m_kick_2x",
        64: "e_green",
        63: "e_blue",
        62: "e_yellow",
        61: "e_red",
        60: "e_kick",
        59: "e_kick_2x",
        51: "animation_floor_tim_rh",
        50: "animation_floor_tom_lh",
        49: "animation_tom_2_rh",
        48: "animation_tom_2_lh",
        47: "animation_tom_1_rh",
        46: "animation_tom_1_lh",
        45: "animation_soft_crash_2_lh",
        44: "animation_crash_2_lh",
        43: "animation_ride_lh",
        42: "animation_ride_cym_rh",
        41: "animation_crash_2_choke",
        40: "animation_crash_1_choke",
        39: "animation_crash_2_soft_rh",
        38: "animation_crash_2_hard_rh",
        37: "animation_crash_1_soft_rh",
        36: "animation_crash_1_hard_rh",
        35: "animation_crash_1_soft_lh",
        34: "animation_crash_1_hard_lh",
        33: "animation_percussion_lh",
        32: "animation_percussion_rh",
        31: "animation_hi_hat_rh",
        30: "animation_hi_hat_lh",
        29: "animation_soft_snare_rh",
        28: "animation_soft_snare_lh",
        27: "animation_snare_rh",
        26: "animation_snare_lh",
        25: "animation_hi_hat_open",
        24: "animation_kick",
    },
    "TRUEDRUMS": {
        # TODO: Fill out list.
        106: "od_activation",
        104: "overdrive",
        106: "fill_kick",  # Technically wrong, but here for compatibility.
    },
    "VOCALS": {
        116: "overdrive",
        106: "phrase_p2",
        105: "phrase_p1",
        97: "percussion_hidden",
        96: "percussion_shown",
        84: "note_c5",
        83: "note_b5",
        82: "note_a#4",
        81: "note_a4",
        80: "note_g#4",
        79: "note_g4",
        78: "note_f#4",
        77: "note_f4",
        76: "note_e4",
        75: "note_d#4",
        74: "note_d4",
        73: "note_c#4",
        72: "note_c4",
        71: "note_b3",
        70: "note_a#3",
        69: "note_a3",
        68: "note_g#3",
        67: "note_g3",
        66: "note_f#3",
        65: "note_f3",
        64: "note_e3",
        63: "note_d#3",
        62: "note_d3",
        61: "note_c#3",
        60: "note_c3",
        59: "note_b2",
        58: "note_a#2",
        57: "note_a2",
        56: "note_g#2",
        55: "note_g2",
        54: "note_f#2",
        53: "note_f2",
        52: "note_e2",
        51: "note_d#2",
        50: "note_d2",
        49: "note_c#2",
        48: "note_c2",
        47: "note_b1",
        46: "note_a#1",
        45: "note_a1",
        44: "note_g#1",
        43: "note_g1",
        42: "note_f#1",
        41: "note_f1",
        40: "note_e1",
        39: "note_d#1",
        38: "note_d1",
        37: "note_c#1",
        36: "note_c1",
        1: "shift_lyrics",
        0: "shift_range",
    },
    "PROKEYS": {
        127: "trill",
        126: "glissando",
        124: "bre_5",
        123: "bre_4",
        122: "bre_3",
        121: "bre_2",
        120: "bre_1",
        116: "overdrive",
        115: "solo",
        72: "note_c4",
        71: "note_b3",
        70: "note_a#3",
        69: "note_a3",
        68: "note_g#3",
        67: "note_g3",
        66: "note_f#3",
        65: "note_f3",
        64: "note_e3",
        63: "note_d#3",
        62: "note_d3",
        61: "note_c#3",
        60: "note_c3",
        59: "note_b2",
        58: "note_a#2",
        57: "note_a2",
        56: "note_g#2",
        55: "note_g2",
        54: "note_f#2",
        53: "note_f2",
        52: "note_e2",
        51: "note_d#2",
        50: "note_d2",
        49: "note_c#2",
        48: "note_c2",
        9: "range_a2_c4",
        7: "range_g2_b3",
        5: "range_f2_a3",
        4: "range_e2_g3",
        2: "range_d2_f3",
        0: "range_c2_e3",
    },
}
