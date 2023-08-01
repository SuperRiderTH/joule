# This is the file for Band related games, for example:
# Rock Band 3, Phase Shift, Clone Hero.

import joule_data
import math
import re

from joule_system import *
from joule_band_handlers import *


#trackNotes[track, note, time]
#trackNotes["PART DRUMS", "x_kick", 0] = True
trackNotesOn = {}
trackNotesOff = {}
trackNotesMeta = {}
trackNotesLyrics = {}

notesname_instruments_array = {}
notesname_array = {}

time_signature_measure          = []
time_signature_time             = []

ticksPerBeat  = 0


# Functions
# ========================================

def section_read( line_start:int ):
    
    inSection = False
    
    sectionName = joule_data.GameDataFile[line_start].strip()[1:-1]
    
    print(sectionName)
    
    if sectionName in joule_data.TracksFound:
        output_add("issues_critical",f"Duplicate track '{sectionName}' found! This duplicate track will not be processed.")
        return
    else:
        joule_data.TracksFound.append(sectionName)
    pass

    lineIndex = line_start

    _tempData = []
    
    for i in range(lineIndex, len(joule_data.GameDataFile)):
        
        line = joule_data.GameDataFile[i]

        if line.strip().startswith("{") or '[' in line:
            
            if inSection == True:
                print(f"Error! Section '{sectionName}' ends early at line {i+1}!")
                return
            else:
                if line.strip().startswith("{"):
                    inSection = True
                pass
            pass
        elif line.strip().startswith("}"):
            joule_data.GameData["Sections"] = trackNotesMeta
            return
        else:
            lineGroups = re.search("(?:\ *)([^\ =]+)(?:\ *)(?:={1})(?:\ *)(.+)(?:)", line).groups()
            
            if sectionName == "Song":
                print(lineGroups)
            
            if lineGroups[0].lower() == "resolution":
                joule_data.TicksPerBeat = int(lineGroups[1])

            #_tempData.update()
            
        


pass


def initialize_band():

    global notesname_array
    global notesname_instruments_array
    global ticksPerBeat

    global time_signature_measure
    global time_signature_time

    base = get_source_data()
    
    notesname_instruments_array = base.notesname_instruments_array
    notesname_array = base.notesname_array

    time_signature_last_position    = 0
    time_signature_last_measure     = 0


    # If we are working with these games they use MIDI for their notes,
    # so we want to process that.
    
    if joule_data.GameDataFileType == "MIDI":
        
        joule_data.TicksPerBeat = joule_data.GameDataFile.ticks_per_beat # type: ignore

        ticksPerBeat = joule_data.TicksPerBeat
        joule_data.NoteTime = math.floor(ticksPerBeat / 32)

        output_add("debug_1",f"ticksPerBeat: {ticksPerBeat}")
        output_add("debug_1",f"NoteTime: {joule_data.NoteTime}")
        
        # Rock Band expects 480 ticks per QN.
        # This should not have made it through Magma, but just in case.
        if joule_data.GameSource == "rb3" or "rb2":
            if ticksPerBeat != 480:
                output_add("issues_critical", "Ticks per Quarter Note is not 480.")
            pass
        pass

        # Track processing
        for i, track in enumerate(joule_data.GameDataFile.tracks): # type: ignore
            trackTime           = 0

            last_time_signature_num        = 4
            last_time_signature_denom      = 4

            print("Found " + track.name + "...")

            #for msg in track:
                #print(msg)

            # Instrument Processing
            if track.name in notesname_instruments_array:

                if track.name in joule_data.TracksFound:
                    output_add("issues_critical",f"Duplicate track '{track.name}' found! This duplicate track will not be processed.")
                    continue
                else:
                    joule_data.TracksFound.append(track.name)
                pass
            
                _tempName = notesname_instruments_array[track.name]

                _unknownNotesSeen = []

                for msg in track:
                    # Add the time to the track.
                    trackTime += msg.time

                    if msg.type == 'note_on':
                        if msg.note in notesname_array[_tempName]:
                            
                            # Oynx doesn't do Off Notes, and instead does this.
                            if msg.velocity == 0:
                                trackNotesOff[track.name,notesname_array[_tempName][msg.note],trackTime] = True
                            else:
                                trackNotesOn[track.name,notesname_array[_tempName][msg.note],trackTime] = True
                            pass
                            
                            output_add("debug_4",f"{track.name} | {notesname_array[_tempName][msg.note]} | {trackTime}")
                        else:
                            output_add("issues_critical",f"{track.name} | Unknown MIDI Note '{str(msg.note)}' found!")
                            trackNotesOn[track.name,str(msg.note),trackTime] = True
                            _unknownNotesSeen.append(msg.note)
                        pass
                    elif msg.type == 'note_off':
                        if msg.note in notesname_array[_tempName]:
                            trackNotesOff[track.name,notesname_array[_tempName][msg.note],trackTime] = True
                        else:
                            if msg.note in _unknownNotesSeen:
                                _unknownNotesSeen.remove(msg.note)
                            else:
                                output_add("issues_critical",f"{track.name} | Unknown MIDI Note Off '{str(msg.note)}' found!")
                            pass

                            trackNotesOff[track.name,str(msg.note),trackTime] = True    
                        pass

                    elif msg.type == 'text':
                        trackNotesMeta[track.name,"text",trackTime] = msg.text

                    elif msg.type == 'lyrics':
                        trackNotesLyrics[track.name,"lyrics",trackTime] = msg.text

                    # Store the length of the track for processing.
                    elif msg.type == 'end_of_track':
                        trackNotesMeta[track.name,"length",0] = trackTime
                pass
            else:
                for msg in track:
                    # Add the time to the track.
                    trackTime += msg.time

                    if track.name == "EVENTS":
                        if msg.type == 'text':
                            trackNotesMeta["meta","events",trackTime] = msg.text

                    if msg.type == 'time_signature':
                        trackNotesMeta["meta","time_signature_num",trackTime] = msg.numerator
                        trackNotesMeta["meta","time_signature_denom",trackTime] = msg.denominator

                        # We need to manually keep track of time signature changes
                        # since we do not have an easy way to do that here.
                        time_signature_time.append(trackTime)

                        tempPosition = trackTime - time_signature_last_position

                        ticks_per_measure = ( ticksPerBeat / last_time_signature_denom ) * last_time_signature_num

                        tempPosition = (tempPosition / ticks_per_measure) / 4

                        time_signature_last_measure     = time_signature_last_measure + tempPosition
                        time_signature_last_position    = trackTime
                        last_time_signature_num         = msg.numerator
                        last_time_signature_denom       = msg.denominator
                        
                        time_signature_measure.append( time_signature_last_measure)

                    pass

                    if msg.type == 'set_tempo':
                        trackNotesMeta["meta","tempo",trackTime] = msg.tempo
                    pass
                    
                pass
            pass
        pass
    pass

    if joule_data.GameDataFileType == "CHART":
        
        # Find every section, do something about it.
        for i in range(0, len(joule_data.GameDataFile)):
            
            line = joule_data.GameDataFile[i]
            
            # We don't want zero width spaces here. Get rid of them.
            if chr(65279) in line:
                joule_data.GameDataFile[i] = line.replace(chr(65279), '')
                line = joule_data.GameDataFile[i]
                
            # If we find a section, we want that info.
            if line.strip().startswith("["):
                section_read(i)
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
    #output_add("debug_4",f"{trackNotesOn}")
    #output_add("debug_4",f"{trackNotesOff}")
    #output_add("debug_4",f"{trackNotesLyrics}")
    #output_add("debug_4",f"{trackNotesMeta}")

    joule_data.GameData["trackNotesOn"] = trackNotesOn
    joule_data.GameData["trackNotesOff"] = trackNotesOff
    joule_data.GameData["trackNotesLyrics"] = trackNotesLyrics
    joule_data.GameData["trackNotesMeta"] = trackNotesMeta

    print ("========================================")

    return
pass

def process_lyrics():

    print("Extracting lyrics...")

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

    pass
 
    joule_data.GameData["phrases"] = phrases

    return

pass

def process_events():

    print("Extracting events...")

    indexesEvents          = get_data_indexes("trackNotesMeta", 'meta', 'events')
    events                 = []

    for i in indexesEvents:

        _event = joule_data.GameData["trackNotesMeta"]["meta","events",i]
        _event = _event.strip()

        if _event not in joule_data_rockband.events_ignore_list:

            if _event in joule_data_rockband.event_friendly_list:
                _event = joule_data_rockband.event_friendly_list[_event]
            pass

            _tempEvent = f"{format_location(i)}: {_event}"
            
            events.append(_tempEvent)
            output_add("events", _tempEvent)
            
        pass

    pass

    joule_data.GameData["events"] = events

    return
pass



