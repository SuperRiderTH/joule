# This is the file for Band related games, for example:
# Rock Band 3, Phase Shift, Clone Hero.

import joule_data

from joule_band_handlers import *

from joule_parser_midi import joule_parse_midi
from joule_parser_chart import joule_parse_chart
from joule_parser_reaper import joule_parse_reaper


#trackNotes[track, note, time]
#trackNotes["PART DRUMS", "x_kick", 0] = True
trackNotesOn = {}
trackNotesOff = {}
trackNotesMeta = {}
trackNotesLyrics = {}

notesname_instruments_array = {}
notename_array = {}

time_signature_measure          = []
time_signature_time             = []

time_signature_last_position    = 0
time_signature_last_measure     = 0
last_time_signature_num        = 4
last_time_signature_denom      = 4

BrokenChordsAllowed     = False
LowerHOPOsAllowed       = False

# Functions
# ========================================

def initialize_band():


    # These variables need to be cleared for repeated runs.
    global notename_array, notesname_instruments_array

    global time_signature_measure, time_signature_time
    global time_signature_last_position, time_signature_last_measure
    global last_time_signature_num, last_time_signature_denom

    global trackNotesOn, trackNotesOff, trackNotesMeta, trackNotesLyrics
    trackNotesOn, trackNotesOff, trackNotesMeta, trackNotesLyrics = {}, {}, {}, {}

    time_signature_measure, time_signature_time = [], []
    time_signature_last_position, time_signature_last_measure = 0, 0
    last_time_signature_num, last_time_signature_denom = 4, 4

    # Parse the data.
    if joule_data.GameDataFileType == "MIDI":
        joule_parse_midi()

    if joule_data.GameDataFileType == "CHART":
        joule_parse_chart()

    if joule_data.GameDataFileType == "REAPER":
        joule_parse_reaper()
    
    
    #joule_print ("========================================")
    #joule_print(trackNotesOn)
    #joule_print ("========================================")
    #joule_print(trackNotesOff)
    #joule_print ("========================================")
    #joule_print(trackNotesLyrics)
    #joule_print ("========================================")
    #joule_print(trackNotesMeta)

    output_add("debug_4",f"{trackNotesOn}")
    output_add("debug_4",f"{trackNotesOff}")
    output_add("debug_4",f"{trackNotesLyrics}")
    output_add("debug_4",f"{trackNotesMeta}")

    joule_data.GameData["trackNotesOn"] = trackNotesOn
    joule_data.GameData["trackNotesOff"] = trackNotesOff
    joule_data.GameData["trackNotesLyrics"] = trackNotesLyrics

    try:
        len(joule_data.GameData["trackNotesMeta"])
    except:
        joule_data.GameData["trackNotesMeta"] = trackNotesMeta
    else:
        joule_data.GameData["trackNotesMeta"].update(trackNotesMeta)
    pass
    
    joule_data.GameData["tracks"] = joule_data.Tracks
    joule_data.GameData["tracksFound"] = joule_data.TracksFound

    # SysEx Event handling.
    if joule_data.GameDataFileType == "MIDI" or joule_data.GameDataFileType == "REAPER":
        patch_sysex()

    generate_seconds()

    output_add("info",f"Length: {format_seconds(get_meta('TotalLength'))}")
    output_add("debug_1",f"TotalLength: {get_meta('TotalLength')}")

    return joule_data.GameData
pass

def process_lyrics():

    #joule_print("Extracting lyrics...")

    indexesVocalsOn        = get_data_indexes("trackNotesOn", 'PART VOCALS', 'phrase')
    indexesVocalsOff       = get_data_indexes("trackNotesOff", 'PART VOCALS', 'phrase')
    indexesVocalsLyrics    = get_data_indexes("trackNotesLyrics", 'PART VOCALS', 'lyrics')

    phrases                = []
    lastTime               = 0

    for index, item in enumerate(indexesVocalsOn):

        # This is for P2 Phrase Markers, if we already checked this Phrase we want to skip it.
        if item == lastTime:
            continue
        else:
            lastTime = item
        pass

        phraseText             = ""

        # Pull out the vocal notes inbetween the start and end of Phrases.
        if index < len(indexesVocalsOff):
            for note in filter(lambda x:x >= item and x < indexesVocalsOff[index], indexesVocalsLyrics):
                tempText:str = joule_data.GameData["trackNotesLyrics"]["PART VOCALS","lyrics",note]

                tempText = tempText.replace("^","")
                tempText = tempText.replace("#","")

                if tempText == "+":
                    continue

                if tempText.endswith("-") or tempText.endswith("="):
                    tempText = tempText[:-1]
                else:
                    tempText += " "

                phraseText += tempText
            pass

            phrases.append(phraseText.strip())
            output_add("lyrics", phraseText.strip())
            #joule_print(phraseText.strip())

    pass

    joule_data.GameData["phrases"] = phrases

    return

pass

def process_events():

    #joule_print("Extracting events...")

    indexesEvents          = get_data_indexes("trackNotesMeta", 'meta', 'events')
    events                 = []

    for i in indexesEvents:
        _events = joule_data.GameData["trackNotesMeta"]["meta","events",i]

        for _event in _events:
            _event = _event.strip()

            if _event not in joule_data_rockband.events_ignore_list:

                if _event in joule_data_rockband.event_friendly_list:
                    _event = joule_data_rockband.event_friendly_list[_event]
                else:

                    # We are doing a quick check to see if anyone is using
                    # Rock Band style events, just not in brackets.
                    _tempEventCheck = f"[{_event}]"

                    if _tempEventCheck in joule_data_rockband.events_ignore_list:
                        continue

                    if _tempEventCheck in joule_data_rockband.event_friendly_list:
                        _event = joule_data_rockband.event_friendly_list[_tempEventCheck]
                    pass

                    _tempEventCheck = f"[prc_{_event}]"

                    if _tempEventCheck in joule_data_rockband.events_ignore_list:
                        continue

                    if _tempEventCheck in joule_data_rockband.event_friendly_list:
                        _event = joule_data_rockband.event_friendly_list[_tempEventCheck]
                    pass

                pass

                _tempEvent = f"{format_location(i)}: {_event}"

                events.append(_tempEvent)
                output_add("events", _tempEvent)
            pass
        pass
    pass

    joule_data.GameData["events"] = events

    return
pass

def patch_sysex():

    global trackNotesOn, trackNotesOff, trackNotesMeta, trackNotesLyrics

    base = get_source_data()

    notesname_instruments_array = base.notesname_instruments_array
    notename_array = base.notename_array
    diff_array = base.diff_array
    notes_lane = base.notes_lane

    for track in joule_data.TracksFound:
        try:
            len(get_data_indexes("trackNotesMeta", track, "sysex"))
        except:
            pass
        else:

            notesSysEx = get_data_indexes("trackNotesMeta", track, "sysex")

            if len(notesSysEx) > 0:
                joule_print(f"SysEx Messages detected in {track}, modifying notes...")

                inOpen = False

                for diff in diff_array:
                    notesOn     = get_data_indexes("trackNotesOn", track, diff)
                    notesOff    = get_data_indexes("trackNotesOff", track, diff)
                    notesAll    = sorted( set( notesOn + notesOff + notesSysEx ) )
                
                for note in notesAll:

                    if note in notesSysEx:
                        data = trackNotesMeta[track,"sysex",note]

                        for entry in data:
                            # Open Notes are 1, Starts with 1, Ends with 0.
                            if entry[5] == 1:
                                if entry[6] == 1:
                                    inOpen = True
                                if entry[6] == 0:
                                    inOpen = False
                                pass
                            pass
                        pass
                    pass

                    # Modify any notes that are in-between Open markers to be Open notes.
                    for noteLane in notes_lane:
                        if inOpen:
                            if get_note_on( track, f"{diff}_{noteLane}", note):
                                trackNotesOn[ track, f"{diff}_{noteLane}", note ] = False
                                trackNotesOn[ track, f"{diff}_{'open'}", note ] = True
                            pass
                            if get_note_off( track, f"{diff}_{noteLane}", note):
                                trackNotesOff[ track, f"{diff}_{noteLane}", note ] = False
                                trackNotesOff[ track, f"{diff}_{'open'}", note ] = True
                            pass
                        pass
                    pass

                pass

                # Since we are making changes, make sure to re-write this.
                joule_data.GameData["trackNotesOn"] = trackNotesOn
                joule_data.GameData["trackNotesOff"] = trackNotesOff
            pass
        pass
    pass
pass
