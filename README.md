# RIXS_41A Software: Blue Magpie 
GUI for 41A beamline user including Image, Command, Status, Spectrum of RIXS experiments.

• The Blue Magpie is a simple and efficient software for RIXS instrument control and data acquisition.

• The codes is written using the Python language, and the communications between the BL devices & instruments are mainly through the EPICS.

• The software has a GUI, composed of a command window for the command line input (CLI) and windows to show images, spectra, BL information and the synchrotron storage ring status.

• In addition to the CLI, the software has a macro window which allows users to run an experiment in a friendly manner.


Command — to specify the values of parameters or to perform an action of controlling the beam line, spectrometer, sample environment or detector

Parameter — a quantity whose value specifies a device/instrument or gives a reading of a device 
    usage: command parameter1 value1, parameter2 value2….
    examples: mv x 2.1 (set the x coordination of the sample to 2.1)
              mvr y 0.2 (move the x coordination of the sample by 0.2)
              xas 520 550 0.02 1 (run a XAS scan from 520 to 550 eV in steps of 0.02 eV with a data taking time of 1 sec)
    data format: HDF5 through the h5py package
