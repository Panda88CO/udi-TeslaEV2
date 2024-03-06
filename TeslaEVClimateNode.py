#!/usr/bin/env python3

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)
import time
        
               
class teslaEV_ClimateNode(udi_interface.Node):

    def __init__(self, polyglot, parent, address, name, id,  TEV):
        super(teslaEV_ClimateNode, self).__init__(polyglot, parent, address, name)
        logging.info('_init_ Tesla ClimateNode Status Node')
        self.poly = polyglot
        self.ISYforced = False
        self.TEV = TEV
        self.EVid = id
        self.address = address 
        self.name = name
        self.nodeReady = False
        #self.node = self.poly.getNode(address)
        self.poly.subscribe(polyglot.START, self.start, address)
        #self.tempUnit = 0

    def start(self):                
        logging.debug('Start TeslaEV Climate Node')  
        self.setDriver('ST', 1, True, True)
        self.nodeReady = True
        #self.updateISYdrivers()
        #self.tempUnit = self.TEV.teslaEV_GetTempUnit()

    def stop(self):
        logging.debug('stop - Cleaning up')
    
    def climateNodeReady (self):
        return(self.nodeReady )
    



    def poll(self):
        
        logging.debug('Climate node {}'.format(self.EVid) )
        if self.nodeReady:
            if self.TEV.carState != 'Offline':
                self.updateISYdrivers()
            else:
                logging.info('Car appears off-line/sleeping - not updating data')

    def bool2ISY(self, bool):
        if bool == None:
            return (99)
        elif bool:
            return(1)
        else:
            return(0)

    def cond2ISY(self, condition):
        if condition == None:
            return(99)
        else:
            return(condition)

    def tempUnitAdjust(self, tempC):
        if self.TEV.teslaEV_GetTempUnit() == 0:
            return(tempC)  # C
        else:
            return(round(tempC*1.8+32, 2)) #F

    def setDriverTemp(self, Id, value):
        logging.debug('setDriverTemp : TempUnit: {}, value: {}'.format(self.TEV.teslaEV_GetTempUnit(), value))
        if value == None:
            self.setDriver(Id, 99, True, True, 25)  
        elif self.TEV.teslaEV_GetTempUnit()  == 0:
            self.setDriver(Id, round(round(2*value,0)/2,1), True, True, 4)
        elif self.TEV.teslaEV_GetTempUnit()  == 1:
            self.setDriver(Id, round(32+ 1.8*value, 0), True, True, 17)
        else:
            self.setDriver(Id, round(round(2*(value+273.15),0)/2,1), True, True, 26)

    def forceUpdateISYdrivers(self):
        logging.debug('forceUpdateISYdrivers: {}'.format(self.EVid))
        time.sleep(1)
        self.TEV.teslaEV_UpdateCloudInfo(self.EVid)
        self.updateISYdrivers()


    def updateISYdrivers(self):
        try:
            logging.info('Climate updateISYdrivers {}'.format(self.EVid))
            logging.debug('Climate updateISYdrivers {}'.format(self.TEV.teslaEV_GetClimateInfo(self.EVid)))

            logging.debug('GV1: {} '.format(self.TEV.teslaEV_GetCabinTemp(self.EVid)))
            self.setDriverTemp('GV1', self.TEV.teslaEV_GetCabinTemp(self.EVid))

            logging.debug('GV2: {} '.format(self.TEV.teslaEV_GetOutdoorTemp(self.EVid)))
            self.setDriverTemp('GV2', self.TEV.teslaEV_GetOutdoorTemp(self.EVid))

            logging.debug('GV3: {}'.format(self.TEV.teslaEV_GetLeftTemp(self.EVid)))
            self.setDriverTemp('GV3', self.TEV.teslaEV_GetLeftTemp(self.EVid))
        
            logging.debug('GV4: {}'.format(self.TEV.teslaEV_GetRightTemp(self.EVid)))
            self.setDriverTemp('GV4', self.TEV.teslaEV_GetRightTemp(self.EVid))

            logging.debug('GV5-9: {}'.format(self.TEV.teslaEV_GetSeatHeating(self.EVid)))
            temp = self.TEV.teslaEV_GetSeatHeating(self.EVid)
            if 'FrontLeft' in temp:
                self.setDriver('GV5', self.cond2ISY(temp['FrontLeft']), True, True)
            if 'FrontRight' in temp: 
                self.setDriver('GV6', self.cond2ISY(temp['FrontRight']), True, True)
            if 'RearLeft' in temp:    
                self.setDriver('GV7', self.cond2ISY(temp['RearLeft']), True, True)
            if 'RearMiddle' in temp:     
                self.setDriver('GV8', self.cond2ISY(temp['RearMiddle']), True, True)
            if 'RearRight' in temp:   
                self.setDriver('GV9', self.cond2ISY(temp['RearRight']), True, True)
            logging.debug('GV10: {}'.format(self.TEV.teslaEV_AutoConditioningRunning(self.EVid)))
            self.setDriver('GV10', self.bool2ISY(self.TEV.teslaEV_AutoConditioningRunning(self.EVid)), True, True)

            logging.debug('GV11: {}'.format(self.TEV.teslaEV_PreConditioningEnabled(self.EVid)))
            self.setDriver('GV11', self.bool2ISY(self.TEV.teslaEV_PreConditioningEnabled(self.EVid)), True, True)
            
            logging.debug('GV12: {}'.format(self.TEV.teslaEV_MaxCabinTempCtrl(self.EVid)))
            self.setDriverTemp('GV12', self.TEV.teslaEV_MaxCabinTempCtrl(self.EVid))

            logging.debug('GV13: {}'.format(self.TEV.teslaEV_MinCabinTempCtrl(self.EVid)))
            self.setDriverTemp('GV13', self.TEV.teslaEV_MinCabinTempCtrl(self.EVid))
            
            logging.debug('GV14: {}'.format(self.TEV.teslaEV_SteeringWheelHeatOn(self.EVid)))
            self.setDriver('GV14', self.cond2ISY(self.TEV.teslaEV_SteeringWheelHeatOn(self.EVid)), True, True) #need to be implemented        

            logging.debug('GV19: {}'.format(round(float(self.TEV.teslaEV_GetTimeSinceLastClimateUpdate(self.EVid)/60/60), 2)))
            self.setDriver('GV19', round(float(self.TEV.teslaEV_GetTimeSinceLastCarUpdate(self.EVid)/60/60), 2), True, True, 20)                                                    

            logging.debug('GV20: {}'.format(round(float(self.TEV.teslaEV_GetTimeSinceLastClimateUpdate(self.EVid)/60/60), 2)))
            self.setDriver('GV20', round(float(self.TEV.teslaEV_GetTimeSinceLastClimateUpdate(self.EVid)/60/60), 2), True, True, 20)
   
        except Exception as e:
            logging.error('updateISYdrivupdateISYdriversrsclimate node  failed: {}'.format(e))


    def ISYupdate (self, command):
        logging.info('ISY-update called')
        self.TEV.teslaEV_UpdateCloudInfo(self.EVid)
        self.updateISYdrivers()
 
    def evWindows (self, command):
        logging.info('evWindows- called')

        windowCtrl = int(float(command.get('value')))
        self.TEV.teslaEV_Wake(self.EVid)
        if windowCtrl == 1:
            self.TEV.teslaEV_Windows(self.EVid, 'vent')
        elif windowCtrl == 0:
            self.TEV.teslaEV_Windows(self.EVid, 'close')            
        else:
            logging.error('Wrong command for evWndows: {}'.format(windowCtrl))
 
        self.forceUpdateISYdrivers()


    def evSunroof (self, command):
        logging.info('evSunroof called')

        sunroofCtrl = int(float(command.get('value')))
        self.TEV.teslaEV_Wake(self.EVid)
        if sunroofCtrl == 1:
            self.TEV.teslaEV_SunRoof(self.EVid, 'vent')
        elif sunroofCtrl == 0:
            self.TEV.teslaEV_SunRoof(self.EVid, 'close')            
        else:
            logging.error('Wrong command for evSunroof: {}'.format(sunroofCtrl)) 

        self.forceUpdateISYdrivers()

    def evAutoCondition (self, command):
        logging.info('evAutoCondition called')  

        autoCond = int(float(command.get('value')))  
        self.TEV.teslaEV_Wake(self.EVid)
        if autoCond == 1:
            self.TEV.teslaEV_AutoCondition(self.EVid, 'start')
        elif autoCond == 0:
            self.TEV.teslaEV_AutoCondition(self.EVid, 'stop')            
        else:
            logging.error('Wrong command for evAutoCondition: {}'.format(autoCond)) 

        self.forceUpdateISYdrivers()
        #self.setDriver('GV10', self.bool2ISY(self.TEV.teslaEV_AutoConditioningRunning(self.EVid)), True, True)

        
    def evDefrostMax (self, command):
        logging.info('evDefrostMax called') 

        defrost = int(float(command.get('value')))  
        self.TEV.teslaEV_Wake(self.EVid)
        if defrost == 1:
            self.TEV.teslaEV_DefrostMax(self.EVid, 'on')
        elif defrost == 0:
            self.TEV.teslaEV_DefrostMax(self.EVid, 'off')            
        else:
            logging.error('Wrong command for evDefrostMax: {}'.format(defrost)) 

        self.forceUpdateISYdrivers()

    def evSetCabinTemp (self, command):
        logging.info('evSetCabinTemp called') 
        cabinTemp = float(command.get('value'))  
        self.TEV.teslaEV_Wake(self.EVid)
        if self.TEV.teslaEV_GetTempUnit() == 1:
            cabinTemp = round((cabinTemp-32)/1.8,2) # Must be set in C
        self.TEV.teslaEV_SetCabinTemps(self.EVid, cabinTemp)
        temp = self.TEV.tesleEV_GetCabinTemp(self.EVid)

        self.forceUpdateISYdrivers()
        #self.setDriverTemp('GV3', self.TEV.teslaEV_GetLeftTemp(self.EVid))
        #self.setDriverTemp('GV4', self.TEV.teslaEV_GetRightTemp(self.EVid))

    def evSetSeat0Heat (self, command):
        logging.info('evSetSeat0Heat called')

        seatTemp = int(float(command.get('value')))  
        self.TEV.teslaEV_Wake(self.EVid)
        self.TEV.teslaEV_SetSeatHeating(self.EVid, 0, seatTemp)
        temp = self.TEV.teslaEV_GetSeatHeating(self.EVid)

        self.forceUpdateISYdrivers()
        #self.setDriver('GV5', self.cond2ISY(temp['FrontLeft']), True, True)
        #self.setDriver('GV6', self.cond2ISY(temp['FrontRight']), True, True)
        #self.setDriver('GV7', self.cond2ISY(temp['RearLeft']), True, True)
        #self.setDriver('GV8', self.cond2ISY(temp['RearMiddle']), True, True)
        #self.setDriver('GV9', self.cond2ISY(temp['RearRight']), True, True)

    def evSetSeat1Heat (self, command):
        logging.info('evSetSeat1Heat called')
  
        seatTemp = int(float(command.get('value')))  
        self.TEV.teslaEV_Wake(self.EVid)
        self.TEV.teslaEV_SetSeatHeating(self.EVid, 1, seatTemp)
        temp = self.TEV.teslaEV_GetSeatHeating(self.EVid)

        self.forceUpdateISYdrivers()
        #self.setDriver('GV5', self.cond2ISY(temp['FrontLeft']), True, True)
        #self.setDriver('GV6', self.cond2ISY(temp['FrontRight']), True, True)
        #self.setDriver('GV7', self.cond2ISY(temp['RearLeft']), True, True)
        #self.setDriver('GV8', self.cond2ISY(temp['RearMiddle']), True, True)
        #self.setDriver('GV9', self.cond2ISY(temp['RearRight']), True, True)

    def evSetSeat2Heat (self, command):
        logging.info('evSetSea2tHeat called')

        seatTemp = int(float(command.get('value')))
        self.TEV.teslaEV_Wake(self.EVid)  
        self.TEV.teslaEV_SetSeatHeating(self.EVid, 2, seatTemp)
        temp = self.TEV.teslaEV_GetSeatHeating(self.EVid)

        self.forceUpdateISYdrivers()
        #self.setDriver('GV5', self.cond2ISY(temp['FrontLeft']), True, True)
        #self.setDriver('GV6', self.cond2ISY(temp['FrontRight']), True, True)
        #self.setDriver('GV7', self.cond2ISY(temp['RearLeft']), True, True)
        #self.setDriver('GV8', self.cond2ISY(temp['RearMiddle']), True, True)
        #self.setDriver('GV9', self.cond2ISY(temp['RearRight']), True, True)

    def evSetSeat4Heat (self, command):
        logging.info('evSetSeat4Heat called')

        seatTemp = int(float(command.get('value')))  
        self.TEV.teslaEV_Wake(self.EVid)
        self.TEV.teslaEV_SetSeatHeating(self.EVid, 4, seatTemp)
        temp = self.TEV.teslaEV_GetSeatHeating(self.EVid)
 
        self.forceUpdateISYdrivers()
        #self.setDriver('GV5', self.cond2ISY(temp['FrontLeft']), True, True)
        #self.setDriver('GV6', self.cond2ISY(temp['FrontRight']), True, True)
        #self.setDriver('GV7', self.cond2ISY(temp['RearLeft']), True, True)
        #self.setDriver('GV8', self.cond2ISY(temp['RearMiddle']), True, True)
        #self.setDriver('GV9', self.cond2ISY(temp['RearRight']), True, True)

    def evSetSeat5Heat (self, command):
        logging.info('evSetSeat5Heat called') 
        seatTemp = int(float(command.get('value'))) 
        self.TEV.teslaEV_Wake(self.EVid) 
        self.TEV.teslaEV_SetSeatHeating(self.EVid, 5, seatTemp)
        temp = self.TEV.teslaEV_GetSeatHeating(self.EVid)

        self.forceUpdateISYdrivers()
        #self.setDriver('GV5', self.cond2ISY(temp['FrontLeft']), True, True)
        #self.setDriver('GV6', self.cond2ISY(temp['FrontRight']), True, True)
        #self.setDriver('GV7', self.cond2ISY(temp['RearLeft']), True, True)
        #self.setDriver('GV8', self.cond2ISY(temp['RearMiddle']), True, True)
        #self.setDriver('GV9', self.cond2ISY(temp['RearRight']), True, True)


    def evSteeringWheelHeat (self, command):
        logging.info('evSteeringWheelHeat called')  
        wheel = int(float(command.get('value')))  
        #self.TEV.teslaEV_Wake(self.EVid)
        if wheel == 1:
            self.TEV.teslaEV_SteeringWheelHeat(self.EVid, 'on')
        elif wheel == 0:
            self.TEV.teslaEV_SteeringWheelHeat(self.EVid, 'off')            
        else:
            logging.error('Wrong command for evDefrostMax: {}'.format(wheel)) 
        #self.setDriver('GV14', self.cond2ISY(self.TEV.teslaEV_SteeringWheelHeatOn(self.EVid)), True, True)
        self.forceUpdateISYdrivers()


    '''
    def setTempUnit(self, command):
        logging.debug('setTempUnit')
        tempUnit  = int(float(command.get('value')))
        self.TEV.teslaEV_SetTempUnit(tempUnit)
        self.setDriver('GV15', self.TEV.teslaEV_GetTempUnit(), True, True)  
        self.forceUpdateISYdrivers()
    '''


    id = 'evclimate'
    commands = { 'UPDATE' : ISYupdate, 
                 'WINDOWS' : evWindows,
                 'SUNROOF' : evSunroof,
                 'AUTOCON' : evAutoCondition,
                 'CABINTEMP' : evSetCabinTemp,
                 'DEFROST' : evDefrostMax,            
                 'SEAT1' :evSetSeat0Heat,
                 'SEAT2' :evSetSeat1Heat,
                 'SEAT3' :evSetSeat2Heat,
                 'SEAT4' :evSetSeat4Heat,
                 'SEAT5' :evSetSeat5Heat,
                 'STEERINGW' : evSteeringWheelHeat,   

                }

    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 2},
            {'driver': 'GV1', 'value': 0, 'uom': 4},  #inside_temp
            {'driver': 'GV2', 'value': 0, 'uom': 4},  #outside_temp
            {'driver': 'GV3', 'value': 0, 'uom': 4},  #driver_temp_setting
            {'driver': 'GV4', 'value': 0, 'uom': 4},  #passenger_temp_setting
            {'driver': 'GV5', 'value': 0, 'uom': 25},  #seat_heater_left
            {'driver': 'GV6', 'value': 0, 'uom': 25},  #seat_heater_right
            {'driver': 'GV7', 'value': 0, 'uom': 25},  #seat_heater_rear_left
            {'driver': 'GV8', 'value': 0, 'uom': 25},  #seat_heater_rear_center
            {'driver': 'GV9', 'value': 0, 'uom': 25},  #seat_heater_rear_right
            {'driver': 'GV10', 'value': 0, 'uom': 25}, #is_auto_conditioning_on
            {'driver': 'GV11', 'value': 0, 'uom': 25}, #is_preconditioning
            {'driver': 'GV12', 'value': 0, 'uom': 4}, #max_avail_temp
            {'driver': 'GV13', 'value': 0, 'uom': 4}, #min_avail_temp   
            {'driver': 'GV14', 'value': 99, 'uom': 25}, #Steering Wheel Heat
            {'driver': 'GV19', 'value': 0, 'uom': 20},  #Last combined update Hours           
            {'driver': 'GV20', 'value': 0, 'uom': 20},  #Last update Hours          
            ]


