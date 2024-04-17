import joule_data
import joule_band

import re

from joule_band_handlers import *

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

# Chart Processing
# ========================================
def joule_parse_chart():

    trackNotesOn        = joule_band.trackNotesOn
    trackNotesOff       = joule_band.trackNotesOff
    trackNotesLyrics    = joule_band.trackNotesLyrics
    trackNotesMeta      = joule_band.trackNotesMeta

    base = get_source_data()

    notesname_instruments_array = base.notesname_instruments_array
    diff_array = base.diff_array

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

    joule_band.trackNotesOn        = trackNotesOn
    joule_band.trackNotesOff       = trackNotesOff
    joule_band.trackNotesLyrics    = trackNotesLyrics
    joule_band.trackNotesMeta      = trackNotesMeta

pass