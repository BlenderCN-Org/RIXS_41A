import epics as e
from epics import PV, ca
import time
import numpy as np

#Get Value
reading = dict(agm="41a:AGM:Energy.RBV", ags="41a:AGS:Energy.RBV", x= "41a:RIXS:xyz:xr", y= "41a:RIXS:xyz:yr",
               z= "41a:RIXS:xyz:zr", hex_x="41a:hexapod:x", hex_y="41a:hexapod:y", hex_z="41a:hexapod:z",
               u="41a:hexapod:u", v="41a:hexapod:v", w="41a:hexapod:w", th="41a:sample:thr",
               tth="41a:sample:tthr", heater="41a:sample:heater", ta="41a:sample:tmp1", tb="41a:sample:tmp2",
               I0="41a:sample:i0", Iph="41a:sample:phdi", Tccd="41a:ccd1:tmpr", gain="41a:ccd1:gain",
               ring="SR-DI-DCCT:BeamCurrent")

#Get Value
movingstat = dict(agm="41a:AGM:Energy.MOVN", ags="41a:AGS:Energy.MOVN", x="41a:RIXS:xyz:x:Moving",
              y="41a:RIXS:xyz:y:Moving", z="41a:RIXS:xyz:z:Moving", hex_x="41a:hexapod:xm", hex_y="41a:hexapod:ym",
              hex_z="41a:hexapod:zm", u="41a:hexapod:um", v="41a:hexapod:vm", w="41a:hexapod:wm", th="41a:sample:thm",
              tth="41a:sample:tthm")


#Put Value
putvalue = dict(agm="41a:AGM:Energy.VAL", ags="41a:AGS:Energy.VAL", x="41a:RIXS:xyz:xw",
              y="41a:RIXS:xyz:yw", z="41a:RIXS:xyz:zw", hex_x="41a:hexapod:xw", hex_y="41a:hexapod:yw",
               hex_z="41a:hexapod:zw", u="41a:hexapod:uw", v="41a:hexapod:vw", w="41a:hexapod:ww", th="41a:sample:thw",
               tth="41a:sample:tthw", heater="41a:sample:heater", ta="41a:sample:tmp1w")

put_xyz = dict(x="41a:RIXS:xyz:x:Move", y="41a:RIXS:xyz:y:Move", z="41a:RIXS:xyz:z:Move")

#Get/Put Value for CCD
ccdict = dict(exposure="41a:ccd1:expot", start="41a:ccd1:start", stop="41a:ccd1:stop", dataok="41a:ccd1:dataok",
              acqmode="41a:ccd1:acqmode", cooler="41a:ccd1:tmpw", accutype="41a:ccd1:imgtype", Tccd="41a:ccd1:tmpw",
              image="41a:ccd1:image")



pvname_list = list(reading.values()) + list(movingstat.values()) + list(ccdict.values())

pv_list = [PV(name) for name in pvname_list] # generate PVs

def getVal(p):
    i = pvname_list.index(reading[p]) # from key(param_index) find pvname
    v = pv_list[i].get()
    if p in ['x','y','z']:
        v = xyz(p, v)
    return v # get PV value

def caget(p):
    v = e.caget(reading[p])  # from key(param_index) find pvname
    if p in ['x', 'y', 'z']:
        v = xyz(p, v)
    return v  # get PV value

def xyz(p, v):
    if p == 'z':
        if v != None:
            v = float(v/32000)
    elif p in ['x','y']:
        if v!= None:
            v = float(v/8000)
    return v

def movStat(p):
    i = pvname_list.index(movingstat[p])
    return (pv_list[i].get())

def ccd(p, value=None):
    keyvalue = ccdict[p] if p != "gain" else reading[p]
    if (p not in ["dataok", "image"]) and (value != None):  # put_value for ccd parameters
        pv_list[pvname_list.index(keyvalue)].put(value)
    elif (p == "image"):
        return e.caget("41a:ccd1:image")
    else:
        return pv_list[pvname_list.index(keyvalue)].get()

def putVal(p, value):
    e.caput(putvalue[p], value)
    print('put {0} = {1}'.format(p, value))
    if p in ['x','y','z']:
        time.sleep(0.2)         # ensure value set correctly
        e.caput(put_xyz[p],1)   # for xyz stage: set target then move, put(1)= Move
        print('start moving..')

def moving(p):
    if p in ['x', 'y', 'z', 'u', 'v', 'w', 'th', 'tth', 'agm', 'ags']:
        if movStat(p) == 1:  # 1: moving, 0: stop
            return True
        else:  # including gain
            return False
    else:
        return False

def refresh(p): #called after moving
    index = pvname_list.index(reading[p])
    pv_list[index] = PV(reading[p])


