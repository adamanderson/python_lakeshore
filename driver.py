# lakeshore.py
#
# Classes that represent Lakeshore boxes with Python bindings to RS-232 and TCP/IO
# commands.
#
# Adam Anderson
# adama@fnal.gov
# 25 April 2016

import socket
import serial
import time

class Lakeshore218:
    def __init__(self, device, channames):
        '''
        Constructor
        
        Parameters
        ----------
        interface : str
            Serial device name.
        channames : Python list of str
            Names of channels
        
        Returns
        -------
        None
        '''
        self.device_name = device
        self.channel_names = channames

        self.serial_interface = serial.Serial(self.device_name, 9600, serial.SEVENBITS, serial.PARITY_ODD, serial.STOPBITS_ONE)


    def get_temps(self):
        '''
        Request a temperature measurement and then get it from 
        the queue, split merrily into a dictionary indexed by 
        channel name.

        Parameters
        ----------
        None

        Returns
        -------
        temps : dict
            Measured temperatures
        '''
        self.serial_interface.write(b'KRDG?\r\n')
        time.sleep(0.1) # wait for response from slow device
        output = self.serial_interface.read(self.serial_interface.inWaiting()).decode()
        temps = {self.channel_names[jchan]: float(output.split(',')[jchan]) \
                 for jchan in range(len(self.channel_names))}
        return temps

    def get_voltage(self):
        '''
        Request a voltage measurement and then get it from
        the queue, split merrily into a dictionary indexed by
        channel name.

        Parameters
        ----------
        None

        Returns
        -------
        volts : dict
            Measured voltages
        '''
        self.serial_interface.write(b'SRDG?\r\n')
        time.sleep(0.1) # wait for response from slow device
        output = self.serial_interface.read(self.serial_interface.inWaiting()).decode()
        volts = {self.channel_names[jchan]: float(output.split(',')[jchan]) \
                 for jchan in range(len(self.channel_names))}
        return volts

class Lakeshore350:
    def __init__(self, address, channames):
        '''
        Constructor

        Parameters
        ----------
        address : str
            IP address of Lakeshore box.
        channames : Python list of str
            Names of channels

        Returns
        -------
        None
        '''
        # check for valid channel names
        if len(channames) != 4:
            print('ERROR: Incorrect number of channel names supplied!')
            return

        self.IPaddress = address
        self.channel_names = channames

        self.tcp_interface = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_interface.connect((self.IPaddress, 7777))
        self.tcp_interface.settimeout(1.0)
    

    def query_temps(self):
        '''
        Request temperature measurements from box.

        Parameters
        ----------
        None

        Returns
        -------
        None
        '''
        self.tcp_interface.sendto(b'KRDG? 0\r\n', (self.IPaddress, 7777))


    def read_queue(self):
        '''
        Read whatever data is in the queue.

        Parameters
        ----------
        None

        Returns
        -------
        output : str
            Contents of the queue.
        '''
        output, _ = self.tcp_interface.recvfrom(2048)
        return output.decode("utf-8")


    def get_temps(self):
        '''
        Request a temperature measurement and then get it from 
        the queue, split merrily into a dictionary indexed by 
        channel name.

        Parameters
        ----------
        None

        Returns
        -------
        temps : dict
            Measured temperatures
        '''
        self.query_temps()
        output = self.read_queue()
        
        temps = {self.channel_names[jchan]: float(output.split(',')[jchan]) \
                 for jchan in range(len(self.channel_names))}
        return temps


    def set_heater_range(self, output, range):
        '''
        Sets the heater range for the PID---morally equivalent to turning
        the heater on and off.
        
        Parameters
        ----------
        output : int
            Heater to configure (1 or 2; 3 and 4 not implemented here)
        range : int
            Heater range (0-5 inclusive, with 0 being off)
        
        Returns
        -------
        None
        '''
        if output in [1,2] and range in [0,1,2,3,4,5]:
            self.tcp_interface.sendto(b'RANGE %d,%d\r\n'%(output, range), (self.IPaddress, 7777))
        else:
            raise ValueError('Heater range or output outside of allowed range!')


    def set_heater_output(self, output, value):
        '''
        Sets the manual output level for a heater. Note that the heater
        must be configured in manual mode for this to do anything useful.

        Parameters
        ----------
        output : int
            Heater to configure (1 or 2; 3 and 4 not implemented here)
        value : float
            Heater value, between 0 and 100

        Returns
        -------
        None
        '''
        if output in [1,2] and value>=0 and value<=100:
            self.tcp_interface.sendto(b'MOUT %d,%.2f\r\n'%(output, value), (self.IPaddress, 7777))
        else:
            raise ValueError('Heater range or value outside of allowed range!')


    def set_PID_temp(self, output, temp):
        '''
        Set the PID temperature setpoint.

        Parameters
        ----------
        output : int
            Heater to configure (1 or 2; 3 and 4 not implemented here)
        temp : float
            Setpoint temperature in K

        Returns
        -------
        None
        '''
        if output in [1,2]:
            self.tcp_interface.sendto(b'SETP %d,%f\r\n'%(output, temp), (self.IPaddress, 7777))
        else:
            raise ValueError('Heater output outside of allowed range!')


    def set_PID_params(self, P, I, D):
        '''
        Set the PID parameters.

        Parameters
        ----------
        P : float
            proportional
        I : float
            integral
        D : float
            derivative

        Returns
        -------
        None
        '''
        self.tcp_interface.sendto(b'PID %f,%f,%f\r\n'%(P, I, D), (self.IPaddress, 7777))


    def config_output(self, output, mode, input):
        '''
        Configures the output.
        
        Parameters
        ----------
        output : int
            Heater to configure (1 or 2; 3 and 4 not implemented here)
        mode : int
            0 = off
            1 = closed loop PID
            2 = zone
            3 = open loop
            4 = monitor out
            5 = warmup supply
        input : int
            0 = None
            1 = A
            2 = B
            3 = C
            4 = D
        
        Returns
        -------
        None
        '''
        if output in [1,2] and mode in range(6) and input in range(5):
            self.tcp_interface.sendto(b'OUTMODE %d,%d,%d,0\r\n'%(output, mode, input), (self.IPaddress, 7777))
        else:
            raise ValueError('Heater output, mode, or input outside of allowed range!')


class Lakeshore372:
    def __init__(self, address, channames):
        '''
        Constructor

        Parameters
        ----------
        address : str
            IP address of Lakeshore box.
        channames : dict
            Dictionary mapping channel numbers (1-16) to channel name strings.

        Returns
        -------
        None
        '''
        self.IPaddress = address
        self.channel_names = channames

        self.tcp_interface = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_interface.connect((self.IPaddress, 7777))
        self.tcp_interface.settimeout(10.0)
    

    def query_temp(self, channum):
        '''
        Request temperature measurements from box.

        Parameters
        ----------
        channum : int
            Channel number to query

        Returns
        -------
        None
        '''
        self.tcp_interface.sendto(bytes('KRDG? {}\r\n'.format(channum), 'utf-8'),
                                  (self.IPaddress, 7777))


    def query_r(self, channum):
        '''
        Request resistance measurements from box.

        Parameters
        ----------
        channum : int
            Channel number to query

        Returns
        -------
        None
        '''
        self.tcp_interface.sendto(bytes('SRDG? {}\r\n'.format(channum), 'utf-8'),
                                  (self.IPaddress, 7777))


    def query_excitation(self, channum):
        '''
        Request excitation powers.

        Parameters
        ----------
        channum : int
            Channel number to query

        Returns
        -------
        None
        '''
        self.tcp_interface.sendto(bytes('RDGPWR? {}\r\n'.format(channum), 'utf-8'),
                                  (self.IPaddress, 7777))
        
        
    def read_queue(self):
        '''
        Read whatever data is in the queue.

        Parameters
        ----------
        None

        Returns
        -------
        output : str
            Contents of the queue.
        '''
        output, _ = self.tcp_interface.recvfrom(2048)
        return output.decode("utf-8")


    def get_temps(self):
        '''
        Request a temperature measurement and then get it from 
        the queue, split merrily into a dictionary indexed by 
        channel name.

        Parameters
        ----------
        None

        Returns
        -------
        temps : dict
            Measured temperatures
        '''
        temps = {}
        for channum in self.channel_names:
            self.query_temp(channum)
            output = self.read_queue()
            temps[self.channel_names[channum]] = float(output)
        return temps


    def get_rs(self):
        '''
        Request a resistance measurement and then get it from 
        the queue, split merrily into a dictionary indexed by 
        channel name.

        Parameters
        ----------
        None

        Returns
        -------
        rs : dict
            Measured resistances.
        '''
        rs = {}
        for channum in self.channel_names:
            self.query_r(channum)
            output = self.read_queue()
            rs[self.channel_names[channum]] = float(output)
        return rs


    def get_excitations(self):
        '''
        Request excitation powers and then get it from 
        the queue, split merrily into a dictionary indexed by 
        channel name.

        Parameters
        ----------
        None

        Returns
        -------
        rs : dict
            Measured resistances.
        '''
        excitations = {}
        for channum in self.channel_names:
            self.query_excitation(channum)
            output = self.read_queue()
            excitations[self.channel_names[channum]] = float(output)
        return excitations
