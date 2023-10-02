'''
Muse is an assistant tool for Joule to automatically determine
the difficulty tiers of the GameData created by Joule.
'''

import joule_data

from joule_system import *
from joule_band_handlers import *

import joule_data_rockband
import joule_data_clonehero
import joule_data_yarg

ValidTracks = [
    "PART GUITAR",
    "PART BASS",
    "PART RHYTHM",
    "Single",
    "DoubleGuitar",
    "DoubleBass",
    "DoubleRhythm",
    "PART DRUMS", "PART DRUMS_2X", "Drums",
    #"PART VOCALS", "HARM1", "HARM2", "HARM3",
    "PART KEYS", "Keyboard",
    "PART REAL_KEYS_X"
]

GuitarTracks = [
    "PART GUITAR",
    "PART BASS",
    "PART RHYTHM",
    "Single",
    "DoubleGuitar",
    "DoubleBass",
    "DoubleRhythm",
]

difficultyNames = [
        "Warmup",
        "Apprentice",
        "Solid",
        "Moderate",
        "Challenging",
        "Nightmare",
        "Impossible",
]

# Based on official instrument difficulty tier values.
scoreThresholds = { 
    "Guitar":   [139,176,221,267,333,409],
    "Bass":     [135,181,228,293,364,436],
    "Drums":    [124,151,178,242,345,448],
    "Vocals":   [132,175,218,279,353,427],
    "Keys":     [153,211,269,327,385,443],

    "ProGuitar":[150,208,267,325,384,442],
    "ProBass":  [150,208,267,325,384,442],
    "ProKeys":  [153,211,269,327,385,443],

    "Band":     [165,215,243,267,292,345]
}

score = {}
tracks = []

scoreNote       = {}
scoreSituation  = {}

# TODO: Score testing, literally all of it.
# TODO: Import vanilla RB3 files, determine scores.

# All notes have a base score, that is adjusted by modifier scores.
scoreNote["Normal"]     = 100

scoreNote["Chord"]      = 3
scoreNote["Broken"]     = 10

scoreNote["Sustain"]  = 2

scoreNote["Limb"]       = 2

# In certain situations, we want to adjust the score of all notes.
scoreSituation["Solo"] = 1
scoreSituation["Overdrive"] = -20
scoreSituation["Unison"] = -50


def muse_run(GameData = None):

    if GameData != None:
        joule_data.GameData = GameData

    if get_meta("TotalLength") == None:
        print("Muse needs to be ran with a processed GameData!")
        return False
        

    if joule_data.GameSource not in joule_data.GameSourceRBLike:
        print(f"{joule_data.GameSourceFull} is not a Rock Band style game! Muse will give you a estimation based on Rock Band standards.")

    joule_data.GameDataOutput.update( { "muse_difficulties":{} } )

    for part in joule_data.TracksFound:
        if part in ValidTracks:
            muse_check(part)
        pass
    pass

pass


def muse_check(part:str):
    
    noteLength64 = joule_data.GameDataFile.ticks_per_beat / 16
    noteLength32 = noteLength64 * 2
    noteLength16 = noteLength64 * 4

    sustainLimit    = get_meta('TicksSustainLimit')
    sustainMinimum  = get_meta('SustainMinimum')

    base = get_source_data()
    diffHighest     = base.diff_highest


    currentInstrument = None

    if part in ( "PART DRUMS", "PART DRUMS_2X", "Drums"):
        currentInstrument = "Drums"
    elif part in GuitarTracks:
        currentInstrument = "Guitar"
    elif part in ( "PART VOCALS", "HARM1", "HARM2", "HARM3"):
        currentInstrument = "Vocals"
    elif part in ( "PART KEYS", "Keyboard" ):
        currentInstrument = "Keys"
    elif part.startswith("PART REAL_KEYS"):
        currentInstrument = "ProKeys"
    pass

    if currentInstrument != None:
        print(f"Analysing difficulty for {part}...")

        score.update( { } )
        
        # Note grabbing
        if currentInstrument == "ProKeys":
            toFind = "note"
        else:
            toFind = f"{diffHighest}"
        pass

        notesOn     = get_data_indexes("trackNotesOn",part,toFind)
        notesOff    = get_data_indexes("trackNotesOff",part,toFind)
        notesAll    = sorted( set( notesOn + notesOff ) )

        currentPosition = 0
        currentNotes = 0

        lastNoteOn = 0
        lastNoteOff = 0

        for note in notesAll:

            while note < joule_data.SecondsList[currentPosition]:
                currentPosition += 1

            if note in notesOff:
                currentNotes -= notesOff.count(note)

                if currentNotes == 0:
                    lastNoteOff = note

                    if lastNoteOff - lastNoteOn > sustainLimit:
                        lastNoteWasSustain = True
                    pass
                pass
            pass

            if note in notesOn:

                if currentNotes == 0:
                    lastNoteOn = note
                pass

                currentNotes += notesOn.count(note)
            pass

        pass

        output_add("muse_difficulties", f"{part} | {difficultyNames[0]} | {0}")

    pass
pass