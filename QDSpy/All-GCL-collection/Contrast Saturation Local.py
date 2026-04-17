# -*- coding: utf-8 -*-
"""
Created on Thu Apr  7 11:32:23 2016

@author: ZZ
"""
import collections
import csv
from functools import partial
import QDS
import math
import numpy as np
import random

# Define global stimulus parameters
p = {'_sName'          : "Contrast saturation",
     '_sDescr'         : "Sine wave ripple with 10%,20%,40%,60%,80%,100% contrast",
     "nTrials"         : 3, 
     "iHalf"           : 127,
     "iFull"           : 254,
     "dxStim_um"       : 100,   # Stimulus size in diameter
     "dxSurd_um"       : 1000,  # Background/surround size in diameter
     "Center"          : 1,      
     "Surround"        : 2,      
     "durFr_s"         : 1/60.0, # Frame duration
     'durRipple'       : 2,
     "tSteadyMID_s"    : 3,    # Light at 50% for steps
     'MarkPer_s'       : 1,
     'nFrPerMarker'    : 2,
     }
     
def buildStimulus(p):
    # Define stimulus objects
    QDS.DefObj_Ellipse(1, p["dxStim_um"], p["dxStim_um"])
    QDS.DefObj_Sector(2,p["dxSurd_um"],p["dxStim_um"]/2,0,360,5)
    
def iterateStimulus(p):    
    folderStr = "C:\\Users\\AGEuler\\Documents\\QDSpy\\Stimuli\ZZ\\cGMP\\"
    tableStr = 'contrast saturation_conditions.csv' 
    f = open(folderStr+tableStr,'r')
    reader = csv.reader(f)
    conditions = []
    for itx,row in enumerate(reader):
        if itx%2 == 0:
            conditions.append([float(state) for state in row])

    for iL in range(p["nTrials"]):
        for (condition,frequency,contrast,time) in conditions:
            #QDS.SetBkgColor((p["iHalf"],p["iHalf"],p["iHalf"]))
            
            Intensity = p["iHalf"]
            RGBh = (int(Intensity),int(Intensity),int(Intensity))
    
            QDS.SetObjColor(1, [p["Center"],p["Surround"]], [RGBh,RGBh])
            QDS.Scene_Render(0.05, 1, [p["Center"],p["Surround"]], [(0,0),(0,0)], _marker = 1)   
            QDS.Scene_Render(2.95, 1, [p["Center"],p["Surround"]], [(0,0),(0,0)], _marker = 0) 
    
            for itx in range(int(time/p['durFr_s'])):
                t_pnt = itx*p['durFr_s']
    
                # Add marker    
                showMarker = 0
                
                # Calculate stimulus intensity
                Intensity = math.sin(2*math.pi*frequency*t_pnt)*contrast/100*p["iHalf"]+p["iHalf"]
                RGB = (int(Intensity),int(Intensity),int(Intensity))
    
                QDS.SetObjColor(1, [p["Center"],p["Surround"]], [RGB,RGBh])
                QDS.Scene_Render(p["durFr_s"], 1, [p["Center"],p["Surround"]], [(0,0),(0,0)], showMarker)    
    
        QDS.SetObjColor(1, [p["Center"],p["Surround"]], [RGBh,RGBh])         
        QDS.Scene_Render(0.05, 1, [p["Center"],p["Surround"]], [(0,0),(0,0)], _marker = 1)   
        QDS.Scene_Render(2.95, 1, [p["Center"],p["Surround"]], [(0,0),(0,0)], _marker = 0) 
        
        #QDS.SetBkgColor((0,0,0))
        QDS.Scene_Clear(0.05, 1)
        QDS.Scene_Clear(2.95, 0)
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