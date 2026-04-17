#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
import os
import QDS

# Initialize QDS
#
QDS.Initialize("GreenCS_5Hz", "")

# Define global stimulus parameters
#
p = {"StimRepetitions"  : 1,
     "durStim_s"        : 0.2,
     "TriggerFreq"      : 1,       # in Hz
     "CentreDiameter"   : 250,  
     "OuterRadius"      : 350, 
     "InnerRadius"      : 125,
     "fIntenW"          : 255,    # intensity factor 
                                  # (pixel value(0,1) x fIntenW)
     "fNameNoise_cGreen": "ColouredCS_cGreen",
     "fNameNoise_sGreen": "ColouredCS_sGreen",
     "durFr_s"          : 1/60.0, # Frame duration
     "nFrPerMarker"     : 1}
     
QDS.LogUserParameters(p)

# Do some calculations and preparations

fPath         = QDS.GetStimulusPath()
durMarker_s   = p["durFr_s"] *p["nFrPerMarker"]
nFrPerTrigger = p["TriggerFreq"]/p["durStim_s"]

# Read files with M sequencefor centre and surround, green and blue LED

try:
  f_cgreen_path = os.path.join(fPath, p["fNameNoise_cGreen"] + '.txt')
  f_cgreen        = open(f_cgreen_path, 'r') # centre spot green LED
  f_sgreen_path = os.path.join(fPath, p["fNameNoise_sGreen"] + '.txt')
  f_sgreen        = open(f_sgreen_path, 'r') # surround spot green LED
  iLn       = 0 
  Frames_centre    = []
  Frames_surround    = []
    
  while 1:
    line_cgreen   = f_cgreen.readline()
    line_sgreen   = f_sgreen.readline()
    if not line_cgreen:
      break
    if iLn == 0:
      nFr   = int(line_cgreen)
    else:
     r_cgreen  = int(line_cgreen) *p["fIntenW"]
     r_sgreen  = int(line_sgreen) *p["fIntenW"]

     Frames_centre.append([(0,r_cgreen,0)])
     Frames_surround.append([(0,r_sgreen,0)])
    iLn += 1
finally:
  f_cgreen.close()
  f_sgreen.close()

# Define centre and surround objects

QDS.DefObj_Ellipse(1,p["CentreDiameter"],p["CentreDiameter"]) # centre spot
QDS.DefObj_Sector (2, p["OuterRadius"], p["InnerRadius"], 180, 360, 1) # surround sector

# Start of stimulus run
#
QDS.StartScript()
QDS.SetBkgColor((0,0,0))
QDS.Scene_Clear(1.0, 0)

for iL in range(p["StimRepetitions"]):
  iT = 1 
  for iF in range(nFr):
    if iF == 0:
      QDS.SetObjColor(1, [1], Frames_centre[iF])
      QDS.SetObjColor(2, [2], Frames_surround[iF])
      QDS.Scene_Render(durMarker_s, 2, [1,2], [(0,0),(0,0)], 1)
      QDS.Scene_Render(p["durStim_s"]-durMarker_s, 2, [1,2], [(0,0),(0,0)], 0)
      iT = 1
    elif iT == nFrPerTrigger:
      QDS.SetObjColor(1, [1], Frames_centre[iF])
      QDS.SetObjColor(2, [2], Frames_surround[iF])
      QDS.Scene_Render(durMarker_s, 2, [1,2], [(0,0),(0,0)], 1)
      QDS.Scene_Render(p["durStim_s"]-durMarker_s, 2, [1,2], [(0,0),(0,0)], 0)
      iT = 1
    else:
      QDS.SetObjColor(1, [1], Frames_centre[iF])
      QDS.SetObjColor(2, [2], Frames_surround[iF])
      QDS.Scene_Render(p["durStim_s"], 2, [1,2], [(0,0),(0,0)], 0)
      iT = iT + 1
QDS.Scene_Clear(1.0, 0)

# Finalize stimulus
#
QDS.EndScript()

# -----------------------------------------------------------------------------
