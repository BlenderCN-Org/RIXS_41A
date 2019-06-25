########## spike removal, last edited April 19, 2019 by DJH
# spikeRemoval removes spikes in a region of interest along x-pixel of an input 2D data array.
# It provides 2D data array after spike removal and locations of spikes.
#### input: data, x1 and x2, discrimination factor d
#### output: data after spike removal, spike list, levels

import numpy as np
from numpy.random import randn
from scipy.signal import find_peaks
import pandas as pd
from scipy.optimize import curve_fit
from scipy import fftpack


def low_pass_fft(spectrum, max_freq=0.3, step=0.05):
    # The FFT of the signal
    spectrum_fft = fftpack.fft(spectrum)
    #The corresponding frequencies
    sample_freq = fftpack.fftfreq(np.size(spectrum), d=step)
    low_freq_fft = np.copy(spectrum_fft)
    low_freq_fft[np.abs(sample_freq) > max_freq] = 0
    spectrum_filtered = fftpack.ifft(low_freq_fft).real # remove imaginary part
    return spectrum_filtered

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

#### removing spikes from data aftre background subtartion
def spikeRemoval_2(data, d=3, f=20):
   data_sp = np.copy(data)
   data_fitted = np.copy(data)
   avg = np.mean(data)
   threshold=  avg*f


   # peak_local_max returns ndarray
   peak_pos = peak_local_max(data, min_distance = d, threshold_abs = threshold, indices = True)
   #print('peak_pos', type(peak_pos))

   # get ndarray size
   N = int(peak_pos.size/2)
   print('size = ', N) #somehow size is doubled (x y) condisered 2
   N1=np.size(data[:,0])
   N2=np.size(data[0,:])


   peak_temp = np.array([])

   for i in range(N):
       (m, n) = peak_pos[i]
       h0 = data[m,n]
       print('I({0}, {1}) = {2}'.format(m, n, h0))
       data_in = data[m-d:m+d+1,n-d:n+d+1]
       if h0 > np.mean(data)*1.2:
           #peak_temp = np.append(peak_temp, np.array([m,n]))
           #get Gaussian width = sigma
           x, y = np.linspace(m-d, m+d, num=2*d+1), np.linspace(n-d, n+d, num=2*d+1)
           #gaussian_1d(x, x0,sigma, H, c):
           initial_guess=(m, 2, data[m,n],avg)
           limit = ([m-d, 0.001, h0*0.8, avg*0.8],[m+d,6, h0*1.2, avg*1.2])
           fit_x, pcov = curve_fit(gaussian_1d, x, data[m-d:m+d+1,n], p0=initial_guess, bounds=limit)
           print('fit_x = ', fit_x)
           initial_guess=(n, 2, data[m,n],avg)
           limit = ([n-d, 0.001, h0*0.8, avg*0.8],[n+d,6, h0*1.2, avg*1.2])
           fit_y, pcov = curve_fit(gaussian_1d, y, data[m, n-d:n+d+1], p0=initial_guess, bounds=limit)
           print('fit_y = ', fit_y)
           xx=np.linspace(0, N1-1, N1)

           bkgd_fit=(fit_x[3]+fit_x[3])/2
           print('bkgd_fit=', bkgd_fit)
           for j in range(m-d, m+d+1):
               for k in range(n-d, n+d+1):
                   #gaussian_2d(x,y, x0, y0, sigma_x, sigma_y, H, c)
                   data_fitted[j,k] = gaussian_2d(j, k, fit_x[0],fit_y[0], fit_x[1], fit_y[1], (fit_x[2]+fit_x[2])/2,avg)
                   data_sp[j, k] = data[j,k]-data_fitted[j,k]+ bkgd_fit

                   if (data_sp[j, k] < bkgd_fit):
                       print("j, k=", j, k)
                       print(data_sp[j, k])
                       data_sp[j, k]= bkgd_fit*(1+np.random.normal(0, 0.05))


   return [data_sp, peak_pos]


# Our function to fit is going to be a sum of two-dimensional Gaussians
def gaussian_2d(x, y, x0, y0, sigma_x, sigma_y, H, c):#, a, b, c):
   return H * np.exp( -0.5*((x-x0)/sigma_x)**2 -0.5*((y-y0)/sigma_y)**2)+c #+a*x+b*y+c

def gaussian_1d(x, x0,sigma, H, c):
   return H * np.exp( -0.5*((x-x0)/sigma)**2)+c


