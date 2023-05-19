import pickle as pkl
import time
from datetime import datetime
from driver import Lakeshore218
from driver import Lakeshore372
from pybluefors.control import TemperatureController

# user settings
output_folder = '/home/mryoung/fridge_logs/window_test/'
ls218_port = '/dev/ttyr02'
ls372_ip = '192.168.1.40'
tc_ip = '192.168.1.20'
chans218 = ['50BC','50BE','50K-stage','empty','4BC','4BE','50K-shield-upper','50-K-shield-lower']
chans372 = ['1BC','1BE','MKID_upper','MKID-lower']
chanstc = ['50K-flange','4K-flange','Still-flange']
sample_interval = 60 #seconds

# set up output files
starttime = datetime.now()
timestring = starttime.strftime("%Y%m%d_%H%M%S")
outname = timestring + '_thermo_log'
header = 'timestamp\t\t'+'\t'.join(map(str,chans218+chans372+chanstc))+'\n'
with open(output_folder+outname+'.txt', 'w') as f:
    f.write(header)
print(header)

# set up data struct.
thermodat = dict.fromkeys(['temperature','voltage','resistance','time'])
thermodat['temperature'] = {chan:[] for chan in chans218+chans372+chanstc}
thermodat['voltage'] = {chan:[] for chan in chans218}
thermodat['resistance'] = {chan:[] for chan in chans372+chanstc}
thermodat['time'] = []

# connect to devices (ls218 channels are 0 indexed, ls372 channels are 1 indexed)
ls218 = Lakeshore218(ls218_port, {i:chan for i, chan in enumerate(chans218)})
ls372 = Lakeshore372(ls372_ip, {i+1:chan for i, chan in enumerate(chans372)})
tc = TemperatureController(tc_ip)

# log thermometry data until keyboard interrupt
try:
    while True:
        # query
        time.sleep(sample_interval - (time.time() % sample_interval))
        timestamp = datetime.now()
        temps218 = ls218.get_temps()
        volts218 = ls218.get_voltage()
        try:
            temps372 = ls372.get_temps()
            res372 = ls372.get_rs()
        except:
            temps372 = {chan:0 for chan in chans372}
            res372 = {chan:0 for chan in chans372}
            print('LS372 TIMEOUT')
        tcdata = {chan:tc.get_data(chan) for chan in chanstc}
        # parse
        for chan in temps218: thermodat['temperature'][chan].append(temps218[chan]) 
        for chan in temps372: thermodat['temperature'][chan].append(temps372[chan])
        for chan in volts218: thermodat['voltage'][chan].append(volts218[chan])
        for chan in res372: thermodat['resistance'][chan].append(res372[chan])
        for chan in tcdata: thermodat['temperature'][chan].append(tcdata[chan]['measurements']['temperature'])
        for chan in tcdata: thermodat['resistance'][chan].append(tcdata[chan]['measurements']['resistance'])
        thermodat['time'].append(timestamp)
        # output
        pkl.dump(thermodat,open(output_folder+outname+'.pkl','wb'))
        thermotext = '\t'.join(map(str,[thermodat['temperature'][chan][-1] for chan in thermodat['temperature']]))
        outtext = timestamp.strftime("%Y-%m-%d_%H:%M:%S") + '\t' + thermotext
        with open(output_folder+outname+'.txt', 'a') as f:
            f.write(outtext+'\n')
        print(outtext)

except KeyboardInterrupt:
    print('Logging stopped')

print(thermodat)

