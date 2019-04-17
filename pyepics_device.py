'''
Created on 20190225

@author: liao.zeno
'''

import time
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
        
        #for sim usage
        self.sim = False
        self.currentValuse = 0
        
    def getValue(self):
        if self.sim:
            v = self.currentValuse
#            print('sim position = ' + str(v))
        else:
            p = e.PV(self.pvroot + "r")
            v = p.get()
        return v        
        
    def setValue(self, value):
        if self.sim:
            self.currentValuse = value
            v = self.currentValuse
            print(self.name + ' move completed.')
        else:
            p = e.PV(self.pvroot + "w")
            v = p.put(value) 
        return v   #why return?
    
    def getStatus(self):
        if self.sim:
            time.sleep(0.01)
            v = 0.0
        else:
            p = e.PV(self.pvroot + "m")
            v = p.get()
        return v

    def stop(self):
        if self.sim:
            print(self.name + ' stop.')
        else:
            p = e.PV(self.pvroot + "s")
            #v = p.put(1)
            v = p.get()
        return v
    