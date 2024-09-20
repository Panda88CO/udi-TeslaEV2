#!/usr/bin/env python3

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)

import time

class teslaEV_ChargeNode(udi_interface.Node):
    #from  udiLib import node_queue, wait_for_node_done, mask2key, latch2ISY, cond2ISY, heartbeat, state2ISY, bool2ISY, online2ISY, EV_setDriver, openClose2ISY
    from  udiLib import node_queue, wait_for_node_done, tempUnitAdjust, latch2ISY, chargeState2ISY, setDriverTemp, cond2ISY,  mask2key, heartbeat, state2ISY, bool2ISY, online2ISY, EV_setDriver, openClose2ISY

    def __init__(self, polyglot, parent, address, name, evid,  TEV):
        super(teslaEV_ChargeNode, self).__init__(polyglot, parent, address, name)
        logging.info('_init_ Tesla Charge Node')
        self.poly = polyglot
        self.ISYforced = False
        self.EVid = evid
        self.TEV = TEV
        self.address = address 
        self.name = name
        self.nodeReady = False



        self.n_queue = []
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.poly.subscribe(self.poly.START, self.start, address)

        self.poly.ready()
        self.poly.addNode(self, conn_status = None, rename = True)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)
        logging.info('_init_ Tesla Charge Node COMPLETE')
        
    def start(self):                
        logging.info('Start Tesla EV charge Node: {}'.format(self.EVid))  
        #self.EV_setDriver('ST', 1)
        self.nodeReady = True
        self.updateISYdrivers()

        

    def stop(self):
        logging.debug('stop - Cleaning up')
    
    def poll(self):
        
        logging.debug('Charge node {}'.format(self.EVid) )
        if self.nodeReady:
            if self.TEV.carState != 'Offline':
                self.updateISYdrivers()
            else:
                logging.info('Car appears off-line/sleeping - not updating data')    
    def chargeNodeReady (self):
        return(self.nodeReady )
   


    def forceUpdateISYdrivers(self):
        logging.debug('forceUpdateISYdrivers: {}'.format(self.EVid))
        time.sleep(1)
        self.TEV.teslaEV_UpdateCloudInfo(self.EVid)
        self.updateISYdrivers()

    def updateISYdrivers(self):
        try:
            logging.info('ChargeNode updateISYdrivers {}'.format(self.EVid))
            #logging.debug('ChargeNode updateISYdrivers {}'.format(self.TEV.teslaEV_GetChargingInfo(self.EVid)))
            #if self.TEV.isConnectedToEV():
            #logging.debug('GV1: {} '.format(self.TEV.teslaEV_FastChargerPresent(self.EVid)))
            self.EV_setDriver('GV1', self.bool2ISY(self.TEV.teslaEV_FastChargerPresent(self.EVid)))
            #logging.debug('GV2: {} '.format(self.TEV.teslaEV_ChargePortOpen(self.EVid)))
            self.EV_setDriver('GV2', self.bool2ISY(self.TEV.teslaEV_ChargePortOpen(self.EVid)))
            #logging.debug('GV3: {}'.format(self.TEV.teslaEV_ChargePortLatched(self.EVid)))
            self.EV_setDriver('GV3', self.latch2ISY(self.TEV.teslaEV_ChargePortLatched(self.EVid)))
            #logging.debug('GV3: {}'.format(self.TEV.teslaEV_ChargePortLatched(self.EVid)))
            #self.EV_setDriver('GV3', self.cond2ISY(self.TEV.teslaEV_ChargePortLatched(self.EVid)))
            #logging.debug('GV4: {} - {}'.format(self.TEV.teslaEV_GetBatteryRange(self.EVid), self.TEV.teslaEV_GetDistUnit()))

            temp_range = self.TEV.teslaEV_GetBatteryRange(self.EVid)
            #logging.debug('GV4: {}'.format(temp_range))
            if temp_range is None:
                self.EV_setDriver('GV4', temp_range, 25)
            else:
                if self.TEV.teslaEV_GetDistUnit() == 1:
                    self.EV_setDriver('GV4', round(float(temp_range),1), 116)
                else:
                    self.EV_setDriver('GV4', round(float(temp_range*1.6),1), 83)

            temp_level = self.TEV.teslaEV_GetBatteryLevel(self.EVid) 
            #logging.debug('BATLVL: {}'.format(temp_level))
            if temp_level != None:

                self.EV_setDriver('BATLVL', temp_level, 51)
            else:
                self.EV_setDriver('BATLVL', temp_level, 25)

            temp_current = self.TEV.teslaEV_MaxChargeCurrent(self.EVid) 
            #logging.debug('GV5: {}'.format(temp_current))
            if temp_current is None:
                self.EV_setDriver('GV5', temp_current, 25)
            else:
                if self.TEV.teslaEV_MaxChargeCurrent(self.EVid) != None:
   
                    self.EV_setDriver('GV5', temp_current, 1)
                else:
                    self.EV_setDriver('GV5', 99, 25)
            
            #logging.debug('GV6: {}'.format(self.TEV.teslaEV_ChargeState(self.EVid)))   
            self.EV_setDriver('GV6',self.chargeState2ISY(self.TEV.teslaEV_ChargeState(self.EVid)), 25)
 
            #logging.debug('GV7: {}'.format(self.TEV.teslaEV_ChargingRequested(self.EVid)))
            
            self.EV_setDriver('GV7', self.bool2ISY(self.TEV.teslaEV_ChargingRequested(self.EVid)))
            temp_CH_pwr = self.TEV.teslaEV_ChargingRequested(self.EVid)
            #logging.debug('GV8: {}'.format(temp_CH_pwr))
            if temp_CH_pwr is None:
                self.EV_setDriver('GV8', temp_CH_pwr, 25)
            else:

                self.EV_setDriver('GV8', self.TEV.teslaEV_GetChargingPower(self.EVid), 30)

            temp_CH_max = self.TEV.teslaEV_GetBatteryMaxCharge(self.EVid)
            #logging.debug('GV9: {}'.format(temp_CH_max))
            if temp_CH_max is None:
                self.EV_setDriver('GV9', temp_CH_max, 25)
            else:
                self.EV_setDriver('GV9', self.TEV.teslaEV_GetBatteryMaxCharge(self.EVid), 51)

                
            #logging.debug('GV10: {}'.format(self.TEV.teslaEV_charger_voltage(self.EVid)))
            self.EV_setDriver('GV10',self.TEV.teslaEV_charger_voltage(self.EVid))
            #logging.debug('GV11: {}'.format(self.TEV.teslaEV_charge_current_request(self.EVid)))
            self.EV_setDriver('GV11', self.TEV.teslaEV_charge_current_request(self.EVid))
            #logging.debug('GV12: {}'.format(self.TEV.teslaEV_charger_actual_current(self.EVid)))
            self.EV_setDriver('GV12', self.TEV.teslaEV_charger_actual_current(self.EVid))
            #logging.debug('GV13: {}'.format(self.TEV.teslaEV_charge_amps(self.EVid)))
            #self.EV_setDriver('GV13', self.TEV.teslaEV_charge_amps(self.EVid))
            #logging.debug('GV14: {}'.format(self.TEV.teslaEV_time_to_full_charge(self.EVid)))
            self.EV_setDriver('GV14', self.TEV.teslaEV_time_to_full_charge(self.EVid))
            #logging.debug('GV15: {}'.format(self.TEV.teslaEV_charge_energy_added(self.EVid)))
            self.EV_setDriver('GV15', self.TEV.teslaEV_charge_energy_added(self.EVid))
            #logging.debug('GV16: {}'.format(self.TEV.teslaEV_charge_miles_added_rated(self.EVid)))
            self.EV_setDriver('GV16', self.TEV.teslaEV_charge_miles_added_rated(self.EVid))
            if self.TEV.teslaEV_GetDistUnit() == 1:
                self.EV_setDriver('GV16', self.TEV.teslaEV_charge_miles_added_rated(self.EVid), 116)
            else:
                self.EV_setDriver('GV16', self.TEV.teslaEV_charge_miles_added_rated(self.EVid)*1.6 , 83 )

            #logging.debug('GV19: {}'.format(round(float(self.TEV.teslaEV_GetTimeSinceLastCarUpdate(self.EVid)/60/60),2)))
            self.EV_setDriver('GV19', round(float(self.TEV.teslaEV_GetTimeSinceLastCarUpdate(self.EVid)/60/60),2), 20)

            #logging.debug('GV20: {}'.format(round(float(self.TEV.teslaEV_GetTimeSinceLastChargeUpdate(self.EVid)/60/60),2)))
            self.EV_setDriver('GV20', round(float(self.TEV.teslaEV_GetTimeSinceLastChargeUpdate(self.EVid)/60/60),2), 20)

        except Exception as e:
            logging.error('updateISYdrivers charge node failed: {}'.format(e))

    def ISYupdate (self, command):
        logging.info('ISY-update called')
        self.TEV.teslaEV_UpdateConnectionStatus()
        self.TEV.teslaEV_UpdateCloudInfo(self.EVid)
        self.updateISYdrivers()
     

    def evChargePort (self, command):
        logging.info('evChargePort called')
        chargePort = int(float(command.get('value')))
        #self.TEV.teslaEV_Wake(self.EVid)
        if chargePort == 1:
            if self.TEV.teslaEV_ChargePort(self.EVid, 'open'):
                self.EV_setDriver('GV2', chargePort)

        elif chargePort == 0:
            if self.TEV.teslaEV_ChargePort(self.EVid, 'close'):
                self.EV_setDriver('GV2', chargePort)
        else:
            logging.debug('Wrong parameter passed to evChargePort : {}'.format(chargePort))
        self.EV_setDriver('GV2', chargePort)
   
        #self.forceUpdateISYdrivers()
        #self.EV_setDriver('GV2', self.cond2ISY(self.TEV.teslaEV_ChargePortOpen(self.EVid)))

    def evChargeControl (self, command):
        logging.info('evChargeControl called')
        chargeCtrl = int(float(command.get('value')))
        #self.TEV.teslaEV_Wake(self.EVid)
        if chargeCtrl == 1:
            if self.TEV.teslaEV_Charging(self.EVid, 'start'):
                self.EV_setDriver('GV6', 3)
        elif chargeCtrl == 0:
            if self.TEV.teslaEV_Charging(self.EVid, 'stop'):
                self.EV_setDriver('GV6', 4)
        else:
            logging.debug('Wrong parameter passed to evChargeControl : {}'.format(chargeCtrl))
        self.EV_setDriver('GV6', chargeCtrl)
        #self.forceUpdateISYdrivers()
        #self.EV_setDriver('GV6',self.state2ISY(self.TEV.teslaEV_ChargeState(self.EVid)))
        #self.EV_setDriver('GV7', self.cond2ISY(self.TEV.teslaEV_ChargingRequested(self.EVid)))

    def evSetBatteryChargeLimit (self, command):
        logging.info('evSetBatteryChargeLimit called')
        batLimitPercent = int(float(command.get('value')))
        #self.TEV.teslaEV_Wake(self.EVid)
        if self.TEV.teslaEV_SetChargeLimit(self.EVid, batLimitPercent):
            self.EV_setDriver('GV9', batLimitPercent)
        #self.forceUpdateISYdrivers()
        #if self.TEV.teslaEV_GetBatteryMaxCharge(self.EVid) != None:
        #    logging.debug('GV9: {}'.format(self.TEV.teslaEV_GetBatteryMaxCharge(self.EVid)))
        #    self.EV_setDriver('GV9', self.TEV.teslaEV_GetBatteryMaxCharge(self.EVid), 51)
        #else:
        #    self.EV_setDriver('GV9', 99, 25)

    def evSetCurrentChargeLimit (self, command):
        logging.info('evSetCurrentChargeLimit called')
        
        ampLimit = int(float(command.get('value')))
        #self.TEV.teslaEV_Wake(self.EVid)
        if self.TEV.teslaEV_SetChargeLimitAmps(self.EVid, ampLimit):
            self.EV_setDriver('CHARGEAMPS', ampLimit)
        #self.forceUpdateISYdrivers()
        #if self.TEV.teslaEV_MaxChargeCurrent(self.EVid) != None:
        #    logging.debug('GV5: {}'.format(self.TEV.teslaEV_MaxChargeCurrent(self.EVid)))
        #    self.EV_setDriver('GV5', self.TEV.teslaEV_MaxChargeCurrent(self.EVid), 1)
        #else:
        #    self.EV_setDriver('GV5', 99, 25)


    id = 'evcharge'

    commands = { 'UPDATE': ISYupdate, 
                 'CHARGEPORT' : evChargePort,
                 'CHARGECTRL' : evChargeControl,
                 'BATPERCENT' : evSetBatteryChargeLimit,
                 'CHARGEAMPS' : evSetCurrentChargeLimit,

                }

    drivers = [
            #{'driver': 'ST', 'value': 0, 'uom': 2},
            {'driver': 'GV1', 'value': 99, 'uom': 25},  #fast_charger_present
            {'driver': 'GV2', 'value': 99, 'uom': 25},  #charge_port_door_open
            {'driver': 'GV3', 'value': 99, 'uom': 25},  #charge_port_latch
            {'driver': 'BATLVL', 'value': 0, 'uom': 51},  #battery_level
            {'driver': 'GV4', 'value': 0, 'uom': 83}, # Estimated range - Miles
            {'driver': 'GV5', 'value': 0, 'uom': 1},  #charge_current_request_max
            {'driver': 'GV6', 'value': 99, 'uom': 25},  #charging_state
            {'driver': 'GV7', 'value': 99, 'uom': 25},  #charge_enable_request
            {'driver': 'GV8', 'value': 0, 'uom':30},  #charger_power
            {'driver': 'GV9', 'value': 0, 'uom': 51},  #bat charge_limit_soc
            {'driver': 'GV10', 'value': 0, 'uom': 72},  #charger_voltage
            {'driver': 'GV11', 'value': 0, 'uom': 1},  #charge_current_request
            {'driver': 'GV12', 'value': 0, 'uom': 1},  #charger_actual_current
            #{'driver': 'GV13', 'value': 0, 'uom': 1},  #charge_amps
            {'driver': 'GV14', 'value': 0, 'uom': 44},  #time_to_full_charge
            {'driver': 'GV15', 'value': 0, 'uom': 33},  #charge_energy_added           
            {'driver': 'GV16', 'value': 0, 'uom': 83},  #charge_miles_added_rated
            {'driver': 'GV19', 'value': 0, 'uom': 20},  #Last combined update Hours           
            {'driver': 'GV20', 'value': 0, 'uom': 20},  #Last update Hours


            ]
            


