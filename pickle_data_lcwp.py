#!/usr/bin/env ipython
import pandas as pd
import sys
from scipy import signal
from os import listdir
import glob

######Notes:
#Run:  python3 filename             input_directory  file_channel for signal(C1)  file_channel for gate/pedestal(C2)
#e.g.: python3 pickle_data_lcwp.py  data/first       C1 			  C2

# Defaults come from TekTronix 'scope
def filter_signal(data, nSamples = 10000, frameSize = 40e-9):
    '''Butterworth filter of signal.'''
    fs = float(nSamples)/frameSize # sample rate (1000 samples in 40ns)
    nyq = fs*0.5 # Nyquist frequency
    high = 700e6/nyq # high frequency cut-off
    b, a = signal.butter(2, high, 'low', analog = False)
    y = signal.lfilter(b, a, data)
    return y

# Conversion factors      # Cn:INSPECT?
vert_gain   = 2.4414e-7 #for C1: signal #2.4414e-6   # "VERTICAL_GAIN"
vert_offset = -3.200e-3#for C1: signal #-5.700e-2   # "VERTICAL_OFFSET"
vert_gain2   = 1.2207e-4 #for C2: gate #2.4414e-6   # "VERTICAL_GAIN"
vert_offset2 = -1.5500e+0#for C2: gate #-5.700e-2   # "VERTICAL_OFFSET"
vert_units  = 'V'         # "VERTUNIT"
horiz_units = 's'         # "HORUNIT"
horiz_scale = 1.2500e-10   #2.500e-10 # "HORIZ_INTERVAL"

# Data characteristics
n_samples = 402          # TODO: find this automatically
frameSize = n_samples*horiz_scale
print("Frame size:", frameSize)

# Initialise dictionaries for producing final DataFrame
output_dict     = {}
output_dict_ped = {}

output_dict['time']                 = []
output_dict_ped['time']             = []
output_dict['eventID']              = []
output_dict_ped['eventID']          = []
output_dict['voltage']              = []
output_dict_ped['voltage']          = []
output_dict['filtered_voltage']     = []
output_dict_ped['filtered_voltage'] = []

# Produce time index
index = [i * horiz_scale * 1e9 for i in range(n_samples)]  # Convert to ns

# Read filenames from directory
#files     = [x for x in listdir('data/' + sys.argv[1])          if x.endswith(sys.argv[2]+'.txt')]
#files_ped = [x for x in listdir('data/' + sys.argv[1] + '_ped') if x.endswith(sys.argv[2]+'.txt')]
filelist=glob.glob(sys.argv[1] + "/*" + sys.argv[2] + ".txt") 
print(filelist, "----- type: ",type(filelist))
files=[x for x in filelist]
filelist_ped=glob.glob(sys.argv[1] + "/*" + sys.argv[3] + ".txt") 
print(filelist_ped, "----- type: ",type(filelist_ped))
files_ped=[x for x in filelist_ped]

#file_pairs = files 
file_pairs =zip(files, files_ped)
#n_files = len(file_pairs)

file_count = 0
# Loop through each file_pair to extract events
#for file,file_ped in file_pairs:
for file,file_ped in file_pairs:
    print("file: ",file," file_ped: ",file_ped)
    data = open(file,'r').read()
    data_ped = open(file_ped,'r').read()
    #data     = open(('data/'+sys.argv[1]+    '/'+file),'r').read()
    #data_ped = open(('data/'+sys.argv[1]+'_ped/'+file),'r').read()
    
    n_points = int(len(data)/4)    
    n_events = int(n_points/n_samples)
    # Convert HEX to mV
    dec_data = []
    dec_data_ped = []
    for i in range(n_points):
        dec_value     = int(data[i*4:(i*4)+4], 16)
        dec_value_ped = int(data_ped[i*4:(i*4)+4], 16)
        
        dec_data    .append((dec_value*vert_gain + vert_offset)*1e3) # to mV
        dec_data_ped.append((dec_value_ped*vert_gain + vert_offset)*1e3) # to mV
    
    # Separate into events
    for i in range(n_events):
        output_dict['time']    .extend(index)
        output_dict_ped['time'].extend(index)
        
        output_dict['eventID']    .extend([i + file_count*n_events] * n_samples)
        output_dict_ped['eventID'].extend([i + file_count*n_events] * n_samples)
        
        voltages     = []
        voltages_ped = []
        for j in range(n_samples):
            voltages    .append(dec_data[i*n_samples+j])
            voltages_ped.append(dec_data_ped[i*n_samples+j])
        output_dict['voltage']    .extend(voltages)
        output_dict_ped['voltage'].extend(voltages_ped)

        # Apply Butterworth filter
        output_dict['filtered_voltage']    .extend(filter_signal(voltages,     n_samples, frameSize))
        output_dict_ped['filtered_voltage'].extend(filter_signal(voltages_ped, n_samples, frameSize))
    
    file_count += 1

# Convert dictionaries to df then pickle
output_df     = pd.DataFrame.from_dict(output_dict)
print("output_df: ",output_df)
output_df_ped = pd.DataFrame.from_dict(output_dict_ped)
print("output_df_ped: ",output_df_ped)

print("Events:", output_df.shape[0]/n_samples," in ped: ", output_df_ped.shape[0]/n_samples)

output_df.to_pickle(sys.argv[1] + "/all" + sys.argv[2] + ".pkl")
output_df_ped.to_pickle(sys.argv[1] + "/all" + sys.argv[3] + ".pkl")

#output_df.to_pickle('data/' + sys.argv[1]+'_'+sys.argv[2]+'.pkl')
#output_df_ped.to_pickle('data/' + sys.argv[1]+'_'+sys.argv[2]+'_ped.pkl')
