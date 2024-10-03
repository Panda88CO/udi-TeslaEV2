#!/usr/bin/env python3

import sys
import time 


try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=20)

from TeslaEVOauth import teslaEVAccess
from TeslaEVStatusNode import teslaEV_StatusNode
#from TeslaCloudEVapi  import teslaCloudEVapi
from TeslaEVOauth import teslaAccess

VERSION = '0.1.15'
class TeslaEVController(udi_interface.Node):
    from  udiLib import node_queue, wait_for_node_done,tempUnitAdjust,  setDriverTemp, cond2ISY,  mask2key, heartbeat, state2ISY, bool2ISY, online2ISY, EV_setDriver, openClose2ISY

    def __init__(self, polyglot, primary, address, name, ev_cloud_access):
        super(TeslaEVController, self).__init__(polyglot, primary, address, name)
        logging.setLevel(10)
        self.poly = polyglot
        self.portalID = None
        self.portalSecret = None
        self.n_queue = []
        self.vehicleList = []
        self.TEVcloud = ev_cloud_access
        
        logging.info('_init_ Tesla EV Controller ')
        self.ISYforced = False
        self.name = 'Tesla EV Info'
        self.primary = primary
        self.address = address
        #self.tokenPassword = ""
        self.n_queue = []
        self.dUnit = 1 #  Miles = 1, Kilometer = 0
        self.tUnit = 0 #  C = 0, F=1,
        self.supportedParams = ['DIST_UNIT', 'TEMP_UNIT']
        self.paramsProcessed = False
        self.customParameters = Custom(self.poly, 'customparams')
        self.portalData = Custom(self.poly, 'customNSdata')
        self.Notices = Custom(polyglot, 'notices')

        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)

        #logging.debug('self.address : ' + str(self.address))
        #logging.debug('self.name :' + str(self.name))
        self.hb = 0
        self.connected = False
        self.nodeDefineDone = False
        self.statusNodeReady = False
        self.customNsDone = False
        self.portalReady = False
        self.poly.updateProfile()
        self.poly.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.status_nodes = {}
        self.node = self.poly.getNode(self.address)
        self.tempUnit = 0 # C
        self.distUnit = 0 # KM
        self.customParam_done = False
        self.config_done = False
        #self.poly.setLogLevel('debug')
        self.EV_setDriver('ST', 1)
        logging.info('Controller init DONE')

    def check_config(self):
        self.nodes_in_db = self.poly.getNodesFromDb()
        self.config_done= True


    def configDoneHandler(self):
        logging.debug('configDoneHandler - config_done')
        # We use this to discover devices, or ask to authenticate if user has not already done so
        self.poly.Notices.clear()
        self.nodes_in_db = self.poly.getNodesFromDb()
        self.config_done= True
        try:
            self.TEVcloud.getAccessToken()
        except ValueError as err:
            logging.warning('Access token is not yet available. Please authenticate.')
            self.poly.Notices['auth'] = 'Please initiate authentication'
        return

    def oauthHandler(self, token):
        # When user just authorized, pass this to your service, which will pass it to the OAuth handler
        self.TEVcloud.oauthHandler(token)
        # Then proceed with device discovery
        self.configDoneHandler()

    def handleLevelChange(self, level):
        logging.info('New log level: {}'.format(level))

    def handleNotices(self, level):
        logging.info('handleNotices:')


    def customNSHandler(self, key, data):        
        self.portalData.load(data)
        logging.debug('customNSHandler : key:{}  data:{}, '.format(key, data))
        if key == 'nsdata':
            if 'portalID' in data:
                self.portalID = data['portalID']
                #self.customNsDone = True
            if 'PortalSecret' in data:
                self.portalSecret = data['PortalSecret']
                #self.customNsDone = True
            if self.TEVcloud.initializePortal(self.portalID, self.portalSecret):
                self.portalReady = True
            logging.debug('Custom Data portal: {} {}'.format(self.portalID , self.portalSecret ))
        self.TEVcloud.customNsHandler(key, data)
        
        

    def customParamsHandler(self, userParams):
        self.customParameters.load(userParams)
        logging.debug('customParamsHandler called {}'.format(userParams))

        oauthSettingsUpdate = {}
        #oauthSettingsUpdate['parameters'] = {}
        oauthSettingsUpdate['token_parameters'] = {}
        # Example for a boolean field

        if 'REGION' in userParams:
            if self.customParameters['REGION'] != 'Input region NA, EU, CN':
                self.region = str(self.customParameters['REGION'])
                if self.region.upper() not in ['NA', 'EU', 'CN']:
                    logging.error('Unsupported region {}'.format(self.region))
                    self.poly.Notices['REGION'] = 'Unknown Region specified (NA = North America + Asia (-China), EU = Europe. middle East, Africa, CN = China)'
                else:
                    self.TEVcloud.cloud_set_region(self.region)
        else:
            logging.warning('No region found')
            self.customParameters['REGION'] = 'Input region NA, EU, CN'
            self.region = None
            self.poly.Notices['region'] = 'Region not specified (NA = Nort America + Asia (-China), EU = Europe. middle East, Africa, CN = China)'
   
        if 'DIST_UNIT' in userParams:
            if self.customParameters['DIST_UNIT'] != 'Km or Miless':
                self.dist_unit = str(self.customParameters['DIST_UNIT'])

                if self.dist_unit.upper() not in ['KM', 'MILES']:
                    logging.error('Unsupported distance unit {}'.format(self.dist_unit))
                    self.poly.Notices['dist'] = 'Unknown distance Unit specified'
                else:
                    if self.dist_unit.upper() == 'KM':
                        self.TEVcloud.teslaEV_SetDistUnit(0)
                    else:
                        self.TEVcloud.teslaEV_SetDistUnit(1)
        else:
            logging.warning('No DIST_UNIT')
            self.customParameters['DIST_UNIT'] = 'Km or Miles'

        if 'TEMP_UNIT' in userParams:
            if self.customParameters['TEMP_UNIT'] != 'C or F':
                self.temp_unit = str(self.customParameters['TEMP_UNIT'])
                if self.temp_unit.upper() not in ['C', 'F']:
                    logging.error('Unsupported temperatue unit {}'.format(self.temp_unit))
                    self.poly.Notices['temp'] = 'Unknown distance Unit specified'
                else:
                    if self.temp_unit.upper() == 'C':
                        self.TEVcloud.teslaEV_SetTempUnit(0)
                    else:
                        self.TEVcloud.teslaEV_SetTempUnit(1)
        else:
            logging.warning('No TEMP_UNIT')
            self.customParameters['TEMP_UNIT'] = 'C or F'    
        logging.debug('customParamsHandler finish ')



        
        if 'LOCATION_EN' in userParams:
            if self.customParameters['LOCATION_EN'] != 'True or False':
                self.locationEn = str(self.customParameters['LOCATION_EN'])
                if self.locationEn.upper() not in ['TRUE', 'FALSE']:
                    logging.error('Unsupported Location Setting {}'.format(self.locationEn))
                    self.poly.Notices['location'] = 'Unknown distance Unit specified'
                else:
                    self.TEVcloud.teslaEV_set_location_enabled(self.locationEn)
                    
        else:
            logging.warning('No LOCATION')
            self.customParameters['LOCATION_EN'] = 'True or False'   
        self.customParam_done = True


    def start(self):
        logging.info('start')
        #self.Parameters.load(customParams)
        self.poly.updateProfile()
        #self.poly.setCustomParamsDoc()

        #while not self.customParam_done or not self.customNsDone and not self.config_done:
        while not self.config_done and not self.portalReady:
            logging.info('Waiting for node to initialize')
            logging.debug(' 1 2 3: {} {} {}'.format(self.customParam_done ,self.TEVcloud.customNsDone(), self.config_done))
            time.sleep(1)

        logging.debug('Portal Credentials: {} {}'.format(self.portalID, self.portalSecret))
        #self.TEVcloud.initializePortal(self.portalID, self.portalSecret)
        while not self.TEVcloud.portal_ready():
            time.sleep(5)
            logging.debug('Waiting for portal connection')
        while not self.TEVcloud.authenticated():
            logging.info('Waiting to authenticate to complete - press authenticate button')
            self.poly.Notices['auth'] = 'Please initiate authentication'
            time.sleep(5)


        self.tesla_initialize()
        code, self.EVs = self.TEVcloud.teslaEV_get_vehicles()
        #self.EVs_installed = {}
        logging.debug('EVs : {}'.format(self.EVs))
        assigned_addresses =['controller']
        self.vehicleList = self.TEVcloud.teslaEV_get_vehicle_list()

        logging.debug('vehicleList: {}'.format(self.vehicleList))
        self.GV1 = len(self.vehicleList)
        self.EV_setDriver('GV1', self.GV1)
        self.EV_setDriver('GV0', 1)
        for indx, EvId in enumerate(self.TEVcloud.teslaEV_get_vehicle_list()):
        #for indx in range(0,len(self.vehicleList)):
            #EvId = self.vehicleList[indx]
            #vehicleId = vehicle['vehicle_id']
            logging.debug('loop: {} {}'.format(indx, EvId ))
            nodeName = None
            #vehicleId = self.vehicleList[vehicle]
            #logging.debug('vehicleId {}'.format(vehicleId))
            code, info = self.TEVcloud.teslaEV_UpdateCloudInfo(EvId)
            logging.debug('self.TEVcloud.teslaEV_UpdateCloudInfo {} {}'.format(code, info))
            if code in ['ok']:
                #if self.TEVcloud.teslaEV_GetCarState(EvId) == 'online':
                vehicleInfo = self.TEVcloud.teslaEV_GetInfo(EvId)
                logging.info('EV info: {} = {}'.format(EvId, vehicleInfo))
                nodeName = self.TEVcloud.teslaEV_GetName(EvId)
            else:
                nodeName = self.EVs[EvId]['display_name']

            if nodeName == ''  or nodeName == None:
                nodeName = 'ev'+str(EvId)
            nodeAdr = 'ev'+str(EvId)[-14:]
            nodeName = self.poly.getValidName(nodeName)
            nodeAdr = self.poly.getValidAddress(nodeAdr)

            if not self.poly.getNode(nodeAdr):
                logging.debug('Node Address : {} {}'.format(self.poly.getNode(nodeAdr),nodeAdr ))
            logging.info('Creating Status node {} for {}'.format(nodeAdr, nodeName))
            #self.TEVcloud.teslaEV_UpdateCloudInfo(EvId)
            self.status_nodes[EvId] = teslaEV_StatusNode(self.poly, nodeAdr, nodeAdr, nodeName, EvId, self.TEVcloud)        
            assigned_addresses.append(nodeAdr)
            while not (self.status_nodes[EvId].subnodesReady() or self.status_nodes[EvId].statusNodeReady):
                logging.debug('Subnodes {}  Status {}'.format(self.status_nodes[EvId].subnodesReady(), self.status_nodes[EvId].statusNodeReady ))
                logging.debug('waiting for nodes to be created')
                time.sleep(5)
            

                #self.wait_for_node_done()     
                #self.statusNodeReady = True
        
        logging.debug('Scanning db for extra nodes : {}'.format(assigned_addresses))
        for nde in range(0, len(self.nodes_in_db)):
            node = self.nodes_in_db[nde]
            logging.debug('Scanning db for node : {}'.format(node))
            if node['primaryNode'] not in assigned_addresses:
                logging.debug('Removing node : {} {}'.format(node['name'], node))
                self.poly.delNode(node['address'])
        
        self.updateISYdrivers()
        self.initialized = True


    def validate_params(self):
        logging.debug('validate_params: {}'.format(self.Parameters.dump()))
        self.paramsProcessed = True


    def stop(self):
        self.Notices.clear()
        #if self.TEV:
        #    self.TEV.disconnectTEV()
        self.EV_setDriver('ST', 0 )
        logging.debug('stop - Cleaning up')
        self.poly.stop()

    def query(self, command=None):
        """
        Optional.

        The query method will be called when the ISY attempts to query the
        status of the node directly.  You can do one of two things here.
        You can send the values currently held by Polyglot back to the
        ISY by calling reportDriver() or you can actually query the 
        device represented by the node and report back the current 
        status.
        """
        nodes = self.poly.getNodes()
        for node in nodes:
            nodes[node].reportDrivers()

    '''
    This may be called multiple times with different settings as the user
    could be enabling or disabling the various types of access.  So if the
    user changes something, we want to re-initialize.
    '''


    def tesla_start(self):
        self.tesla_initialize()
        self.createNodes()

    def tesla_initialize(self):
        logging.info('starting Login process')
        try:
            self.EV_setDriver('GV0', 1)
            #self.TEV.teslaEV_SetDistUnit(self.dUnit)
            #self.TEV.teslaEV_SetTempUnit(self.tUnit)
            #self.TEV.teslaEV_SetRegion(self.region)


        except Exception as e:
            logging.debug('Exception Controller start: '+ str(e))
            logging.error('Did not connect to Tesla Cloud ')

        logging.debug ('Controller - initialization done')

    def portal_initialize(self, portalId, portalSecret):
        logging.debug('portal_initialize {} {}'.format(portalId, portalSecret))
        #portalId = None
        #portalSecret = None
        self.TEVcloud.initializePortal(portalId, portalSecret)

    def systemPoll(self, pollList):
        logging.debug('systemPoll - {}'.format(pollList))
        if self.TEVcloud:
            if self.TEVcloud.authenticated():
                #self.TEVcloud.teslaEV_get_vehicles()
                if 'longPoll' in pollList: 
                    self.longPoll()
                    if 'shortPoll' in pollList: #send short polls heart beat as shortpoll is not executed
                        self.heartbeat()
                elif 'shortPoll' in pollList:
                    self.shortPoll()
            else:
                logging.info('Waiting for system/nodes to initialize')

# Something is not correct here - too many times through
    def shortPoll(self):
        logging.info('Tesla EV Controller shortPoll(HeartBeat)')
        self.heartbeat()
        try:
            temp_list = self.TEVcloud.teslaEV_get_vehicle_list()
            logging.debug('long poll list {}'.format(temp_list))
            for indx, vehicleID in enumerate(temp_list):
                logging.debug('short pool loop {} {}'.format(indx, vehicleID))
                code, data =  self.TEVcloud.teslaEV_update_connection_status(vehicleID)
                if self.TEVcloud.teslaEV_GetCarState(vehicleID) == 'online':
                    code, data  = self.TEVcloud.teslaEV_UpdateCloudInfoAwake(vehicleID)
                logging.debug('Main Long Poll status {} - {}'.format(code, data))
                self.status_nodes[vehicleID].poll(code)

        except Exception as E:
            logging.info('Not all nodes ready: {}'.format(E))

#            self.Rtoken  = self.TEVcloud.getRtoken()
#            if self.Rtoken  != self.Parameters['REFRESH_TOKEN']:
#                self.Parameters['REFRESH_TOKEN'] = self.Rtoken 
        
    def longPoll(self):
        logging.info('Tesla EV  Controller longPoll - connected = {}'.format(self.TEVcloud.authenticated()))        

        try:
            #logging.debug('self.vehicleList {}'.format(self.TEVcloud.teslaEV_get_vehicle_list()))
            temp_list = self.TEVcloud.teslaEV_get_vehicle_list()
            logging.debug('long poll list {}'.format(temp_list))
            for indx, vehicleID in enumerate (temp_list):
                logging.debug('long poll loop {} {} {}'.format(indx, vehicleID, temp_list))
                code, data =  self.TEVcloud.teslaEV_UpdateCloudInfo(vehicleID)
                logging.debug('Main Long Poll status {} - {}'.format(code, data))
                self.status_nodes[vehicleID].poll(code)

        except Exception as E:
            logging.info('Not all nodes ready: {}'.format(E))

#            self.Rtoken  = self.TEVcloud.getRtoken()
#            if self.Rtoken  != self.Parameters['REFRESH_TOKEN']:
#                self.Parameters['REFRESH_TOKEN'] = self.Rtoken


    def poll(self, status_code): # dummey poll function
        if status_code == 'ok':
            self.updateISYdrivers()
        else:

            pass

    def updateISYdrivers(self):
        logging.debug('System updateISYdrivers - Controller')       
        value = self.TEVcloud.authenticated()
        self.EV_setDriver('GV0', value)
        self.EV_setDriver('GV1', self.GV1)
        self.EV_setDriver('GV2', self.dUnit)
        self.EV_setDriver('GV3', self.tUnit)



    def ISYupdate (self, command):
        logging.debug('ISY-update main node called')
        if self.TEVcloud.authenticated():
            self.longPoll()

 
    id = 'controller'
    commands = { 'UPDATE': ISYupdate ,
                
                }

    drivers = [
            {'driver': 'ST', 'value':0, 'uom':2},
            {'driver': 'GV0', 'value':0, 'uom':25},  
            {'driver': 'GV1', 'value':0, 'uom':107},
            {'driver': 'GV2', 'value':0, 'uom':25},  
            {'driver': 'GV3', 'value':0, 'uom':25},     
                  
            ]
            # ST - node started
            # GV0 Access to TeslaApi
            # GV1 Number of EVs



if __name__ == "__main__":
    try:
        logging.info('Starting TeslaEV Controller')
        polyglot = udi_interface.Interface([])

        #TeslaEVController(polyglot, 'controller', 'controller', 'Tesla EVs')
        polyglot.start(VERSION)
        #polyglot.updateProfile()
        polyglot.setCustomParamsDoc()

        TEV_cloud = teslaEVAccess(polyglot, 'energy_device_data energy_cmds vehicle_device_data vehicle_cmds vehicle_charging_cmds open_id offline_access')
        #TEV_cloud = teslaEVAccess(polyglot, 'energy_device_data energy_cmds open_id offline_access')
        #TEV_cloud = teslaEVAccess(polyglot, 'open_id vehicle_device_data vehicle_cmds  vehicle_charging_cmds offline_access')
        logging.debug('TEV_Cloud {}'.format(TEV_cloud))
        TEV =TeslaEVController(polyglot, 'controller', 'controller', 'Tesla EVs', TEV_cloud)

        
        logging.debug('before subscribe')
        polyglot.subscribe(polyglot.STOP, TEV.stop)
        polyglot.subscribe(polyglot.CUSTOMPARAMS, TEV.customParamsHandler)
        polyglot.subscribe(polyglot.CONFIGDONE, TEV.configDoneHandler)
        #polyglot.subscribe(polyglot.ADDNODEDONE, TEV.node_queue)        
        polyglot.subscribe(polyglot.LOGLEVEL, TEV.handleLevelChange)
        polyglot.subscribe(polyglot.NOTICES, TEV.handleNotices)
        polyglot.subscribe(polyglot.POLL, TEV.systemPoll)
        polyglot.subscribe(polyglot.START, TEV.start, 'controller')
        logging.debug('Calling start')
        polyglot.subscribe(polyglot.CUSTOMNS, TEV.customNSHandler)
        polyglot.subscribe(polyglot.OAUTH, TEV.oauthHandler)
        logging.debug('after subscribe')
        polyglot.ready()
        polyglot.runForever()

        polyglot.setCustomParamsDoc()
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
