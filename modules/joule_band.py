# This is the file for Band related games, for example:
# Rock Band 3, Phase Shift, Clone Hero.

import joule_data
import math
import re

from joule_band_handlers import *

try:
    import mido
except ImportError:
    pass

try:
    from reaper_python import *
except ImportError:
    pass


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

    #joule_print(f"Found {numerator}/{denominator} at {ticks}.")

    global time_signature_last_position
    global time_signature_last_measure
    global last_time_signature_num
    global last_time_signature_denom
    global trackNotesMeta

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

    joule_print("Found " + sectionName + "...")
    joule_data.Tracks.append(sectionName)

    if sectionName in joule_data.GameData["sections"]:
        output_add("issues_critical",f"Duplicate section '{sectionName}' found! This duplicate section will not be processed.")
        return

    lineIndex = line_start

    for i in range(lineIndex, len(joule_data.GameDataFile)):

        line = joule_data.GameDataFile[i]

        if line.strip().startswith("{") or line.strip().startswith('['):

            if inSection == True:
                joule_print(f"Error! Section '{sectionName}' ends early at line {i+1}!")
                return
            else:
                if line.strip().startswith("{"):
                    inSection = True
                    sectionData = []
                pass
            pass
        elif line.strip().startswith("}"):
            joule_data.GameData["sections"][sectionName] = sectionData
            #joule_print(sectionData)
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

            #joule_print("Found " + track.name + "...")
            output_add("debug_3",f"Found {track.name}")
            joule_data.Tracks.append(track.name)

            if track.name in notesname_instruments_array:
                if track.name in joule_data.TracksFound:
                    output_add("issues_critical",f"Duplicate track '{track.name}' found! This duplicate track will not be processed.")
                    continue
                else:
                    joule_data.TracksFound.append(track.name)
                pass
            pass

            

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
                                pass
                            elif msg.type == 'note_off':
                                if msg.note in unknownNotesSeen:
                                    unknownNotesSeen.remove(msg.note)
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

                    # Enhanced Open checking.
                    if currentNoteName.endswith("_open")\
                    and not currentNoteName.startswith("animation_"):
                        try:
                            _enhanced = False
                            if "[ENHANCED_OPENS]" in trackNotesMeta[track.name, "text", 0]:
                                _enhanced = True
                        except:
                            pass
                        finally:
                            if _enhanced == False:
                                output_add("issues_critical", f"{track.name} | Open notes found without ENHANCED_OPENS on {diff_array[currentNoteName[0]]}.", True)
                        pass
                    pass

                elif msg.type == 'note_off':
                    trackNotesOff[track.name, currentNoteName, trackTime] = True

                elif msg.type == 'text' or msg.type == 'lyrics':

                    if msg.type == 'lyrics':
                        if track.name == "PART VOCALS" or track.name.startswith("HARM"):
                            try:
                                len( trackNotesLyrics[track.name, "lyrics", trackTime] )
                            except:
                                trackNotesLyrics[track.name, "lyrics", trackTime] = msg.text
                            else:
                                output_add("issues_critical", f"{track.name} | Multiple Lyrics found at the same position.")
                            pass
                        else:
                            if msg.text.startswith("[") and msg.text.endswith("]") and track.name == "EVENTS":
                                output_add("issues_critical", f"{track.name} | Event '{msg.text}' found as a Lyric in the EVENTS track.")
                            else:
                                output_add("issues_minor", f"{track.name} | Lyric '{msg.text}' found in a non-vocal track.")
                            pass

                            # Add this to the text data for the track, because this should be there instead of a lyric.
                            try:
                                len(trackNotesMeta[track.name, "text", trackTime])
                            except:
                                trackNotesMeta[track.name, "text", trackTime] = [ msg.text ]
                            else:
                                trackNotesMeta[track.name, "text", trackTime].append(msg.text)
                            pass
                        pass
                    else:
                        try:
                            len(trackNotesMeta[track.name, "text", trackTime])
                        except:
                            trackNotesMeta[track.name, "text", trackTime] = [ msg.text ]
                        else:
                            trackNotesMeta[track.name, "text", trackTime].append(msg.text)
                        pass
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
                            #joule_print("Tap On")
                        if msg.data[6] == 0:
                            trackNotesOff[ track.name, "tap", trackTime ] = True
                            #joule_print("Tap Off")
                    else:
                        pass
                        #joule_print(f"{msg.data}")

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
                        trackNotesMeta["meta","tempo",int(lineKey)] = bpm2tempo((float(noteValue) / 1000))
                        
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


    # REAPER Processing
    # ========================================
    if joule_data.GameDataFileType == "REAPER":

        last_time_signature_num        = 4
        last_time_signature_denom      = 4

        project_dump = []
        project_data = []
        project_data_track = []
        project_known_tracks = []

        # We have this variable just to make some functions
        # look nicer instead of using 0 everywhere.
        current_project = 0

        # Get the amount of items from REAPER.
        num_media_items = RPR_CountMediaItems(current_project)

        # Get the information from REAPER.
        for media_item in range(0, num_media_items):

            item = RPR_GetMediaItem(current_project, media_item)
            results = RPR_GetSetItemState(item, "", 1048576)

            track = RPR_GetMediaItem_Track(item)
            trackMuted = RPR_GetMediaTrackInfo_Value(track, "B_MUTE")

            if trackMuted == True:
                continue

            project_data.append(results[2])
            project_data_track.append(track)

            # Get the content of the track.
            project_dump.append("~START")

            project_dump.append(f"~TRACK: { RPR_GetMediaItem_Track(item)}")

            for line in results[2].splitlines():
                project_dump.append(line)

            project_dump.append("~END")

        pass

        if joule_data.Debug > 2:

            # Dump REAPER info to a file for reading.
            with open(joule_data.GameDataLocation + ".reaper-info.txt", "w", encoding="utf-8") as _file:

                for line in project_dump:
                    _file.write(line)
                    _file.write("\n")

                    if line == "~END":
                        _file.write("\n")

                _file.close()

            pass


        # Grab the Ticks Per Beat from the REAPER project.
        TicksPerBeat = -1

        # We are just going to go through all the items until we find one.
        for item in project_data:

            if TicksPerBeat != -1:
                break

            if "HASDATA 1" in item:
                for line in item.splitlines():
                    if "HASDATA 1" in line and "QN" in line:
                        TicksPerBeat = int(line.split()[2])
                        joule_data.TicksPerBeat = TicksPerBeat
                        break
                    pass
                pass
            pass

        pass

        output_add("debug_1",f"ticksPerBeat: {joule_data.TicksPerBeat}")

        # Rock Band expects 480 ticks per QN.
        if joule_data.GameSource == "rb3" or joule_data.GameSource == "rb2":
            if joule_data.TicksPerBeat != 480:
                output_add("issues_critical", "Ticks per Quarter Note is not 480.")
            pass
        pass


        # Sustain Limit calculation.
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


        project_bpm = 120
        project_time_signature_num = 4
        project_time_signature_denom = 4
        project_time_signature_location_time = 0


        # Get the beginning of the song's time signature and BPM.
        (NULL, NULL, project_time_signature_num, project_time_signature_denom, project_bpm) = RPR_TimeMap_GetTimeSigAtTime(0, 0, 0, 0, 0)
        #joule_print(project_bpm)

        process_time_signature(0, project_time_signature_num, project_time_signature_denom)
        trackNotesMeta["meta","tempo",0] = bpm2tempo(project_bpm)

        project_time_signature_next_time = RPR_TimeMap2_GetNextChangeTime(0,project_time_signature_location_time)

        while project_time_signature_next_time != -1:

            #joule_print(project_time_signature_next_time)
            (NULL, NULL, project_time_signature_num, project_time_signature_denom, project_bpm) = RPR_TimeMap_GetTimeSigAtTime(0, project_time_signature_next_time, 0, 0, 0)

            # Convert the time we are at to ticks for the note locations.
            _QN = RPR_TimeMap_timeToQN(project_time_signature_next_time)
            _ticks = int(_QN * joule_data.TicksPerBeat)

            process_time_signature(_ticks, project_time_signature_num, project_time_signature_denom)
            trackNotesMeta["meta","tempo",_ticks] = bpm2tempo(project_bpm)

            project_time_signature_next_time = RPR_TimeMap2_GetNextChangeTime(0,project_time_signature_next_time)
            #joule_print(f"{project_time_signature_num}/{project_time_signature_denom} - {project_bpm}")

        # Get the information from all the media items.
        for data_index, item in enumerate(project_data):

            trackTime           = 0
            unknownNotesSeen    = []

            current_part = None

            data_lines = item.splitlines()

            for index, line in enumerate(data_lines):

                if current_part == "SKIP_PART":
                    continue

                messageType = None
                noteText = None
                noteNumber = None

                # Text Events
                if line.lower().startswith("<x"):
                    note_parts = line.split()

                    trackTime += int(note_parts[1])

                    textData = decode_reaper_text( data_lines[index+1] )
                    noteText = textData[1]
                    messageType = "text"
                    #joule_print( textData )

                    # Track Detection
                    if textData[0] == 3:
                        messageType = "name"
                        output_add("debug_3",f"Found {textData[1]}")
                        joule_data.Tracks.append(textData[1])

                        current_track = project_data_track[data_index]

                        # Because multiple Media items can be on the same track,
                        # we need to see if we are working with the same one.
                        if textData[1] in notesname_instruments_array:
                            if textData[1] in joule_data.TracksFound:
                                for track in project_known_tracks:
                                    if track[0] == textData[1] and track[1] != current_track:
                                        output_add("issues_critical",f"Duplicate track '{textData[1]}' found! This duplicate track will not be processed.")
                                        current_part = "SKIP_PART"
                                    pass
                                pass
                            else:
                                project_known_tracks.append( [textData[1], current_track] )
                                joule_data.TracksFound.append(textData[1])
                                current_part = textData[1]
                            pass
                        else:
                            current_part = textData[1]
                        pass
                    pass

                    if textData[0] == 5:
                        messageType = "lyrics"
                    pass

                    if textData[0] == 80:
                        messageType = "sysex"
                    pass
                
                # Notes
                elif line.lower().startswith("e"):
                    note_parts = line.split()

                    trackTime += int( note_parts[1] )
                    noteNumber = int( note_parts[3], 16 )
                    noteVelocity = int( note_parts[4], 16 )

                    if note_parts[2].startswith("9"):
                        messageType = 'note_on'
                    if note_parts[2].startswith("8"):
                        messageType = 'note_off'

                    if messageType == 'note_on' and noteVelocity == 0:
                        messageType = 'note_off'


                    # Set the note name.
                    if messageType == 'note_on' or messageType == 'note_off':
                        currentNoteName = str( noteNumber )

                        if current_part in notesname_instruments_array:
                            _tempName = notesname_instruments_array[current_part]

                            # Translate the name of the note, if we have it.
                            if noteNumber in notename_array[_tempName]:
                                currentNoteName = notename_array[_tempName][noteNumber]
                            else:
                                if messageType == 'note_on':
                                    output_add("issues_critical",f"{current_part} | Unknown MIDI Note '{str(noteNumber)}' found!")
                                    unknownNotesSeen.append(noteNumber)
                                    pass
                                elif messageType == 'note_off':
                                    if noteNumber in unknownNotesSeen:
                                        unknownNotesSeen.remove(noteNumber)
                                    else:
                                        output_add("issues_critical",f"{current_part} | Unknown MIDI Note Off '{str(noteNumber)}' found!")
                                    pass
                                pass
                            pass
                        pass
                    pass
                pass


                if messageType != None:
                    if messageType == 'note_on':
                        trackNotesOn[ current_part, currentNoteName, trackTime ] = True

                        # Enhanced Open checking.
                        if currentNoteName.endswith("_open")\
                        and not currentNoteName.startswith("animation_"):
                            try:
                                _enhanced = False
                                if "[ENHANCED_OPENS]" in trackNotesMeta[current_part, "text", 0]:
                                    _enhanced = True
                            except:
                                pass
                            finally:
                                if _enhanced == False:
                                    output_add("issues_critical", f"{current_part} | Open notes found without ENHANCED_OPENS on {diff_array[currentNoteName[0]]}.", True)
                            pass
                        pass
                    elif messageType == 'note_off':
                        trackNotesOff[current_part, currentNoteName, trackTime] = True
                    elif messageType == 'text' or messageType == 'lyrics':

                        if messageType == 'lyrics':
                            if current_part == "PART VOCALS" or current_part.startswith("HARM"):
                                try:
                                    len( trackNotesLyrics[current_part, "lyrics", trackTime] )
                                except:
                                    trackNotesLyrics[current_part, "lyrics", trackTime] = noteText
                                else:
                                    output_add("issues_critical", f"{current_part} | Multiple Lyrics found at the same position.")
                                pass
                            else:
                                if noteText.startswith("[") and noteText.endswith("]") and current_part == "EVENTS":
                                    output_add("issues_critical", f"{current_part} | Event '{noteText}' found as a Lyric in the EVENTS track.")
                                else:
                                    output_add("issues_minor", f"{current_part} | Lyric '{noteText}' found in a non-vocal track.")
                                pass

                                # Add this to the text data for the track, because this should be there instead of a lyric.
                                try:
                                    len(trackNotesMeta[current_part, "text", trackTime])
                                except:
                                    trackNotesMeta[current_part, "text", trackTime] = [ noteText ]
                                else:
                                    trackNotesMeta[current_part, "text", trackTime].append(noteText)
                                pass
                            pass
                        else:
                            try:
                                len(trackNotesMeta[current_part, "text", trackTime])
                            except:
                                trackNotesMeta[current_part, "text", trackTime] = [ noteText ]
                            else:
                                trackNotesMeta[current_part, "text", trackTime].append(noteText)
                            pass
                        pass

                        if current_part == "EVENTS":
                            try:
                                len(trackNotesMeta["meta","events",trackTime])
                            except:
                                trackNotesMeta["meta","events",trackTime] = [ noteText ]
                            else:
                                trackNotesMeta["meta","events",trackTime].append(noteText)
                            pass
                        pass
                    elif messageType == 'sysex':

                        try:
                            len(trackNotesMeta[current_part,"sysex",trackTime])
                        except:
                            trackNotesMeta[current_part,"sysex",trackTime] = [ noteText ]
                        else:
                            trackNotesMeta[current_part,"sysex",trackTime].append(noteText)
                        pass

                        # If we find tap note modifiers, we want to translate that.
                        if noteText[5] == 4:
                            if noteText[6] == 1:
                                trackNotesOn[ current_part, "tap", trackTime ] = True
                                #joule_print("Tap On")
                            if noteText[6] == 0:
                                trackNotesOff[ current_part, "tap", trackTime ] = True
                                #joule_print("Tap Off")
                        else:
                            pass
                            #joule_print(f"{noteText}")
                        pass
                    pass
                pass
            pass

            # Check to see if we found the length. If we didn't, we write it.
            try:
                len(trackNotesMeta[current_part,"length",0])
            except:
                trackNotesMeta[current_part,"length",0] = trackTime
            pass

            output_add("debug_2",f"{current_part} Length: {trackTime}")

            if get_meta("TotalLength") != None:
                if get_meta("TotalLength") < trackTime:
                    write_meta("TotalLength", trackTime)
                pass
            else:
                write_meta("TotalLength", trackTime)
            pass

        pass


    pass

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
