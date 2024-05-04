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
    from  udiLib import node_queue, wait_for_node_done, tempUnitAdjust,  setDriverTemp, cond2ISY,  mask2key, heartbeat, state2ISY, bool2ISY, online2ISY, EV_setDriver, openClose2ISY

    def __init__(self, polyglot, primary, address, name, id, TEV):
        super(teslaEV_StatusNode, self).__init__(polyglot, primary, address, name)
        logging.info('_init_ Tesla EV  Status Node')
        self.n_queue = []
        self.ISYforced = False
        self.EVid = id
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
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)

    def start(self):       
        logging.info('Start Tesla EV Status Node for {}'.format(self.EVid)) 
        tmpStr = re.findall('[0-9]+', self.address)
        self.nbrStr = tmpStr.pop()
        self.EV_setDriver('ST', 1)
        #self.forceUpdateISYdrivers()
        self.createSubNodes()
        self.updateISYdrivers()
        self.statusNodeReady = True
        
    def createSubNodes(self):
        logging.debug('Creating sub nodes for {}'.format(self.EVid))
        nodeAdr = 'climate'+self.nbrStr
        if not self.poly.getNode(nodeAdr):
            logging.info('Creating ClimateNode: {} - {} {} {} {}'.format(nodeAdr, self.address, nodeAdr,'EV climate Info',  self.EVid ))
            teslaEV_ClimateNode(self.poly, self.address, nodeAdr, 'EV climate Info', self.EVid, self.TEV )
            #self.poly.addNode(climateNode)             
            #self.wait_for_node_done()   
            #self.climateNodeReady =True
            #climateNode.updateISYdrivers()

        nodeAdr = 'charge'+self.nbrStr
        if not self.poly.getNode(nodeAdr):
            logging.info('Creating ChargingNode: {} - {} {} {} {}'.format(nodeAdr, self.address, nodeAdr,'EV Charging Info',  self.EVid ))
            teslaEV_ChargeNode(self.poly, self.address, nodeAdr, 'EV Charging Info', self.EVid, self.TEV )
            #self.poly.addNode(chargeNode)             
            #self.wait_for_node_done()   
            #self.chargeNodeReady = True
            #chargeNode.updateISYdrivers()

    def subnodesReady(self):
        return(self.climateNodeReady and self.chargeNodeReady )

    def stop(self):
        logging.debug('stop - Cleaning up')


    def ready(self):
        return(self.chargeNodeReady and self.climateNodeReady)

    def poll (self):    
        logging.info('Status Node Poll for {}'.format(self.EVid))        
        self.TEV.teslaEV_GetInfo(self.EVid)
        if self.statusNodeReady:
            if self.TEV.carState != 'Offline':
                self.updateISYdrivers()
            else:
                logging.info('Car appears off-line/sleeping - not updating data')

    #def forceUpdateISYdrivers(self):
    #    logging.debug('forceUpdateISYdrivers: {}'.format(self.EVid))
    #    time.sleep(1)
    #    self.TEV.teslaEV_UpdateCloudInfo(self.EVid)
    #    self.updateISYdrivers()


    def updateISYdrivers(self):
        try:
            
            logging.info('updateISYdrivers - Status for {}'.format(self.EVid))
            #if self.TEV.isConnectedToEV():
            #self.TEV.teslaEV_GetInfo(self.EVid)
            temp = {}
            logging.debug('StatusNode updateISYdrivers {}'.format(self.TEV.teslaEV_GetStatusInfo(self.EVid)))
            self.EV_setDriver('GV1', self.TEV.teslaEV_GetCenterDisplay(self.EVid))
            self.EV_setDriver('GV2', self.bool2ISY(self.TEV.teslaEV_HomeLinkNearby(self.EVid)))
            self.EV_setDriver('GV0', self.TEV.teslaEV_nbrHomeLink(self.EVid))
            self.EV_setDriver('GV3', self.bool2ISY(self.TEV.teslaEV_GetLockState(self.EVid)))
            if self.TEV.teslaEV_GetDistUnit() == 1:
                self.EV_setDriver('GV4', self.TEV.teslaEV_GetOdometer(self.EVid), 116)
            else:
                self.EV_setDriver('GV4', self.TEV.teslaEV_GetOdometer(self.EVid), 83)

            self.EV_setDriver('GV5', self.online2ISY(self.TEV.teslaEV_GetOnlineState(self.EVid)))
            temp = self.TEV.teslaEV_GetWindoStates(self.EVid)
            if  temp['FrontLeft'] == None:
                temp['FrontLeft'] = 99
            if temp['FrontRight'] == None:    
                temp['FrontRight'] = 99
            if temp['RearLeft'] == None:    
                temp['RearLeft'] = 99
            if temp['RearRight'] == None:    
                temp['RearRight'] = 99
            self.EV_setDriver('GV6', temp['FrontLeft'])
            self.EV_setDriver('GV7', temp['FrontRight'])
            self.EV_setDriver('GV8', temp['RearLeft'])
            self.EV_setDriver('GV9', temp['RearRight'])
            self.EV_setDriver('GV10', self.TEV.teslaEV_GetSunRoofPercent(self.EVid), 51)
            #elif self.TEV.teslaEV_GetSunRoofState(self.EVid) != None:
            #    logging.debug('GV10: {}'.format(self.TEV.teslaEV_GetSunRoofState(self.EVid)))
            #    self.EV_setDriver('GV10', self.openClose2ISY(self.TEV.teslaEV_GetSunRoofState(self.EVid)), True, True, 25)

            self.EV_setDriver('GV11', self.TEV.teslaEV_GetTrunkState(self.EVid))
            self.EV_setDriver('GV12', self.TEV.teslaEV_GetFrunkState(self.EVid))
            self.EV_setDriver('GV13', self.state2ISY(self.TEV.teslaEV_GetCarState(self.EVid)))
            '''
            ideal_bat = self.TEV.teslaEV_GetIdelBatteryRange(self.EVid)
            if ideal_bat:
                ideal_bat = round(ideal_bat, 2)
                logging.debug('GV16: {}'.format(ideal_bat))
                self.EV_setDriver('GV16', ideal_bat, True, True, 56)   
            else:
                logging.debug('GV16: {}'.format('NONE'))
                self.EV_setDriver('GV16', 99, True, True, 25)
            '''      
            
            location = self.TEV.teslaEV_GetLocation(self.EVid)
            if location['longitude']:
                logging.debug('GV17: {}'.format(round(location['longitude'], 3)))
                self.EV_setDriver('GV17', round(location['longitude'], 3), 56)
            else:
                logging.debug('GV17: {}'.format('NONE'))
                self.EV_setDriver('GV17', 99, 25)
            if location['latitude']:
                logging.debug('GV18: {}'.format(round(location['latitude'], 3)))
                self.EV_setDriver('GV18', round(location['latitude'], 3), 56)
            else:
                logging.debug('GV18: {}'.format('NONE'))
                self.EV_setDriver('GV18', 99, 25)

            self.EV_setDriver('GV19', round(float(self.TEV.teslaEV_GetTimeSinceLastCarUpdate(self.EVid)/60/60), 2), 20)            
            self.EV_setDriver('GV20', round(float(self.TEV.teslaEV_GetTimeSinceLastStatusUpdate(self.EVid)/60/60), 2), 20)
       
            #else:
            #    logging.info('System not ready yet')

        except Exception as e:
            logging.error('updateISYdriver Status node failed: {}'.format(e))

    def ISYupdate (self, command):
        logging.info('ISY-update called')
        self.TEV.teslaEV_UpdateCloudInfo(self.EVid)
        self.updateISYdrivers()

    def evWakeUp (self, command):
        logging.info('EVwakeUp called')
        self.TEV.teslaEV_Wake(self.EVid)

        self.forceUpdateISYdrivers()

    def evHonkHorn (self, command):
        logging.info('EVhonkHorn called')
        #self.TEV.teslaEV_Wake(self.EVid)
        self.TEV.teslaEV_HonkHorn(self.EVid)

        self.forceUpdateISYdrivers()

    def evFlashLights (self, command):
        logging.info('EVflashLights called')
        #self.TEV.teslaEV_Wake(self.EVid)
        self.TEV.teslaEV_FlashLights(self.EVid)

        self.forceUpdateISYdrivers()

    def evControlDoors (self, command):
        logging.info('EVctrlDoors called')
        #self.TEV.teslaEV_Wake(self.EVid)
        doorCtrl = int(float(command.get('value')))
        if doorCtrl == 1:
            self.TEV.teslaEV_Doors(self.EVid, 'unlock')
        elif doorCtrl == 0:
            self.TEV.teslaEV_Doors(self.EVid, 'lock')            
        else:
            logging.error('Unknown command for evControlDoors {}'.format(command))
        #self.EV_setDriver('GV3', self.bool2ISY(self.TEV.teslaEV_GetLockState(self.EVid)), True, True)
  
        self.forceUpdateISYdrivers()


    def evControlSunroof (self, command):
        logging.info('evControlSunroof called')
        #self.TEV.teslaEV_Wake(self.EVid)
        sunroofCtrl = int(float(command.get('value')))
        if sunroofCtrl == 1:
            self.TEV.teslaEV_SunRoof(self.EVid, 'vent')
        elif sunroofCtrl == 0:
            self.TEV.teslaEV_SunRoof(self.EVid, 'close')            
        else:
            logging.error('Wrong command for evSunroof: {}'.format(sunroofCtrl))         
        if self.TEV.teslaEV_GetSunRoofPercent(self.EVid) != None:
            logging.debug('GV10: {}'.format(self.TEV.teslaEV_GetSunRoofPercent(self.EVid)))
            self.EV_setDriver('GV10', self.TEV.teslaEV_GetSunRoofPercent(self.EVid), 51)
        elif self.TEV.teslaEV_GetSunRoofState(self.EVid) != None:
            logging.debug('GV10: {}'.format(self.TEV.teslaEV_GetSunRoofState(self.EVid)))
            self.EV_setDriver('GV10', self.openClose2ISY(self.TEV.teslaEV_GetSunRoofState(self.EVid)), 25)

        self.forceUpdateISYdrivers()

    def evOpenFrunk (self, command):
        logging.info('evOpenFrunk called')
        #self.TEV.teslaEV_Wake(self.EVid)                
        self.TEV.teslaEV_TrunkFrunk(self.EVid, 'Frunk')

        self.forceUpdateISYdrivers()
        #self.EV_setDriver('GV12', self.TEV.teslaEV_GetFrunkState(self.EVid), True, True)

    def evOpenTrunk (self, command):
        logging.info('evOpenTrunk called')   
        #self.TEV.teslaEV_Wake(self.EVid)             
        self.TEV.teslaEV_TrunkFrunk(self.EVid, 'Trunk')

        self.forceUpdateISYdrivers()
        #self.EV_setDriver('GV11', self.TEV.teslaEV_GetTrunkState(self.EVid), True, True)


    def evHomelink (self, command):
        logging.info('evHomelink called')
        #self.TEV.teslaEV_Wake(self.EVid)   
        self.TEV.teslaEV_HomeLink(self.EVid)

        self.forceUpdateISYdrivers()
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
                }


    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 2},
            
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
            {'driver': 'GV10', 'value': 0, 'uom': 51}, #sun_roof_percent_open
            {'driver': 'GV11', 'value': 0, 'uom': 25}, #trunk
            {'driver': 'GV12', 'value': 0, 'uom': 25}, #frunk
            {'driver': 'GV13', 'value': 99, 'uom': 25}, #car State
            #{'driver': 'GV16', 'value': 99, 'uom': 25}, #longitude
            {'driver': 'GV17', 'value': 99, 'uom': 25}, #longitude
            {'driver': 'GV18', 'value': 99, 'uom': 25}, #latitude   
            {'driver': 'GV19', 'value': 0, 'uom': 20},  #Last combined update Hours           
            {'driver': 'GV20', 'value': 0, 'uom': 20},  #Last update hours                        
            ]


