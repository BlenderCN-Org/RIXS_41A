########## spike removal, last edited April 19, 2019 by DJH
# spikeRemoval removes spikes in a region of interest along x-pixel of an input 2D data array.
# It provides 2D data array after spike removal and locations of spikes.
#### input: data, x1 and x2, discrimination factor d
#### output: data after spike removal, spike list, levels

import numpy as np
from numpy.random import randn
from scipy.signal import find_peaks
import pandas as pd

def spikeRemoval(data, x1=400, x2=600, d=3):
    # --- data is a 2D np.array
    # --- x1 and x2 set the region of interest of x pixels between x1 and x2
    # --- d is a discrimination factor which sets a discriminator level H (the spike removal level)
    #        defined as H = (avgerage)*d, where "avgearge" is, for a given y-pixel, the data average of x pixels between x1 and x2.
    # return list: [data_sp, peak_x, level]
    # --- data_sp is a np.array for 2D data after spike removal
    # --- peak_x is a list storing the spike locations. Each element, which is a np.array, and its index store
    #     y-pixels and x-pixels of spikes, accordingly.
    #     i.e. peak_x[i] = a list containing the y pixels of spikes for an x-pixel of i
    # --- level is a np.array which stores the discriminator levels (the spike removal level) for all y pixels
    # --- level[j] = the data average of a given y-pixe of j with x pixels between x1 and x2.

    H0=0
    Th0=0
    data_sp = np.copy(data)
    rang = np.size(data[0,:])
    level = np.copy(data[0,:]) # with y-pixel as the array index
    #spike = pd.Series([])
    spike =[]
    for j in range(rang):
        data2x = np.copy(data[:,j]) #1D data array before spike removal
        avg0 = np.mean(data2x[x1:x2]) #get a prelimary average before spike removal
        peak1x, _ = find_peaks(data2x, height=avg0*3)  # remove spikes
        data_x = np.delete(data2x, peak1x) #1D data array after spike removal; its size has been reduced by np.size(peak_x))
        avg_1 = np.mean(data_x[x1:x2]) #average after a prelimary spike removal

        ### remove spikes again
        H = (avg_1) *d
        Th =avg_1

        peak1x, _ = find_peaks(data2x, height=H, threshold=Th)  # indices of spikes which has intensity largern than "H"
        #and its intensity difference with neighbours is larger than "Th"
        peak2x, _ = find_peaks(data2x, height=(H,np.inf), width=(1, 5))  # indices of spikes with intenisty larger than "H"
        # and its width is between 1 and 5

        peak_temp = np.array([])
        for m in range(np.size(peak2x)):
            # to include the x pixels (i.e. indices) which are 5 below and 5 above around peak2x
            q=int(peak2x[m])
            for n in range(-5, 5):
                if ((q+n)>0 and (q+n)< np.size(data2x)) and data2x[q+n] > H:
                    peak_temp = np.append(peak_temp, np.array([q+n]))
        peak_temp = peak_temp.astype(int)  # to covert the contains peak_temp to be intergers
        px= np.concatenate((peak1x, peak2x, peak_temp),axis=0)
        peak_x = np.unique(px) # to remove the overlap
        data_x = np.delete(data2x, peak_x) #1D data array after spike removal; its size has been reduced by np.size(peak_x))
        #print('number of total spikes = ', np.size(peak_x))

        #print('number of total spikes = ', np.size(peak_x))
        #print(peak_x)

        avg = np.mean(data_x) # average after spike removal
        #print('average along s =  ', avg)
        spike.append(peak_x)
        for m in peak_x:
            #print('m=', m)
            data2x[m]=avg+(0.5-np.random.rand(1)) # replace the vacancy points at the "spike positions"

        #now data2x are the data after spikle removal  and its size remains unchanged
        data_sp[:,j]=np.copy(data2x)
        level[j] = H  # a np.array which stores the discriminator level corresponding y pixels

    return [data_sp, spike, level]
