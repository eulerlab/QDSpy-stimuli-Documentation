#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
import QDS

QDS.Initialize("Flashes_BigSmall")

# Define global stimulus parameters
#
p = {"nTrials"          : 3,
     "TimeOn_s"         : 1.0,
     "TimeOff_s"        : 2.0,
     "dxStimStart"      : 25,   # Stimulus size centre
     "nSteps"           : 10,
     "durFr_s"          : 1/60.0, # Frame duration
     "nFrPerMarker"     : 1,
     "RGB"              : (255,255,255)}
QDS.LogUserParameters(p)

# Do some calculations
#
durMarker_s    = p["durFr_s"] *p["nFrPerMarker"]

# Define stimulus objects
#
QDS.DefObj_Ellipse(1, 20,20)
QDS.DefObj_Ellipse(2, 40,40)
QDS.DefObj_Ellipse(3, 60,60)
QDS.DefObj_Ellipse(4, 80,80)
QDS.DefObj_Ellipse(5, 100,100)
QDS.DefObj_Ellipse(6, 150,150)
QDS.DefObj_Ellipse(7, 200,200)
QDS.DefObj_Ellipse(8, 300,300)
QDS.DefObj_Ellipse(9, 400,400)
QDS.DefObj_Ellipse(10, 500,500)

# Start of stimulus run
#
QDS.StartScript() 

QDS.SetBkgColor((0,0,0))
QDS.Scene_Clear(1.0, 0)

for iT in range(p["nTrials"]):
  for iS in range(p["nSteps"]):
    QDS.SetObjColor (iS+1, [iS+1], [p["RGB"]])
    QDS.Scene_Render(durMarker_s, iS+1, [iS+1], [(0,0)], 1)
    QDS.Scene_Render(p["TimeOn_s"] - durMarker_s, iS+1, [iS+1], [(0,0)], 0)
    QDS.Scene_Clear(p["TimeOff_s"], 0)
  QDS.Scene_Clear(3.0, 0)
# Finalize stimulus
#
QDS.EndScript()

# --------------------------------------------------------------------------
