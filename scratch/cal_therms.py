from re import S
import numpy as np
import pickle
import time
from pybluefors.control import TemperatureController
from python_lakeshore.driver import Lakeshore372

test_mode = False

Pmin = 1e-6
Pmax = 1e-3
Pvals = np.logspace(np.log10(Pmin), np.log10(Pmax), 31)
wait_time = 600

chans = {1:'U08163', 2:'U08164', 3:'U08165', 4:'U08167',
         5:'U09138', 6:'U09140', 7:'U09144', 8:'U09146'}

tc = TemperatureController('192.168.1.20')
ls = Lakeshore372('192.168.0.15', chans)

mxc_data = {}
therms_temp = {}
therms_r = {}

for P in Pvals:
    print('Setting MXC power to {:.2e} W'.format(P))
    if test_mode:
        time.sleep(2)
    else:
        tc.set_heater('MXC-heater', 0, P)
        time.sleep(wait_time)

    mxc_data[P] = tc.get_data('MXC-flange')
    therms_temp[P] = ls.get_temps()
    therms_r[P] = ls.get_rs()

    print('MXC temp = ')
    print(mxc_data[P])
    print('thermometer temps = ')
    print(therms_temp[P])
    print('thermometer Rs = ')
    print(therms_r[P])

with open('cal_data.pkl', 'wb') as f:
    save_data = {'MXC temps':mxc_data,
                 'thermometer temps':therms_temp,
                 'thermometer Rs':therms_r,
                 'powers':Pvals}
    pickle.dump(save_data, f)

tc.set_heater('MXC-heater', 0, 0)