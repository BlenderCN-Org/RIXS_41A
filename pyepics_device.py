'''
Created on 20190225

@author: liao.zeno
'''

import epics as e

class Devices(object):
    '''
    classdocs
    '''


    def __init__(self, name, pvroot):
        '''
        Constructor
        '''
        self.name = name
        self.pvroot = pvroot

    def getValue(self):
        p = e.PV(self.pvroot + "r")
        v = p.get()
        return v
        
    def setValue(self, value):
        p = e.PV("w")
        v = p.put(value)
        return v
    
    def getStatus(self):
        p = e.PV(self.pvroot + "m")
        v = p.get()
        return v

    def stop(self):
        p = e.PV(self.pvroot + "s")
        #v = p.put(1)
        v = p.get()
        return v
    