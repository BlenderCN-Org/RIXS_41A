########## spike removal, last edited July 14, 2019 by DJH
# spikeRemoval removes spikes in a region of interest along x-pixel of an input 2D data array.
# It provides 2D data array after spike removal
#### input: data, x1 and x2, discrimination factor d
#### output: data after spike removal

import numpy as np
from numpy.random import randn
from scipy.signal import find_peaks, peak_widths
import pandas as pd
from scipy.optimize import curve_fit
from scipy import fftpack
from matplotlib.colors import LogNorm
import matplotlib.pyplot as plt

def low_pass_fft(spectrum, max_freq=0.15, step=1):
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

    return data_sp



def spikeRemoval(data, d=3): # the 3rd version
    # --- data is a 2D np.array
    # return list: [data_sp]
    # --- data_sp is a np.array for 2D data after spike removal
    # --- level is a np.array which stores the discriminator levels (the spike removal level) for all y pixels
    # --- level[j] = the data average of a given y-pixe of j with x pixels between x1 and x2.
    if d<2:
        d = 2
    size_y = np.size(data[0,:])
    size_x = np.size(data[:,0])
    level = np.copy(data[0,:]) # with y-pixel as the array index
    spike =[]
    for j in range(size_y): # size_y = total y-pixel
        data_x = np.copy(data[:,j]) #1D data array (x-pixel) before spike removal for y-pixel = j
        data_x_new = np.copy(data[:,j])
        data_x_2nd = np.copy(data[:,j])
        avg0 = np.mean(data_x) #get a prelimary average before spike removal
        #### get an initial avg
        data2x = np.copy(data[:,j]) #1D data array (x-pixel) before spike removal for y-pixel = j
        peak_x_0, _ = find_peaks(data2x, height=avg0*2)
        avg_1 = avg0
        if np.size(peak_x_0)>0:
                data_x_0 = np.delete(data2x, peak_x_0)# remove the elements of data_x which have indexes of peak_x_0
                avg_1 = np.mean(data_x_0) #average after a prelimary spike removal

        H = avg_1 *d

        ###### finding spkies of a given y pixel
        peak_x, _ = find_peaks(data_x_new, height=(H,np.inf), width=(0.2, 6), distance=10)
        width_half= peak_widths(data_x_new, peak_x, rel_height=0.5)  # indices of spikes with intenisty larger than "H"
        peak_temp = np.array([])

        if np.size(peak_x) > 0:
            #print("y-piexel = ", j, "number of peak_x = ", np.size(peak_x))
            #print("peak_x = ", peak_x)
            width = width_half[0]
            #print ('width_half =', width)
            ww = np.copy(width_half[0])
            ww=np.round(ww)
            ww = ww.astype(int)
            #print ('ww =', ww)
            peak_temp = np.copy(peak_x)

            n=0 # index for the spike found
            for m in peak_temp:
                #print(n+1,'-th point, x-piexel = ', peak_temp[n])

                ## consider a 21-piexel range around the spike
                m1 = max(0, m-10)
                m2 = min(m+10, size_x)
                avg = (21*np.mean(data_x_new[m1:m2])- data_x_new[m-1:m]-data_x_new[m:m+1]-data_x_new[m+1:m+2])/18# average around the peak
                #print("peak index = ", m, ' peak intensity = ', data_x_new[m], '  avg =  ', avg, '   sp factor =', d)
                h0= data_x_new[m] - avg

                w = 7 ## a wondow for curve fit is set to 2w+1
                if m > w and m < (size_x-w-1):
                    x= np.linspace(m-w, m+w, num=2*w+1)
                    data_sp= data_x_new[m-w:m+w+1]
                    loop =0
                    while 1:
                        #peak_x_1, _ =find_peaks(data_sp, height=avg*d, width=(0.2, 4))
                        #print('peaks found: ', peak_x_1)
                        peak = np.max(data_sp[3:11])
                        peak_index = np.argmax(data_sp[3:11])+m-5
                        avg_2 = np.mean(data_sp)
                        hh= peak - avg_2
                        #print('peak= ', peak, 'avg_2= ', avg_2)
                        if peak > 1.5* avg_2:
                            print('loop = ', loop)
                            print("data before sp_removing", data_sp.astype(int))
                            # gaussian_1d(x, x0,sigma, H, c)
                            initial_guess = (peak_index, width[n]/2.355, hh, avg_2)
                            limit = ([m-3, 0.1, hh*0.5, avg_2*0.8],[m+3, 5, hh*2, avg_2*1.2])

                            try:
                                fit_x, pcov = curve_fit(gaussian_1d, x, data_sp, p0=initial_guess, bounds=limit)
                                #print ("fit results:", gaussian_1d(x, fit_x[0], fit_x[1], fit_x[2], fit_x[3])+ fit_x[3])
                                data_sp = data_sp - gaussian_1d(x, fit_x[0], fit_x[1], fit_x[2], fit_x[3])+ fit_x[3]
                                for q in range(np.size(data_sp)):
                                    if data_sp[q] < np.mean(data_sp)*0.9:
                                        data_sp[q]= np.mean(data_sp)

                                #print("after sp_removing", data_sp.astype(int))

                            except RuntimeError:
                                print("Error - curve_fit failed, using peak_widths")
                                data_sp = data_sp - gaussian_1d(x, m, width[n]/2.355, hh, avg_2)+avg_2
                        else:
                            data_x_new[m-w:m+w+1] =np.copy(data_sp)
                            break
                        if loop > 10:
                            data_x_new[m-w:m+w+1] =np.copy(data_sp)
                            break
                        loop +=1

                    data_x_new[m-w:m+w+1] =np.copy(data_sp)
                    data_int = data_sp.astype(int)
                    #print("final data after sp_removing", data_int)
                n +=1
        data[:,j] = data_x_new
    return data


#### removing spikes from data aftre background subtartion
def spikeRemoval_2(data, d=3, f=20):
    data_sp = np.copy(data)
    data_fitted = np.copy(data)
    avg = np.mean(data)
    threshold=  avg*f
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

def spikeRemoval_fft(data,alpha):

    data_fft = fftpack.fft2(data)
    #print(data)
    #print(data_fft)
    #fig = plt.figure()
    #ax1 = fig.add_subplot(1,2,1)
    #ax2 = fig.add_subplot(1,2,2)
    #ax1.plot(data)
    #ax2.plot(data_fft)

    #fig, ax = plt.subplots(2)
    data_fft2 = data_fft.copy()
    row, col = data_fft2.shape
    data_fft2[int(row*alpha):,:] = 0

    fig, (ax1, ax2) = plt.subplots(nrows=2)
    ax1.imshow(data)
    ax2.imshow(np.abs(data_fft2), norm=LogNorm(vmin=5))
    ax1.set_title('Original image')
    ax2.set_title('Fourier image')
    #plt.subplot_tool()
    #plt.colorbar()
    plt.show()
    data_new = fftpack.ifft2(data_fft2).real
    return [data_new]

# Our function to fit is going to be a sum of two-dimensional Gaussians
def gaussian_2d(x, y, x0, y0, sigma_x, sigma_y, H, c):#, a, b, c):
   return H * np.exp( -0.5*((x-x0)/sigma_x)**2 -0.5*((y-y0)/sigma_y)**2)+c #+a*x+b*y+c

def gaussian_1d(x, x0,sigma, H, c):
   return H * np.exp( -0.5*((x-x0)/sigma)**2)+c


def plot_spectrum(im_fft):
    # A logarithmic colormap
    plt.imshow(np.abs(im_fft), norm=LogNorm(vmin=5))
    plt.colorbar()


#filename='/Users/djhuang/Google_Drive/DJH_Google＿drive/B大組_科學研究與實驗設施/TPS_41A/AGS_AGM_TPS_beamline/RIXS_software/test_data/rixs_20190710_47_img012.img'
#filename='/Users/djhuang/Google_Drive/DJH_Google＿drive/B大組_科學研究與實驗設施/TPS_41A/AGS_AGM_TPS_beamline/RIXS_software/test_data/5mintues_signal.txt'

#data = np.genfromtxt(filename, delimiter=',')
#if data.size > 2097152:
#    data = data[np.logical_not(np.isnan(data))]     # remove nan
#    data = np.take(data, list(range(0, 2097152)))   # get 1024*2048 (original 2061)

#data = np.reshape(data, (1024, 2048), order='F')

#spikeRemoval(data)
#print('spike removal results:', spikeRemoval_3(data))
