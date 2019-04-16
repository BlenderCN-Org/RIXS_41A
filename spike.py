import numpy as np
from numpy.random import randn
from scipy.signal import find_peaks

########## spike removal along t -- 2061

H0=0
Th0=0


# data: 2D numpy array
# x1 and x2: region of interest along the x-pixel
# d: discrimination factor
def spikeRemoval(data, x1=400, x2=600, d=3):
    H0=0
    Th0=0
    data_sp =np.copy(data)
    rang=np.size(data[:,0])
    for j in range(rang):
        data2x = np.copy(data[j,:]) #1D data array before spike removal
        H = np.mean(data2x[x1:x2])*d
        H0 += H
        Th =np.mean(data2x[x1:x2])*2
        Th0 += Th
        avg0 = np.mean(data2x) #get average before spike removal
        peak1x, _ = find_peaks(data2x, height=H, threshold=Th)  # indices of spikes which has intensity largern than "H"
        #and its intensity difference with neighbours is larger than "Th"
        peak2x, _ = find_peaks(data2x, height=(H,np.inf), width=(1, 10))  # indices of spikes with intenisty larger than "H"
        # and its width is between 1 and 10

        peak_temp = np.array([])
        for m in range(np.size(peak2x)):
            # to include the pixels (i.e. indices) which are 5 below and 5 above around peak2x
            q=int(peak2x[m])
            for n in range(-5, 5):
                if ((q+n)>0 and (q+n)< 1024) and data2x[q+n] > np.mean(data2x[x1:x2])*1.2:
                    peak_temp = np.append(peak_temp, np.array([q+n]))
        peak_temp = peak_temp.astype(int)
        px= np.concatenate((peak1x, peak2x, peak_temp),axis=0)
        peak_x = np.unique(px) # to remove the overlap
        data_x = np.delete(data2x, peak_x) #1D data array after spike removal; its size has been reduced by np.size(peak_x))
        #print('number of total spikes = ', np.size(peak_x))

        avg = np.mean(data_x) #get average after spike removal
        #print('average along s =  ', avg)
        for m in peak_x:
            #print('m=', m)
            data2x[m]=avg+(0.5-np.random.rand(1)) # replace the vacancy points at the "spike positions"
            #now data2x are the data after spikle removal  and its size remains unchanged
            data_sp[j,:]=np.copy(data2x)
        H0 = H0/rang
        Th0 = H0/rang

    return data_sp
