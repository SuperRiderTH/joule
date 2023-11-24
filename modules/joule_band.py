# This is the file for Band related games, for example:
# Rock Band 3, Phase Shift, Clone Hero.

import joule_data
import math
import re
import mido

from joule_system import *
from joule_band_handlers import *


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

# Functions
# ========================================


def process_time_signature( ticks:int, numerator:int, denominator:int ):

    #print(f"Found {numerator}/{denominator} at {ticks}.")

    global time_signature_last_position
    global time_signature_last_measure
    global last_time_signature_num
    global last_time_signature_denom

    trackNotesMeta["meta","time_signature_num",ticks] = numerator
    trackNotesMeta["meta","time_signature_denom",ticks] = denominator

    # We need to manually keep track of time signature changes
    # since we do not have an easy way to do that here.
    time_signature_time.append(ticks)

    tempPosition = ticks - time_signature_last_position

    ticks_per_measure = ( joule_data.TicksPerBeat / last_time_signature_denom ) * last_time_signature_num

    tempPosition = (tempPosition / ticks_per_measure) / 4

    time_signature_last_measure     = time_signature_last_measure + tempPosition
    time_signature_last_position    = ticks
    last_time_signature_num         = numerator
    last_time_signature_denom       = denominator

    time_signature_measure.append( time_signature_last_measure)
pass

def section_read( line_start:int ):

    inSection = False
    sectionData = []

    sectionName = re.search(r"(?:\ *)(?:\[+)(.+)(?:\])", joule_data.GameDataFile[line_start]).groups()[0]

    print("Found " + sectionName + "...")
    joule_data.Tracks.append(sectionName)

    if sectionName in joule_data.GameData["sections"]:
        output_add("issues_critical",f"Duplicate section '{sectionName}' found! This duplicate section will not be processed.")
        return

    lineIndex = line_start

    for i in range(lineIndex, len(joule_data.GameDataFile)):

        line = joule_data.GameDataFile[i]

        if line.strip().startswith("{") or line.strip().startswith('['):

            if inSection == True:
                print(f"Error! Section '{sectionName}' ends early at line {i+1}!")
                return
            else:
                if line.strip().startswith("{"):
                    inSection = True
                    sectionData = []
                pass
            pass
        elif line.strip().startswith("}"):
            joule_data.GameData["sections"][sectionName] = sectionData
            #print(sectionData)
            return
        else:
            sectionData.append(line.strip())
        pass
    pass
pass


def initialize_band():

    global notename_array, notesname_instruments_array

    global time_signature_measure, time_signature_time
    global time_signature_last_position, time_signature_last_measure
    global last_time_signature_num, last_time_signature_denom

    global trackNotesOn, trackNotesOff, trackNotesMeta, trackNotesLyrics
    trackNotesOn, trackNotesOff, trackNotesMeta, trackNotesLyrics = {}, {}, {}, {}

    time_signature_measure, time_signature_time = [], []
    time_signature_last_position, time_signature_last_measure = 0, 0
    last_time_signature_num, last_time_signature_denom = 4, 4

    base = get_source_data()

    notesname_instruments_array = base.notesname_instruments_array
    notename_array = base.notename_array
    diff_array = base.diff_array
    notes_lane = base.notes_lane

    # MIDI Processing
    # ========================================
    if joule_data.GameDataFileType == "MIDI":

        joule_data.TicksPerBeat = joule_data.GameDataFile.ticks_per_beat # type: ignore

        output_add("debug_1",f"ticksPerBeat: {joule_data.TicksPerBeat}")

        # Rock Band expects 480 ticks per QN.
        # This should not have made it through Magma, but just in case.
        if joule_data.GameSource == "rb3" or joule_data.GameSource == "rb2":
            if joule_data.TicksPerBeat != 480:
                output_add("issues_critical", "Ticks per Quarter Note is not 480.")
            pass
        pass


        # It is possible to specify the length of a note needed
        # in order for it to be a sustain. Rock Band uses a 1/16
        # note by default, but we need to calculate the length
        # needed if it is specified.
        WhammyCutoff = get_meta("WhammyCutoff")

        if WhammyCutoff != None:
            write_meta("TicksSustainLimit", joule_data.TicksPerBeat * WhammyCutoff)
        else:
            if joule_data.GameSource in joule_data.GameSourceRBLike:
                write_meta("TicksSustainLimit", joule_data.TicksPerBeat / 4)
            else:
                if joule_data.GameSource == "ch":
                    factor = 0.45
                elif joule_data.GameSource == "ghwtde":
                    factor = 0.5
                pass
                
                write_meta("TicksSustainLimit", joule_data.TicksPerBeat * factor)
            pass
        pass

        output_add("debug_1",f"TicksSustainLimit: {get_meta('TicksSustainLimit')}")

        # Track processing
        for i, track in enumerate(joule_data.GameDataFile.tracks): # type: ignore
            trackTime           = 0
            unknownNotesSeen    = []

            last_time_signature_num        = 4
            last_time_signature_denom      = 4

            #print("Found " + track.name + "...")
            joule_data.Tracks.append(track.name)

            if track.name in notesname_instruments_array:
                if track.name in joule_data.TracksFound:
                    output_add("issues_critical",f"Duplicate track '{track.name}' found! This duplicate track will not be processed.")
                    continue
                else:
                    joule_data.TracksFound.append(track.name)
                pass
            pass

            
            lastSeenTime = 0

            # Process all MIDI messages.
            for msg in track:
                trackTime += msg.time
                
                # Set the note name.
                if msg.type == 'note_on' or msg.type == 'note_off':
                    currentNoteName = str(msg.note)

                    if track.name in notesname_instruments_array:
                        _tempName = notesname_instruments_array[track.name]

                        # Translate the name of the note, if we have it.
                        if msg.note in notename_array[_tempName]:
                            currentNoteName = notename_array[_tempName][msg.note]
                        else:
                            if msg.type == 'note_on':
                                output_add("issues_critical",f"{track.name} | Unknown MIDI Note '{str(msg.note)}' found!")
                                unknownNotesSeen.append(msg.note)
                                lastSeenTime = trackTime
                                pass
                            elif msg.type == 'note_off':
                                if msg.note in unknownNotesSeen:
                                    unknownNotesSeen.remove(msg.note)
                                    print(f"Length: {trackTime - lastSeenTime}")
                                else:
                                    output_add("issues_critical",f"{track.name} | Unknown MIDI Note Off '{str(msg.note)}' found!")
                                pass
                            pass
                        pass
                    pass
                pass

                if msg.type == 'note_on':
                    # Check for 0 velocity notes,
                    # as Onyx and other MIDI devices use this for off notes.
                    if msg.velocity == 0:
                        trackNotesOff[ track.name, currentNoteName, trackTime ] = True
                    else:
                        trackNotesOn[ track.name, currentNoteName, trackTime ] = True
                    pass
                    output_add("debug_4",f"{track.name} | {currentNoteName} | {trackTime}")

                elif msg.type == 'note_off':
                    trackNotesOff[track.name, currentNoteName, trackTime] = True

                elif msg.type == 'text':
                    try:
                        len( trackNotesMeta[track.name, "text", trackTime] )
                    except:
                        trackNotesMeta[track.name, "text", trackTime] = [ msg.text ]
                    else:
                        trackNotesMeta[track.name, "text", trackTime].append(msg.text)
                    pass

                    if track.name == "EVENTS":
                        try:
                            len(trackNotesMeta["meta","events",trackTime])
                        except:
                            trackNotesMeta["meta","events",trackTime] = [ msg.text ]
                        else:
                            trackNotesMeta["meta","events",trackTime].append(msg.text)
                        pass
                    pass

                elif msg.type == 'lyrics':
                    try:
                        len( trackNotesLyrics[track.name, "lyrics", trackTime] )
                    except:
                        trackNotesLyrics[track.name, "lyrics", trackTime] = msg.text
                    else:
                        output_add("issues_critical", f"{track.name} | Multiple Lyrics found at the same position.")
                    pass
                    
                elif msg.type == 'time_signature':
                    process_time_signature(trackTime, msg.numerator, msg.denominator)

                elif msg.type == 'set_tempo':
                    trackNotesMeta["meta","tempo",trackTime] = msg.tempo

                elif msg.type == 'sysex':
                    try:
                        len(trackNotesMeta[track.name,"sysex",trackTime])
                    except:
                        trackNotesMeta[track.name,"sysex",trackTime] = [ msg.data ]
                    else:
                        trackNotesMeta[track.name,"sysex",trackTime].append(msg.data)
                    pass

                    # If we find tap note modifiers, we want to translate that.
                    if msg.data[5] == 4:
                        if msg.data[6] == 1:
                            trackNotesOn[ track.name, "tap", trackTime ] = True
                            #print("Tap On")
                        if msg.data[6] == 0:
                            trackNotesOff[ track.name, "tap", trackTime ] = True
                            #print("Tap Off")
                    else:
                        pass
                        #print(f"{msg.data}")

                elif msg.type == 'end_of_track':
                    trackNotesMeta[track.name,"length",0] = trackTime
                    continue
                pass
            pass

            # Check to see if we found the length. If we didn't, we write it.
            try:
                len(trackNotesMeta[track.name,"length",0])
            except:
                trackNotesMeta[track.name,"length",0] = trackTime
            pass

            output_add("debug_2",f"{track.name} Length: {trackTime}")

            if get_meta("TotalLength") != None:
                if get_meta("TotalLength") < trackTime:
                    write_meta("TotalLength", trackTime)
                pass
            else:
                write_meta("TotalLength", trackTime)
            pass
        pass

    pass


    # Chart Processing
    # ========================================
    if joule_data.GameDataFileType == "CHART":

        notename_chart_notes = base.notename_chart_notes
        notename_chart_phrase = base.notename_chart_phrase

        # Parse the .chart, obtain all the section data.

        for index, line in enumerate(joule_data.GameDataFile):
            # We don't want zero width spaces here. Get rid of them.
            if chr(65279) in line:
                joule_data.GameDataFile[index] = line.replace(chr(65279), '')
                line = joule_data.GameDataFile[index]

            # If we find a section, read the info.
            test = None

            if "=" not in line:
                test = re.search(r"(?:\ *)(?:\[+)(.+)(?:\])", line)

            if test != None:
                section_read(index)
            pass

        pass

        # Translate the chart into our format for processing.

        # First we need the notes per tick that this file uses,
        # so we grab that from the Song section.
        _songData = joule_data.GameData["sections"]["Song"]

        joule_data.TicksPerBeat = 192

        for line in _songData:
            _tempGroup = line_groups(line)
            if _tempGroup[0] == "Resolution":
                joule_data.TicksPerBeat = int(_tempGroup[1])
            pass
        pass

        WhammyCutoff = get_meta("WhammyCutoff")

        if WhammyCutoff != None:
            write_meta("TicksSustainLimit", joule_data.TicksPerBeat * WhammyCutoff)
        else:

            if joule_data.GameSource == "ch":
                factor = 0.45
            else:
                factor = 0.5

            write_meta("TicksSustainLimit", joule_data.TicksPerBeat * factor)
            
        pass

        output_add("debug_1",f"ticksPerBeat: {joule_data.TicksPerBeat}")
        output_add("debug_1",f"TicksSustainLimit: {get_meta('TicksSustainLimit')}")

        # Events parsing
        _songData = joule_data.GameData["sections"]["Events"]

        for line in _songData:
            lineGroups = line_groups(line)

            lineKey     = lineGroups[0]
            lineValue   = lineGroups[1]

            if lineValue.startswith("E"):
                _tempLine = lineValue.lstrip("E")
                _tempLine = _tempLine.strip()
                _tempLine = _tempLine.strip("\"")

                if _tempLine.startswith("section"):
                    _tempLine = _tempLine.lstrip("section")
                    _tempLine = _tempLine.strip()
                    
                    try:
                        len(trackNotesMeta["meta","events",int(lineKey)])
                    except:
                        trackNotesMeta["meta","events",int(lineKey)] = [ _tempLine ]
                    else:
                        trackNotesMeta["meta","events",int(lineKey)].append(_tempLine)
                    pass

                elif _tempLine.startswith("lyric"):
                    _tempLine = _tempLine.lstrip("lyrics")
                    _tempLine = _tempLine.strip()

                    # We are creating artificial notes for vocals to display lyrics.
                    # .chart doesn't support Vocals, so we are okay to do this.
                    trackNotesLyrics["PART VOCALS","lyrics",int(lineKey)] = _tempLine
                    trackNotesOn["PART VOCALS", "note_c1", int(lineKey)] = True
                    trackNotesOff["PART VOCALS", "note_c1", int(lineKey) + 1] = True

                elif _tempLine.startswith("phrase_start"):
                    trackNotesOn["PART VOCALS", "phrase_p1", int(lineKey)] = True

                elif _tempLine.startswith("phrase_end"):
                    trackNotesOff["PART VOCALS", "phrase_p1", int(lineKey)] = True

                else:
                    try:
                        len(trackNotesMeta["meta","events",int(lineKey)])
                    except:
                        trackNotesMeta["meta","events",int(lineKey)] = [ _tempLine ]
                    else:
                        trackNotesMeta["meta","events",int(lineKey)].append(_tempLine)
                    pass
                pass
            else:
                output_add("issues_critical", f"Events | {lineKey} | Unknown Event '{lineValue}' found!")
            pass
        pass

        # Instrument Processing
        for i, track in enumerate(joule_data.GameData["sections"]):

            # We need both the full name, and single letter for the difficulties.
            diff_keys   = list(diff_array.keys())
            diff_values = list(diff_array.values())

            part_name = ""

            for line in joule_data.GameData["sections"][track]:
                lineGroups = line_groups(line)

                lineKey     = lineGroups[0]
                lineValue   = lineGroups[1]

                if track == "SyncTrack":
                    _tempData = lineValue.split(" ")

                    noteType    = _tempData[0]
                    noteValue   = _tempData[1]

                    if noteType == "A":
                        # Tempo anchors are not necessary for gameplay, and is just used for chart editing.
                        output_add("debug_1",f"{track} | {lineKey} | Tempo position anchors are not supported.")

                    elif noteType == "B":
                        trackNotesMeta["meta","tempo",int(lineKey)] = mido.bpm2tempo((float(noteValue) / 1000))
                        
                    elif noteType == "TS":
                        num = int(noteValue)

                        # The default denominator is "2", but check if there is one specified.
                        if len(_tempData) == 3:
                            den = int(_tempData[2])
                        else:
                            den = 2
                        pass

                        # Time Signatures in .chart use an exponent for the denominator.
                        process_time_signature( int(lineKey), num, (2 ** den) )

                    else:
                        output_add("issues_critical",f"{track} | {lineKey} | Unknown Note Type '{str(noteType)}' found!")
                    pass

                # We start reading with difficulties, because that is how they start.
                for i, diff_name in enumerate(diff_values):
                    diff = diff_keys[i]

                    if track.startswith(diff_name):
                        part_name = track.replace(diff_name, "")

                        # We can have duplicates now, unlike in MIDI checking.
                        if part_name in notesname_instruments_array:
                            if part_name not in joule_data.TracksFound:
                                joule_data.TracksFound.append(part_name)
                            pass

                            # Store the type of instrument we are, for example "5LANE".
                            _tempName = notesname_instruments_array[part_name]

                            _tempData = lineValue.split(" ")

                            noteType    = _tempData[0]
                            noteValue   = _tempData[1]

                            # Note and Special Phrase checking
                            if noteType == "N" or noteType == "S":

                                if len(_tempData) != 3:
                                    output_add("issues_critical",f"{track} | {lineKey} | Invalid Note found!")
                                    continue

                                noteValue   = int(noteValue)
                                noteLength  = int(_tempData[2])

                                # We don't want 0 length notes here,
                                # overriding it to 1 should be fine.
                                noteLength  = max(noteLength, 1)

                                # Get the note names depending on the note type.
                                if noteType == "N":
                                    notenames = notename_chart_notes
                                if noteType == "S":
                                    notenames = notename_chart_phrase


                                if noteValue in notenames[_tempName]:

                                    noteName = notenames[_tempName][noteValue]

                                    # If it is an played note, we give it a difficulty.
                                    if noteType == "N":
                                        noteName = f"{diff}_{noteName}"
                                    pass

                                    trackNotesOn[part_name, noteName, int(lineKey)] = True
                                    trackNotesOff[part_name, noteName, int(lineKey) + noteLength] = True

                                    length = int(lineKey) + noteLength
                                    trackNotesMeta[part_name, "length", 0] = length

                                else:
                                    # Yes, this error outputs in tick time.
                                    output_add("issues_critical",f"{track} | {lineKey} | Unknown Note '{str(noteValue)}' found!")
                                pass

                            # Events in instruments
                            elif noteType == "E":

                                if noteValue == "solo":
                                    trackNotesOn[part_name, "solo", int(lineKey)] = True

                                elif noteValue == "soloend":
                                    trackNotesOff[part_name, "solo", int(lineKey)] = True

                                elif noteValue == "end":
                                    pass

                                else:
                                    try:
                                        len(trackNotesMeta[part_name,"text",int(lineKey)])
                                    except:
                                        trackNotesMeta[part_name,"text",int(lineKey)] = [ noteValue ]
                                    else:
                                        trackNotesMeta[part_name,"text",int(lineKey)].append(noteValue)
                                    pass
                                pass

                            else:
                                output_add("issues_critical",f"{track} | {lineKey} | Unknown Note Type '{str(noteType)}' found!")
                            pass
                        pass
                    pass
                pass
            pass
        pass

        for part_name in joule_data.TracksFound:
            length = trackNotesMeta[part_name, "length", 0]
            output_add("debug_2",f"{part_name} Length: {length}")

            if get_meta("TotalLength") != None:
                if get_meta("TotalLength") < length:
                    write_meta("TotalLength", length)
                pass
            else:
                write_meta("TotalLength", length)
            pass

        pass

    pass

    #print ("========================================")
    #print(trackNotesOn)
    #print ("========================================")
    #print(trackNotesOff)
    #print ("========================================")
    #print(trackNotesLyrics)
    #print ("========================================")
    #print(trackNotesMeta)

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
    if joule_data.GameDataFileType == "MIDI":

        for track in joule_data.TracksFound:
            try:
                len(get_data_indexes("trackNotesMeta", track, "sysex"))
            except:
                pass
            else:

                notesSysEx = get_data_indexes("trackNotesMeta", track, "sysex")

                if len(notesSysEx) > 0:
                    print(f"SysEx Messages detected in {track}, modifying notes...")

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
                                    trackNotesOn[ track, f"{diff}_{"open"}", note ] = True
                                pass
                                if get_note_off( track, f"{diff}_{noteLane}", note):
                                    trackNotesOff[ track, f"{diff}_{noteLane}", note ] = False
                                    trackNotesOff[ track, f"{diff}_{"open"}", note ] = True
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

    generate_seconds()

    output_add("info",f"Length: {format_seconds(get_meta('TotalLength'))}")
    output_add("debug_1",f"TotalLength: {get_meta('TotalLength')}")

    return joule_data.GameData
pass

def process_lyrics():

    #print("Extracting lyrics...")

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
            #print(phraseText.strip())

    pass

    joule_data.GameData["phrases"] = phrases

    return

pass

def process_events():

    #print("Extracting events...")

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


def validate_open_notes(partname:str):
    base = get_source_data()
    diff_array = base.diff_array

    # If we are using MIDI as our base, we want to check to make sure
    # we are using ENHANCED_OPENS.

    if joule_data.GameDataFileType == "MIDI":
        enhancedOpens = False

        try:
            len( trackNotesMeta[partname, "text", 0] )
        except:
            enhancedOpens = False
        else:
            if "[ENHANCED_OPENS]" in trackNotesMeta[partname, "text", 0]:
                enhancedOpens = True
                return
            pass
        pass

        for diff in diff_array:
            if len( get_data_indexes( "trackNotesOn", partname, f"{diff}_open" ) ) > 0:
                if enhancedOpens == False:
                    output_add("issues_critical", f"{partname} | Open notes found without ENHANCED_OPENS on {diff_array[diff]}.")
                pass
            pass
        pass

    pass
pass