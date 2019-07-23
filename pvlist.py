import epics as e
from epics import PV, ca
import time
import numpy as np

class pvlist():
    def __init__(self):
        super().__init__()
        self.cta = None
        self.THoffset = 0

        #Get Value
        self.reading = dict(agm="41a:AGM:Energy.RBV", ags="41a:AGS:Energy.RBV", x= "41a:RIXS:xyz:xr", y= "41a:RIXS:xyz:yr",
                       z= "41a:RIXS:xyz:zr", hex_x="41a:hexapod:x", hex_y="41a:hexapod:y", hex_z="41a:hexapod:z",
                       u="41a:hexapod:u", v="41a:hexapod:v", w="41a:hexapod:w", th="41a:sample:thr",
                       det="41a:sample:tthr", heater="41a:sample:heater", ta="41a:sample:tmp1", tb="41a:sample:tmp2",
                       I0="41a:sample:i0", Iph="41a:sample:phdi", Itey="41a:sample:TEY", Tccd="41a:ccd1:tmpr", gain="41a:ccd1:gain",
                       ring="SR-DI-DCCT:BeamCurrent", chmbr="41a:sample:transr", tth="41a:agsm:tthr")

        #Get Value
        self.movingstat = dict(agm="41a:AGM:Energy.MOVN", ags="41a:AGS:Energy.MOVN", x="41a:RIXS:xyz:x:Moving",
                      y="41a:RIXS:xyz:y:Moving", z="41a:RIXS:xyz:z:Moving", hex_x="41a:hexapod:xm", hex_y="41a:hexapod:ym",
                      hex_z="41a:hexapod:zm", u="41a:hexapod:um", v="41a:hexapod:vm", w="41a:hexapod:wm", th="41a:sample:thm",
                      det="41a:sample:tthm", chmbr="41a:sample:transm", tth="41a:agsm:tthm")


        #Put Value
        self.putvalue = dict(agm="41a:AGM:Energy.VAL", ags="41a:AGS:Energy.VAL", x="41a:RIXS:xyz:xw",
                      y="41a:RIXS:xyz:yw", z="41a:RIXS:xyz:zw", hex_x="41a:hexapod:xw", hex_y="41a:hexapod:yw",
                       hex_z="41a:hexapod:zw", u="41a:hexapod:uw", v="41a:hexapod:vw", w="41a:hexapod:ww", th="41a:sample:thw",
                       det="41a:sample:tthw", heater="41a:sample:heater", ta="41a:sample:tmp1w", chmbr="41a:sample:transw", tth="41a:agsm:tthw")

        self.put_xyz = dict(x="41a:RIXS:xyz:x:Move", y="41a:RIXS:xyz:y:Move", z="41a:RIXS:xyz:z:Move")

        #Get/Put Value for CCD
        self.ccdict = dict(exposure="41a:ccd1:expot", start="41a:ccd1:start", stop="41a:ccd1:stop", dataok="41a:ccd1:dataok",
                      acqmode="41a:ccd1:acqmode", cooler="41a:ccd1:tmpw", accutype="41a:ccd1:imgtype", Tccd="41a:ccd1:tmpw",
                      image="41a:ccd1:image", accunum="41a:ccd1:accunum")

        self.stop = dict(x="41a:RIXS:xyz:x:Stop", y="41a:RIXS:xyz:y:Stop", z="41a:RIXS:xyz:z:Stop", hex_x="41a:hexapod:xs",
                    hex_y="41a:hexapod:ys", hex_z="41a:hexapod:zs", u="41a:hexapod:us", v="41a:hexapod:vs",
                    w="41a:hexapod:ws", th="41a:sample:ths", det="41a:sample:tths", chmbr="41a:sample:transs", tth="41a:agsm:tths")


        self.pvname_list = list(self.reading.values()) + list(self.movingstat.values()) + list(self.ccdict.values())

        try:
            self.pv_list = [PV(name) for name in self.pvname_list] # generate PVs
        except:
            print('failed to initialize PVs, lost hardware connection.')

    def getVal(self, p):
        i = self.pvname_list.index(self.reading[p]) # from key(param_index) find pvname
        v = self.pv_list[i].get()
        if p in ['x','y','z']:
            v = self.xyz(p, v)

        return v # get PV value

    def caget(self, p):
        v = e.caget(self.reading[p])  # from key(param_index) find pvname
        if p in ['x', 'y', 'z']:
            v = self.xyz(p, v)
        return v  # get PV value

    def xyz(self, p, v):
        if p == 'z':
            if v != None:
                v = float(v/32000)
        elif p in ['x','y']:
            if v!= None:
                v = float(v/8000)
        return v

    def movStat(self, p):
        i = self.pvname_list.index(self.movingstat[p])
        return (self.pv_list[i].get())

    def ccd(self, p, value=None):
        keyvalue = self.ccdict[p] if p != "gain" else self.reading[p]
        if (p not in ["dataok", "image"]) and (value != None):  # put_value for ccd parameters
            self.pv_list[self.pvname_list.index(keyvalue)].put(value)
        elif (p == "image"):
            return e.caget("41a:ccd1:image")
        else:
            return self.pv_list[self.pvname_list.index(keyvalue)].get()

    def putVal(self, p, value):
        if e.caget(self.putvalue[p]) != value:
            e.caput(self.putvalue[p], value)
            print('put {0} = {1}'.format(p, value))
            if p in ['x','y','z']:
                time.sleep(0.2)         # ensure value set correctly
                e.caput(self.put_xyz[p],1)   # for xyz stage: set target then move, put(1)= Move
                print('start moving..')
        else:
            print('{0} is already at position :{1},  move aborted.'.format(p, value))

    def moving(self, p):
        if p in ['x', 'y', 'z', 'u', 'v', 'w', 'th', 'det', 'agm', 'ags', 'chmbr']:
            if self.movStat(p) == 1:  # 1: moving, 0: stop
                return True
            else:  # including gain
                return False
        if p in ['ta']:
            try:
                val = float(self.getVal(p))
                dval = abs(self.cta-val) if self.cta != None else 0
                if (dval/val) > 0.05:
                    self.cta = val
                    return True
                else:
                    return False
            except: #get None and failed calculating val, dval
                return False
        else:
            return False

    def refresh(self, p): #called after moving
        index = self.pvname_list.index(self.reading[p])
        self.pv_list[index] = PV(self.reading[p])

    def stopMove(self, p):
        try:
            e.caput(stop[p],1)
            print('stop signal emitted')
        except:
            print('not stoppable parameter.')

    def thOffset(self, flag = False, v= 0):
        if flag:
            self.THoffset = v
        else:
            return self.THoffset

            