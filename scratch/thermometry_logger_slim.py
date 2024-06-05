import pickle as pkl
import time
from datetime import datetime
from python_lakeshore.driver import Lakeshore218
import os

# user settings
output_folder = '/home/slimjim/fridge_logs/'
ls218_50K_port = '/dev/ttyr01'
ls218_4K_port = '/dev/ttyr00'
chans218_50K = ['50K head', '50K outer ring', '50K inner ring', '50K hand hole plate', '50K top of shield', '4K top of shield']
chans218_4K = ['4K head', '4K heat strap (bus side)', '4K stage (near bus)', '4K stage (opposite bus)']
chans_voltage_all = chans218_50K + chans218_4K
chans_resistance_all = []
chans_all = chans_voltage_all + chans_resistance_all
sample_interval = 60 #seconds

# set up output files
starttime = datetime.now()
timestring = starttime.strftime("%Y%m%d_%H%M%S")
outname = timestring + '_thermo_log'
header = 'timestamp\t\t'+'\t'.join(chans_all)+'\n'
with open(output_folder+outname+'.txt', 'w') as f:
    f.write(header)
print(header)

# set up data struct.
thermodat = dict.fromkeys(['temperature','voltage','resistance','time'])
thermodat['temperature'] = {chan:[] for chan in chans_all}
thermodat['voltage'] = {chan:[] for chan in chans_voltage_all}
thermodat['resistance'] = {chan:[] for chan in chans_resistance_all}
thermodat['time'] = []

# connect to devices (ls218 channels are 0 indexed, ls372 channels are 1 indexed)
ls218_50K = Lakeshore218(ls218_50K_port, {i:chan for i, chan in enumerate(chans218_50K)})
ls218_4K = Lakeshore218(ls218_4K_port, {i:chan for i, chan in enumerate(chans218_4K)})

# log thermometry data until keyboard interrupt
try:
    while True:
        # query
        time.sleep(sample_interval - (time.time() % sample_interval))
        timestamp = datetime.now()
        temps218_50K = ls218_50K.get_temps()
        volts218_50K = ls218_50K.get_voltage()
        temps218_4K = ls218_4K.get_temps()
        volts218_4K = ls218_4K.get_voltage()

        # parse
        for chan in temps218_50K: thermodat['temperature'][chan].append(temps218_50K[chan]) 
        for chan in volts218_50K: thermodat['voltage'][chan].append(volts218_50K[chan])
        for chan in temps218_4K: thermodat['temperature'][chan].append(temps218_4K[chan]) 
        for chan in volts218_4K: thermodat['voltage'][chan].append(volts218_4K[chan])
        thermodat['time'].append(timestamp)

        # output
        pkl.dump(thermodat,open(output_folder+outname+'.pkl','wb'))
        thermotext = '\t'.join(map(str,[thermodat['temperature'][chan][-1] for chan in thermodat['temperature']]))
        outtext = timestamp.strftime("%Y-%m-%d_%H:%M:%S") + '\t' + thermotext
        with open(os.path.join(output_folder, outname+'.txt'), 'a') as f:
            f.write(outtext+'\n')
        print(outtext)

except KeyboardInterrupt:
    print('Logging stopped')

print(thermodat)

