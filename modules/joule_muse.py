'''
Muse is an assistant tool for Joule to automatically determine
the difficulty tiers of the GameData created by Joule.

This is incomplete, and will never be a perfect tool.

'''

import joule_data
import os

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
    "PART RHYTHM",
    "Single",
    "DoubleGuitar",
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

difficultyIcons = [
        "○○○○○",
        "◉○○○○",
        "◉◉○○○",
        "◉◉◉○○",
        "◉◉◉◉○",
        "◉◉◉◉◉",
        "●●●●●",
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
scoreMultiplierOffset = {}

# TODO: Score testing, literally all of it.
# TODO: Import vanilla RB3 files, determine scores.
    # Addendum: RB3 Tiers are actually plain wrong, 

# Base score per each whole number of NPS.
scoreNPS                = 80

# All notes have a base score, that is adjusted by modifier scores.
scoreNote["Normal"]     = 0.1
scoreNote["Kick"]       = 0.15
scoreNote["Repeat"]     = -20
scoreNote["Pattern"]     = -20

scoreNote["Chord"]      = 0.1
scoreNote["Broken"]     = 0.3

scoreNote["Sustain"]    = 0.005

scoreNote["Limb"]       = 1

# In certain situations, we want to adjust the score of all notes.
scoreSituation["Solo"] = 1
scoreSituation["Overdrive"] = -20
scoreSituation["Unison"] = -50

scoreMultiplierOffset["Drums"] = 0.60


def muse_run(GameData = None):

    if GameData != None:
        joule_data.GameData = GameData

    if get_meta("TotalLength") == None:
        joule_print("Muse needs to be ran with a processed GameData!")
        return False
        

    if joule_data.GameSource not in joule_data.GameSourceRBLike:
        joule_print(f"{joule_data.GameSourceFull} is not a Rock Band style game! Muse will give you a estimation based on Rock Band standards.")

    joule_data.GameDataOutput.update( { "muse_difficulties":{} } )

    joule_print(f"Analysing difficulties...\n")

    for part in joule_data.TracksFound:
        if part in ValidTracks:
            muse_check(part)
        pass
    pass

pass


def muse_check(part:str):
    
    noteLength64 = joule_data.TicksPerBeat / 16
    noteLength32 = noteLength64 * 2
    noteLength16 = noteLength64 * 4

    sustainLimit    = get_meta('TicksSustainLimit')
    sustainMinimum  = get_meta('SustainMinimum')

    base = get_source_data()
    diffHighest     = base.diff_highest
    totalLength     = get_meta('TotalLength')

    tierKnown           = None
    gameDataDirectory   = os.path.dirname(joule_data.GameDataLocation)

    partToFind          = None

    currentInstrument = None

    if part in ( "PART DRUMS", "PART DRUMS_2X", "Drums"):
        currentInstrument = "Drums"
    elif part in GuitarTracks:
        currentInstrument = "Guitar"
    elif part in ( "PART VOCALS", "HARM1", "HARM2", "HARM3"):
        currentInstrument = "Vocals"
    elif part in ( "PART KEYS", "Keyboard" ):
        currentInstrument = "Keys"
    elif part in ( "PART BASS", "DoubleBass" ):
        currentInstrument = "Bass"
    elif part.startswith("PART REAL_KEYS"):
        currentInstrument = "ProKeys"
    pass

    if currentInstrument != None:

        #joule_print(f"{part}")

        if currentInstrument == "Guitar":
            partToFind = "diff_guitar"
            partNotes = base.notes_lane
        elif currentInstrument == "Drums":
            partToFind = "diff_drums"
            partNotes = base.notes_pads
        elif currentInstrument == "ProKeys":
            partToFind = "diff_keys_real"
            partNotes = None
        elif currentInstrument == "Keys":
            partToFind = "diff_keys"
            partNotes = base.notes_lane
        elif currentInstrument == "Bass":
            partToFind = "diff_bass"
            partNotes = base.notes_lane
        elif currentInstrument == "Vocals":
            partToFind = "diff_vocals"
            partNotes = None

        try:
            _temp = open(gameDataDirectory + "/song.ini", mode="r")
            _tempLines = _temp.readlines()

            for line in _tempLines:
                lineGroups = line_groups(line)

                if lineGroups != None:

                    keyCheck = lineGroups[0].strip().lower()
                    
                    if partToFind == keyCheck:
                        tierKnown = int(lineGroups[1].strip())
                        if tierKnown == -1:
                            tierKnown = None
                        pass
                    pass

                pass

        except OSError:
            pass
        pass
        
        
        # Note grabbing
        if currentInstrument == "ProKeys":
            toFind = "note"
        else:
            toFind = f"{diffHighest}"
        pass

        notesOn     = get_data_indexes("trackNotesOn",part,toFind)
        notesOff    = get_data_indexes("trackNotesOff",part,toFind)
        notesAll    = sorted( set( notesOn + notesOff ) )

        if len(notesOn) < 2:
            return

        score.update( { f"{part}":[] } )

        currentNotes = 0
        currentPosition = 0

        lastNoteOn = 0
        lastNoteOff = 0


        _score          = []
        _nps            = []
        scoreSeconds    = []

        noteMask = ""
        noteMaskSame    = 0

        noteMaskPattern = []
        noteMaskPatternTemp = []

        for index in range(totalLength):
            _score.append(0)

        for index in range(len(joule_data.SecondsList)):
            scoreSeconds.append(0)
            _nps.append(0)
            

        for note in notesAll:

            if note in notesOff:
                currentNotes -= notesOff.count(note)

                if currentNotes == 0:
                    lastNoteOff = note

                    if lastNoteOff - lastNoteOn > sustainLimit:
                        for ind in range(lastNoteOn, lastNoteOff):
                            _score[ind] += scoreNote["Sustain"]
                        pass
                    pass

                pass
            pass

            if note in notesOn:

                if partNotes != None:
                    
                    _noteMask = ""
                    for _noteType in partNotes:
                        if get_note_on(part,f"{toFind}_{_noteType}",note):
                            _noteMask += "1"
                        else:
                            _noteMask += "0"
                        pass
                    pass

                    for _noteType in base.notes_kick:
                        if get_note_on(part,f"{toFind}_{_noteType}",note):
                            _noteMask += "1"
                        else:
                            _noteMask += "0"
                        pass
                    pass

                    if _noteMask != noteMask:
                        noteMask = _noteMask
                        noteMaskSame = 0
                        '''
                        if noteMaskPatternTemp != noteMaskPattern:
                            noteMaskPattern = noteMaskPatternTemp
                        elif len(noteMaskPatternTemp) > 2:
                            _score[note] += scoreNote["Pattern"] * min(len(noteMaskPattern), 10)
                            #joule_print(f"Pattern Found \n{noteMaskPattern}")
                            noteMaskPatternTemp = []
                        '''
                    else:
                        noteMaskSame += 1
                        _score[note] += ( scoreNote["Repeat"] * min(noteMaskSame, 4) )
                        #noteMaskPatternTemp.append(noteMask)
                    pass
                pass

                if currentNotes == 0:
                    lastNoteOn = note
                else:
                    _score[note] += scoreNote["Broken"]
                pass

                currentNotes += notesOn.count(note)

                for _noteType in base.notes_kick:
                    if get_note_on(part,f"{toFind}_{_noteType}",note):
                        _score[note] += scoreNote["Kick"]
                    pass
                pass
            
                while index > joule_data.SecondsList[currentPosition]:
                    if currentPosition < len(joule_data.SecondsList)  - 1:
                        currentPosition += 1
                    else:
                        break
                    pass

                _nps[currentPosition] += 1

                if currentNotes > 1:

                    noteType = None

                    if currentInstrument == "Drums":
                        noteType = "Limb"
                    
                    if currentInstrument == "Guitar":
                        noteType = "Chord"

                    if noteType != None:
                        _score[note] += scoreNote[noteType] * currentNotes
                pass

            pass

        pass


        

        currentPosition = 0

        for index, scoreAt in enumerate(_score):

            while index > joule_data.SecondsList[currentPosition]:
                if currentPosition < len(joule_data.SecondsList)  - 1:
                    currentPosition += 1
                else:
                    break
                pass
            pass

            scoreSeconds[currentPosition] += scoreAt

        pass

        preScoreSeconds = scoreSeconds
        scoreSeconds    = []

        numOfEmptySeconds = 0
        for index, scoreAt in enumerate(preScoreSeconds):
            if scoreAt == 0:
                numOfEmptySeconds += 1
            else:
                numOfEmptySeconds = 0

            if numOfEmptySeconds < 6:
                scoreSeconds.append(scoreAt)
            pass
        pass


        _rawScore   = sum(scoreSeconds)

        _averageScore = sum(scoreSeconds) / len(scoreSeconds)

        if currentInstrument == "Drums":
            _averageScore = _averageScore * scoreMultiplierOffset["Drums"]

        _preNPS     = sum(_nps) / len(scoreSeconds)

        _calcScoreNPS   = scoreNPS * _preNPS

        # Weigh the length of the song against drums
        if currentInstrument == "Drums":
            _calcScoreNPS = _calcScoreNPS * ( 1 + ( len(scoreSeconds) * 0.0005 )  )

        _finalScore     = _calcScoreNPS + _averageScore

        _finalNPS   = cleaner_decimal(_preNPS)

        _tempDiff   = 0

        for index, diff in enumerate(scoreThresholds[currentInstrument]):
            if _finalScore > diff:
                _tempDiff = index + 1
            else:
                continue
            pass

        strDiff = str(_tempDiff)


        if tierKnown != None:
            strDiff += f" | Known: {tierKnown}"

        _output = f"{part} | {strDiff} | {difficultyIcons[_tempDiff]} | {difficultyNames[_tempDiff]}\n{cleaner_decimal(_finalNPS)} NPS\n{ cleaner_decimal(_averageScore) } Average Score | {cleaner_decimal(_calcScoreNPS)} Calculated NPS Score\n{cleaner_decimal(_finalScore)} Final Score\n"
        joule_print(_output)

        _outputFile = f"{part} | {strDiff} | {cleaner_decimal(_finalNPS)} NPS | {cleaner_decimal(_finalScore)} Score"
        output_add("muse_difficulties", f"{_outputFile}")

    pass
pass
