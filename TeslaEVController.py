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


from TeslaEVStatusNode import teslaEV_StatusNode
from TeslaCloudEVapi  import teslaCloudEVapi



class TeslaEVController(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name):
        super(TeslaEVController, self).__init__(polyglot, primary, address, name)
        logging.setLevel(10)
        self.poly = polyglot
        self.n_queue = []
        self.TEV = None
        logging.info('_init_ Tesla EV Controller ')
        self.ISYforced = False
        self.name = 'Tesla EV Info'
        self.primary = primary
        self.address = address
        #self.tokenPassword = ""
        self.Rtoken = None
        self.dUnit = 1 #  Miles = 1, Kilometer = 0
        self.tUnit = 0 #  C = 0, F=1, K=2
        self.supportedParams = ['REFRESH_TOKEN', 'DIST_UNIT', 'TEMP_UNIT']
        self.paramsProcessed = False
        self.Parameters = Custom(polyglot, 'customParams')      
        self.Notices = Custom(polyglot, 'notices')

        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.LOGLEVEL, self.handleLevelChange)
        self.poly.subscribe(self.poly.CUSTOMPARAMS, self.handleParams)
        self.poly.subscribe(self.poly.POLL, self.systemPoll)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.poly.subscribe(self.poly.CONFIGDONE, self.validate_params)



        #logging.debug('self.address : ' + str(self.address))
        #logging.debug('self.name :' + str(self.name))
        self.hb = 0

        self.connected = False
        self.nodeDefineDone = False
        self.statusNodeReady = False

        self.poly.updateProfile()
        self.poly.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.setDriver('ST', 1, True, True)

        self.tempUnit = 0 # C
        self.distUnit = 0 # KM

        #self.poly.setLogLevel('debug')
        logging.info('Controller init DONE')

    def node_queue(self, data):
        self.n_queue.append(data['address'])

    def wait_for_node_done(self):
        while len(self.n_queue) == 0:
            time.sleep(0.1)
        self.n_queue.pop()


    def start(self):
        logging.info('start')
        #self.Parameters.load(customParams)
        self.poly.updateProfile()
        #self.poly.setCustomParamsDoc()
        '''
        for param in self.supportedParams:
            if param not in self.Parameters:
                self.Parameters[param] = ''
        '''
        while not self.paramsProcessed:
            time.sleep(2)
        if len(self.Rtoken) > 1 : # token has a value
            self.tesla_start()

        # Wait for things to initialize....
        # Poll for current values (and update drivers)
        #self.TEV.pollSystemData('all')          
        #self.updateISYdrivers('all')
        #self.systemReady = True

    def validate_params(self):
        logging.debug('validate_params: {}'.format(self.Parameters.dump()))
        self.paramsProcessed = True


    def stop(self):
        self.Notices.clear()
        #if self.TEV:
        #    self.TEV.disconnectTEV()
        self.setDriver('ST', 0 , True, True)
        logging.debug('stop - Cleaning up')
        self.poly.stop()

    def query(self,command=None):
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
            logging.debug('token = {}'.format(self.Rtoken[0:25]))
            while self.Rtoken == '':
                logging.info('Waiting for token')
                time.sleep(10)
            self.TEV = teslaCloudEVapi(self.Rtoken)
            self.connected = self.TEV.isConnectedToEV()
            if not self.connected:
                logging.error ('Failed to get acces to Tesla Cloud')
                exit()
            else:
                self.setDriver('GV0', 1, True, True)
                self.TEV.teslaEV_SetDistUnit(self.dUnit)
                self.TEV.teslaEV_SetTempUnit(self.tUnit)

        except Exception as e:
            logging.debug('Exception Controller start: '+ str(e))
            logging.error('Did not connect to Tesla Cloud ')

        logging.debug ('Controller - initialization done')

    def createNodes(self):
        try:
            self.vehicleList = self.TEV.teslaEV_GetIdList()
            logging.debug('vehicleList: {}'.format(self.vehicleList))
            self.GV1 =len(self.vehicleList)
            self.setDriver('GV1', self.GV1, True, True)
            self.setDriver('GV0', 1, True, True)
            for vehicle in range(0,len(self.vehicleList)):
                nodeName = None
                vehicleId = self.vehicleList[vehicle]
                #logging.debug('vehicleId {}'.format(vehicleId))
                self.TEV.teslaEV_UpdateCloudInfo(vehicleId)
                #logging.debug('self.TEV.teslaEV_UpdateCloudInfo')
                vehicleInfo = self.TEV.teslaEV_GetInfo(vehicleId)
                logging.info('EV info: {} = {}'.format(vehicleId, vehicleInfo))

                if 'display_name' in vehicleInfo:
                    nodeName = vehicleInfo['display_name']                                          
                if 'vehicle_config' in vehicleInfo:
                    logging.debug( 'display_name = {}'.format(nodeName))
                    if  'vehicle_name' in vehicleInfo['vehicle_config']:
                        nodeName = vehicleInfo['vehicle_config']['vehicle_name']
                if 'vehicle_state' in vehicleInfo:
                    if  'vehicle_name' in vehicleInfo['vehicle_state']:
                        nodeName = vehicleInfo['vehicle_state']['vehicle_name']
                if nodeName == '' or nodeName == None:
                    nodeName = 'EV'+str(vehicle+1) 
                nodeAdr = 'vehicle'+str(vehicle+1)
                if not self.poly.getNode(nodeAdr):
                    logging.info('Creating Status node for {}'.format(nodeAdr))
                    statusNode = teslaEV_StatusNode(self.poly, nodeAdr, nodeAdr, nodeName, vehicleId, self.TEV)
                    self.poly.addNode(statusNode )             
                    self.wait_for_node_done()     
                    self.statusNodeReady = True
                    
            self.longPoll()
        except Exception as e:
            logging.error('Exception Controller start: '+ str(e))
            logging.info('Did not obtain data from EV ')




    def handleLevelChange(self, lev):
        logging.info('New log level: {}'.format(lev))
        #logging.setLevel(lev)


    def handleParams (self, customParams ):
        logging.debug('handleParams')
        tempDict1 = customParams
        self.Parameters.load(customParams)
        tempDict2 = customParams
        logging.debug('handleParams load - {} Before: {} After:{}'.format(customParams,tempDict1, tempDict2 ))
        #logging.debug(self.Parameters)  ### TEMP
        self.poly.Notices.clear()
        self.cloudAccess = False

        if 'REFRESH_TOKEN' in customParams:
            
            self.Rtoken = customParams['REFRESH_TOKEN']
            logging.debug('REFRESH_TOKEN : {}'.format(self.Rtoken[0:25]))
            if self.Rtoken  == '' or self.Rtoken == None:
                self.poly.Notices['REFRESH_TOKEN'] = 'Missing Cloud Refresh Token'

            else:
                if 'REFRESH_TOKEN' in self.poly.Notices:
                    self.poly.Notices.delete('REFRESH_TOKEN')                   
        else:
            self.poly.Notices['REFRESH_TOKEN'] = 'Missing Cloud Refresh Token'
            self.Rtoken  = ''
           
        if 'DIST_UNIT' in customParams:
            
            temp  = customParams['DIST_UNIT']
            logging.debug('DIST_UNIT: {}'.format(temp))
            if temp == '' or temp == None:
                self.poly.Notices['DIST_UNIT'] = 'Missing Distance Unit ((M)iles/(K)ilometers)'
            else:
                if temp[0] == 'k' or temp[0] == 'K':
                    self.dUnit = 0
                    if 'DIST_UNIT' in self.poly.Notices:
                        self.poly.Notices.delete('DIST_UNIT')

                elif temp[0] == 'm' or temp[0] == 'M':
                    self.dUnit = 1
                    if 'DIST_UNIT' in self.poly.Notices:
                        self.poly.Notices.delete('DIST_UNIT')

        if 'TEMP_UNIT' in customParams:
             
            temp  = customParams['TEMP_UNIT']
            logging.debug('TEMP_UNIT: {}'.format(temp))
            if temp == '' or temp == None:
                self.poly.Notices['TEMP_UNIT'] = 'Missing Distance Unit ((M)iles/(K)ilometers)'
            else:
                if temp[0] == 'C' or temp[0] == 'c':
                    self.tUnit = 0
                    if 'TEMP_UNIT' in self.poly.Notices:
                        self.poly.Notices.delete('TEMP_UNIT')

                elif temp[0] == 'F' or temp[0] == 'f':
                    self.tUnit = 1
                    if 'TEMP_UNIT' in self.poly.Notices:
                        self.poly.Notices.delete('TEMP_UNIT')
                elif temp[0] == 'K' or temp[0] == 'k':
                    self.tUnit = 2
                    if 'TEMP_UNIT' in self.poly.Notices:
                        self.poly.Notices.delete('TEMP_UNIT')
                

        logging.debug('done processing parameter')
        

    def heartbeat(self):
        logging.debug('heartbeat: ' + str(self.hb))
        if self.hb == 0:
            self.reportCmd('DON',2)
            self.hb = 1
        else:
            self.reportCmd('DOF',2)
            self.hb = 0
        
    def systemPoll(self, pollList):
        logging.debug('systemPoll')
        if self.TEV:
            if self.TEV.isConnectedToEV(): 
                if 'longPoll' in pollList:
                    self.longPoll()
                elif 'shortPoll' in pollList:
                    self.shortPoll()
            else:
                logging.info('Waiting for system/nodes to initialize')


    def shortPoll(self):
        logging.info('Tesla EV Controller shortPoll(HeartBeat)')
        self.heartbeat()    
        if self.TEV.isConnectedToEV():
            for vehicle in range(0,len(self.vehicleList)):                
                try:
                    self.TEV.teslaEV_getLatestCloudInfo(self.vehicleList[vehicle])
                    nodes = self.poly.getNodes()
                    for node in nodes:
                        #if node != 'controller'    
                        logging.debug('Controller poll  node {}'.format(node) )
                        nodes[node].poll()
                except Exception as E:
                    logging.info('Not all nodes ready: {}'.format(E))

            self.Rtoken  = self.TEV.getRtoken()
            if self.Rtoken  != self.Parameters['REFRESH_TOKEN']:
                self.Parameters['REFRESH_TOKEN'] = self.Rtoken 
        
    def longPoll(self):
        logging.info('Tesla EV  Controller longPoll - connected = {}'.format(self.TEV.isConnectedToEV()))
        
        if self.TEV.isConnectedToEV():
            for vehicle in range(0,len(self.vehicleList)):
                 self.TEV.teslaEV_UpdateCloudInfo(self.vehicleList[vehicle])
            try:
                nodes = self.poly.getNodes()
                for node in nodes:
                    #if node != 'controller'    
                    logging.debug('Controller poll  node {}'.format(node) )
                    nodes[node].poll()
            except Exception as E:
                logging.info('Not all nodes ready: {}'.format(E))

            self.Rtoken  = self.TEV.getRtoken()
            if self.Rtoken  != self.Parameters['REFRESH_TOKEN']:
                self.Parameters['REFRESH_TOKEN'] = self.Rtoken 


    def poll(self): # dummey poll function 
        self.updateISYdrivers()
        pass

    def updateISYdrivers(self):
        logging.debug('System updateISYdrivers - Controller')       
        value = self.TEV.isConnectedToEV()
        self.setDriver('GV0', value, True, True)
        self.setDriver('GV1', self.GV1, True, True)
        self.setDriver('GV2', self.dUnit, True, True)
        self.setDriver('GV3', self.tUnit, True, True)



    def ISYupdate (self, command):
        logging.debug('ISY-update called')

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
        polyglot.start('0.2.31')
        TeslaEVController(polyglot, 'controller', 'controller', 'Tesla EVs')


        polyglot.setCustomParamsDoc()
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
