# Joule
A modular rhythm game validation tool.

## How to run
- Some variables can be changed using values in `joule_config.ini`

### Command line usage:

Using Python 3, run `joule.py` with the location of the game file you wish to run checks on. A .json file will be created next to the file that is being checked.

If you are loading MIDI files, `mido` is required.

A second argument can be given to specify a different game to run checks for. If none is provided, the default source located in `joule_data.py` is assumed.

- Example: `joule.py D:\RockBandJunk\song.mid rb3`

Alternatively, you can import the function `joule_run` and provide both arguments.

- Example: `joule_run("D:\RockBandJunk\song.mid", "rb3")`


### Using REAPER:
- Mido is not required when using Joule inside of REAPER.
  
REAPER must have Python 3 enabled for use in ReaScripts.

Once Python is enabled, all you need to do is run `joule.py` as a ReaScript in REAPER.

The default game source located in `joule_data.py` or `joule_config.ini` is used.

## Supported Games:
* Rock Band 3: `rb3`
* Rock Band 2: `rb2`
* Lego Rock Band: `lego`
* The Beatles: Rock Band: `beatles`
* Phase Shift: `ps`
* Yet Another Rhythm Game: `yarg`
  * Missing True Drums support.
* Clone Hero: `ch`
  * Missing 6 Lane support.
* Guitar Hero World Tour: Definitive Edition: `ghwtde`
  * Does not support native files, supports MIDI and .chart.
