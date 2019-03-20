'''
Created on 20190225

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

    def statr(self, value):
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

    def setExposureTime(self, value):
        if self.sim:
            self.exposureTime = value
            print('[sim EMCCD] setExposureTime = ' + value)
        else:
            p = e.PV(self.pvroot + ":expot")
            p.put(value)

    def getImage(self):
        if self.sim:
#            v = np.random.randn(2097152, 1)
            v = np.random.randn(10, 1)
#            print('[sim EMCCD] image array size = ' + str(len(v)))
            print('[sim EMCCD] getImage.')
        else:
            p = e.PV(self.pvroot + ":image")
            v = p.get()
#            print('[EMCCD] image array size = ' + str(len(v)))
        return v
    
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
        
    def getStatus(self):
        if self.sim:
            time.sleep(self.exposureTime)
            v = 1.0
        else:
            p = e.PV(self.pvroot + "m")
            v = p.get()
        return v
    