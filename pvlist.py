import epics as e
from epics import PV
import time
import numpy as np

reading = dict(agm="41a:AGM:Energy.RBV", ags="41a:AGS:Energy.RBV", x="41a:hexapod:x", y="41a:hexapod:y",
               z="41a:hexapod:z", u="41a:hexapod:u", v="41a:hexapod:v", w="41a:hexapod:w", th="41a:sample:thr",
               tth="41a:sample:tthr", heater="41a:sample:heater", ta="41a:sample:tmp1", tb="41a:sample:tmp2",
               I0="41a:sample:i0", Iph="41a:sample:phdi", Tccd="41a:ccd1:tmpr", gain="41a:ccd1:gain")

moving = dict(agm="41a:AGM:Energy.MOVN", ags="41a:AGS:Energy.MOVN", x="41a:hexapod:xm", y="41a:hexapod:ym",
              z="41a:hexapod:zm", u="41a:hexapod:um", v="41a:hexapod:vm", w="41a:hexapod:wm", th="41a:sample:thm",
              tth="41a:sample:tthm")

pvname_list = list(reading.values()) + list(moving.values())

pv_list = [PV(name) for name in pvname_list] # generate PVs

def getVal(parameter_index):
    i = pvname_list.index(reading[parameter_index]) # from reading get pvname to check index in pvname_list
    return (pv_list[i].get()) # get PV value

def getMovn(parameter_index):
    i = pvname_list.index(moving[parameter_index])
    return (pv_list[i].get())