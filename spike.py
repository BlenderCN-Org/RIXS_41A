########## spike removal, last edited April 19, 2019 by DJH
# spikeRemoval removes spikes in a region of interest along x-pixel of an input 2D data array.
# It provides 2D data array after spike removal and locations of spikes.
#### input: data, x1 and x2, discrimination factor d
#### output: data after spike removal, spike list, levels

import numpy as np
from numpy.random import randn
from scipy.signal import find_peaks
from scipy import optimize
import pandas as pd
from scipy import ndimage
from skimage.feature import peak_local_max
from scipy.optimize import curve_fit

#2D Gaussian fit
#https://scipython.com/blog/non-linear-least-squares-fitting-of-a-two-dimensional-data/

def spikeRemoval(data, d=3, f=12):
    # input:
    # --- data: input data of 2D np.array
    # --- f: a discrimination factor which sets a discriminator level H (the spike removal level
    #        defined as H = (avgerage)*d, where "avgearge" is, for a given y-pixel, the data average of x pixels between x1 and x2.
    # --- d: minimum number of pixels separating peaks in a region of 2 * min_distance + 1
    # output :
    # --- data_sp: a np.array for 2D data after spike removal
    # --- spike_position: coordinates of spikes found
    data_sp = np.copy(data)
    avg = np.mean(data)
    threshold=  avg*f

    # peak_local_max returns ndarray
    peak_pos = peak_local_max(data, min_distance = d, threshold_abs = threshold, indices = True)
    print('peak_pos', type(peak_pos))
    print(peak_pos)

    # get ndarray size
    N = int(peak_pos.size/2)
    print('size = ', N) #somehow size is doubled (x y) condisered 2

    for i in range(N):
        (m, n) = peak_pos[i]
        h0 = data[m,n]
        #print('I({0}, {1}) = {2}'.format(m, n, h0))

        #get Gaussian width = sigma
        data_in = data[m-d:m+d+1,n-d:n+d+1]
        x, y = np.linspace(m-d, m+d, num=2*d+1), np.linspace(n-d, n+d, num=2*d+1)
        xx, yy = np.meshgrid(x, y)

        # We need to ravel the meshgrids of xx, yy points to a pair of 1-D arrays.
        xdata = np.vstack((xx.ravel(), yy.ravel()))

        #gaussian(xy, x0, y0, sigma_x, sigmayx, H, a, b, c)
        #initial_guess = (m,n,d,d,data[m, n], 0, 0, avg)
        initial_guess = (m,n,d,d,data[m, n], avg)
        fit_p, pcov = curve_fit(gaussian, xdata, data_in.ravel(), p0=initial_guess)
        #fit_p, pcov = curve_fit(gaussian, xdata, data_in.ravel())
        #print('fit_p =', fit_p)
        #print('pcov =', pcov)
        data_fitted = np.reshape(gaussian(xdata, *fit_p),(2*d+1,2*d+1))
        #print('after reshaps, data_fitted=', data_fitted)

        for x in range(m-d, m+d+1):
            for y in range(n-d, n+d+1):
                data_sp[x,y]= data[x,y] - data_fitted[x-m+d, y-n+d]+ fit_p[5]
                #print('({0}, {1}) = {2}'.format(x, y, data_sp[x,y]))

    return [data_sp, peak_pos]

# Our function to fit is going to be a sum of two-dimensional Gaussians
def gaussian(xy, x0, y0, sigma_x, sigma_y, H, c):#, a, b, c):
    x, y = xy
    return H * np.exp( -0.5*((x-x0)/sigma_x)**2 -0.5*((y-y0)/sigma_y)**2)+c #+a*x+b*y+c

# test data for independently using spike.py
#data = np.genfromtxt('C:\\Users\jason\Downloads\\5mintues_signal.txt', delimiter=',')
#if data.size > 2097152:
#    data = data[np.logical_not(np.isnan(data))]     # remove nan
#    data = np.take(data, list(range(0, 2097152)))   # get 1024*2048 (original 2061)
#data = np.reshape(data, (1024, 2048), order='F')
#
#print('spike removal results:', spikeRemoval(data))
