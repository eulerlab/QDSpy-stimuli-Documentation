#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
import os
import QDS 

# Initialize QDS 
#
QDS.Initialize("BlueCS_5Hz", "")

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
     "fNameNoise_cBlue" : "ColouredCS_cBlue",
     "fNameNoise_sBlue" : "ColouredCS_sBlue",
     "durFr_s"          : 1/60.0, # Frame duration
     "nFrPerMarker"     : 1}
     
QDS.LogUserParameters(p)

# Do some calculations and preparations

fPath         = QDS.GetStimulusPath()
durMarker_s   = p["durFr_s"] *p["nFrPerMarker"]
nFrPerTrigger = p["TriggerFreq"]/p["durStim_s"]

# Read files with M sequencefor centre and surround, green and blue LED

try:
  f_cblue_path = os.path.join(fPath, p["fNameNoise_cBlue"] +'.txt')
  f_sblue_path = os.path.join(fPath, p["fNameNoise_sBlue"] +'.txt')
  f_cblue         = open(f_cblue_path, 'r') # centre spot blue LED
  f_sblue         = open(f_sblue_path, 'r') # surround spot blue LED
  iLn       = 0 
  Frames_centre    = []
  Frames_surround    = []
    
  while 1:
    line_cblue    = f_cblue.readline()
    line_sblue    = f_sblue.readline()
    if not line_cblue:
      break
    if iLn == 0:
      nFr   = int(line_cblue)
    else:
     r_cblue   = int(line_cblue) *p["fIntenW"]
     r_sblue   = int(line_sblue) *p["fIntenW"]

     Frames_centre.append([(0,0,r_cblue)])
     Frames_surround.append([(0,0,r_sblue)])
    iLn += 1
finally:
  f_cblue.close()
  f_sblue.close()

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
