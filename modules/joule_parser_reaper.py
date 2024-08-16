import joule_data
import joule_band

from joule_band_handlers import *

try:
    from reaper_python import *
except ImportError:
    pass


# REAPER Processing
# ========================================
def joule_parse_reaper():

    base = get_source_data()

    notesname_instruments_array = base.notesname_instruments_array
    notename_array = base.notename_array
    diff_array = base.diff_array

    project_dump = []
    project_data = []
    project_data_track = []
    project_known_tracks = []

    trackNotesOn = joule_band.trackNotesOn
    trackNotesOff = joule_band.trackNotesOff
    trackNotesLyrics = joule_band.trackNotesLyrics
    trackNotesMeta = joule_band.trackNotesMeta

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

    # Dump REAPER info to a file for reading.
    if joule_data.Debug > 2:
        with open(
            joule_data.GameDataLocation + ".reaper-info.txt", "w", encoding="utf-8"
        ) as _file:
            for line in project_dump:
                _file.write(line)
                _file.write("\n")

                if line == "~END":
                    _file.write("\n")
            _file.close()
        pass
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

    output_add("debug_1", f"ticksPerBeat: {joule_data.TicksPerBeat}")

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

    output_add("debug_1", f"TicksSustainLimit: {get_meta('TicksSustainLimit')}")

    project_bpm = 120
    project_time_signature_num = 4
    project_time_signature_denom = 4
    project_time_signature_location_time = 0

    # Get the beginning of the song's time signature and BPM.
    (
        NULL,
        NULL,
        project_time_signature_num,
        project_time_signature_denom,
        project_bpm,
    ) = RPR_TimeMap_GetTimeSigAtTime(0, 0, 0, 0, 0)
    # joule_print(project_bpm)

    process_time_signature(0, project_time_signature_num, project_time_signature_denom)
    trackNotesMeta["meta", "tempo", 0] = bpm2tempo(project_bpm)

    project_time_signature_next_time = RPR_TimeMap2_GetNextChangeTime(
        0, project_time_signature_location_time
    )

    while project_time_signature_next_time != -1:

        # joule_print(project_time_signature_next_time)
        (
            NULL,
            NULL,
            project_time_signature_num,
            project_time_signature_denom,
            project_bpm,
        ) = RPR_TimeMap_GetTimeSigAtTime(0, project_time_signature_next_time, 0, 0, 0)

        # Convert the time we are at to ticks for the note locations.
        _QN = RPR_TimeMap_timeToQN(project_time_signature_next_time)
        _ticks = int(_QN * joule_data.TicksPerBeat)

        process_time_signature(
            _ticks, project_time_signature_num, project_time_signature_denom
        )
        trackNotesMeta["meta", "tempo", _ticks] = bpm2tempo(project_bpm)

        project_time_signature_next_time = RPR_TimeMap2_GetNextChangeTime(
            0, project_time_signature_next_time
        )
        # joule_print(f"{project_time_signature_num}/{project_time_signature_denom} - {project_bpm}")

    # Get the information from all the media items.
    for data_index, item in enumerate(project_data):

        trackTime = 0
        unknownNotesSeen = []

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

                textData = decode_reaper_text(data_lines[index + 1])
                noteText = textData[1]
                messageType = "text"
                # joule_print( textData )

                # Track Detection
                if textData[0] == 3:
                    messageType = "name"
                    output_add("debug_3", f"Found {textData[1]}")
                    joule_data.Tracks.append(textData[1])

                    current_track = project_data_track[data_index]

                    # Because multiple Media items can be on the same track,
                    # we need to see if we are working with the same one.
                    if textData[1] in notesname_instruments_array:
                        if textData[1] in joule_data.TracksFound:
                            for track in project_known_tracks:
                                if (
                                    track[0] == textData[1]
                                    and track[1] != current_track
                                ):
                                    output_add(
                                        "issues_critical",
                                        f"Duplicate track '{textData[1]}' found! This duplicate track will not be processed.",
                                    )
                                    current_part = "SKIP_PART"
                                pass
                            pass
                        else:
                            project_known_tracks.append([textData[1], current_track])
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

                trackTime += int(note_parts[1])
                noteNumber = int(note_parts[3], 16)
                noteVelocity = int(note_parts[4], 16)

                if note_parts[2].startswith("9"):
                    messageType = "note_on"
                if note_parts[2].startswith("8"):
                    messageType = "note_off"

                if messageType == "note_on" and noteVelocity == 0:
                    messageType = "note_off"

                # Set the note name.
                if messageType == "note_on" or messageType == "note_off":
                    currentNoteName = str(noteNumber)

                    if current_part in notesname_instruments_array:
                        _tempName = notesname_instruments_array[current_part]

                        # Translate the name of the note, if we have it.
                        if noteNumber in notename_array[_tempName]:
                            currentNoteName = notename_array[_tempName][noteNumber]
                        else:
                            if messageType == "note_on":
                                output_add(
                                    "issues_critical",
                                    f"{current_part} | Unknown MIDI Note '{str(noteNumber)}' found!",
                                )
                                unknownNotesSeen.append(noteNumber)
                                pass
                            elif messageType == "note_off":
                                if noteNumber in unknownNotesSeen:
                                    unknownNotesSeen.remove(noteNumber)
                                else:
                                    output_add(
                                        "issues_critical",
                                        f"{current_part} | Unknown MIDI Note Off '{str(noteNumber)}' found!",
                                    )
                                pass
                            pass
                        pass
                    pass
                pass
            pass

            if messageType != None:
                if messageType == "note_on":
                    trackNotesOn[current_part, currentNoteName, trackTime] = True

                    # Enhanced Open checking.
                    if currentNoteName.endswith(
                        "_open"
                    ) and not currentNoteName.startswith("animation_"):
                        try:
                            _enhanced = False
                            if (
                                "[ENHANCED_OPENS]"
                                in trackNotesMeta[current_part, "text", 0]
                            ):
                                _enhanced = True
                        except:
                            pass
                        finally:
                            if _enhanced == False:
                                output_add(
                                    "issues_critical",
                                    f"{current_part} | Open notes found without ENHANCED_OPENS on {diff_array[currentNoteName[0]]}.",
                                    True,
                                )
                        pass
                    pass
                elif messageType == "note_off":
                    trackNotesOff[current_part, currentNoteName, trackTime] = True
                elif messageType == "text" or messageType == "lyrics":

                    if messageType == "lyrics":
                        if current_part == "PART VOCALS" or current_part.startswith(
                            "HARM"
                        ):
                            try:
                                len(trackNotesLyrics[current_part, "lyrics", trackTime])
                            except:
                                trackNotesLyrics[current_part, "lyrics", trackTime] = (
                                    noteText
                                )
                            else:
                                output_add(
                                    "issues_critical",
                                    f"{current_part} | Multiple Lyrics found at the same position.",
                                )
                            pass
                        else:
                            if (
                                noteText.startswith("[")
                                and noteText.endswith("]")
                                and current_part == "EVENTS"
                            ):
                                output_add(
                                    "issues_critical",
                                    f"{current_part} | Event '{noteText}' found as a Lyric in the EVENTS track.",
                                )
                            else:
                                output_add(
                                    "issues_minor",
                                    f"{current_part} | Lyric '{noteText}' found in a non-vocal track.",
                                )
                            pass

                            # Add this to the text data for the track, because this should be there instead of a lyric.
                            try:
                                len(trackNotesMeta[current_part, "text", trackTime])
                            except:
                                trackNotesMeta[current_part, "text", trackTime] = [
                                    noteText
                                ]
                            else:
                                trackNotesMeta[current_part, "text", trackTime].append(
                                    noteText
                                )
                            pass
                        pass
                    else:
                        try:
                            len(trackNotesMeta[current_part, "text", trackTime])
                        except:
                            trackNotesMeta[current_part, "text", trackTime] = [noteText]
                        else:
                            trackNotesMeta[current_part, "text", trackTime].append(
                                noteText
                            )
                        pass
                    pass

                    if current_part == "EVENTS":
                        try:
                            len(trackNotesMeta["meta", "events", trackTime])
                        except:
                            trackNotesMeta["meta", "events", trackTime] = [noteText]
                        else:
                            trackNotesMeta["meta", "events", trackTime].append(noteText)
                        pass
                    pass
                elif messageType == "sysex":

                    try:
                        len(trackNotesMeta[current_part, "sysex", trackTime])
                    except:
                        trackNotesMeta[current_part, "sysex", trackTime] = [noteText]
                    else:
                        trackNotesMeta[current_part, "sysex", trackTime].append(
                            noteText
                        )
                    pass

                    # If we find tap note modifiers, we want to translate that.
                    if noteText[5] == 4:
                        if noteText[6] == 1:
                            trackNotesOn[current_part, "tap", trackTime] = True
                            # joule_print("Tap On")
                        if noteText[6] == 0:
                            trackNotesOff[current_part, "tap", trackTime] = True
                            # joule_print("Tap Off")
                    else:
                        pass
                        # joule_print(f"{noteText}")
                    pass
                pass
            pass
        pass

        if current_part != None:

            # Check to see if we found the length. If we didn't, we write it.
            try:
                len(trackNotesMeta[current_part, "length", 0])
            except:
                trackNotesMeta[current_part, "length", 0] = trackTime
            pass

            output_add("debug_2", f"{current_part} Length: {trackTime}")

            if get_meta("TotalLength") != None:
                if get_meta("TotalLength") < trackTime:
                    write_meta("TotalLength", trackTime)
                pass
            else:
                write_meta("TotalLength", trackTime)
            pass

        pass

    pass

    joule_band.trackNotesOn = trackNotesOn
    joule_band.trackNotesOff = trackNotesOff
    joule_band.trackNotesLyrics = trackNotesLyrics
    joule_band.trackNotesMeta = trackNotesMeta


pass
