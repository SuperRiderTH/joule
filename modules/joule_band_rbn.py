import joule_data

from joule_system import *
from joule_band_handlers import *

import joule_data_rockband
import joule_data_clonehero
import joule_data_yarg

# We need this for later if HARM3 is accessed.
indexesVocalPhrasesOn_HARM2 = []
indexesVocalPhrasesOff_HARM2 = []


def set_source_data():

    global notename_array
    global notes_pads
    global notes_drum
    global notes_lane
    global diff_array
    global diff_highest
    global chord_limit
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
    chord_limit_keys_pro = base.chord_limit_keys_pro
    note_overdrive = base.note_overdrive
    notesname_instruments_array = base.notesname_instruments_array
    span_limit_keys_pro = base.span_limit_keys_pro

    joule_data.BrokenChordsAllowed = base.brokenChordsAllowed
    joule_data.LowerHOPOsAllowed = base.lowerHOPOsAllowed

pass


# template function
def validate_THING(partname:str):
    set_source_data()

    for diff in diff_array:
        print(f"Processsing THING for {partname} on {diff_array[diff]}...")
    return

pass

def validate_spacing(partname:str):

    if notesname_instruments_array[partname] == "VOCALS":
        validate_spacing_vocals(partname)
        
    # TODO: Other instruments.

pass

def validate_spacing_vocals(partname:str):
    set_source_data()

    global notename_array

    noteLength64 = joule_data.GameDataFile.ticks_per_beat / 16
    noteLength32 = noteLength64 * 2
    noteLength16 = noteLength64 * 4

    print(f"Processsing vocal note spacing for {partname}...")

    global indexesVocalPhrasesOn_HARM2
    global indexesVocalPhrasesOff_HARM2

    indexesVocalPhrasesOn   = get_data_indexes("trackNotesOn", partname, 'phrase')
    indexesVocalPhrasesOff  = get_data_indexes("trackNotesOff", partname, 'phrase')
    indexesVocalsLyrics     = get_data_indexes("trackNotesLyrics", partname, 'lyrics')


    # Store this for HARM3 use.
    if partname == "HARM2":
        indexesVocalPhrasesOn_HARM2 = indexesVocalPhrasesOn
        indexesVocalPhrasesOff_HARM2 = indexesVocalPhrasesOff

    if partname == "HARM3":
        if len(indexesVocalPhrasesOn_HARM2) > 0:
            indexesVocalPhrasesOn = indexesVocalPhrasesOn_HARM2
            indexesVocalPhrasesOff = indexesVocalPhrasesOff_HARM2
        else:
            return
        pass
    pass


    # Note spacing
    # ========================================

    indexesVocalsOn = get_data_indexes("trackNotesOn", partname, "note")
    indexesVocalsOff = get_data_indexes("trackNotesOff", partname, "note")

    for index, note in enumerate(indexesVocalsOn):
        if index > 0:
            if note < indexesVocalsOff[index - 1] + (noteLength32):
                output_add("issues_major", f"{partname} | {format_location(note)} | Vocal notes should have a 32nd note gap from the previous note.")

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
                        if indexesVocalPhrasesOn[index] < ( indexesVocalPhrasesOff[index - 1] + (noteLength16) ):
                            output_add("issues_critical", f"{partname} | {format_location(note)} | Spoken words starting a Phrase require a 16th note gap between Phrase Markers.")

            if currentLyric.endswith('^') or currentLyric.endswith('#'):
                lastWordIsPitched = False
            else:
                lastWordIsPitched = True
            pass

            firstNote = False
        pass
    pass

pass

def rbn_hopos(partname:str):
    set_source_data()
    
    if joule_data.LowerHOPOsAllowed:
        return
    else:
        
        print(f"Processsing HOPOs for {partname}...")

        for diff in diff_array:
            if diff == "m" or diff == "e":
                if len(get_data_indexes("trackNotesOn",partname,f"{diff}_hopo")) > 0:
                    output_add("issues_major", f"{partname} | Forced HOPOs are not allowed on {diff_array[diff]}.")
                pass
            pass
        pass
    pass

pass

def tow_check():
    
    phrasesP1 = get_data_indexes("trackNotesOn", "PART VOCALS", 'phrase_p1')
    phrasesP2 = get_data_indexes("trackNotesOn", "PART VOCALS", 'phrase_p2')
    
    if len(phrasesP2) > 0:
        if len(phrasesP1) != len(phrasesP2):
            output_add("issues_major", f"PART VOCALS | Player 1 and 2 do not have an equal amount of Tug of War Markers.")
        pass
    pass

pass


def rbn_vocals_lyrics(partname:str):
    print(f"Processsing Lyrics for {partname}...")
    set_source_data()

    global indexesVocalPhrasesOn_HARM2
    global indexesVocalPhrasesOff_HARM2

    indexesVocalPhrasesOn        = get_data_indexes("trackNotesOn", partname, 'phrase')
    indexesVocalPhrasesOff       = get_data_indexes("trackNotesOff", partname, 'phrase')
    indexesVocalsLyrics    = get_data_indexes("trackNotesLyrics", partname, 'lyrics')

    # Store this for HARM3 use.
    if partname == "HARM2":
        indexesVocalPhrasesOn_HARM2 = indexesVocalPhrasesOn
        indexesVocalPhrasesOff_HARM2 = indexesVocalPhrasesOff
    pass

    if partname == "HARM3":
        if len(indexesVocalPhrasesOn_HARM2) > 0:
            indexesVocalPhrasesOn = indexesVocalPhrasesOn_HARM2
            indexesVocalPhrasesOff = indexesVocalPhrasesOff_HARM2
        else:
            output_add("issues_critical", "HARM2 Phrase Markers do not exist! HARM3 can not be processed!")
            return
        pass
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
                syllable = syllable.strip()
            pass

            # Latin-1 Check.
            for character in syllable:
                if ( ord(character) > 255  ):
                    output_add("issues_critical", f"{partname} | {format_location(note)} | '{character}' in {syllableRaw} is a Non-Latin-1 character.")
                pass
            pass

            if partname == "PART VOCALS":
                if syllable.endswith("$"):
                    output_add("issues_major", f"{partname} | {format_location(note)} | Lyrics can not be hidden in PART VOCALS, found in '{syllableRaw}'.")
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
            pass

            # Check syllable for special characters
            for character in syllable:
                if character in punctuationError:
                    output_add("issues_minor", f"{partname} | {format_location(note)} | {punctuationErrorFriendly[character]} should never be used, found in '{syllableRaw}'.")
                pass
            pass

            # Capitalization checking.
            if syllable[0].isalpha():
                if phraseStart or checkCaps:
                    phraseStart = False
                    if not syllable[0].isupper():
                        output_add("issues_minor",f"{partname} | {format_location(note)} | '{syllableRaw}' should be uppercase.")
                    pass
                    checkCaps = False
                else:
                    if syllable not in reservedSyllables:
                        if syllable[0].isupper():
                            output_add("issues_minor",f"{partname} | {format_location(note)} | '{syllableRaw}' should not be uppercase.")
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

    return

pass

def rbn_guitar_chords(partname:str):
    set_source_data()

    notesOn = {}
    notesOff = {}

    notesOnDiff = {}
    notesOffDiff = {}
    notesAllDiff = {}

    notesOnHighest = sorted( set( get_data_indexes("trackNotesOn",partname,f"{diff_highest}") ) )
    
    # Init the notes for each difficulty.
    # ========================================
    
    for diff in diff_array:
        
        notesOnDiff[diff] = {}
        notesOffDiff[diff] = {}
        notesAllDiff[diff] = {}

        for note in notes_lane:
            notesOnDiff[diff].update( { f"{note}" : get_data_indexes("trackNotesOn",partname,f"{diff}_{note}") } )
            notesOffDiff[diff].update( { f"{note}" : get_data_indexes("trackNotesOff",partname,f"{diff}_{note}") } )
            notesAllDiff[diff] = sorted(set( get_data_indexes("trackNotesOn",partname,f"{diff}") + get_data_indexes("trackNotesOff",partname,f"{diff}") ))
        pass    
    pass

    for diff in diff_array:
        
        if len(get_data_indexes("trackNotesOn",partname,f"{diff}")) == 0:
            output_add("debug_3", f"{partname} | rbn_guitar_chords | No notes found on {diff_array[diff]}.")
            continue

        print(f"Processsing chords for {partname} on {diff_array[diff]}...")

        notesOn      = notesOnDiff[diff]
        notesOff     = notesOffDiff[diff]

        # notesAll is a list of every position where there is a note on and off, without any duplicates.
        notesAll      = notesAllDiff[diff]


        # Green Orange chord detection
        # ========================================

        for note in notesOn["orange"]:
            if note in notesOn["green"]:
                if note in notesOn["red"] or note in notesOn["yellow"] or note in notesOn["blue"]:
                    output_add("issues_major", f"{partname} | {format_location(note)} | Found note paired with Green and Orange gems on {diff_array[diff]}.")
                pass

                # Green Orange chords are not allowed on anything below Expert.
                if diff != "x":
                    output_add("issues_major", f"{partname} | {format_location(note)} | Green and Orange chords are not allowed on {diff_array[diff]}.")
                pass
            pass
        pass


        rbn_broken_chords(partname,diff)

        # Chord note counting
        # ========================================

        for note in notesAll:
            noteCount = 0
            noteCountHighest = 0

            for noteLane in notes_lane:
                if note in notesOn[noteLane]:
                    noteCount += 1
            
            # If there isn't any notes here, skip the rest.
            if noteCount == 0:
                continue


            if diff != diff_highest:

                # If chords are not allowed, we skip checking.
                if chord_limit[diff] > 1:

                    for noteLaneHighest in notes_lane:
                        if note in notesOnDiff[diff_highest][noteLaneHighest]:
                            noteCountHighest += 1
                        pass
                    pass

                    if noteCountHighest > 1:
                        # This note should be a chord.
                        if noteCount < 2:
                            output_add("issues_major", f"{partname} | {format_location(note)} | Single note found on {diff_array[diff]}, expected a chord based on {diff_array[diff_highest]}.")
                        pass
                    pass
                pass 
            pass

    return

pass


def rbn_drums_limbs(partname:str):
    set_source_data()
        

    for diff in diff_array:
        
        if len(get_data_indexes("trackNotesOn",partname,f"{diff}")) == 0:
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
                pass
                if gems_with_kick > 0 and diff == "e":
                    output_add("debug_2", f"{partname} | {kick} | {format_location(kick)} | {gems_with_kick} Gems | {diff_array[diff]}")
                    output_add("issues_major", f"{partname} | {format_location(kick)} | No Gems are allowed with Kick notes on {diff_array[diff]}.")
                pass
            pass
        pass

    pass

    return

pass

def rbn_drums_fills(partname:str):
    set_source_data()

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
            elif od_note == item:
                output_add("issues_critical",f"{partname} | {format_location(od_note)} | Overdrive ends right before Drum Fill {index+1}.")
            else:
                output_add("issues_critical",f"{partname} | {format_location(od_note)} | Overdrive overlaps Drum Fill {index+1}.")
            pass

        if fillStartAll.count(fillStart[index]) != 5:
            output_add("issues_critical",f"{partname} | {format_location(fillStart[index])} | Drum Fill {index+1} notes do not start simultaneously.")
        pass

        if fillEndAll.count(fillEnd[index]) != 5:
            output_add("issues_critical",f"{partname} | {format_location(fillEnd[index])} | Drum Fill {index+1} notes do not end simultaneously.")
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
        pass
    
        if note in rollSingleStart or note in rollSwellStart:
            if inRollSingle == True and inRollSwell == True:
                output_add("issues_critical",f"{partname} | {format_location(note)} | Drum Roll and Swell happening simultaneously.")
            pass
        pass
    
    pass

    return

pass

# template function
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
            for diff in diff_array:
                
                if len(get_data_indexes("trackNotesOn",track,f"{diff}")) == 0:
                    output_add("debug_3", f"{track} | validate_instrument_phrases | No notes found on {diff_array[diff]}.")
                    
                    if joule_data.GameSource in joule_data.GameSourceRBLike and joule_data.GameSource != "yarg":
                        output_add("issues_critical", f"{track} | No notes found on {diff_array[diff]}.")
                    
                    continue
                
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
                
                
                
                notesAll = sorted(set(notesOn + notesOff + checkOn + checkOff))
                
                for note in notesAll:
                    
                    if note in checkOff:
                        inSpecialNote = False
                        
                        if checkNextNote:
                            output_add("issues_critical", f"{track} | {format_location(lastNoteStart)} | No notes in {noteType} Phrase on {diff_array[diff]}.")
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
        pass

    return

pass



def rbn_broken_chords(partname:str, diff:str):
    set_source_data()
    
    notesOn       = {}
    notesOff      = {}
    notesAll      = []

    lanesUsed = 0

    noteStartTime = 0
    lastReportedTime = 0
    chordHappening = False
    brokenChordsAllowed = False

    if joule_data.BrokenChordsAllowed\
    or partname in ("PART KEYS", "Keyboard"):
        brokenChordsAllowed = True
    pass

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
                        pass
                    pass
                pass
            pass

            lanesUsed += notesOn["lane"].count(note)

            if lanesUsed > 1:
                chordHappening = True
            pass

            # Chord limit testing here, as we can use this for broken chords.
            if lanesUsed > chord_limit[diff]:
                if chord_limit[diff] == 1:
                    output_add("issues_major", f"{partname} | {format_location(noteStartTime)} | Chords are not allowed on {diff_array[diff]}.")
                else:
                    output_add("issues_major", f"{partname} | {format_location(noteStartTime)} | Too many notes in chord on {diff_array[diff]}. Found {lanesUsed}, max is {chord_limit[diff]}.")
                pass
            pass

        pass
    pass

    return
pass

def rbn_keys_real_chords(partname:str):
    set_source_data()
    
    print(f"Processsing chords for {partname}...")

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
        "range_c2_c3"
    ]

    notesOn.update( { "notes":[] } )
    notesOff.update( { "notes":[] } )
    
    noteNames = notesname_instruments_array[partname]
    
    diff = partname[len(partname)-1].lower()


    # Gather the notes for checking.
    
    for noteCheck in range(48,73):
        tempNotesOn = ( get_data_indexes("trackNotesOn", partname, notename_array[noteNames][noteCheck]) )
        tempNotesOff = ( get_data_indexes("trackNotesOff", partname, notename_array[noteNames][noteCheck]) )
        
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
                    pass
                
                    output_add("debug_3",_tempStr)
                    
                pass
            
            pass
        
            if ( chordHighest - chordLowest > ( span_limit_keys_pro[diff] ) ):
                output_add("issues_major", f"{partname} | {format_location(noteStartTime)} | Found chord spanning more than {span_limit_keys_pro[diff]} notes on {diff_array[diff]}.")
            pass

            if lanesUsed > chord_limit_keys_pro[diff]:
                if chord_limit_keys_pro[diff] == 1:
                    output_add("issues_major", f"{partname} | {format_location(noteStartTime)} | Chords are not allowed on {diff_array[diff]}.")
                else:
                    output_add("issues_major", f"{partname} | {format_location(noteStartTime)} | Too many notes in chord on {diff_array[diff]}. Found {lanesUsed}, max is {chord_limit_keys_pro[diff]}.")
                pass
            pass

        pass
    pass

    return

pass