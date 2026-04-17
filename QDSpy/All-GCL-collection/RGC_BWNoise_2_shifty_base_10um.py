#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
import QDS
import os
import sys
import random

# Initialize QDS
#
QDS.Initialize(
    "RGC_Noise_shifty_b10um ",
    "'noise' in fingerprinting stimulus set, with pixel shift, base=10um"
  )

# Define global stimulus parameters
#
# pylint: enable=bad-whitespace
p = {"durStim_s"       : 0.200,
     "boxDx_um"        : 40,
     "boxDy_um"        : 40,
     "base_um"         : 10,
     "fIntenW"         : 255,    # intensity factor
                                 # (pixel value(0,1) x fIntenW)
     "fNameNoise"      : "RGC_BWNoise_official",
     "durFr_s"         : 1/60.0, # Frame duration
     "nFrPerMarker"    : 3}
# pylint: disable=bad-whitespace

QDS.LogUserParameters(p)

# Do some calculations and preparations
#
fPath = QDS.GetStimulusPath()
durMarker_s = p["durFr_s"] *p["nFrPerMarker"]
fname_noise = p["fNameNoise"] +'.txt'
fname_shift = p["fNameNoise"] +"_shifty_{0}um".format(p["base_um"]) +".txt"

# Read file with M sequence
#
try:
  f = open(fPath +"\\" +fname_noise, 'r')
  iLn = 0
  Frames = []

  while True:
    line = f.readline()
    if not line:
      break
    parts = line.split(',')
    if iLn == 0:
      nX = int(parts[0])
      nY = int(parts[1])
      nFr = int(parts[2])
      nB = nX*nY
    else:
      Frame = []
      for iB in range(1, nB+1):
        r = int(parts[iB-1]) *p["fIntenW"]
        Frame.append((r,r,r))
      Frames.append(Frame)
    iLn += 1
finally:
  f.close()

# ***************************************************************************
# Generate new random shift series;
# ACTIVATE ONLY IF YOU KNOW WHAT YOU ARE DOING
"""
try:
  f = open(fPath +"\\" +fname_shift, "w")
  s1 = p["boxDx_um"] -p["base_um"]
  ds = p["base_um"]
  f.write(f"{nFr}\n")
  for iF in range(nFr):
    xs = random.randrange(-s1, s1, ds)
    ys = random.randrange(-s1, s1, ds)
    f.write(f"{xs},{ys}\n")
finally:
  print("Generated file `"+ fname_shift +"`.")
  f.close()
  sys.exit()
"""  
# ***************************************************************************
# Read file with random shifts
#
try:
  f = open(fPath +"\\" +fname_shift, 'r')
  iLn = 0
  Shifts = []

  while True:
    line = f.readline()
    if not line:
      break
    parts = line.split(',')
    if iLn == 0:
      nFrShifts = int(parts[0])
      assert nFrShifts == nFr, "# of noise frames and shifts do not match!!"
    else:
      Shifts.append((int(parts[0]), int(parts[1])))
    iLn += 1
finally:
  f.close()
  assert iLn-1 == nFrShifts, "Incorrect number of lines in shift file"


# Define objects
#
# Create box objects, one for each field of the checkerboard, such that we
# can later just change their color to let them appear or disappear
#
for iB in range(1, nB+1):
  QDS.DefObj_Box(iB, p["boxDx_um"], p["boxDy_um"], 0)

# Create two lists, one with the indices of the box objects and one with
# their positions in the checkerboard; these lists later facilitate using
# the Scene_Render() command to display the checkerboard
#
BoxIndList = []
BoxPosList = []
for iX in range(nX):
  for iY in range(nY):
    iB = 1 +iX +iY*nX
    x  = iX*p["boxDx_um"] -(p["boxDx_um"]*nX/2)
    y  = iY*p["boxDy_um"] -(p["boxDy_um"]*nY/2)
    BoxIndList.append(iB)
    BoxPosList.append((x,y))

# Start of stimulus run
#
QDS.StartScript()
QDS.Scene_Clear(1.0, 0)

for iF in range(nFr):
   QDS.SetObjColor(nB, BoxIndList, Frames[iF])
   SBoxPosList = [
       (BoxPosList[i][0] +Shifts[iF][0],
        BoxPosList[i][1] +Shifts[iF][1])
       for i in range(len(BoxPosList))
     ]
   QDS.Scene_Render(durMarker_s, nB, BoxIndList, BoxPosList, 1)
   QDS.Scene_Render(p["durStim_s"] -durMarker_s, nB, BoxIndList, SBoxPosList, 0)

QDS.Scene_Clear(1.0, 0)

# Finalize stimulus
#
QDS.EndScript()

# -----------------------------------------------------------------------------
