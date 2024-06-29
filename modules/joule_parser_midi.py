import joule_data
import joule_band

from joule_band_handlers import *


# MIDI Processing
# ========================================
def joule_parse_midi():

    trackNotesOn        = joule_band.trackNotesOn
    trackNotesOff       = joule_band.trackNotesOff
    trackNotesLyrics    = joule_band.trackNotesLyrics
    trackNotesMeta      = joule_band.trackNotesMeta

    base = get_source_data()

    notesname_instruments_array = base.notesname_instruments_array
    notename_array = base.notename_array
    diff_array = base.diff_array

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

    joule_band.trackNotesOn        = trackNotesOn
    joule_band.trackNotesOff       = trackNotesOff
    joule_band.trackNotesLyrics    = trackNotesLyrics
    joule_band.trackNotesMeta      = trackNotesMeta

pass