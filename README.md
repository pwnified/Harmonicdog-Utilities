Harmonicdog Utilities
---------------------


## Welcome
Ccode and scripts associated with the MultiTrack DAW iOS app

***
*mtdawRead.py*
This script reads a MultiTrack DAW song project and prints some info about the song to the terminal. Uses PyObjC to parse the `Tracks2.plist` and `project.plist` files. Also decodes the wav filenames into the metadata for each wav file in the song projects `Bin` directory. To use the script, call it with the song project directory as its only argument, e.g
	ReadProject.py "path/to/song.mtdaw"

*Dependencies:*
python3

`pip install pyobjc`
`pip install crccheck`

