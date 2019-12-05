Harmonicdog Utilities
---------------------


## Welcome
Code and scripts associated with the MultiTrack DAW iOS app

***
*mtdawRead.py*
This script reads a MultiTrack DAW song project and prints some info about the song to the terminal. Uses PyObjC to parse the `Tracks2.plist` and `project.plist` files. Also decodes the wav filenames into metadata for each wav file in the  projects `Bin` directory. Call it with the song project directory as its only argument, e.g
	./mtdawRead.py path/to/song.mtdaw

*Dependencies:*
python3

```python
pip install pyobjc
pip install crccheck
```

