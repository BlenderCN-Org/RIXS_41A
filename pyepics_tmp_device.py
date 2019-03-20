'''
Created on 20190225

@author: liao.zeno
'''

import epics as e

class TmpDevices(object):
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
        p = e.PV(self.pvroot)
        v = p.get('value', as_string=False)
        return v
        
#    def setValue(self, value):
#        p = e.PV(self.pvroot + "w")
#        v = p.put(value)
#        return v

    