import inspect

import joule_data

from joule_system import *
from joule_band_handlers import *

import joule_data_rockband
import joule_data_clonehero
import joule_data_yarg

def set_source_data():

    global notename_array
    global notes_pads
    global notes_drum
    global notes_lane
    global diff_array
    global diff_highest
    global chord_limit
    global chord_limit_keys
    global chord_limit_keys_pro
    global note_overdrive
    global notesname_instruments_array
    global span_limit_keys_pro

    base = get_source_data()

    notename_array = base.notename_array
    notes_pads = base.notes_pads
    notes_drum = base.notes_drum
    notes_lane = base.notes_lane
    diff_array = base.diff_array
    diff_highest = base.diff_highest
    chord_limit = base.chord_limit
    chord_limit_keys = base.chord_limit_keys
    chord_limit_keys_pro = base.chord_limit_keys_pro
    note_overdrive = base.note_overdrive
    notesname_instruments_array = base.notesname_instruments_array
    span_limit_keys_pro = base.span_limit_keys_pro

    joule_data.BrokenChordsAllowed = base.brokenChordsAllowed
    joule_data.LowerHOPOsAllowed = base.lowerHOPOsAllowed

    tempNO = get_meta("NoteOverdrive")
    if tempNO != None:
        note_overdrive = tempNO

    write_meta("SustainMinimum", base.sustainMinimum)

pass


# template function
def validate_THING(partname:str):
    set_source_data()
    result = True

    for diff in diff_array:
        print(f"Processsing THING for {partname} on {diff_array[diff]}...")
    return

    output_add("check_results", f"{partname} | {inspect.stack()[0][3]} | {result}")

pass

def validate_sustains(partname:str, isRealKeys=False):
    set_source_data()
    result = True

    global notename_array

    noteLength64    = joule_data.TicksPerBeat / 16 #30, assuming 480.

    noteLength32    = joule_data.TicksPerBeat / 8  #60
    noteLength32T   = joule_data.TicksPerBeat / 12 #40

    noteLength16    = joule_data.TicksPerBeat / 4  #120
    noteLength16T   = joule_data.TicksPerBeat / 6  #80

    sustainLimit = get_meta('TicksSustainLimit')
    sustainMinimum = get_meta('SustainMinimum')

    diffs = diff_array

    if isRealKeys:
        diffs = [partname[-1].lower()]

    for diff in diffs:

        notesOn     = { "lane":[] }
        notesOff    = { "lane":[] }
        notesAll    = {}

        if isRealKeys:
            toFind = "note"
        else:
            toFind = f"{diff}"
        pass

        notesOn.update( { "lane" : get_data_indexes("trackNotesOn",partname,toFind) } )
        notesOff.update( { "lane" : get_data_indexes("trackNotesOff",partname,toFind) } )
        notesAll = sorted(set( get_data_indexes("trackNotesOn",partname,toFind) + get_data_indexes("trackNotesOff",partname,toFind) ))


        if len(get_data_indexes("trackNotesOn", partname, toFind)) < 2:
            output_add("debug_3", f"{partname} | validate_sustains | No notes found on {diff_array[diff]}.")

            if joule_data.GameSource in joule_data.GameSourceRBLike and joule_data.GameSource != "yarg":
                output_add("issues_critical", f"{partname} | No notes found on {diff_array[diff]}.")
                result = False

            continue


        statusString = f"Processsing sustains for {partname}"
        
        if not partname.startswith("PART REAL_KEYS"):
            statusString += f" on {diff_array[diff]}"
            
        print(f"{statusString}...")


        lastNoteOn          = 0
        lastNoteOff         = 0
        lastNoteWasSustain  = False
        currentNotes        = 0

        for note in notesAll:

            if note in notesOff["lane"]:
                currentNotes -= notesOff["lane"].count(note)

                if currentNotes == 0:
                    
                    lastNoteOff = note

                    if lastNoteOff - lastNoteOn > sustainLimit:
                        lastNoteWasSustain = True
                    else:
                        lastNoteWasSustain = False
                    pass

                    if lastNoteWasSustain:
                        sustainLength = joule_data.Seconds[lastNoteOff] - joule_data.Seconds[lastNoteOn]
                        #print(f"{format_location(lastNoteOn, True)} - {sustainLength}")

                        if sustainLength < sustainMinimum:
                            output_add("issues_major", f"{partname} | {format_location(lastNoteOn)} | Note on {diff_array[diff]} is too short to be a sustain.")
                            result = False
                        pass

                    pass

                pass
            pass

            if note in notesOn["lane"]:
                if currentNotes == 0:

                    # Sustain gap Check
                    if ( ( note - lastNoteOff ) < noteLength32T ) and lastNoteWasSustain:
                        output_add("issues_major", f"{partname} | {format_location(note)} | Note on {diff_array[diff]} should have a 32nd note gap from a sustain.")
                        result = False
                    pass

                    lastNoteOn = note
                pass
                currentNotes += notesOn["lane"].count(note)
            pass

        pass
    pass

    output_add("check_results", f"{partname} | {inspect.stack()[0][3]} | {result}")

pass

def validate_spacing_vocals(partname:str):
    set_source_data()
    result = True

    global notename_array

    noteLength64    = joule_data.TicksPerBeat / 16 #30, assuming 480.

    noteLength32    = joule_data.TicksPerBeat / 8  #60
    noteLength32T   = joule_data.TicksPerBeat / 12 #40

    noteLength16    = joule_data.TicksPerBeat / 4  #120
    noteLength16T   = joule_data.TicksPerBeat / 6  #80

    print(f"Processsing vocal note spacing for {partname}...")

    # All harmonies must follow the Phrase Markers from HARM1.
    if partname != "PART VOCALS":
        _toFind = "HARM1"
    else:
        _toFind = partname
    pass

    indexesVocalPhrasesOn  = get_data_indexes("trackNotesOn", _toFind, 'phrase')
    indexesVocalPhrasesOff = get_data_indexes("trackNotesOff", _toFind, 'phrase')
    indexesVocalsLyrics    = get_data_indexes("trackNotesLyrics", partname, 'lyrics')

    if len(indexesVocalPhrasesOn) > 0:
        pass
    else:
        output_add("issues_critical", f"{_toFind} Phrase Markers do not exist! Spacing for {partname} can not be processed.")
        output_add("check_results", f"{partname} | {inspect.stack()[0][3]} | {False}")
        return
    pass


    # Note spacing
    # ========================================

    indexesVocalsOn = get_data_indexes("trackNotesOn", partname, "note")
    indexesVocalsOff = get_data_indexes("trackNotesOff", partname, "note")

    for index, note in enumerate(indexesVocalsOn):
        if index > 0:
            if note < indexesVocalsOff[index - 1] + (noteLength32T):
                output_add("issues_major", f"{partname} | {format_location(note)} | Vocal notes should have a 32nd note gap from the previous note.")
                result = False

    lastTime = 0
    lastWordIsPitched = False

    # Rock Band 3 Vocal Bug checking.
    # See: http://docs.c3universe.com/rbndocs/index.php?title=Vocal_Authoring#Pitched

    # Get the start of every Phrase Marker
    for index, item in enumerate(indexesVocalPhrasesOn):

        # This is for P2 Phrase Markers, if we already checked this Phrase we want to skip it.
        if item == lastTime:
            continue
        else:
            lastTime = item
        pass

        firstNote = True

        # Check every Lyric in that Phrase
        for note in filter(lambda x:x >= item and x <= indexesVocalPhrasesOff[index], indexesVocalsLyrics):

            currentLyric:str = joule_data.GameData["trackNotesLyrics"][partname,"lyrics",note]

            if firstNote == True and index > 0:
                if currentLyric.endswith('^') or currentLyric.endswith('#'):
                    if lastWordIsPitched:
                        if indexesVocalPhrasesOn[index] < ( indexesVocalPhrasesOff[index - 1] + (noteLength16T) ):
                            output_add("issues_critical", f"{partname} | {format_location(note)} | Spoken words starting a Phrase require a 16th note gap between Phrase Markers.")
                            result = False

            if currentLyric.endswith('^') or currentLyric.endswith('#'):
                lastWordIsPitched = False
            else:
                lastWordIsPitched = True
            pass

            firstNote = False
        pass
    pass

    output_add("check_results", f"{partname} | {inspect.stack()[0][3]} | {result}")

pass

def rbn_hopos(partname:str):
    set_source_data()
    result = True

    if joule_data.LowerHOPOsAllowed:
        return
    else:

        print(f"Processsing HOPOs for {partname}...")

        for diff in diff_array:
            if diff == "m" or diff == "e":
                if len(get_data_indexes("trackNotesOn",partname,f"{diff}_hopo")) > 0:
                    output_add("issues_major", f"{partname} | Forced HOPOs are not allowed on {diff_array[diff]}.")
                    result = False
                pass
            pass
        pass
    pass

    output_add("check_results", f"{partname} | {inspect.stack()[0][3]} | {result}")

pass

def tow_check(partname:str):
    result = True

    if partname == "PART VOCALS":
        _note = "phrase"
    else:
        _note = "tow"

    phrasesP1 = get_data_indexes("trackNotesOn", "PART VOCALS", f'{_note}_p1')
    phrasesP2 = get_data_indexes("trackNotesOn", "PART VOCALS", f'{_note}_p2')

    if len(phrasesP2) > 0:
        if len(phrasesP1) != len(phrasesP2):
            output_add("issues_major", f"{partname} | Player 1 and 2 do not have an equal amount of Tug of War Markers.")
            result = False
        pass
    pass

    output_add("check_results", f"{partname} | {inspect.stack()[0][3]} | {result}")

pass


def rbn_vocals_lyrics(partname:str):
    print(f"Processsing Lyrics for {partname}...")
    set_source_data()
    result = True

    # All harmonies must follow the Phrase Markers from HARM1.
    if partname != "PART VOCALS":
        _toFind = "HARM1"
    else:
        _toFind = partname
    pass

    indexesVocalPhrasesOn  = get_data_indexes("trackNotesOn", _toFind, 'phrase')
    indexesVocalPhrasesOff = get_data_indexes("trackNotesOff", _toFind, 'phrase')
    indexesVocalsLyrics    = get_data_indexes("trackNotesLyrics", partname, 'lyrics')

    if len(indexesVocalPhrasesOn) > 0:
        pass
    else:
        output_add("issues_critical", f"{_toFind} Phrase Markers do not exist! Lyrics for {partname} can not be processed.")
        output_add("check_results", f"{partname} | {inspect.stack()[0][3]} | {False}")
        return
    pass

    lastTime               = 0

    gameCharactersToRemove = ['$','-','=','^','#']

    reservedSyllables = ["I","I'm","I'ma","I'mma","I'll","I'd","I've","God"]

    punctuation = ['?','!']

    punctuationError = ['.',',','"']
    punctuationErrorFriendly = {
        '.': "Periods",
        ',' : "Commas",
        '"': "Quotation marks",
        }


    for index, item in enumerate(indexesVocalPhrasesOn):

        phraseStart = True
        checkCaps = False

        # This is for P2 Phrase Markers, if we already checked this Phrase we want to skip it.
        if item == lastTime:
            continue
        else:
            lastTime = item
        pass

        # Check every lyric inside the Phrase Markers.
        for note in filter(lambda x:x >= item and x <= indexesVocalPhrasesOff[index], indexesVocalsLyrics):

            syllable:str = joule_data.GameData["trackNotesLyrics"][partname,"lyrics",note]
            syllableRaw = syllable

            # Check for space around the syllable.
            if syllable != syllable.strip():
                output_add("issues_major", f"{partname} | {format_location(note)} | Syllable '{syllableRaw}' has extra spacing around the characters.")
                result = False
                syllable = syllable.strip()
            pass

            # Latin-1 Check.
            for character in syllable:
                if ( ord(character) > 255  ):
                    output_add("issues_critical", f"{partname} | {format_location(note)} | '{character}' in {syllableRaw} is a Non-Latin-1 character.")
                    result = False
                pass
            pass

            if partname == "PART VOCALS":
                if syllable.endswith("$"):
                    output_add("issues_major", f"{partname} | {format_location(note)} | Lyrics can not be hidden in PART VOCALS, found in '{syllableRaw}'.")
                    result = False
                pass
            pass

            # Strip game characters out of the syllable
            syllable = ''.join(x for x in syllable if not x in gameCharactersToRemove)

            # We are ignoring this symbol if it is used to start the syllable.
            if syllable.startswith("'"):
                syllable = syllable[1:]
            pass

            if syllable.endswith("!?"):
                output_add("issues_minor", f"{partname} | {format_location(note)} | Question mark should be before the exclamation point, found in '{syllableRaw}'.")
                result = False
            pass

            # Check syllable for special characters
            for character in syllable:
                if character in punctuationError:
                    output_add("issues_minor", f"{partname} | {format_location(note)} | {punctuationErrorFriendly[character]} should never be used, found in '{syllableRaw}'.")
                    result = False
                pass
            pass

            # Capitalization checking.
            if syllable[0].isalpha():
                if phraseStart or checkCaps:
                    phraseStart = False
                    if not syllable[0].isupper():
                        output_add("issues_minor",f"{partname} | {format_location(note)} | '{syllableRaw}' should be uppercase.")
                        result = False
                    pass
                    checkCaps = False
                else:
                    if syllable not in reservedSyllables:
                        if syllable[0].isupper():
                            output_add("issues_minor",f"{partname} | {format_location(note)} | Unexpected uppercase syllable '{syllableRaw}'.")
                            result = False
                        pass
                    pass
                pass
            pass

            # Syllable ends in punctuation, we want to check the next one for a capital letter.
            if syllable[-1:] in punctuation:
                checkCaps = True
            pass
        pass
    pass

    output_add("check_results", f"{partname} | {inspect.stack()[0][3]} | {result}")
    return

pass

def rbn_guitar_chords(partname:str):
    set_source_data()
    result = True

    for diff in diff_array:

        notesAll = sorted(set( get_data_indexes("trackNotesOn",partname,f"{diff}") + get_data_indexes("trackNotesOff",partname,f"{diff}") ))
    
        if len(get_data_indexes("trackNotesOn",partname,f"{diff}")) < 2:
            output_add("debug_3", f"{partname} | rbn_guitar_chords | No notes found on {diff_array[diff]}.")
            continue

        print(f"Processsing chords for {partname} on {diff_array[diff]}...")

        for note in notesAll:

            # Green Orange chord detection
            # ========================================
            if get_note_on( partname, f"{diff}_{'orange'}", note):
                if get_note_on( partname, f"{diff}_{'green'}", note):
                    
                    if get_note_on( partname, f"{diff}_{'red'}", note)\
                    or get_note_on( partname, f"{diff}_{'yellow'}", note)\
                    or get_note_on( partname, f"{diff}_{'blue'}", note):
                        output_add("issues_major", f"{partname} | {format_location(note)} | Found note paired with Green and Orange gems on {diff_array[diff]}.")
                        result = False
                    pass

                    # Green Orange chords are not allowed on anything below Expert.
                    if diff != "x":
                        output_add("issues_major", f"{partname} | {format_location(note)} | Green and Orange chords are not allowed on {diff_array[diff]}.")
                        result = False
                    pass
                pass
            pass

            noteCount = 0
            noteCountHighest = 0

            for noteLane in notes_lane:
                if get_note_on( partname, f"{diff}_{noteLane}", note):
                    noteCount += 1
                pass
            pass

            # If there isn't any notes here, skip the rest.
            if noteCount == 0:
                continue
            
            if diff != diff_highest:
                # If chords are not allowed, we skip checking.
                if chord_limit[diff] > 1:

                    for noteLane in notes_lane:
                        if get_note_on( partname, f"{diff_highest}_{noteLane}", note):
                            noteCountHighest += 1
                        pass
                    pass

                    if noteCountHighest > 1:
                        # This note should be a chord.
                        if noteCount < 2:
                            output_add("issues_major", f"{partname} | {format_location(note)} | Single note found on {diff_array[diff]}, expected a chord based on {diff_array[diff_highest]}.")
                            result = False
                        pass
                    pass
                pass
            pass
        pass
 
    output_add("check_results", f"{partname} | {inspect.stack()[0][3]} | {result}")
    return

pass


def rbn_drums_limbs(partname:str):
    set_source_data()
    result = True

    for diff in diff_array:

        if len(get_data_indexes("trackNotesOn",partname,f"{diff}")) < 2:
            output_add("debug_3", f"{partname} | rbn_drums_limbs | No notes found on {diff_array[diff]}.")
            continue

        print(f"Processsing limbs for {partname} on {diff_array[diff]}...")

        notesOn       = {}
        notesOff      = {}
        notesAll      = []

        armsUsed = 0

        notesOn.update( { "pads":[] } )
        notesOff.update( { "pads":[] } )

        notesAll = sorted(set( get_data_indexes("trackNotesOn",partname,f"{diff}") + get_data_indexes("trackNotesOff",partname,f"{diff}") ))

        for note in notes_drum:

            tempNotesOn = get_data_indexes("trackNotesOn",partname,f"{diff}_{note}")
            tempNotesOff = get_data_indexes("trackNotesOff",partname,f"{diff}_{note}")

            notesOn.update( { f"{note}" : tempNotesOn } )
            notesOff.update( { f"{note}" : tempNotesOff } )

            if note in notes_pads:
                notesOn["pads"] += tempNotesOn
                notesOff["pads"] += tempNotesOff


        for note in notesAll:

            if note in notesOff["pads"]:
                armsUsed -= notesOff["pads"].count(note)
            pass

            if note in notesOn["pads"]:
                armsUsed += notesOn["pads"].count(note)

                if armsUsed > 2:
                    output_add("issues_major", f"{partname} | {format_location(note)} | {armsUsed} Arms used on {diff_array[diff]}.")
                    result = False
                pass
            pass


        pass



        # Kick checking
        # ========================================

        for kick in notesOn["kick"]:

            gems_with_kick = notesOn["pads"].count(kick)

            if joule_data.GameSource in joule_data.GameSourceRBLike:
                if gems_with_kick > 1 and diff == "m":
                    output_add("debug_2", f"{partname} | {kick} | {format_location(kick)} | {gems_with_kick} Gems | {diff_array[diff]}")
                    output_add("issues_major", f"{partname} | {format_location(kick)} | More than two limbs used on {diff_array[diff]}.")
                    result = False
                pass
                if gems_with_kick > 0 and diff == "e":
                    output_add("debug_2", f"{partname} | {kick} | {format_location(kick)} | {gems_with_kick} Gems | {diff_array[diff]}")
                    output_add("issues_major", f"{partname} | {format_location(kick)} | No Gems are allowed with Kick notes on {diff_array[diff]}.")
                    result = False
                pass
            pass
        pass

    pass

    output_add("check_results", f"{partname} | {inspect.stack()[0][3]} | {result}")
    return

pass

def rbn_drums_fills(partname:str):
    set_source_data()
    result = True

    print(f"Processsing fills for {partname}...")

    fillStart = get_data_indexes("trackNotesOn",partname,"fill_kick")
    fillEnd =  get_data_indexes("trackNotesOff",partname,"fill_kick")

    fillStartAll = get_data_indexes("trackNotesOn",partname,"fill")
    fillEndAll =  get_data_indexes("trackNotesOff",partname,"fill")

    overdriveStart = get_data_indexes("trackNotesOn",partname,"overdrive")
    overdriveEnd = get_data_indexes("trackNotesOff",partname,"overdrive")

    soloStart = get_data_indexes("trackNotesOn",partname,"solo")
    soloEnd =  get_data_indexes("trackNotesOff",partname,"solo")

    rollStart = get_data_indexes("trackNotesOn",partname,"roll")
    rollEnd =  get_data_indexes("trackNotesOff",partname,"roll")

    rollSingleStart = get_data_indexes("trackNotesOn",partname,"roll_single")
    rollSingleEnd = get_data_indexes("trackNotesOff",partname,"roll_single")

    rollSwellStart = get_data_indexes("trackNotesOn",partname,"roll_swell")
    rollSwellEnd = get_data_indexes("trackNotesOff",partname,"roll_swell")

    notesAll = sorted( set( (overdriveStart + overdriveEnd + fillStart + fillEnd + soloStart + soloEnd + rollStart + rollEnd) ) )

    inFill          = False
    inSolo          = False
    inOverdrive     = False
    inRoll          = False
    inRollSingle    = False
    inRollSwell     = False


    for index, item in enumerate(fillStart):

        for od_note in filter(lambda x:x >= item and x <= fillEnd[index], overdriveStart + overdriveEnd):

            if od_note == fillEnd[index]:
                output_add("issues_critical",f"{partname} | {format_location(od_note)} | Overdrive starts right after Drum Fill {index+1}.")
                result = False
            elif od_note == item:
                output_add("issues_critical",f"{partname} | {format_location(od_note)} | Overdrive ends right before Drum Fill {index+1}.")
                result = False
            else:
                output_add("issues_critical",f"{partname} | {format_location(od_note)} | Overdrive overlaps Drum Fill {index+1}.")
                result = False
            pass

        if joule_data.GameDataFileType != "CHART":

            if fillStartAll.count(fillStart[index]) != 5:
                output_add("issues_critical",f"{partname} | {format_location(fillStart[index])} | Drum Fill {index+1} notes do not start simultaneously.")
                result = False
            pass

            if fillEndAll.count(fillEnd[index]) != 5:
                output_add("issues_critical",f"{partname} | {format_location(fillEnd[index])} | Drum Fill {index+1} notes do not end simultaneously.")
                result = False
            pass


    for note in notesAll:

        if note in fillEnd:
            inFill = False
        if note in overdriveEnd:
            inOverdrive = False
        if note in soloEnd:
            inSolo = False
        if note in rollSingleEnd:
            inRollSingle = False
        if note in rollSwellEnd:
            inRollSwell = False

        if inRollSingle == False and inRollSwell == False:
            inRoll = False
        pass

        if inSolo:
            if note in fillStart:
                output_add("issues_critical",f"{partname} | {format_location(note)} | Drum Fills are not allowed in Solos.")
                result = False
            pass
        pass

        if note in fillStart:
            inFill = True
        if note in overdriveStart:
            inOverdrive = True
        if note in soloStart:
            inSolo = True
        if note in rollSingleStart:
            inRollSingle = True
        if note in rollSwellStart:
            inRollSwell = True
        pass

        if inRollSingle == True or inRollSwell == True:
            inRoll = True
        pass

        if inRoll and inFill:
            output_add("issues_critical",f"{partname} | {format_location(note)} | Drum Rolls are not allowed in Drum Fills.")
            result = False
        pass

        if note in rollSingleStart or note in rollSwellStart:
            if inRollSingle == True and inRollSwell == True:
                output_add("issues_critical",f"{partname} | {format_location(note)} | Drum Roll and Swell happening simultaneously.")
                result = False
            pass
        pass

    pass

    output_add("check_results", f"{partname} | {inspect.stack()[0][3]} | {result}")
    return

pass

def validate_instrument_phrases():
    set_source_data()

    notesOn         = {}
    notesOff        = {}
    notesAll        = []

    noteCheck       = []
    unisonCheck     = []

    notesToCheck        = "Solo", "Overdrive"

    inSpecialNote       = False
    overdriveCount      = 0

    lastNoteStart       = 0
    lastNoteWasCheck    = False
    checkNextNote       = False


    # Gather tracks for testing.
    for track in joule_data.TracksFound:

        if notesname_instruments_array[track] == "5LANES"\
        or notesname_instruments_array[track] == "DRUMS":
            noteCheck.append(track)
            unisonCheck.append(track)
        pass

        if notesname_instruments_array[track] == "PROKEYS":
            noteCheck.append(track)
        pass

    pass

    for noteType in notesToCheck:

        for track in noteCheck:
            print(f"Checking {noteType} for {track}...")
            result = True
            for diff in diff_array:

                if track.startswith("PART REAL_KEYS"):
                    _tempCheck = "note"
                else:
                    _tempCheck = diff
                pass

                if notesname_instruments_array[track] == "PROKEYS":

                    if track != f"PART REAL_KEYS_{diff.capitalize()}":
                        continue

                    notesOn         = get_data_indexes("trackNotesOn",f"PART REAL_KEYS_{diff.capitalize()}","note")
                    notesOff        = get_data_indexes("trackNotesOff",f"PART REAL_KEYS_{diff.capitalize()}","note")

                    checkOn     = get_data_indexes("trackNotesOn","PART REAL_KEYS_X",noteType.lower())
                    checkOff    = get_data_indexes("trackNotesOff","PART REAL_KEYS_X",noteType.lower())
                else:
                    notesOn         = get_data_indexes("trackNotesOn",track,f"{diff}")
                    notesOff        = get_data_indexes("trackNotesOff",track,f"{diff}")

                    checkOn     = get_data_indexes("trackNotesOn",track,noteType.lower())
                    checkOff    = get_data_indexes("trackNotesOff",track,noteType.lower())
                pass

                if len( get_data_indexes( "trackNotesOn", track, _tempCheck ) ) < 2:
                    output_add("debug_3", f"{track} | validate_instrument_phrases | No notes found on {diff_array[diff]}.")
                    continue

                notesAll = sorted(set(notesOn + notesOff + checkOn + checkOff))

                for note in notesAll:

                    if note in checkOff:
                        inSpecialNote = False

                        if checkNextNote:
                            output_add("issues_critical", f"{track} | {format_location(lastNoteStart)} | No notes in {noteType} Phrase on {diff_array[diff]}.")
                            result = False
                        pass

                    pass

                    if note in checkOn:
                        inSpecialNote = True
                        checkNextNote = True
                        lastNoteStart = note
                    pass

                    if note in notesOn:

                        if checkNextNote:
                            checkNextNote = False

                            if lastNoteWasCheck and inSpecialNote and noteType == "Overdrive":
                                output_add("issues_critical", f"{track} | {format_location(note)} | Notes are missing on {diff_array[diff]} between two {noteType} Phrases.")
                                result = False
                            pass
                        pass


                        if inSpecialNote:
                            lastNoteWasCheck = True
                        else:
                            lastNoteWasCheck = False
                        pass

                    pass
                pass
            pass

            output_add("check_results", f"{track} | {inspect.stack()[0][3]} | {result}")

        pass

    return

pass



def rbn_broken_chords(partname:str):
    set_source_data()
    result = True

    notesOn       = {}
    notesOff      = {}
    notesAll      = []

    lanesUsed = 0

    noteStartTime = 0
    lastReportedTime = 0
    chordHappening = False
    brokenChordsAllowed = False

    chordLimit = False

    if joule_data.BrokenChordsAllowed\
    or partname in ("PART KEYS", "Keyboard"):
        brokenChordsAllowed = True
    pass

    if partname in ("PART KEYS", "Keyboard"):
        chordLimit = chord_limit_keys
    else:
        chordLimit = chord_limit
    pass

    for diff in diff_array:

        notesOn.update( { "lane":[] } )
        notesOff.update( { "lane":[] } )

        notesAll = sorted(set( get_data_indexes("trackNotesOn",partname,f"{diff}") + get_data_indexes("trackNotesOff",partname,f"{diff}") ))

        # Gather the notes for checking.
        for note in notes_lane:

            tempNotesOn = get_data_indexes("trackNotesOn",partname,f"{diff}_{note}")
            tempNotesOff = get_data_indexes("trackNotesOff",partname,f"{diff}_{note}")

            notesOn.update( { f"{note}" : tempNotesOn } )
            notesOff.update( { f"{note}" : tempNotesOff } )

            if note in notes_lane:
                notesOn["lane"] += tempNotesOn
                notesOff["lane"] += tempNotesOff

        # Check the notes.
        for note in notesAll:

            if note in notesOff["lane"]:
                lanesUsed -= notesOff["lane"].count(note)

                if lanesUsed == 0:
                    chordHappening = False
                else:
                    if not brokenChordsAllowed:
                        if lastReportedTime != noteStartTime:
                            lastReportedTime = noteStartTime
                            output_add("issues_critical", f"{partname} | {format_location(noteStartTime)} | Broken chord on {diff_array[diff]}.")
                            result = False
                        pass
                    pass
                pass

            pass

            if note in notesOn["lane"]:

                if lanesUsed == 0:
                    noteStartTime = note
                else:
                    if not brokenChordsAllowed:
                        if noteStartTime != note:
                            if lastReportedTime != noteStartTime:
                                lastReportedTime = noteStartTime
                                output_add("issues_critical", f"{partname} | {format_location(noteStartTime)} | Broken chord on {diff_array[diff]}.")
                                result = False
                            pass
                        pass
                    pass
                pass

                lanesUsed += notesOn["lane"].count(note)

                if lanesUsed > 1:
                    chordHappening = True
                pass

                # Chord limit testing here, as we can use this for broken chords.
                if lanesUsed > chordLimit[diff]:
                    if chordLimit[diff] == 1:
                        output_add("issues_major", f"{partname} | {format_location(noteStartTime)} | Chords are not allowed on {diff_array[diff]}.")
                        result = False
                    else:
                        output_add("issues_major", f"{partname} | {format_location(noteStartTime)} | Too many notes in chord on {diff_array[diff]}. Found {lanesUsed}, max is {chord_limit[diff]}.")
                        result = False
                    pass
                pass

            pass
        pass
    pass

    output_add("check_results", f"{partname} | {inspect.stack()[0][3]} | {result}")
    return
pass

def rbn_keys_real_shifts(partname:str):
    set_source_data()
    
    print(f"Processsing ranges for {partname}...")
    result = True

    diff = partname[len(partname)-1].lower()

    # The amount of time that notes can be seen on screen in seconds.
    trackLengthList     = [(138/60), (115/60), (93/60), (69/60)]
    trackLengthListAIM  = [(93/60), (87/60), (81/60), (75/60)]
    trackLengthDiffs    = ["e","m","h","x"]

    trackLength      = trackLengthList[trackLengthDiffs.index(diff)]
    trackLengthAIM   = trackLengthListAIM[trackLengthDiffs.index(diff)]

    noteRangeIndex  = [57,55,53,52,50,48]
    noteRangeNames  = [
        "range_a2_c4",
        "range_g2_b3",
        "range_f2_a3",
        "range_e2_g3",
        "range_d2_f3",
        "range_c2_e3"
    ]

    noteRange       = [ [],[],[],[],[],[] ]

    # Generate a list of vaild notes to check for.
    noteKeys = []

    for note in notename_array["PROKEYS"]:

        # Create Note Ranges
        for index, noteRangeCheck in enumerate(noteRangeIndex):
            if note >= noteRangeCheck:
                if note <= noteRangeCheck + 16:
                    noteRange[index].append(notename_array["PROKEYS"][note])
                pass
            pass
        pass

        # Create Notes
        if notename_array["PROKEYS"][note].startswith("note"):
            noteKeys.append(notename_array["PROKEYS"][note])
        pass

    pass


    # Create a list of all the notes we are looking for.
    notesOn         = get_data_indexes( "trackNotesOn",    partname, "note" )
    notesOff        = get_data_indexes( "trackNotesOff",   partname, "note" )
    notesOnRanges   = get_data_indexes( "trackNotesOn",    partname, "range" )

    notesAll        = sorted( set( notesOn + notesOff + notesOnRanges ) )

    notesHappening  = []

    currentRangeTime    = 0
    currentRange        = []
    pastRange           = []

    # Check the notes
    for note in notesAll:

        if note in notesOff:
            for key in noteKeys:
                if get_note_off(partname,key,note):
                    notesHappening.remove(key)
                pass
            pass
        pass
        
        if note in notesOnRanges:
            for nRange in noteRangeNames:
                if get_note_on(partname,nRange,note):
                    pastRange = currentRange

                    currentRange = noteRange[noteRangeNames.index(nRange)]
                    currentRangeTime = note
                    
                    for happen in notesHappening:
                        if happen not in currentRange:
                            output_add("issues_major", f"{partname} | {format_location(note)} | Sustain appears off the Track on {diff_array[diff]}.")
                            result = False
                        pass
                    pass

                pass
            pass
        pass

        if note in notesOn:
            for key in noteKeys:
                if get_note_on(partname,key,note):
                    notesHappening.append(key)

                    if joule_data.Seconds[note] < ( joule_data.Seconds[currentRangeTime] + trackLength )\
                    or joule_data.Seconds[note] < ( joule_data.Seconds[currentRangeTime] + trackLengthAIM ):
                        if key not in pastRange:
                            _outputString = f"Note '{key.replace('note_','').upper() }' appears off the Track on {diff_array[diff]}"

                            if joule_data.Seconds[note] < ( joule_data.Seconds[currentRangeTime] + trackLengthAIM ):
                                _outputString += " in All Instruments Mode"

                            _outputString += "."

                            output_add("issues_major", f"{partname} | {format_location(note)} | {_outputString}")
                            output_add("debug_3", f"{format_location(note)} | {joule_data.Seconds[note]} - {( joule_data.Seconds[currentRangeTime] + trackLength )} | {key}")
                            result = False
                        pass
                    pass

                pass
            pass
        pass

        #print(f"{format_location(note)} - {notesHappening}")

    pass

    output_add("check_results", f"{partname} | {inspect.stack()[0][3]} | {result}")

pass

def rbn_keys_real_chords(partname:str):
    set_source_data()

    print(f"Processsing chords for {partname}...")
    result = True

    notesOn       = {}
    notesOff      = {}
    notesAll      = []

    lanesUsed = 0

    noteStartTime = 0
    lastReportedTime = 0
    chordHappening = False

    chordHighest    = 48
    chordLowest     = 72

    currentRange    = 0

    noteRangeIndex  = [57,55,53,52,50,48]
    noteRanges      = [
        "range_a2_c4",
        "range_g2_b3",
        "range_f2_a3",
        "range_e2_g3",
        "range_d2_f3",
        "range_c2_e3"
    ]

    notesOn.update( { "notes":[] } )
    notesOff.update( { "notes":[] } )

    noteNames = notesname_instruments_array[partname]

    diff = partname[len(partname)-1].lower()


    # Gather the notes for checking.

    for noteCheck in range(48,73):
        tempNotesOn = ( get_data_indexes("trackNotesOn", partname, notename_array[noteNames][noteCheck], True) )
        tempNotesOff = ( get_data_indexes("trackNotesOff", partname, notename_array[noteNames][noteCheck], True) )

        notesOn.update( { f"{notename_array[noteNames][noteCheck]}" : tempNotesOn } )
        notesOff.update( { f"{notename_array[noteNames][noteCheck]}" : tempNotesOff } )

        notesOn["notes"] += tempNotesOn
        notesOff["notes"] += tempNotesOff
    pass

    _tempNotesAll = []

    for nRange in noteRanges:
        _tempOn = get_data_indexes("trackNotesOn",partname,f"{nRange}")
        notesOn.update( { f"{nRange}" : _tempOn } )

        _tempNotesAll += _tempOn

    pass

    _tempNotesAll += notesOn["notes"] + notesOff["notes"]

    notesAll = sorted(set( _tempNotesAll ))

    # Check the notes.
    for note in notesAll:

        if note in notesOff["notes"]:
            lanesUsed -= notesOff["notes"].count(note)

            if lanesUsed == 0:
                chordHappening = False
                chordHighest    = 48
                chordLowest     = 72
            pass

        pass

        for nRange in noteRanges:
            if note in notesOn[nRange]:

                if diff == "e" or diff == "m":
                    if currentRange != 0:
                        output_add("issues_major", f"{partname} | {format_location(note)} | Lane Shifts are not allowed on {diff_array[diff]}.")
                        result = False
                    pass
                pass

                currentRange = noteRangeIndex[noteRanges.index(nRange)]
                output_add("debug_3",f"{partname} | {format_location(note)} | {nRange}")

            pass
        pass

        if note in notesOn["notes"]:

            if lanesUsed == 0:
                noteStartTime = note
            pass

            lanesUsed += notesOn["notes"].count(note)

            if lanesUsed > 1:
                chordHappening = True
            pass

            for noteCheck in range(48,73):
                if note in notesOn[notename_array[noteNames][noteCheck]]:
                    if (chordLowest > noteCheck):
                        chordLowest = noteCheck
                    pass

                    if chordHighest < noteCheck:
                        chordHighest = noteCheck
                    pass

                    _tempStr = f"{partname} | {format_location(note)} | {currentRange}:{currentRange + 16} | {noteCheck} | {notename_array[noteNames][noteCheck]}"

                    if ( noteCheck < currentRange or noteCheck > ( currentRange + 16) ):
                        _tempStr += " | Outside Range"
                        output_add("issues_major", f"{partname} | {format_location(noteStartTime)} | Note is outside of Note Range on {diff_array[diff]}.")
                        result = False
                    pass

                    output_add("debug_3",_tempStr)

                pass

            pass

            if ( chordHighest - chordLowest > ( span_limit_keys_pro[diff] ) ):
                output_add("issues_major", f"{partname} | {format_location(noteStartTime)} | Found chord spanning more than {span_limit_keys_pro[diff]} notes on {diff_array[diff]}.")
                result = False
            pass

            if lanesUsed > chord_limit_keys_pro[diff]:
                if chord_limit_keys_pro[diff] == 1:
                    output_add("issues_major", f"{partname} | {format_location(noteStartTime)} | Chords are not allowed on {diff_array[diff]}.")
                    result = False
                else:
                    output_add("issues_major", f"{partname} | {format_location(noteStartTime)} | Too many notes in chord on {diff_array[diff]}. Found {lanesUsed}, max is {chord_limit_keys_pro[diff]}.")
                    result = False
                pass
            pass

        pass
    pass

    output_add("check_results", f"{partname} | {inspect.stack()[0][3]} | {result}")
    return

pass
