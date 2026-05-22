There are 4 versions:

1. (v1) high UV (test_images_rand_right.jpg, ...)
2. (v2) adjusted UV, but flipped for Setup 1 (MC2_test_rgb_72x64_right.jpg, ...)
3. (v2new) similar as v2: adjusted UV, but also correctly rotated for Setup 1 (MC2_test_rgb_72x64_right-new.jpg, ...); The QDSPy script is also called "*new*"
4. (v3) MC3 ..., like the previous one but with moving blobs. Was not really used so far.

Notes:
v1 only makes sense for Setup3 because it's signal is in the first and second channel (on Setup3 that is UV and green).
All other versions currently only work on Setup1 as they assume the color inversion (RGB to BGR) from Setup1.

v1 was replaced as it leads to has strong UV signals, so scence changes need some adaptation.
v2 was incorrectly flipped because of some bug and using the number 4 to test the calibration, which is roughly symmetric along one axis.
v2new fixes this bug.
v3 is adds more local motion to the stimulus.
