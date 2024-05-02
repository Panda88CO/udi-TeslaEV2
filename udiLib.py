#!/usr/bin/env python3
"""
Polyglot TEST v3 node server 


MIT License
"""

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)

from os import truncate
import time
import math
import numbers 

def node_queue(self, data):
    #logging.debug('node_queue {}'.format(data))
    self.n_queue.append(data['address'])

def wait_for_node_done(self):
    while len(self.n_queue) == 0:
        time.sleep(0.1)
    self.n_queue.pop()

def mask2key (self, mask):
    logging.debug('mask2key : {}'.format(mask))
    return(int(round(math.log2(mask),0)))
    
def daysToMask (self, dayList):
    daysValue = 0 
    i = 0
    for day in self.daysOfWeek:
        if day in dayList:
            daysValue = daysValue + pow(2,i)
        i = i+1
    return(daysValue)

def maskToDays(self, daysValue):
    daysList = []
    for i in range(0,7):
        mask = pow(2,i)
        if (daysValue & mask) != 0 :
            daysList.append(self.daysOfWeek[i])
    return(daysList)


def bool2Nbr(self, bool):
    if bool == True:
        return(1)
    elif bool == False:
        return(0)
    else:
        return(None)
    
def round2ISY(self,nbr, res):
    if isinstance(nbr, numbers.Number):
        return(round(nbr, res))
    else:
        return(None)

def bool2ISY (self, data):
    if data:
        return(1)
    else:
        return(0)

def state2Nbr(self, val):
    if val == 'normal':
        return(0)
    elif val == 'alert':
        return(1)
    else:
        return(99)

def isy_value(self, value):
    if value == None:
        return (99)
    else:
        return(value)
    
def daylist2bin(self, daylist):
    sum = 0
    if 'sun' in daylist:
        sum = sum + 1
    if 'mon' in daylist:
        sum = sum + 2       
    if 'tue' in daylist:
        sum = sum + 4
    if 'wed' in daylist:
        sum = sum + 8
    if 'thu' in daylist:
        sum = sum + 16
    if 'fri' in daylist:
        sum = sum + 32
    if 'sat' in daylist:
        sum = sum + 64
    return(sum)


def season2ISY(self, season):
    logging.debug('season2ISY {}'.format(season))
    if season.upper() == 'WINTER':
        return(0)
    elif season.upper() == 'SUMMER':
        return(1)
    elif season != None:
        return(2)
    else:
        return (99)
    
def state2ISY(self, state):
    if state.lower() == 'offline':
        return(0)
    elif state.lower() == 'online':
        return(1)
    elif state.lower() == 'sleeping':
        return(2) 
    elif state.lower() == 'unknown':
        return(99)
    else:          
        logging.error('Unknown state passed {}'.format(state))
        return(99)



def online2ISY(self, state):
    if state.lower() == 'online':
        return(1)
    else:
        return(0)

def openClose2ISY(self, state):
    if state == None:
        return(99)
    elif state == 'closed':
        return(0)
    else:
        return(1)

def cond2ISY(self, condition):
    if condition == None:
        return(99)
    else:
        return(condition)
    
def latch2ISY(self, state):
    if state.lower() == 'engaged':
        return(1)
    elif state.lower() == 'blocking':
        return(2)
    elif state.lower() == 'disengaged':
        return(0)
    else:
        return(99)

def period2ISY(self, period):
    logging.debug('period2ISY {}'.format(period))
    if period.upper() == 'OFF_PEAK':
        return(0)
    elif period.upper() == 'PARTIAL_PEAK':
        return(1)
    elif period.upper() == 'PEAK':
        return(2)
    else:
        return (99) 

def EV_setDriver(self, key, value, Unit=None):
    logging.debug('EV_setDriver : {} {} {}'.format(key, value, Unit))
    if value == None:
        logging.debug('None value passed = seting 99, UOM 25')
        self.node.setDriver(key, 99, True, True, 25)
    else:
        if Unit:
            self.node.setDriver(key, value, True, True, Unit)
        else:
            self.node.setDriver(key, value)

def tempUnitAdjust(self, tempC):
    if self.TEV.teslaEV_GetTempUnit() == 0:
        return(tempC)  # C
    else:
        return(round(tempC*1.8+32, 2)) #F
    
def setDriverTemp(self, Id, value):
    logging.debug('setDriverTemp : TempUnit: {}, value: {}'.format(self.TEV.teslaEV_GetTempUnit(), value))
    if value == None:
        self.ev_setDriver(Id, 99,25)  
    elif self.TEV.teslaEV_GetTempUnit()  == 0:
        self.ev_setDriver(Id, round(round(2*value,0)/2,1),4)
    elif self.TEV.teslaEV_GetTempUnit()  == 1:
        self.ev_setDriver(Id, round(32+ 1.8*value, 0),17)
    else:
        self.ev_setDriver(Id, round(round(2*(value+273.15),0)/2,1),26)

def send_rel_temp_to_isy(self, temperature, stateVar):
    logging.debug('convert_temp_to_isy - {}'.format(temperature))
    logging.debug('ISYunit={}, Mess_unit={}'.format(self.ISY_temp_unit , self.messana_temp_unit ))
    if self.ISY_temp_unit == 0: # Celsius in ISY
        if self.messana_temp_unit == 'Celsius' or self.messana_temp_unit == 0:
            self.node.setDriver(stateVar, round(temperature,1), True, True, 4)
        else: # messana = Farenheit
            self.node.setDriver(stateVar, round(temperature*5/9,1), True, True, 17)
    elif  self.ISY_temp_unit == 1: # Farenheit in ISY
        if self.messana_temp_unit == 'Celsius' or self.messana_temp_unit == 0:
            self.node.setDriver(stateVar, round((temperature*9/5),1), True, True, 4)
        else:
            self.node.setDriver(stateVar, round(temperature,1), True, True, 17)
    else: # kelvin
        if self.messana_temp_unit == 'Celsius' or self.messana_temp_unit == 0:
            self.node.setDriver(stateVar, round((temperature,1), True, True, 4))
        else:
            self.node.setDriver(stateVar, round((temperature)*9/5,1), True, True, 17)


def send_temp_to_isy (self, temperature, stateVar):
    logging.debug('convert_temp_to_isy - {}'.format(temperature))
    logging.debug('ISYunit={}, Mess_unit={}'.format(self.ISY_temp_unit , self.messana_temp_unit ))
    if self.ISY_temp_unit == 0: # Celsius in ISY
        if self.messana_temp_unit == 'Celsius' or self.messana_temp_unit == 0:
            self.node.setDriver(stateVar, round(temperature,1), True, True, 4)
        else: # messana = Farenheit
            self.node.setDriver(stateVar, round((temperature-32)*5/9,1), True, True, 17)
    elif  self.ISY_temp_unit == 1: # Farenheit in ISY
        if self.messana_temp_unit == 'Celsius' or self.messana_temp_unit == 0:
            self.node.setDriver(stateVar, round((temperature*9/5+32),1), True, True, 4)
        else:
            self.node.setDriver(stateVar, round(temperature,1), True, True, 17)
    else: # kelvin
        if self.messana_temp_unit == 'Celsius' or self.messana_temp_unit == 0:
            self.node.setDriver(stateVar, round((temperature+273.15,1), True, True, 4))
        else:
            self.node.setDriver(stateVar, round((temperature+273.15-32)*9/5,1), True, True, 17)



def heartbeat(self):
    logging.debug('heartbeat: ' + str(self.hb))
    
    if self.hb == 0:
        self.reportCmd('DON',2)
        self.hb = 1
    else:
        self.reportCmd('DOF',2)
        self.hb = 0

def handleLevelChange(self, level):
    logging.info('New log level: {}'.format(level))        