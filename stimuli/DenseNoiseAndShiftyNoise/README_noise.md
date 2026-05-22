# Noise Versions

There are two noise versions:
1. is standard dense noise: 1500 @ 5 Hz frames (=5 min), 40 µm checkers (the DN.py and Noise_RGC.py are actually identical)
2. the same but shifted on a 10 µm grid

There are 2 things worth noting about these stimuli.
1. The standard dense noise is not completely centered on the recording field. It is shifted by half a pixel in both x and y.
2. The original shifty noise stimulus has a bug, such that the shift is not applied when the trigger is on (the first 50 ms of each frame), but only applied when it is off (the last 150 ms of each frame), effectively resulting in a 20 Hz instead of 5 Hz stimulus.