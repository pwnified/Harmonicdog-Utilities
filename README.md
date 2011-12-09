Harmonicdog Utilities
---------------------


## Welcome
This is a place for public code and scripts associated with the MultiTrack DAW iOS app. Feel free to use anything here for your own projects or converters. If you would like develop a converter to/from another DAW, let us know!

***
*ReadProject.py*
This python script reads a MultiTrack DAW song project and prints some info about the song to the terminal. Uses PyObjC to parse the `Tracks.plist` and `project.plist` files. Also decodes the wav filenames into the metadata for each wav file in the song projects `Bin` directory. To use the script, call it with the song project directory as its only argument, e.g
    ./ReadProject.py "/Path/To/SongFolders/My Song 1"

