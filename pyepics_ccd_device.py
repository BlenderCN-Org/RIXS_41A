'''
Created on 20190326

@author: liao.zeno
'''

import time
import epics as e

import numpy as np

class CcdDevices(object):
    '''
    classdocs
    '''


    def __init__(self, name, pvroot):
        '''
        Constructor
        '''
        self.name = name
        self.pvroot = pvroot
        
        #for sim usage
        self.sim = True
        self.currentValuse = 0
        self.exposureTime = 0
      
        self.acqmode = 0
        self.accutype = 0
        self.accunum = 0
        self.gain = 0
        self.cooler = 0
        self.temperature = 0
        self.savebgnd = 0
        self.imagetype = 0

    def start(self, value):
        if self.sim:
            print('[sim EMCCD] start = ' + value)
        else:
            p = e.PV(self.pvroot + ":start")
            p.put(value)

    def stop(self, value):
        if self.sim:
            print('[sim EMCCD] stop = ' + value)
        else:
            p = e.PV(self.pvroot + ":stop")
            p.put(value)

    def getExposureTime(self):
        if self.sim:
            v = self.exposureTime
            print('[sim EMCCD] getExposureTime = ' + str(v))
        else:
            p = e.PV(self.pvroot + ":expot")
            v = p.get()
        return v

    #Unit: second
    def setExposureTime(self, value):
        if self.sim:
            self.exposureTime = value
            print('[sim EMCCD] setExposureTime = ' + value)
        else:
            p = e.PV(self.pvroot + ":expot")
            p.put(value)

    #Get CCD image. 1024x2048 = data DBR_FLOAT waveform. 2,097,152 x 4 = 8,388,608 bytes
    def getImage(self):
        if self.sim:
            v = np.random.randn(2097152, 1)
#            print('[sim EMCCD] image array size = ' + str(len(v)))
            print('[sim EMCCD] getImage.')
        else:
            p = e.PV(self.pvroot + ":image")
            v = p.get()
#            print('[EMCCD] image array size = ' + str(len(v)))
        return v

    '''
    Waveform, get RIXS spectrum, 2048 data point float array
    41a:ccd1:imgtype will determine display and rixs data type
    41a:ccd1:accutype will determine what data will be accumulated in accumulation mode.
    '''
    def getRIXS(self):
        if self.sim:
            v = np.random.randn(2048, 1)
#            print('[sim EMCCD] RIXS array size = ' + str(len(v)))
            print('[sim EMCCD] getRIXS.')
        else:
            p = e.PV(self.pvroot + ":rixs")
            v = p.get()
#            print('[EMCCD] RIXS array size = ' + str(len(v)))
        return v

    '''
    1: exposure complete, image captured.
    0: image data is not ready.
    '''        
    def getStatus(self):
        if self.sim:
            time.sleep(self.exposureTime)
            v = 1.0
        else:
            p = e.PV(self.pvroot + ":dataok")
            v = p.get()
        return v
    
    def getAcqMode(self):
        if self.sim:
            v = self.acqmode
            print('[sim EMCCD] getAcqMode = ' + str(v))
        else:
            p = e.PV(self.pvroot + ":acqmode")
            v = p.get()
        return v

    #0: video; 1: single (obsolete); 2: accumulation
    def setAcqMode(self, value):
        if self.sim:
            self.acqmode = value
            print('[sim EMCCD] setAcqMode = ' + value)
        else:
            p = e.PV(self.pvroot + ":acqmode")
            p.put(value)

    def getAccuType(self):
        if self.sim:
            v = self.accutype
            print('[sim EMCCD] getAccuType = ' + str(v))
        else:
            p = e.PV(self.pvroot + ":accutype")
            v = p.get()
        return v

    #0: raw image; 2: differnece image
    def setAccuType(self, value):
        if self.sim:
            self.accutype = value
            print('[sim EMCCD] setAccuType = ' + value)
        else:
            p = e.PV(self.pvroot + ":accutype")
            p.put(value)

    def getAccuNum(self):
        if self.sim:
            v = self.accunum
            print('[sim EMCCD] getAccuNum = ' + str(v))
        else:
            p = e.PV(self.pvroot + ":accunum")
            v = p.get()
        return v

    def setAccuNum(self, value):
        if self.sim:
            self.accunum = value
            print('[sim EMCCD] setAccuNum = ' + value)
        else:
            p = e.PV(self.pvroot + ":accunum")
            p.put(value)
            
    def getGain(self):
        if self.sim:
            v = self.gain
            print('[sim EMCCD] getGain = ' + str(v))
        else:
            p = e.PV(self.pvroot + ":gain")
            v = p.get()
        return v

    #EMCCD gain 0 ~ 100
    def setGain(self, value):
        if self.sim:
            self.gain = value
            print('[sim EMCCD] setGain = ' + value)
        else:
            p = e.PV(self.pvroot + ":gain")
            p.put(value)
            
    def getCooler(self):
        if self.sim:
            v = self.cooler
            print('[sim EMCCD] getCooler = ' + str(v))
        else:
            p = e.PV(self.pvroot + ":cooler")
            v = p.get()
        return v

    # 1: turn on; 0: turn off
    def setCooler(self, value):
        if self.sim:
            self.cooler = value
            print('[sim EMCCD] setCooler = ' + value)
        else:
            p = e.PV(self.pvroot + ":cooler")
            p.put(value)

    def getTemperature(self):
        if self.sim:
            v = self.temperature
            print('[sim EMCCD] getTemperature = ' + str(v))
        else:
            p = e.PV(self.pvroot + ":tmpr")
            v = p.get()
        return v

    def setTemperature(self, value):
        if self.sim:
            self.temperature = value
            print('[sim EMCCD] setTemperature = ' + value)
        else:
            p = e.PV(self.pvroot + ":tmpw")
            p.put(value)

    def getSaveBgnd(self):
        if self.sim:
            v = self.savebgnd
            print('[sim EMCCD] getSaveBgnd = ' + str(v))
        else:
            p = e.PV(self.pvroot + ":savebgnd")
            v = p.get()
        return v

    '''
    1: Save current image as background
    2: Take a refreshed background image
    The value will be reset to 0 automatically after process is complete.
    '''
    def setSaveBgnd(self, value):
        if self.sim:
            self.savebgnd = value
            print('[sim EMCCD] setSaveBgnd = ' + value)
        else:
            p = e.PV(self.pvroot + ":savebgnd")
            p.put(value)
            
    def getImageType(self):
        if self.sim:
            v = self.imagetype
            print('[sim EMCCD] getImageType = ' + str(v))
        else:
            p = e.PV(self.pvroot + ":imgtype")
            v = p.get()
        return v

    '''
    This PV will determine the data that will be sent by command 41a:ccd1:image.
    0: raw image
    1: accumulation image
    2: difference image
    3: background
    4: smoothed background
    '''
    def setImageType(self, value):
        if self.sim:
            self.imagetype = value
            print('[sim EMCCD] setImageType = ' + value)
        else:
            p = e.PV(self.pvroot + ":imgtype")
            p.put(value)