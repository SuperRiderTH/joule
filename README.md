# Joule
A modular rhythm game validation tool.

## How to run
* Requirements: mido

Run `joule.py` with the location of the game file you wish to run checks on. A .json file will be written next to the game file that is being checked.

A second argument can be given to specify a different game to run checks for. If none is provided, Rock Band 3 is assumed.

Example: `joule.py D:\RockBandJunk\song.mid rb3`

Alternatively, you can import the function `joule_run` and provide both arguments.

Example: `joule_run("D:\RockBandJunk\song.mid", "rb3")`

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
