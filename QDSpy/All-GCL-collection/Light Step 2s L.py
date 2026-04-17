#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
import collections
from functools import partial
import QDS
import math 

# Define global stimulus parameters
p = {'_sName'          : "Light Step",
     '_sDescr'         : "2 seconds ON/OFF light step",
     "nTrials"         : 1000, 
     "tSteadyOFF_s"    : 1.0,    # Light OFF at beginning ...
     "tSteadyON_s"     : 2.0,    # Light 100% ON before
     "IHalf"           : 127,
     "IFull"           : 254,
     "dxStim_um"       : 100,   # Stimulus size
     "durFr_s"         : 1/60.0, # Frame duration
     "nFrPerMarker"    : 3}
     
def buildStimulus(p):
    p['durMarker_s']     = p["durFr_s"]*p["nFrPerMarker"]
    p['RGB_IHalf']       = 3 *(p["IHalf"],)
    p['RGB_IFull']       = 3 *(p["IFull"],)
    
    # Define stimulus objects
    QDS.DefObj_Ellipse(1, p["dxStim_um"], p["dxStim_um"])

def iterateStimulus(p):
    for iL in range(p["nTrials"]):
      # Steady steps
      QDS.Scene_Clear(p["tSteadyOFF_s"] -p['durMarker_s'], 0)
      
      QDS.Scene_Clear(p['durMarker_s'], 1) 
      QDS.SetObjColor(1, [1,], [p['RGB_IFull']])
      QDS.Scene_Render(p["tSteadyON_s"], [1,], [1,], [(0,0)], 0)

      QDS.Scene_Clear(p['durMarker_s'], 0)
      QDS.Scene_Clear(p["tSteadyOFF_s"] -p['durMarker_s'], 0)


# --------------------------------------------------------------------------
dispatcher = collections.OrderedDict([
    ('init', partial(QDS.Initialize,p['_sName'],p['_sDescr'])),
    ('log', partial(QDS.LogUserParameters,p)),
    ('build', partial(buildStimulus,p)),
    ('start', QDS.StartScript),
    ('clear1', partial(QDS.Scene_Clear,1.0, 0)),
    ('iter', partial(iterateStimulus,p)),
    ('clear2', partial(QDS.Scene_Clear,1.0, 0)),
    ('stop', QDS.EndScript)]                               
)

[dispatcher[process]() for process in list(dispatcher.keys())]