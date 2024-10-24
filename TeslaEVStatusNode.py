#!/usr/bin/env python3

import time
import re
from TeslaEVChargeNode import teslaEV_ChargeNode
from TeslaEVClimateNode import teslaEV_ClimateNode 

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)

               
               
class teslaEV_StatusNode(udi_interface.Node):
    from  udiLib import node_queue, command_res2ISY, wait_for_node_done, tempUnitAdjust, latch2ISY, chargeState2ISY, setDriverTemp, cond2ISY,  code2ISY, mask2key, heartbeat, state2ISY, bool2ISY, online2ISY, EV_setDriver, openClose2ISY

    def __init__(self, polyglot, primary, address, name, evid, TEV):
        super(teslaEV_StatusNode, self).__init__(polyglot, primary, address, name)
        logging.info('_init_ Tesla EV  Status Node')
        self.poly = polyglot
        self.ISYforced = False
        self.EVid = evid
        self.TEV = TEV
        self.primary = primary
        self.address = address
        self.name = name
        self.statusNodeReady = False
        self.climateNodeReady = False
        self.chargeNodeReady = False
        self.n_queue = []
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.poly.subscribe(self.poly.START, self.start, address)

        self.poly.ready()
        self.poly.addNode(self, conn_status = None, rename = True)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)
        logging.info('_init_ Tesla EV  Status Node COMLETE')


    def start(self):       
        logging.info('Start Tesla EV Status Node for {self.EVid}') 

        #self.EV_setDriver('ST', 1)
        #self.forceUpdateISYdrivers()
        self.createSubNodes()
        self.updateISYdrivers()
        self.statusNodeReady = True
        
    def createSubNodes(self):
        logging.debug('Creating sub nodes for {self.EVid}')
        nodeAdr = 'cl'+str(self.EVid)[-14:]
        nodeName = self.poly.getValidName('Climate Info')
        nodeAdr = self.poly.getValidAddress(nodeAdr)
        #if not self.poly.getNode(nodeAdr):
        logging.info('Creating ClimateNode: {nodeAdr} - {self.address} {nodeAdr} {nodeName} {self.EVid}')
        self.climateNode = teslaEV_ClimateNode(self.poly, self.address, nodeAdr, nodeName, self.EVid, self.TEV )


        nodeAdr = 'cg'+str(self.EVid)[-14:]
        nodeName = self.poly.getValidName('Charging Info')
        nodeAdr = self.poly.getValidAddress(nodeAdr)
        #if not self.poly.getNode(nodeAdr):
        logging.info('Creating ChargingNode: {nodeAdr} - {self.address} {nodeAdr} {nodeName} {self.EVid}')
        self.chargeNode = teslaEV_ChargeNode(self.poly, self.address, nodeAdr, nodeName, self.EVid, self.TEV )


    def subnodesReady(self):
        return(self.climateNodeReady and self.chargeNodeReady )

    def stop(self):
        logging.debug('stop - Cleaning up')


    def ready(self):
        return(self.chargeNodeReady and self.climateNodeReady)

    def poll (self, code = 'ok'):    
        logging.info('Status Node Poll for {self.EVid} - code: {code}')        

        try:
            if code == 'ok':
                self.updateISYdrivers()
                self.climateNode.updateISYdrivers()
                self.chargeNode.updateISYdrivers()

            elif code in['offline', 'overload', 'error', 'unknown']:
                self.EV_setDriver('GV13', self.code2ISY(code), 25)
                logging.info('Car appears off-line/sleeping or overload  - not updating data')
            else:
                self.EV_setDriver('GV13', 99, 25)
        except Exception as e:
            logging.error('Status Poll exception : {e}')



    def updateISYdrivers(self):
        try:
            
            logging.info('updateISYdrivers - Status for {self.EVid}')

            temp = {}


            self.EV_setDriver('GV1', self.TEV.teslaEV_GetCenterDisplay(self.EVid), 25)

            self.EV_setDriver('GV2', self.bool2ISY(self.TEV.teslaEV_HomeLinkNearby(self.EVid)), 25)
            self.EV_setDriver('GV0', self.TEV.teslaEV_nbrHomeLink(self.EVid), 25)


            self.EV_setDriver('GV3', self.bool2ISY(self.TEV.teslaEV_GetLockState(self.EVid)), 25)
            if self.TEV.teslaEV_GetDistUnit() == 1:
                self.EV_setDriver('GV4', self.TEV.teslaEV_GetOdometer(self.EVid), 116)
            else:
                self.EV_setDriver('GV4', self.TEV.teslaEV_GetOdometer(self.EVid), 83)

            self.EV_setDriver('GV5', self.online2ISY(self.TEV.teslaEV_GetConnectionStatus(self.EVid)),25)
            
            windows  = self.TEV.teslaEV_GetWindoStates(self.EVid)
            if 'FrontLeft' not in windows:
                windows['FrontLeft'] = None
            if 'FrontRight' not in windows:
                windows['FrontRight'] = None
            if 'RearLeft' not in windows:
                windows['RearLeft'] = None
            if 'RearRight' not in windows:
                windows['RearRight'] = None
            self.EV_setDriver('GV6', windows['FrontLeft'], 25)
            self.EV_setDriver('GV7', windows['FrontRight'], 25)
            self.EV_setDriver('GV8', windows['RearLeft'], 25)
            self.EV_setDriver('GV9', windows['RearRight'], 25)
            
            #self.EV_setDriver('GV10', self.TEV.teslaEV_GetSunRoofPercent(self.EVid), 51)
            #if self.TEV.teslaEV_GetSunRoofState(self.EVid) != None:
            #    self.EV_setDriver('GV10', self.openClose2ISY(self.TEV.teslaEV_GetSunRoofState(self.EVid)), 25)
    
            self.EV_setDriver('GV11', self.TEV.teslaEV_GetTrunkState(self.EVid), 25)
            self.EV_setDriver('GV12', self.TEV.teslaEV_GetFrunkState(self.EVid), 25)
            self.EV_setDriver('GV13', self.state2ISY(self.TEV.teslaEV_GetCarState(self.EVid)), 25)
   
            if self.TEV.location_enabled():
                location = self.TEV.teslaEV_GetLocation(self.EVid)
                logging.debug('teslaEV_GetLocation {location}')
                if location['longitude']:
                    logging.debug('GV17: {}'.format(round(location['longitude'], 3)))
                    self.EV_setDriver('GV17', round(location['longitude'], 3), 56)
                else:
                    logging.debug('GV17: NONE')
                    self.EV_setDriver('GV17', None, 25)
                if location['latitude']:
                    logging.debug('GV18: {}'.format(round(location['latitude'], 3)))
                    self.EV_setDriver('GV18', round(location['latitude'], 3), 56)
                else:
                    logging.debug('GV18: NONE')
                    self.EV_setDriver('GV18', None, 25)
            else:
                self.EV_setDriver('GV17', 98, 25)
                self.EV_setDriver('GV18', 98, 25)            

            try:
                temp = round(float(self.TEV.teslaEV_GetTimeSinceLastCarUpdate(self.EVid)/60/60), 2)
                self.EV_setDriver('GV19', temp ,20)   
            except ValueError:
                self.EV_setDriver('GV19', None, 25)                                                 
            try:
                temp = round(float(self.TEV.teslaEV_GetTimeSinceLastStatusUpdate(self.EVid)/60/60), 2)
                self.EV_setDriver('GV20', temp, 20)
            except ValueError:
                self.EV_setDriver('GV20', None, 25)           
            #else:
            #    logging.info('System not ready yet')

        except Exception as e:
            logging.error('updateISYdriver Status node failed: {e}')

    def ISYupdate (self, command):
        logging.info('ISY-update status node  called')
        code, state = self.TEV.teslaEV_update_connection_status(self.EVid)
        self.EV_setDriver('GV13', self.state2ISY(self.TEV.teslaEV_GetCarState(self.EVid)), 25)
        code, res = self.TEV.teslaEV_UpdateCloudInfo(self.EVid)
        self.updateISYdrivers()
        self.EV_setDriver('GV21', self.command_res2ISY(code), 25)

    def evWakeUp (self, command):
        logging.info('EVwakeUp called')
        code, res = self.TEV._teslaEV_Wake(self.EVid)
        logging.debug('Wake result {code} - {res}')
        if code in ['ok']:               
            code, res = self.TEV.teslaEV_UpdateCloudInfoAwake(self.EVid)
            self.updateISYdrivers()
        self.EV_setDriver('GV21', self.command_res2ISY(code), 25)
        self.EV_setDriver('GV13', self.state2ISY(self.TEV.teslaEV_GetCarState(self.EVid)),25)


    def evHonkHorn (self, command):
        logging.info('EVhonkHorn called')        
        code, res = self.TEV.teslaEV_HonkHorn(self.EVid)
        logging.info('return  {code} - {res}')
        if code in ['ok']:
             self.EV_setDriver('GV21', self.command_res2ISY(res),25)
        else:
            self.EV_setDriver('GV21', self.code2ISY(code),25)
        self.EV_setDriver('GV13', self.state2ISY(self.TEV.teslaEV_GetCarState(self.EVid)),25)

        #return(code, res)
            
        #self.EV_setDriver()
        #self.forceUpdateISYdrivers()

    def evFlashLights (self, command):
        logging.info('EVflashLights called')
        code, res = self.TEV.teslaEV_FlashLights(self.EVid)
        logging.info('return  {code} - {res}')
        if code in ['ok']:
             self.EV_setDriver('GV21', self.command_res2ISY(res),25)
        else:
            self.EV_setDriver('GV21', self.code2ISY(code),25)

        self.EV_setDriver('GV21', self.command_res2ISY(code),25)
        self.EV_setDriver('GV13', self.state2ISY(self.TEV.teslaEV_GetCarState(self.EVid)),25)


        #self.forceUpdateISYdrivers()

    def evControlDoors (self, command):
        logging.info('EVctrlDoors called')
        #self.TEV.teslaEV_Wake(self.EVid)
 
        doorCtrl = int(float(command.get('value')))
        if doorCtrl == 1:
            cmd = 'unlock'
            #code, red =  self.TEV.teslaEV_Doors(self.EVid, 'unlock')
            #self.EV_setDriver('GV3', doorCtrl )
        elif doorCtrl == 0:
            cmd = 'unlock'
            #code, res =  self.TEV.teslaEV_Doors(self.EVid, 'lock')
            #self.EV_setDriver('GV3', doorCtrl )            
        else:
            logging.error('Unknown command for evControlDoors {command}')
            self.EV_setDriver('GV21', self.command_res2ISY('error'), 25)
            return('error', 'code wrong')
        code, res =  self.TEV.teslaEV_Doors(self.EVid, cmd)
        logging.info('return  {code} - {res}')
        self.EV_setDriver('GV3', doorCtrl, 25)
        if code in ['ok']:
             self.EV_setDriver('GV21', self.command_res2ISY(res),25)
        else:
            self.EV_setDriver('GV21', self.code2ISY(code),25)
            self.EV_setDriver('GV3', None, 25)
        self.EV_setDriver('GV13', self.state2ISY(self.TEV.teslaEV_GetCarState(self.EVid)),25)

    def evPlaySound (self, command):
        logging.info('evPlaySound called')
        #self.TEV.teslaEV_Wake(self.EVid)
        sound = int(float(command.get('value')))
        if sound == 0 or sound == 2000: 
            code, res = self.TEV.teslaEV_PlaySound(self.EVid, sound)
            if code in ['ok']:
                self.EV_setDriver('GV21', self.command_res2ISY(res),25)
            else:
                self.EV_setDriver('GV21', self.code2ISY(code),25)
        self.EV_setDriver('GV13', self.state2ISY(self.TEV.teslaEV_GetCarState(self.EVid)),25)


    # needs update
    def evControlSunroof (self, command):
        logging.info('evControlSunroof called')
        #self.TEV.teslaEV_Wake(self.EVid)
        sunroofCtrl = int(float(command.get('value')))
        res = False
        if sunroofCtrl == 1:
            code, res = self.TEV.teslaEV_SunRoof(self.EVid, 'vent')
            #self.EV_setDriver()
        elif sunroofCtrl == 0:
            code, res = self.TEV.teslaEV_SunRoof(self.EVid, 'close')    
        elif sunroofCtrl == 2:
            code, res = self.TEV.teslaEV_SunRoof(self.EVid, 'stop')                  
        else:
            logging.error('Wrong command for evSunroof: {sunroofCtrl}')
            code = 'error'
        if code in ['ok']:
             self.EV_setDriver('GV21', self.command_res2ISY(res), 25)
        else:
            self.EV_setDriver('GV21', self.code2ISY(code), 25)
        self.EV_setDriver('GV13', self.state2ISY(self.TEV.teslaEV_GetCarState(self.EVid)), 25)


    def evOpenFrunk (self, command):
        logging.info('evOpenFrunk called')
        #self.TEV.teslaEV_Wake(self.EVid)     
        code, res = self.TEV.teslaEV_TrunkFrunk(self.EVid, 'Frunk')
        logging.debug('Frunk result {code} - {res}')
        if code in ['ok']:
            self.EV_setDriver('GV12', 1, 25)
            self.EV_setDriver('GV21', self.command_res2ISY(res), 25)
        else:
            logging.info('Not able to send command - EV is not online')
            self.EV_setDriver('GV21', self.code2ISY(code), 25)
            self.EV_setDriver('GV12', None, 25)
        self.EV_setDriver('GV13', self.state2ISY(self.TEV.teslaEV_GetCarState(self.EVid)), 25)


    def evOpenTrunk (self, command):
        logging.info('evOpenTrunk called')   
        code, res = self.TEV.teslaEV_TrunkFrunk(self.EVid, 'Trunk')
        logging.debug('Trunk result {code} - {res}')
        if code in ['ok']:
            self.EV_setDriver('GV11', 1, 25)
            self.EV_setDriver('GV21', self.command_res2ISY(res), 25)    
        else:
            logging.info('Not able to send command - EV is not online')
            self.EV_setDriver('GV21', self.code2ISY(code), 25)
            self.EV_setDriver('GV11', None, 25)
        self.EV_setDriver('GV13', self.state2ISY(self.TEV.teslaEV_GetCarState(self.EVid)), 25)


    def evHomelink (self, command):
        logging.info('evHomelink called')
        code, res = self.TEV.teslaEV_HomeLink(self.EVid)
        if code in ['ok']:
             self.EV_setDriver('GV21', self.command_res2ISY(res), 25)
        else:
            self.EV_setDriver('GV21', self.code2ISY(code), 25)
        self.EV_setDriver('GV13', self.state2ISY(self.TEV.teslaEV_GetCarState(self.EVid)), 25)

    '''
    def setDistUnit(self,command):
        logging.debug('setDistUnit')
        distUnit = int(float(command.get('value')))   
        self.TEV.teslaEV_SetDistUnit( distUnit )

        self.forceUpdateISYdrivers()
    '''   

    id = 'evstatus'
    commands = { 'UPDATE': ISYupdate, 
                 'WAKEUP' : evWakeUp,
                 'HONKHORN' : evHonkHorn,
                 'FLASHLIGHT' : evFlashLights,
                 'DOORS' : evControlDoors,
                 'SUNROOF' : evControlSunroof,
                 'TRUNK' : evOpenTrunk,
                 'FRUNK' : evOpenFrunk,
                 'HOMELINK' : evHomelink,
                 'PLAYSOUND' : evPlaySound,
                }


    drivers = [
            #{'driver': 'ST', 'value': 0, 'uom': 2},
            
            {'driver': 'GV1', 'value': 99, 'uom': 25},  #center_display_state
            {'driver': 'GV2', 'value': 99, 'uom': 25},  # Homelink Nearby
            {'driver': 'GV0', 'value': 99, 'uom': 25},  # nbr homelink devices
            {'driver': 'GV3', 'value': 99, 'uom': 25},  #locked
            {'driver': 'GV4', 'value': 0, 'uom': 116},  #odometer
            {'driver': 'GV5', 'value': 99, 'uom': 25},  #state (on line)
            {'driver': 'GV6', 'value': 99, 'uom': 25},  #fd_window
            {'driver': 'GV7', 'value': 99, 'uom': 25},  #fp_window
            {'driver': 'GV8', 'value': 99, 'uom': 25},  #rd_window
            {'driver': 'GV9', 'value': 99, 'uom': 25},  #rp_window
            #{'driver': 'GV10', 'value': 0, 'uom': 51}, #sun_roof_percent_open
            {'driver': 'GV11', 'value': 0, 'uom': 25}, #trunk
            {'driver': 'GV12', 'value': 0, 'uom': 25}, #frunk
            {'driver': 'GV13', 'value': 99, 'uom': 25}, #car State
            #{'driver': 'GV16', 'value': 99, 'uom': 25}, #longitude
            {'driver': 'GV17', 'value': 99, 'uom': 25}, #longitude
            {'driver': 'GV18', 'value': 99, 'uom': 25}, #latitude
            {'driver': 'GV19', 'value': 0, 'uom': 20},  #Last combined update Hours
            {'driver': 'GV20', 'value': 0, 'uom': 20},  #Last update hours
            {'driver': 'GV21', 'value': 99, 'uom': 25}, #Last Command status
            ]


