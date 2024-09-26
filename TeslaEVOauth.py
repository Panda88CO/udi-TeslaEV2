
#!/usr/bin/env python3

### Your external service class
'''
Your external service class can be named anything you want, and the recommended location would be the lib folder.
It would look like this:

External service sample code
Copyright (C) 2023 Universal Devices

MIT License
'''
import json
import requests
import time
from datetime import timedelta, datetime
from TeslaOauth import teslaAccess
#from udi_interface import logging, Custom
#from oauth import OAuth
try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
    ISY = udi_interface.ISY
except ImportError:
    import logging
    logging.basicConfig(level=30)


#from udi_interface import LOGGER, Custom, OAuth, ISY
#logging = udi_interface.LOGGER
#Custom = udi_interface.Custom
#ISY = udi_interface.ISY



# Implements the API calls to your external service
# It inherits the OAuth class
class teslaEVAccess(teslaAccess):
    yourApiEndpoint = 'https://fleet-api.prd.na.vn.cloud.tesla.com'

    def __init__(self, polyglot, scope):
        super().__init__(polyglot, scope)
        logging.info('OAuth initializing')
        self.poly = polyglot
        self.scope = scope
        self.customParameters = Custom(self.poly, 'customparams')
        #self.scope_str = None
        self.EndpointNA= 'https://fleet-api.prd.na.vn.cloud.tesla.com'
        self.EndpointEU= 'https://fleet-api.prd.eu.vn.cloud.tesla.com'
        self.EndpointCN= 'https://fleet-api.prd.cn.vn.cloud.tesla.cn'
        self.api  = '/api/1'

        #self.state = secrets.token_hex(16)
        self.region = 'NA'
        self.handleCustomParamsDone = False
        #self.customerDataHandlerDone = False
        self.customNsHandlerDone = False
        self.customOauthHandlerDone = False
        self.temp_unit = 0
        self.dist_unit = 1

        self.carInfo = {}
        self.carStateList = ['online', 'Offline', 'aleep', 'unknown', 'error']
        self.carState = 'Unknown'

        self.locationEn = False
        self.canActuateTrunks = False
        self.sunroofInstalled = False
        self.readSeatHeat = False
        self.steeringWheeelHeat = False
        self.steeringWheelHeatDetected = False
        self.evs = {}
        self.ev_list = []
        self.poly = polyglot
        temp = time.time() - 1 # Assume calls can be made
        self.next_wake_call = temp
        self.next_command_call = temp
        self.next_chaging_call = temp
        self.next_device_data_call = temp


        time.sleep(1)

        #while not self.handleCustomParamsDone:
        #    logging.debug('Waiting for customParams to complete - getAccessToken')
        #    time.sleep(0.2)
        # self.getAccessToken()
    
    # The OAuth class needs to be hooked to these 3 handlers
    #def customDataHandler(self, data):
    #    logging.debug('customDataHandler called')
        #while not self.handleCustomParamsDone:
        #    logging.debug('Waiting for customDataHandler to complete')
        #    time.sleep(1)
    #    super().customDataHandler(data)
    #    self.customDataHandlerDone = True
    #    logging.debug('customDataHandler Finished')

    ##def customNsHandler(self, key, data):
    ##    logging.debug('customNsHandler called')
    #    #while not self.customParamsDone():
    #    #    logging.debug('Waiting for customNsHandler to complete')
    #    #    time.sleep(1)
    #    #self.updateOauthConfig()
    #    super().customNsHandler(key, data)
    #    self.customNsHandlerDone = True
    #    logging.debug('customNsHandler Finished')

    #def oauthHandler(self, token):
    #    logging.debug('oauthHandler called')
    #    while not (self.customParamsDone() and self.customNsDone()):
    #        logging.debug('Waiting for initilization to complete before oAuth')
    #        time.sleep(5)
    #    #logging.debug('oauth Parameters: {}'.format(self.getOauthSettings()))
    #    super().oauthHandler(token)
        #self.customOauthHandlerDone = True
    #    logging.debug('oauthHandler Finished')

    def customNsDone(self):
        return(self.customNsHandlerDone)
    
    def customDateDone(self):
        return(self.customDataHandlerDone )

    def customParamsDone(self):
        return(self.handleCustomParamsDone)

    #def customOauthDone(self):
    #    return(self.customOauthHandlerDone )
    # Your service may need to access custom params as well...



    def location_enabled(self):
        return(self.locationEn)
    
    def teslaEV_set_location_enabled(self, state):
        self.locationEn = ( state.upper() == 'TRUE')

    
    def main_module_enabled(self, node_name):
        logging.debug('main_module_enabled called {}'.format(node_name))
        if node_name in self.customParameters :           
            return(int(self.customParameters[node_name]) == 1)
        else:
            self.customParameters[node_name] = 1 #add and enable by default
            self.poly.Notices['home_id'] = 'Check config to select which home/modules should be used (1 - used, 0 - not used) - then restart'
            return(True)

    '''         
    def customParamsHandler(self, userParams):
        self.customParameters.load(userParams)
        logging.debug('customParamsHandler called {}'.format(userParams))

        oauthSettingsUpdate = {}
        #oauthSettingsUpdate['parameters'] = {}
        oauthSettingsUpdate['token_parameters'] = {}
        # Example for a boolean field

        if 'region' in userParams:
            if self.customParameters['region'] != 'enter region (NA, EU, CN)':
                self.region = str(self.customParameters['region'])
                if self.region.upper() not in ['NA', 'EU', 'CN']:
                    logging.error('Unsupported region {}'.format(self.region))
                    self.poly.Notices['region'] = 'Unknown Region specified (NA = North America + Asia (-China), EU = Europe. middle East, Africa, CN = China)'
                #else:

        else:
            logging.warning('No region found')
            self.customParameters['region'] = 'enter region (NA, EU, CN)'
            self.region = None
            self.poly.Notices['region'] = 'Region not specified (NA = Nort America + Asia (-China), EU = Europe. middle East, Africa, CN = China)'
   
        if 'DIST_UNIT' in userParams:
            if self.customParameters['DIST_UNIT'] != 'enter Km or Miles':
                self.dist_unit = str(self.customParameters['DIST_UNIT'])
                if self.region.upper() not in ['KM', 'MILES']:
                    logging.error('Unsupported distance unit {}'.format(self.dist_unit))
                    self.poly.Notices['dist'] = 'Unknown distance Unit specified'
                #else:

        else:
            logging.warning('No DIST_UNIT')
            self.customParameters['DIST_UNIT'] = 'Km or Miles'

        if 'TEMP_UNIT' in userParams:
            if self.customParameters['TEMP_UNIT'] != 'enter C or F':
                self.temp_unit = str(self.customParameters['TEMP_UNIT'])
                if self.region.upper() not in ['C', 'F']:
                    logging.error('Unsupported temperatue unit {}'.format(self.temp_unit))
                    self.poly.Notices['temp'] = 'Unknown distance Unit specified'
                #else:

        else:
            logging.warning('No DIST_UNIT')
            self.customParameters['DIST_UNIT'] = 'Km or Miles'       

        if 'LOCATION_EN' in userParams:
            if self.customParameters['LOCATION'] != 'True or False':
                self.locationEn = str(self.customParameters['LOCATION'])
                if self.locationEn.upper() not in ['TRUE', 'FALSE']:
                    logging.error('Unsupported Location Setting {}'.format(self.locationEn))
                    self.poly.Notices['location'] = 'Unknown distance Unit specified'
                #else:

        else:
            logging.warning('No LOCATION')
            self.customParameters['LOCATION'] = 'True or False'   

        logging.debug('region {}'.format(self.region))
        oauthSettingsUpdate['scope'] = self.scope 
        oauthSettingsUpdate['auth_endpoint'] = 'https://auth.tesla.com/oauth2/v3/authorize'
        oauthSettingsUpdate['token_endpoint'] = 'https://auth.tesla.com/oauth2/v3/token'
        #oauthSettingsUpdate['redirect_uri'] = 'https://my.isy.io/api/cloudlink/redirect'
        #oauthSettingsUpdate['cloudlink'] = True
        oauthSettingsUpdate['addRedirect'] = True
        #oauthSettingsUpdate['state'] = self.state
        if self.region.upper() == 'NA':
            self.Endpoint = self.EndpointNA
        elif self.region.upper() == 'EU':
            self.Endpoint = self.EndpointEU
        elif self.region.upper() == 'CN':
            self.Endpoint = self.EndpointCN
        else:
            logging.error('Unknow region specified {}'.format(self.region))
            return
           
        self.yourApiEndpoint = self.Endpoint+self.api 
        oauthSettingsUpdate['token_parameters']['audience'] = self.Endpoint
        #oauthSettingsUpdate['token_parameters']['client_id'] = '6e635ec38dc4-4d2a-a35e-f164b51f3d96'
        #oauthSettingsUpdate['token_parameters']['client_secret'] = 'ta-secret.S@z5uUjp*sxoS2rS'
        #oauthSettingsUpdate['token_parameters']['addRedirect'] = True
        self.updateOauthSettings(oauthSettingsUpdate)
        time.sleep(0.1)
        temp = self.getOauthSettings()
        #logging.debug('Updated oAuth config 2: {}'.format(temp))
        
        self.handleCustomParamsDone = True
        self.poly.Notices.clear()
        '''

    def add_to_parameters(self,  key, value):
        '''add_to_parameters'''
        self.customParameters[key] = value

    def check_parameters(self, key, value):
        '''check_parameters'''
        if key in self.customParameters:
            return(self.customParameters[key]  == value)
        else:
            return(False)
    ###  Register car pem


       
    '''
    def tesla_get_products(self) -> dict:
        self.products= {}
        EVs = {}
        logging.debug('tesla_get_products ')
        try:
            code, temp = self._callApi('GET','/products' )
            #code, temp = self._callApi('GET','/vehicles' )
            logging.debug('products: {} '.format(temp))
            if 'response' in temp:
                #for indx in range(0,len(temp['response'])):
                #    site = temp['response'][indx]
                for indx, site in enumerate(temp['response']):
                    if 'vehicle_id' in site:
                        EVs[str(site['id'])] = site
                        #self.ev_list.append(site['id'])
                        self.ev_list.append(site['vin']) # vin needed to send commands

            self.evs = EVs
            self.products = temp
            return(EVs)
        except Exception as e:
            logging.error('tesla_get_products Exception : {}'.format(e))
    '''


    def extract_needed_delay(self, input_string):
        temp =  [int(word) for word in input_string.split() if word.isdigit()]
        if temp != []:
            return(temp[0])
        else:
            return(0)
        

    def teslaEV_get_vehicles(self) -> dict:
        self.products= {}
        EVs = {}
        logging.debug('teslaEV_get_vehicles ')
        try:
    
            code, temp = self._callApi('GET','/vehicles' )
            logging.debug('vehicles: {} '.format(temp))
            if code == 'ok':
                for indx, site in enumerate(temp['response']):
                    if 'vin' in site:
                        EVs[str(site['vin'])] = site
                        #self.ev_list.append(site['id'])
                        self.ev_list.append(site['vin']) # vin needed to send commands
                        self.carInfo[site['vin']] = site
            self.evs = EVs
            self.products = temp
            return(code, EVs)
        except Exception as e:
            logging.error('teslaEV_get_vehicles Exception : {}'.format(e))
    
   
    def teslaEV_wake_ev(self, EVid):
        logging.debug('wake_ev - {}'.format(EVid))
        trys = 1
        timeNow = time.time()
        try:
            code, state = self.teslaEV_GetConnectionStatus(EVid)
            if code == 'ok':
                if timeNow >= self.next_wake_call:
                    if state in ['asleep']:     
                        code, res  = self._callApi('POST','/vehicles/'+str(EVid) +'/wake_up')
                        logging.debug('wakeup: {} - {}'.format(code, res))
                        if code == 'ok':
                            time.sleep(5)
                            code, state = self.teslaEV_UpdateConnectionStatus(EVid)
                            while code == 'ok' and state != 'online' and trys < 5:
                                trys += 1
                                time.sleep(5)
                                code, state = self.teslaEV_UpdateConnectionStatus(EVid)
                        if code == 'overload':
                            delay = self.extract_needed_delay(res)
                            self.next_wake_call = timeNow + int(delay)
                    return(code, state)
                else:          
                    logging.warning('Too many calls to wake API - need to wait {} secods'.format(delay))
                    return(code, state)
        except Exception as e:
            logging.error('teslaEV_get_vehicles Exception : {}'.format(e))


    def teslaEV_get_ev_data(self, EVid):
        logging.debug('get_ev_data - state {}:'.format(EVid))
        if self.locationEn:
            payload = {'endpoints':'charge_state;climate_state;drive_state;location_data;vehicle_config;vehicle_state'}
        else:
            payload = {'endpoints':'charge_state;climate_state;drive_state;vehicle_config;vehicle_state'}
        code, res = self._callApi('GET','/vehicles/'+str(EVid) +'/vehicle_data', payload  )
        logging.debug('vehicel data: {} {}'.format(code, res))
        return(code, res)

    def teslaEV_send_ev_command(self, command, params, EVid ):
        logging.debug('send_ev_command - command  {} - params: {} - {}'.format(command, params, EVid))

    def teslaEV_GetIdList(self ):
        logging.debug('teslaEV_GetVehicleIdList:')
        return(self.ev_list)


    def get_delay(self, string):
        numbers = [int(word) for word in string.split() if word.isdigit()]
        if numbers != []:
            return(numbers[0]) 

    def teslaEV_UpdateCloudInfo(self, EVid):
        logging.debug('teslaEV_UpdateCloudInfo: {}'.format(EVid))
        code = 'unknown'
        try:
            code, state  = self.teslaEV_wake_ev(EVid)                
            if code == 'ok':
                logging.debug('Wake_up result : {}'.format(state))
                if state in ['online']:
                    code, res = self.teslaEV_get_ev_data(EVid)
                    if code == 'ok':
                        self.carInfo[EVid] = self.process_EV_data(res)
                return(code, res)
            elif code == 'overload':
                delay = self.next_wake_call - time.time()
                return(code, delay)
            else:
                return(code, state)
            

        except Exception as e:
            logging.debug('Exception teslaEV_UpdateCloudInfo: {} '.format(e))
            return('error')

    def teslaEV_UpdateCloudInfoAwake(self, EVid, online_known = False):
            logging.debug('teslaEV_UpdateCloudInfoAwake: {}'.format(EVid))
            try:
                code, state = self.teslaEV_UpdateConnectionStatus(EVid)
                if code == 'ok' and state in ['online']:
                    code, res = self.teslaEV_get_ev_data(EVid)
                    if code == 'ok':
                        self.carInfo[EVid] = self.process_EV_data(res)
                    return(code, res)
                elif code == 'overload':
                    delay = self.next_wake_call - time.time()
                    return(code, delay)
                else:
                    return(code, state)
            except Exception as e:
                logging.debug('Exception teslaEV_UpdateCloudInfo: {} '.format(e))
                return('error')
   
    
    def process_EV_data(self, carData):
        logging.debug('process_EV_data')
        if 'response' in carData:
            if 'version' in carData['response']:
                if carData['response']['version'] == 9: # latest release
                    temp = carData['response']['data']
            else:
                temp = carData['response']
        else:
            temp = 'Error'
        logging.debug('process_EV_data: {}'.format(temp))
        return(temp)
            

    #def teslaEV_GetCarState(self, EVid):
    #    logging.debug('teslaEV_GetCarState: {}'.format(self.carState))
    #    return(self.carState)

    def teslaEV_GetCarState(self, EVid):
        try:
            logging.debug('teslaEV_GetCarState: {}'.format(self.carInfo[EVid]['state']))

            return(self.carInfo[EVid]['state'])
        except Exception as e:
            logging.error('teslaEV_GetCarState Exception : {}'.format(e))
            return(None)


    def teslaEV_GetConnectionStatus(self, EVid):
        #logging.debug('teslaEV_GetConnectionStatus: for {}'.format(EVid))
        return(self.carInfo[EVid]['state'])



    def teslaEV_UpdateConnectionStatus(self, EVid):
        #logging.debug('teslaEV_GetConnectionStatus: for {}'.format(EVid))
        try:
            self.teslaEV_get_vehicles()
            return(self.carInfo[EVid]['state'])
        except Exception as e:
            logging.error('teslaEV_UpdateConnectionStatus - {}'.format(e))
            return('error')

    def teslaEV_GetName(self, EVid):
        try:
            return(self.carInfo[EVid]['vehicle_state']['vehicle_name'])

        except Exception as e:
            logging.debug('teslaEV_GetName - No EV name found - {}'.format(e))
            return(None)


    def teslaEV_GetInfo(self, EVid):
        if EVid in self.carInfo:
            #logging.debug('teslaEV_GetInfo {}'.format(self.carInfo))
            logging.debug('teslaEV_GetInfo {}: {}'.format(EVid, self.carInfo[EVid]))
            return(self.carInfo[EVid])
        else:
            return(None)


    def teslaEV_GetLocation(self, EVid):
        logging.debug('teslaEV_GetLocation: {} for {}'.format(EVid,self.carInfo[EVid]['drive_state'] ))
        temp = {}
        temp['longitude'] = None
        temp['latitude'] = None
        try:
            if 'longitude' in self.carInfo[EVid]['drive_state']:
                temp['longitude'] = self.carInfo[EVid]['drive_state']['longitude']
                temp['latitude'] = self.carInfo[EVid]['drive_state']['latitude']
            elif 'active_route_longitude'in self.carInfo[EVid]['drive_state']:
                temp['longitude'] = self.carInfo[EVid]['drive_state']['active_route_longitude']
                temp['latitude'] = self.carInfo[EVid]['drive_state']['active_route_latitude']                
            return(temp)
        except Exception as e:
            logging.error('teslaEV_GetLocation - location error')
            return(temp)


    def teslaEV_SetDistUnit(self, dUnit):
        logging.debug('teslaEV_SetDistUnit: {}'.format(dUnit))
        self.dist_unit = dUnit

    def teslaEV_GetDistUnit(self):
        #logging.debug('teslaEV_GetDistUnit: {}'.format(self.dist_unit))
        return(self.dist_unit)

    def teslaEV_SetTempUnit(self, tUnit):
        logging.debug('teslaEV_SetDistUnit: {}'.format(tUnit))
        self.temp_unit = tUnit

    def teslaEV_GetTempUnit(self):
        #logging.debug('teslaEV_GetTempUnit: {}'.format(self.temp_unit))
        return(self.temp_unit)


    def teslaEV_SetRegion(self, tRegion):
        logging.debug('teslaEV_SetRegion: {}'.format(tRegion))
        self.region = tRegion

    def teslaEV_GetTimeSinceLastCarUpdate(self, EVid):
        try:
            logging.debug('teslaEV_GetTimeSinceLastCarUpdate')
            timeNow = int(time.time())
            lst = [self.teslaEV_GetTimeSinceLastClimateUpdate(EVid),self.teslaEV_GetTimeSinceLastChargeUpdate(EVid), self.teslaEV_GetTimeSinceLastStatusUpdate(EVid)]

            timeMinimum =  min(filter(lambda x: x is not None, lst)) if any(lst) else None
            #timeMinimum = min( self.teslaEV_GetTimeSinceLastClimateUpdate(EVid),self.teslaEV_GetTimeSinceLastChargeUpdate(EVid), self.teslaEV_GetTimeSinceLastStatusUpdate(EVid) )
            logging.debug('Time Now {} Last UPdate {}'.format(timeNow, timeMinimum ))
            return(float(timeMinimum))
        except Exception as e:
            logging.debug('Exception teslaEV_GetTimeSinceLastCarUpdate - {}'.format(e))
            return(None)

####################
# Charge Data
####################
    '''
    def teslaEV_GetChargingInfo(self, EVid):
        logging.debug('teslaEV_GetChargingInfo: for {}'.format(EVid))
        temp = {}
        if 'fast_charger_present' in  self.carInfo[EVid]['charge_state']:
            temp['fast_charger_present'] = self.carInfo[EVid]['charge_state']['fast_charger_present']
        if 'charge_port_latch' in  self.carInfo[EVid]['charge_state']:    
            temp['charge_port_latch'] =  self.carInfo[EVid]['charge_state']['charge_port_latch']
        if 'charge_port_door_open' in  self.carInfo[EVid]['charge_state']: 
            temp['charge_port_door_open'] =  self.carInfo[EVid]['charge_state']['charge_port_door_open']
        if 'battery_range' in  self.carInfo[EVid]['charge_state']: 
            temp['battery_range'] = self.carInfo[EVid]['charge_state']['battery_range']            
        if 'battery_level' in  self.carInfo[EVid]['charge_state']: 
            temp['battery_level'] = self.carInfo[EVid]['charge_state']['battery_level']
        if 'charge_current_request_max' in  self.carInfo[EVid]['charge_state']: 
            temp['charge_current_request_max'] = self.carInfo[EVid]['charge_state']['charge_current_request_max']
        if 'charging_state' in  self.carInfo[EVid]['charge_state']: 
            temp['charging_state'] = self.carInfo[EVid]['charge_state']['charging_state']
        if 'charge_enable_request' in  self.carInfo[EVid]['charge_state']: 
            temp['charge_enable_request'] = self.carInfo[EVid]['charge_state']['charge_enable_request']
        if 'charger_power' in  self.carInfo[EVid]['charge_state']: 
            temp['charger_power'] = self.carInfo[EVid]['charge_state']['charger_power']
        if 'charge_limit_soc' in  self.carInfo[EVid]['charge_state']: 
            temp['charge_limit_soc'] = self.carInfo[EVid]['charge_state']['charge_limit_soc']      
        if 'charge_current_request_max' in  self.carInfo[EVid]['charge_state']: 
            temp['charge_current_request_max'] = self.carInfo[EVid]['charge_state']['charge_current_request_max']      
        if 'charge_current_request' in  self.carInfo[EVid]['charge_state']: 
            temp['charge_current_request'] = self.carInfo[EVid]['charge_state']['charge_current_request']      
        if 'charger_actual_current' in  self.carInfo[EVid]['charge_state']: 
            temp['charger_actual_current'] = self.carInfo[EVid]['charge_state']['charger_actual_current']      
        if 'charge_amps' in  self.carInfo[EVid]['charge_state']: 
            temp['charge_amps'] = self.carInfo[EVid]['charge_state']['charge_amps']      
        if 'time_to_full_charge' in  self.carInfo[EVid]['charge_state']: 
            temp['time_to_full_charge'] = self.carInfo[EVid]['charge_state']['time_to_full_charge']      
        if 'charge_energy_added' in  self.carInfo[EVid]['charge_state']: 
            temp['charge_energy_added'] = self.carInfo[EVid]['charge_state']['charge_energy_added']      
        if 'charge_miles_added_rated' in  self.carInfo[EVid]['charge_state']: 
            temp['charge_miles_added_rated'] = self.carInfo[EVid]['charge_state']['charge_miles_added_rated']      
        if 'charger_voltage' in  self.carInfo[EVid]['charge_state']: 
            temp['charger_voltage'] = self.carInfo[EVid]['charge_state']['charger_voltage']                
        if 'ideal_battery_range' in  self.carInfo[EVid]['charge_state']: 
            temp['ideal_battery_range'] = self.carInfo[EVid]['charge_state']['ideal_battery_range']   
        if 'timestamp' in  self.carInfo[EVid]['charge_state']: 
            temp['timestamp'] = int(self.carInfo[EVid]['charge_state']['timestamp'] /1000) # Tesla reports in miliseconds                
        return(temp)
    '''

    def teslaEV_GetChargeTimestamp(self, EVid):
        try:
            return(self.carInfo['charge_state']['timestamp'])
        except Exception as e:
            logging.debug('Exception teslaEV_GetChargeTimestamp - {}'.format(e))
            return(None)


    def teslaEV_GetIdelBatteryRange(self, EVid):
        try:
            if 'ideal_battery_range' in self.carInfo[EVid]['charge_state']:
                return(round(self.carInfo[EVid]['charge_state']['ideal_battery_range'],2))
            else:
                return(None)
        except Exception as e:
            logging.debug('Exception teslaEV_GetIdelBatteryRange - {}'.format(e))
            return(None)



    def teslaEV_charge_current_request_max(self, EVid):
        try:
            #logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
            if 'charge_current_request_max' in self.carInfo[EVid]['charge_state']:
                return(round(self.carInfo[EVid]['charge_state']['charge_current_request_max'],1)) 
            else:
                return(None)
        except Exception as e:
            logging.debug('Exception teslaEV_charge_current_request_max - {}'.format(e))
            return(None)            

    def teslaEV_charge_current_request(self, EVid):
        try:
            #logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
            if 'charge_current_request' in self.carInfo[EVid]['charge_state']:
                return(round(self.carInfo[EVid]['charge_state']['charge_current_request'],1)) 
            else:
                return(None)
        except Exception as e:
            logging.debug('Exception teslaEV_charge_current_request - {}'.format(e))
            return(None)            
            

    def teslaEV_charger_actual_current(self, EVid):
        try:
            #logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
            if 'charger_actual_current' in self.carInfo[EVid]['charge_state']:
                return(round(self.carInfo[EVid]['charge_state']['charger_actual_current'],1)) 
            else:
                return(None)
        except Exception as e:
            logging.debug('Exception teslaEV_charger_actual_current - {}'.format(e))
            return(None)              

    def teslaEV_charge_amps(self, EVid):
        try:
            #logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
            if 'charge_amps' in self.carInfo[EVid]['charge_state']:
                return(round(self.carInfo[EVid]['charge_state']['charge_amps'],1)) 
            else:
                return(None)      
        except Exception as e:
            logging.debug('Exception teslaEV_charge_amps - {}'.format(e))
            return(None)         

    def teslaEV_time_to_full_charge(self, EVid):
        try:
            #logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
            if 'time_to_full_charge' in self.carInfo[EVid]['charge_state']:
                return(round(self.carInfo[EVid]['charge_state']['time_to_full_charge']*60,0)) 
            else:
                return(None)            
        except Exception as e:
            logging.debug('Exception teslaEV_time_to_full_charge - {}'.format(e))
            return(None)         
        
    def teslaEV_charge_energy_added(self, EVid):
        try:
            #logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
            if 'charge_energy_added' in self.carInfo[EVid]['charge_state']:
                return(round(self.carInfo[EVid]['charge_state']['charge_energy_added'],1)) 
            else:
                return(None)  
        except Exception as e:
            logging.debug('Exception teslaEV_charge_energy_added - {}'.format(e))
            return(None)                        

    def teslaEV_charge_miles_added_rated(self, EVid):
        try:
            #logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
            if 'time_to_full_charge' in self.carInfo[EVid]['charge_state']:
                return(round(self.carInfo[EVid]['charge_state']['charge_miles_added_rated'],1)) 
            else:
                return(None)            
        except Exception as e:
            logging.debug('Exception teslaEV_charge_miles_added_rated - {}'.format(e))
            return(None)                        

    def teslaEV_charger_voltage(self, EVid):
        try:
            #logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
            if 'charger_voltage' in self.carInfo[EVid]['charge_state']:
                return(round(self.carInfo[EVid]['charge_state']['charger_voltage'],0)) 
            else:
                return(None)       
        except Exception as e:
            logging.debug('Exception teslaEV_charger_voltage - {}'.format(e))
            return(None)                  

    def teslaEV_GetTimeSinceLastChargeUpdate(self, EVid):
        try:
            timeNow = int(time.time())
            logging.debug('Time Now {} Last UPdate {}'.format(timeNow,self.carInfo[EVid]['charge_state']['timestamp']/1000 ))
            return(int(timeNow - float(self.carInfo[EVid]['charge_state']['timestamp']/1000)))
        except Exception as e:
            logging.debug('Exception teslaEV_GetTimeSinceLastChargeUpdate - {}'.format(e))
            return(None)  
        
    def teslaEV_FastChargerPresent(self, EVid):
        #logging.debug('teslaEV_FastchargerPresent for {}'.format(EVid))
        try:
            return(self.carInfo[EVid]['charge_state']['fast_charger_present'])
        except Exception as e:
            logging.debug('Exception teslaEV_FastChargerPresent - {}'.format(e))
            return(None)  
  
    def teslaEV_ChargePortOpen(self, EVid):
        #logging.debug('teslaEV_ChargePortOpen for {}'.format(EVid))
        try:
            return(self.carInfo[EVid]['charge_state']['charge_port_door_open']) 
        except Exception as e:
            logging.debug('Exception teslaEV_ChargePortOpen - {}'.format(e))
            return(None)  

    def teslaEV_ChargePortLatched(self, EVid):
        #logging.debug('teslaEV_ChargePortOpen for {}'.format(EVid))
        try:
            return(self.carInfo[EVid]['charge_state']['charge_port_latch']) 
        except Exception as e:
            logging.debug('Exception teslaEV_ChargePortLatched - {}'.format(e))
            return(None)  
        
    def teslaEV_GetBatteryRange(self, EVid):
        try:
            #logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
            if 'battery_range' in self.carInfo[EVid]['charge_state']:
                return(round(self.carInfo[EVid]['charge_state']['battery_range'],0)) 
            else:
                return(None)
        except Exception as e:
            logging.debug('Exception teslaEV_GetBatteryRange - {}'.format(e))
            return(None)  
        
    def teslaEV_GetBatteryLevel(self, EVid):
        try:
            #logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
            if 'battery_level' in self.carInfo[EVid]['charge_state']:
                return(round(self.carInfo[EVid]['charge_state']['battery_level'],1)) 
            else:
                return(None)
        except Exception as e:
            logging.debug('Exception teslaEV_GetBatteryLevel - {}'.format(e))
            return(None)  
        
    def teslaEV_MaxChargeCurrent(self, EVid):
        #logging.debug('teslaEV_MaxChargeCurrent for {}'.format(EVid))
        try:
            return( self.carInfo[EVid]['charge_state']['charge_current_request_max'])             
        except Exception as e:
            logging.debug('Exception teslaEV_MaxChargeCurrent - {}'.format(e))
            return(None)       

    def teslaEV_ChargeState(self, EVid):
        #logging.debug('teslaEV_GetChargingState for {}'.format(EVid))
        try:
            return( self.carInfo[EVid]['charge_state']['charging_state'])  
        except Exception as e:
            logging.debug('Exception teslaEV_ChargeState - {}'.format(e))
            return(None)     
        
    def teslaEV_ChargingRequested(self, EVid):
        #logging.debug('teslaEV_ChargingRequested for {}'.format(EVid))
        try:
            return(  self.carInfo[EVid]['charge_state']['charge_enable_request'])  
        except Exception as e:
            logging.debug('Exception teslaEV_ChargingRequested - {}'.format(e))
            return(None)  
    
    def teslaEV_GetChargingPower(self, EVid):
        try:
            #logging.debug('teslaEV_GetChargingPower for {}'.format(EVid))
            if 'charger_power' in self.carInfo[EVid]['charge_state']:
                return(round(self.carInfo[EVid]['charge_state']['charger_power'],1)) 
            else:
                return(None)
        except Exception as e:
            logging.debug('Exception teslaEV_GetChargingPower - {}'.format(e))
            return(None)              

    def teslaEV_GetBatteryMaxCharge(self, EVid):
        try:
            #logging.debug('teslaEV_GetBatteryMaxCharge for {}'.format(EVid))
            if 'charge_limit_soc' in self.carInfo[EVid]['charge_state']:
                return(round(self.carInfo[EVid]['charge_state']['charge_limit_soc'],1)) 
            else:
                return(None)
        except Exception as e:
            logging.debug('Exception teslaEV_GetBatteryMaxCharge - {}'.format(e))
            return(None)              
           


    def teslaEV_ChargePort(self, EVid, ctrl):
        logging.debug('teslaEV_ChargePort{} for {}'.format(ctrl, EVid))
 
        #S = self.teslaApi.teslaConnect()
        #with requests.Session() as s:
        try:
            #s.auth = OAuth2BearerToken(S['access_token'])    
            #payload = {}      
            if ctrl == 'open':  
                code, temp = self._callApi('POST', '/vehicles/'+str(EVid) +'/command/charge_port_door_open') 
            elif ctrl == 'close':
                code, temp = self._callApi('POST', '/vehicles/'+str(EVid) +'/command/charge_port_door_close') 
            else:
                logging.debug('Unknown teslaEV_ChargePort command passed for vehicle id (open, close) {}: {}'.format(EVid, ctrl))
                return(False)
            logging.debug(temp['response']['result'])
            return(temp['response']['result'])
        except Exception as e:
            logging.error('Exception teslaEV_ChargePort for vehicle id {}: {}'.format(EVid, e))
            logging.error('Trying to reconnect')
            return(False)


    def teslaEV_Charging(self, EVid, ctrl):
        logging.debug('teslaEV_Charging {} for {}'.format(ctrl, EVid))
 
        #S = self.teslaApi.teslaConnect()
        #with requests.Session() as s:
        try:
            #s.auth = OAuth2BearerToken(S['access_token'])    
            #payload = {}      
            if ctrl == 'start':  
                code, temp = self._callApi('POST','/vehicles/'+str(EVid) +'/command/charge_start' ) 
            elif ctrl == 'stop':
                code, temp = self._callApi('POST', '/vehicles/'+str(EVid) +'/command/charge_stop' ) 
            else:
                logging.debug('Unknown teslaEV_Charging command passed for vehicle id (start, stop) {}: {}'.format(EVid, ctrl))
                return(False)
            #temp = r.json()
            logging.debug(temp['response']['result'])
            return(temp['response']['result'])
        except Exception as e:
            logging.error('Exception teslaEV_AteslaEV_ChargingutoCondition for vehicle id {}: {}'.format(EVid, e))
            logging.error('Trying to reconnect')
            
            return(False)


    def teslaEV_SetChargeLimit (self, EVid, limit):
        logging.debug('teslaEV_SetChargeLimit {} for {}'.format(limit, EVid))
       
        if int(limit) > 100 or int(limit) < 0:
            logging.error('Invalid seat heat level passed (0-100%) : {}'.format(limit))
            return(False)
        #S = self.teslaApi.teslaConnect()
        #with requests.Session() as s:
        try:
            payload = { 'percent':int(limit)}    
            #s.auth = OAuth2BearerToken(S['access_token'])
            #logging.debug('POST: {} {}'.format(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/set_charge_limit', payload ))
            code, temp = self._callApi('POST','/vehicles/'+str(EVid) +'/command/set_charge_limit',  payload ) 
            #logging.debug('teslaEV_SetChargeLimit r :'.format(r))
            #temp = r.json()
            logging.debug('teslaEV_SetChargeLimit temp :'.format(temp))
            return(temp['response']['result'])
        except Exception as e:
            logging.error('Exception teslaEV_SetChargeLimit for vehicle id {}: {}'.format(EVid, e))
            logging.error('Trying to reconnect')
            
            return(False)

    def teslaEV_SetChargeLimitAmps (self, EVid, limit):
        logging.debug('teslaEV_SetChargeLimitAmps {} for {} -'.format(limit, EVid))
       
        if limit > 300 or limit < 0:
            logging.error('Invalid seat heat level passed (0-300A) : {}'.format(limit))
            return(False)
        #S = self.teslaApi.teslaConnect()
        #with requests.Session() as s:
        try:
            payload = { 'charging_amps': int(limit)}    
            #s.auth = OAuth2BearerToken(S['access_token'])
            code, temp = self._callApi('POST','/vehicles/'+str(EVid) +'/command/set_charging_amps', payload ) 
            #temp = r.json()
            return(temp['response']['result'])
        except Exception as e:
            logging.error('Exception teslaEV_SetChargeLimitAmps for vehicle id {}: {}'.format(EVid, e))
            logging.error('Trying to reconnect')
            
            return(False)




####################
# Climate Data
####################

    '''
    def teslaEV_GetClimateInfo(self, EVid):
        logging.debug('teslaEV_GetClimateInfo: for {}'.format(EVid))
        temp = {}
        if 'climate_state' in self.carInfo[EVid]:
            if 'inside_temp' in self.carInfo[EVid]['climate_state']:
                temp['inside_temp'] = self.carInfo[EVid]['climate_state']['inside_temp']
            if 'outside_temp' in self.carInfo[EVid]['climate_state']:
                temp['outside_temp'] = self.carInfo[EVid]['climate_state']['outside_temp']
            if 'driver_temp_setting' in self.carInfo[EVid]['climate_state']:
                temp['driver_temp_setting'] = self.carInfo[EVid]['climate_state']['driver_temp_setting']
            if 'passenger_temp_setting' in self.carInfo[EVid]['climate_state']:
                temp['passenger_temp_setting'] = self.carInfo[EVid]['climate_state']['passenger_temp_setting']
            if 'seat_heater_left' in self.carInfo[EVid]['climate_state']:
                temp['seat_heater_left'] = self.carInfo[EVid]['climate_state']['seat_heater_left']
            if 'seat_heater_right' in self.carInfo[EVid]['climate_state']:
                temp['seat_heater_right'] = self.carInfo[EVid]['climate_state']['seat_heater_right']
            if 'seat_heater_rear_center' in self.carInfo[EVid]['climate_state']:
                temp['seat_heater_rear_center'] = self.carInfo[EVid]['climate_state']['seat_heater_rear_center']
            if 'seat_heater_rear_left' in self.carInfo[EVid]['climate_state']:
                temp['seat_heater_rear_left'] = self.carInfo[EVid]['climate_state']['seat_heater_rear_left']
            if 'seat_heater_rear_right' in self.carInfo[EVid]['climate_state']:
                temp['seat_heater_rear_right'] = self.carInfo[EVid]['climate_state']['seat_heater_rear_right']
            if 'is_auto_conditioning_on' in self.carInfo[EVid]['climate_state']:
                temp['is_auto_conditioning_on'] = self.carInfo[EVid]['climate_state']['is_auto_conditioning_on']
            if 'is_preconditioning' in self.carInfo[EVid]['climate_state']:
                temp['is_preconditioning'] = self.carInfo[EVid]['climate_state']['is_preconditioning']
            if 'max_avail_temp' in self.carInfo[EVid]['climate_state']:
                temp['max_avail_temp'] = self.carInfo[EVid]['climate_state']['max_avail_temp']
            if 'min_avail_temp' in self.carInfo[EVid]['climate_state']:
                temp['min_avail_temp'] = self.carInfo[EVid]['climate_state']['min_avail_temp']
            if 'timestamp' in  self.carInfo[EVid]['climate_state']: 
                temp['timestamp'] = int(self.carInfo[EVid]['climate_state']['timestamp'] /1000) # Tesla reports in miliseconds
        if 'steering_wheel_heater' in self.carInfo[EVid]['vehicle_state']: 
            self.steeringWheeelHeat = self.carInfo[EVid]['vehicle_state']['steering_wheel_heater']
            self.steeringWheelHeatDetected = True
    '''

    def teslaEV_GetClimateTimestamp(self, EVid):
        try:
            return(self.carInfo[EVid]['climate_state']['timestamp'])
        except Exception as e:
            logging.debug(' Exception teslaEV_GetClimateTimestamp - {}'.format(e))
            return(None)

    def teslaEV_GetTimeSinceLastClimateUpdate(self, EVid):
        try:
            timeNow = int(time.time())
            logging.debug('Time Now {} Last UPdate {}'.format(timeNow,self.carInfo[EVid]['climate_state']['timestamp']/1000 ))

            return(int(timeNow - float(self.carInfo[EVid]['climate_state']['timestamp']/1000)))
        except Exception as e:
            logging.debug(' Exception teslaEV_GetTimeSinceLastClimateUpdate - {}'.format(e))
            return(None)

    def teslaEV_GetCabinTemp(self, EVid):
        try:
            logging.debug('teslaEV_GetCabinTemp for {} - {}'.format(EVid, self.carInfo[EVid]['climate_state']['inside_temp'] ))
            if 'inside_temp' in self.carInfo[EVid]['climate_state']:
                return(round(self.carInfo[EVid]['climate_state']['inside_temp'],1)) 
            else:
                return(None)
        except Exception as e:
            logging.debug(' Exception teslaEV_GetCabinTemp - {}'.format(e))
            return(None)
        
    def teslaEV_GetOutdoorTemp(self, EVid):
        try:
            logging.debug('teslaEV_GetOutdoorTemp for {} = {}'.format(EVid, self.carInfo[EVid]['climate_state']['outside_temp']))
            if 'outside_temp' in self.carInfo[EVid]['climate_state']:
                return(round(self.carInfo[EVid]['climate_state']['outside_temp'],1)) 
            else:
                return(None)
        except Exception as e:
            logging.debug(' Exception teslaEV_GetOutdoorTemp - {}'.format(e))
            return(None)
        
    def teslaEV_GetLeftTemp(self, EVid):
        try:
            #logging.debug('teslaEV_GetLeftTemp for {}'.format(EVid))
            if 'driver_temp_setting' in self.carInfo[EVid]['climate_state']:
                return(round(self.carInfo[EVid]['climate_state']['driver_temp_setting'],1))   
            else:
                return(None) 
        except Exception as e:
            logging.debug(' Exception teslaEV_GetLeftTemp - {}'.format(e))
            return(None)            

    def teslaEV_GetRightTemp(self, EVid):
        try:
            #logging.debug('teslaEV_GetRightTemp for {}'.format(EVid))
            if 'passenger_temp_setting' in self.carInfo[EVid]['climate_state']:
                return(round(self.carInfo[EVid]['climate_state']['passenger_temp_setting'],1))   
            else:
                return(None)
        except Exception as e:
            logging.debug(' Exception teslaEV_GetRightTemp - {}'.format(e))
            return(None)            

    def teslaEV_GetSeatHeating(self, EVid):
        try:
        #logging.debug('teslaEV_GetSeatHeating for {}'.format(EVid))
            temp = {}
            if 'seat_heater_left' in self.carInfo[EVid]['climate_state']:
                temp['FrontLeft'] = self.carInfo[EVid]['climate_state']['seat_heater_left']
            if 'seat_heater_right' in self.carInfo[EVid]['climate_state']:
                temp['FrontRight'] = self.carInfo[EVid]['climate_state']['seat_heater_right']   
            if 'seat_heater_rear_left' in self.carInfo[EVid]['climate_state']:
                temp['RearLeft'] = self.carInfo[EVid]['climate_state']['seat_heater_rear_left']   
            if 'seat_heater_rear_center' in self.carInfo[EVid]['climate_state']:
                temp['RearMiddle'] = self.carInfo[EVid]['climate_state']['seat_heater_rear_center']           
            if 'seat_heater_rear_right' in self.carInfo[EVid]['climate_state']:
                temp['RearRight'] = self.carInfo[EVid]['climate_state']['seat_heater_rear_right']           
            return(temp)
        except Exception as e:
            logging.debug(' Exception teslaEV_GetSeatHeating - {}'.format(e))
            return(temp)            
 

    def teslaEV_AutoConditioningRunning(self, EVid):
        try:

            return( self.carInfo[EVid]['climate_state']['is_auto_conditioning_on']) 
        except Exception as e:
            logging.debug(' Exception teslaEV_AutoConditioningRunning - {}'.format(e))
            return(None)      

    def teslaEV_PreConditioningEnabled(self, EVid):
        #logging.debug('teslaEV_PreConditioningEnabled for {}'.format(EVid))
        try:
            return(self.carInfo[EVid]['climate_state']['is_preconditioning']) 
        except Exception as e:
            logging.debug(' Exception teslaEV_PreConditioningEnabled - {}'.format(e))
            return(None)      

    def teslaEV_MaxCabinTempCtrl(self, EVid):
        #logging.debug('teslaEV_MaxCabinTempCtrl for {}'.format(EVid))
        try:
            if 'max_avail_temp' in self.carInfo[EVid]['climate_state']:
                return(round(self.carInfo[EVid]['climate_state']['max_avail_temp'],1))   
            else:
                return(None)
        except Exception as e:
            logging.debug(' Exception teslaEV_MaxCabinTempCtrl - {}'.format(e))
            return(None)
        
        
    def teslaEV_MinCabinTempCtrl(self, EVid):
        #logging.debug('teslaEV_MinCabinTempCtrl for {}'.format(EVid))
        try:
            if 'min_avail_temp' in self.carInfo[EVid]['climate_state']:
                return(round(self.carInfo[EVid]['climate_state']['min_avail_temp'],1))   
            else:
                return(None)
        except Exception as e:
            logging.debug(' Exception teslaEV_MinCabinTempCtrl - {}'.format(e))
            return(None)
        
    def teslaEV_SteeringWheelHeatOn(self, EVid):
        #logging.debug('teslaEV_SteeringWheelHeatOn for {}'.format(EVid))
        try:
            if (self.carInfo[EVid]['climate_state']['steering_wheel_heater']):
                return(self.carInfo[EVid]['climate_state']['steering_wheel_heat_level'])
            else:
                return(None)
            

        except Exception as e:
            logging.error('teslaEV_SteeringWheelHeatOn Exception : {}'.format(e))
            return(None)

    def teslaEV_Windows(self, EVid, cmd):
        logging.debug('teslaEV_Windows {} for {}'.format(cmd, EVid))
        #S = self.teslaApi.teslaConnect()
        #with requests.Session() as s:
        try:
            if cmd != 'vent' and cmd != 'close':
                logging.error('Wrong command passed to (vent or close) to teslaEV_Windows: {} '.format(cmd))
                return(False)
            #s.auth = OAuth2BearerToken(S['access_token'])    
            payload = {'lat':self.carInfo[EVid]['drive_state']['latitude'],
                        'lon':self.carInfo[EVid]['drive_state']['longitude'],
                        'command': cmd}        
            code, temp = self._callApi('POST', '/vehicles/'+str(EVid) +'/command/window_control', payload ) 
            #temp = r.json()
            if code == 'ok':
                logging.debug(temp['response']['result'])
                return(temp['response']['result'])
            else:
                return(None)
        except Exception as e:
            logging.error('Exception teslaEV_Windows for vehicle id {}: {}'.format(EVid, e))
            logging.error('Trying to reconnect')            
            return(False)


    def teslaEV_SunRoof(self, EVid, cmd):
        logging.debug('teslaEV_SunRoof {} for {}'.format(cmd, EVid))
        #S = self.teslaApi.teslaConnect()
        #with requests.Session() as s:
        try:
            if cmd not in ['vent','close', 'stop'] :
                logging.error('Wrong command passed to (vent or close) to teslaEV_SunRoof: {} '.format(cmd))
                return(False)
            #s.auth = OAuth2BearerToken(S['access_token'])    
            payload = { 'state': cmd}        
            code, temp = self._callApi('POST','/vehicles/'+str(EVid) +'/command/sun_roof_control', payload ) 
            #temp = r.json()
            logging.debug(temp['response']['result'])
            return(temp['response']['result'])
        except Exception as e:
            logging.error('Exception teslaEV_SunRoof for vehicle id {}: {}'.format(EVid, e))
            logging.error('Trying to reconnect')
            
            return(False)


    def teslaEV_AutoCondition(self, EVid, ctrl):
        logging.debug('teslaEV_AutoCondition {} for {}'.format(ctrl, EVid))
        
        #S = self.teslaApi.teslaConnect()
        #with requests.Session() as s:
        try:
            #s.auth = OAuth2BearerToken(S['access_token'])    
            payload = {}      
            if ctrl == 'start':  
                code, temp = self._callApi('POST','/vehicles/'+str(EVid) +'/command/auto_conditioning_start',  payload ) 
            elif ctrl == 'stop':
                code, temp = self._callApi('POST', '/vehicles/'+str(EVid) +'/command/auto_conditioning_stop',  payload ) 
            else:
                logging.debug('Unknown AutoCondition command passed for vehicle id {}: {}'.format(EVid, ctrl))
                return(False)
            #temp = r.json()
            logging.debug(temp['response']['result'])
            return(temp['response']['result'])
        except Exception as e:
            logging.error('Exception teslaEV_AutoCondition for vehicle id {}: {}'.format(EVid, e))
            logging.error('Trying to reconnect')
            
            return(False)


    def teslaEV_SetCabinTemps(self, EVid, driverTempC, passergerTempC):
        logging.debug('teslaEV_AutoCondition {} / {}for {}'.format(driverTempC, passergerTempC, EVid))
        
        #S = self.teslaApi.teslaConnect()
        #with requests.Session() as s:
        try:
            #s.auth = OAuth2BearerToken(S['access_token'])    
            payload = {'driver_temp' : int(driverTempC), 'passenger_temp':int(passergerTempC) }      
            code, temp = self._callApi('POST', '/vehicles/'+str(EVid) +'/command/set_temps', payload ) 
            #temp = r.json()
            logging.debug('call-API {}'.format( temp['response']['result']))
            return(temp['response']['result'])
        except Exception as e:
            logging.error('Exception teslaEV_AutoCondition for vehicle id {}: {}'.format(EVid, e))
            logging.error('Trying to reconnect')
            
            return(False)


    def teslaEV_DefrostMax(self, EVid, ctrl):
        logging.debug('teslaEV_DefrostMax {} for {}'.format(ctrl, EVid))
 
        #S = self.teslaApi.teslaConnect()
        #with requests.Session() as s:
        try:
            payload = {}    
            if ctrl == 'on':
                payload = {'on':True,'manual_override':True }  
            elif  ctrl == 'off':
                payload = {'on':False,'manual_override':True }  
            else:
                logging.error('Wrong parameter for teslaEV_DefrostMax (on/off) for vehicle id {}: {}'.format(EVid, ctrl))
                return(False)
            #s.auth = OAuth2BearerToken(S['access_token'])
            code, temp = self._callApi('POST','/vehicles/'+str(EVid) +'/command/set_preconditioning_max', payload ) 
            #temp = r.json()
            logging.debug(temp['response']['result'])
            return(temp['response']['result'])
        except Exception as e:
            logging.error('Exception teslaEV_AutoCondition for vehicle id {}: {}'.format(EVid, e))
            logging.error('Trying to reconnect')
            
            return(False)


    def teslaEV_SetSeatHeating (self, EVid, seat, levelHeat):
        logging.debug('teslaEV_SetSeatHeating {}, {} for {}'.format(levelHeat, seat, EVid))
        seats = [0, 1, 2, 4, 5 ] 
        rearSeats =  [2, 4, 5 ] 
        if int(levelHeat) > 3 or int(levelHeat) < 0:
            logging.error('Invalid seat heat level passed (0-3) : {}'.format(levelHeat))
            return(False)
        if seat not in seats: 
            logging.error('Invalid seatpassed 0,1, 2, 4, 5 : {}'.format(seat))
            return(False)  
        elif not self.rearSeatHeat and seat in rearSeats:
            logging.error('Rear seat heat not supported on this car')
            return (False)  

        #S = self.teslaApi.teslaConnect()
    #with requests.Session() as s:
        try:
            payload = { 'heater': seat, 'level':int(levelHeat)}    
            #s.auth = OAuth2BearerToken(S['access_token'])
            code, temp = self._callApi('POST', '/vehicles/'+str(EVid) +'/command/remote_seat_heater_request', payload ) 
            #temp = r.json()
            logging.debug(temp['response']['result'])
            return(temp['response']['result'])
        except Exception as e:
            logging.error('Exception teslaEV_SetSeatHeating for vehicle id {}: {}'.format(EVid, e))
            logging.error('Trying to reconnect')
            
            return(False)


    def teslaEV_SteeringWheelHeat(self, EVid, ctrl):
        logging.debug('teslaEV_SteeringWheelHeat {} for {}'.format(ctrl, EVid))
        if self.steeringWheelHeatDetected:
            #S = self.teslaApi.teslaConnect()
            #with requests.Session() as s:
            try:
                payload = {}    
                if ctrl == 'on':
                    payload = {'on':True}  
                elif  ctrl == 'off':
                    payload = {'on':False}  
                else:
                    logging.error('Wrong paralf.carInfo[id]meter for teslaEV_SteeringWheelHeat (on/off) for vehicle id {}: {}'.format(EVid, ctrl))
                    return(False)
                #s.auth = OAuth2BearerToken(S['access_token'])
                code, temp = self._callApi('POST','/vehicles/'+str(EVid) +'/command/remote_steering_wheel_heater_request', payload ) 
                #temp = r.json()
                logging.debug(temp['response']['result'])
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_SteeringWheelHeat for vehicle id {}: {}'.format(EVid, e))
                logging.error('Trying to reconnect')
                
                return(False)
        else:
            logging.error('Steering Wheet does not seem to support heating')
            return(False)


####################
# Status Data
####################
    '''
    def teslaEV_GetStatusInfo(self, EVid):
        logging.debug('teslaEV_GetStatusInfo: for {} : {}'.format(EVid, self.carInfo[EVid]))

        temp = {}
        if 'vehicle_state' in self.carInfo[EVid]:
            if 'center_display_state' in self.carInfo[EVid]['vehicle_state']:
                temp['center_display_state'] = self.carInfo[EVid]['vehicle_state']['center_display_state']
            if 'homelink_device_count' in self.carInfo[EVid]['vehicle_state']:    
                temp['homelink_device_count'] = self.carInfo[EVid]['vehicle_state']['homelink_device_count']
            if 'homelink_nearby' in self.carInfo[EVid]['vehicle_state']:    
                temp['homelink_nearby'] = self.carInfo[EVid]['vehicle_state']['homelink_nearby']
            if 'hfd_window' in self.carInfo[EVid]['vehicle_state']:        
                temp['fd_window'] = self.carInfo[EVid]['vehicle_state']['fd_window']
            if 'fp_window' in self.carInfo[EVid]['vehicle_state']:    
                temp['fp_window'] = self.carInfo[EVid]['vehicle_state']['fp_window']
            if 'rd_window' in self.carInfo[EVid]['vehicle_state']:    
                temp['rd_window'] = self.carInfo[EVid]['vehicle_state']['rd_window']
            if 'rp_window' in self.carInfo[EVid]['vehicle_state']:    
                temp['rp_window'] = self.carInfo[EVid]['vehicle_state']['rp_window']
            if 'ft' in self.carInfo[EVid]['vehicle_state']:    
                temp['frunk'] = self.carInfo[EVid]['vehicle_state']['ft']
            if 'rt' in self.carInfo[EVid]['vehicle_state']:    
                temp['trunk'] = self.carInfo[EVid]['vehicle_state']['rt']
            if 'locked' in self.carInfo[EVid]['vehicle_state']:    
                temp['locked'] = self.carInfo[EVid]['vehicle_state']['locked']
            if 'odometer' in self.carInfo[EVid]['vehicle_state']:    
                temp['odometer'] = self.carInfo[EVid]['vehicle_state']['odometer']
            if 'sun_roof_percent_open' in self.carInfo[EVid]['vehicle_state']:    
                temp['sun_roof_percent_open'] = self.carInfo[EVid]['vehicle_state']['sun_roof_percent_open']
            #if 'sun_roof_state' in self.carInfo[EVid]['vehicle_state']:
            #    temp['sun_roof_state'] = self.carInfo[EVid]['vehicle_state']['sun_roof_state']
            if 'state' in self.carInfo[EVid]['vehicle_state']:    
                temp['state'] = self.carInfo[EVid]['state']
            if 'timestamp' in  self.carInfo[EVid]['vehicle_state']: 
                temp['timestamp'] = int(self.carInfo[EVid]['vehicle_state']['timestamp'] /1000) # Tesla reports in miliseconds
        
            if 'can_actuate_trunks' in  self.carInfo[EVid]['vehicle_config']: 
                self.canActuateTrunks = self.carInfo[EVid]['vehicle_config']['can_actuate_trunks']    
            if 'sun_roof_installed' in  self.carInfo[EVid]['vehicle_config']: 
                if type(self.carInfo[EVid]['vehicle_config']['sun_roof_installed']) != int:
                    self.sunroofInstalled = False
                else:   
                    self.sunroofInstalled = (self.carInfo[EVid]['vehicle_config']['sun_roof_installed']   > 0)
            if 'rear_seat_heaters' in  self.carInfo[EVid]['vehicle_config']: 
                if type (self.carInfo[EVid]['vehicle_config']['rear_seat_heaters']) !=  int:
                    self.rearSeatHeat = False
                else:
                    self.rearSeatHeat = (self.carInfo[EVid]['vehicle_config']['rear_seat_heaters']   > 0)
                
            if 'steering_wheel_heater' in self.carInfo[EVid]['vehicle_state']: 
                self.steeringWheeelHeat = self.carInfo[EVid]['vehicle_state']['steering_wheel_heater']
                self.steeringWheelHeatDetected = True
    '''
        


    def teslaEV_GetCenterDisplay(self, EVid):

        #logging.debug('teslaEV_GetCenterDisplay: for {}'.format(EVid))
        #logging.debug('Car info : {}'.format(self.carInfo[EVid]))
        try:
            return(self.carInfo[EVid]['vehicle_state']['center_display_state'])
        except Exception as e:
            logging.debug(' Exception teslaEV_GetCenterDisplay - {}'.format(e))
            return(None)

    def teslaEV_GetStatusTimestamp(self, EVid):
        try:
            return(self.carInfo[EVid]['vehicle_state']['timestamp'])
        except Exception as e:
            logging.debug(' Exception teslaEV_GetStatusTimestamp - {}'.format(e))
            return(None)

    def teslaEV_GetTimeSinceLastStatusUpdate(self, EVid):
        try:
            timeNow = int(time.time())
            logging.debug('Time Now {} Last Update {}'.format(timeNow,self.carInfo[EVid]['vehicle_state']['timestamp']/1000 ))
            return(int(timeNow - float(self.carInfo[EVid]['vehicle_state']['timestamp']/1000)))
        except Exception as e:
            logging.debug(' Exception teslaEV_GetTimeSinceLastStatusUpdate - {}'.format(e))
            return(None)

    def teslaEV_HomeLinkNearby(self, EVid):
        #logging.debug('teslaEV_HomeLinkNearby: for {}'.format(EVid))
        try:
            return(self.carInfo[EVid]['vehicle_state']['homelink_nearby'])
        except Exception as e:
            logging.debug(' Exception teslaEV_HomeLinkNearby - {}'.format(e))
            return(None)

    def teslaEV_nbrHomeLink(self, EVid):
        logging.debug('teslaEV_nbrHomeLink: for {}'.format(EVid))
        try:
            return(self.carInfo[EVid]['vehicle_state']['homelink_device_count'])
        except Exception as e:
            logging.debug(' Exception teslaEV_nbrHomeLink - {}'.format(e))
            return(None)

    def teslaEV_GetLockState(self, EVid):
        #logging.debug('teslaEV_GetLockState: for {}'.format(EVid))
        try:
            return(self.carInfo[EVid]['vehicle_state']['locked'])
        except Exception as e:
            logging.debug(' Exception teslaEV_GetLockState - {}'.format(e))
            return(None)
    def teslaEV_GetWindoStates(self, EVid):
        #logging.debug('teslaEV_GetWindoStates: for {}'.format(EVid))
        try:
            temp = {}
            if 'fd_window' in self.carInfo[EVid]['vehicle_state']:
                temp['FrontLeft'] = self.carInfo[EVid]['vehicle_state']['fd_window']
            else:
                temp['FrontLeft'] = None
            if 'fp_window' in self.carInfo[EVid]['vehicle_state']:
                temp['FrontRight'] = self.carInfo[EVid]['vehicle_state']['fp_window']
            else:
                temp['FrontRight'] = None
            if 'rd_window' in self.carInfo[EVid]['vehicle_state']:
                temp['RearLeft'] = self.carInfo[EVid]['vehicle_state']['rd_window']
            else:
                temp['RearLeft'] = None
            if 'rp_window' in self.carInfo[EVid]['vehicle_state']:
                temp['RearRight'] = self.carInfo[EVid]['vehicle_state']['rp_window']
            else:
                temp['RearRight'] = None
            return(temp)
        except Exception as e:
            logging.debug(' Exception teslaEV_GetWindoStates - {}'.format(e))
            return(temp)
        

    def teslaEV_GetOdometer(self, EVid):
        try:
            #logging.debug('teslaEV_GetOdometer: for {}'.format(EVid))
            if 'odometer' in self.carInfo[EVid]['vehicle_state']:
                return(round(self.carInfo[EVid]['vehicle_state']['odometer'], 2))
            else:
                return(0.0)
        except Exception as e:
            logging.debug(' Exception teslaEV_GetOdometer - {}'.format(e))
            return(None)
        

    #def teslaEV_GetSunRoofPercent(self, EVid):
    #    try:
    #        #logging.debug('teslaEV_GetSunRoofState: for {}'.format(EVid))
    #        if 'sun_roof_percent_open' in self.carInfo[EVid]['vehicle_state']:
    #            return(round(self.carInfo[EVid]['vehicle_state']['sun_roof_percent_open']))
    #        else:
    #            return(None)
    #    except Exception as e:
    #       logging.debug(' Exception teslaEV_GetSunRoofPercent - {}'.format(e))
    #        return(None)
        
    def teslaEV_GetSunRoofState(self, EVid):
        #logging.debug('teslaEV_GetSunRoofState: for {}'.format(EVid))
        try:
            if 'sun_roof_state' in self.carInfo[EVid]['vehicle_config'] and self.sunroofInstalled:
                return(round(self.carInfo[EVid]['vehicle_state']['sun_roof_state']))
            else:
                return(None)
        except Exception as e:
            logging.error('teslaEV_GetSunRoofState Excaption: {}'.format(e))
            return(None)

    def teslaEV_GetTrunkState(self, EVid):
        #logging.debug('teslaEV_GetTrunkState: for {}'.format(EVid))
        try:
            if self.carInfo[EVid]['vehicle_state']['rt'] == 0:
                return(0)
            else:
                return(1)
        except Exception as e:
            logging.error('teslaEV_GetTrunkState Excaption: {}'.format(e))
            return(None)

    def teslaEV_GetFrunkState(self, EVid):
        #logging.debug('teslaEV_GetFrunkState: for {}'.format(EVid))
        try:
            if self.carInfo[EVid]['vehicle_state']['ft'] == 0:
                return(0)
            else:
                return(1)
        except Exception as e:
            logging.error('teslaEV_GetFrunkState Excaption: {}'.format(e))
            return(None)
###############
# Controls
################
    def teslaEV_FlashLights(self, EVid):
        logging.debug('teslaEV_GetVehicleInfo: for {}'.format(EVid))       
        #S = self.teslaApi.teslaConnect()
        #with requests.Session() as s:
        try:
            #s.auth = OAuth2BearerToken(S['access_token'])
            state = self.teslaEV_GetConnectionStatus(EVid) 
            if state in ['asleep']:             
                state = self.teslaEV_Wake(EVid)
            if state in ['online']:   
                code, temp = self._callApi('POST','/vehicles/'+str(EVid) +'/command/flash_lights')                    
                logging.debug('temp {}'.format(temp))
            #temp = r.json()
                if  temp is not None:
                    if 'response' in temp:
                        self.carInfo[EVid] = temp['response']
                        return(self.carInfo[EVid])
                    else:
                        return(None)
            else:
                return(None)
        except Exception as e:
            logging.error('Exception teslaEV_FlashLight for vehicle id {}: {}'.format(EVid, e))
            logging.error('Trying to reconnect')
            return(None)


    def teslaEV_Wake(self, EVid):
        logging.debug('teslaEV_Wake: for {}'.format(EVid))
        #S = self.teslaApi.teslaConnect()
        online = False
        attempts = 0 
        MAX_ATTEMPTS = 6 # try for 1 minute max
        #with requests.Session() as s:
        try:
            state = self.teslaEV_GetConnectionStatus(EVid)
            if state in ['asleep']:  
                state = self.teslaEV_Wake(EVid)
                #s.auth = OAuth2BearerToken(S['access_token'])            
            self.online == state       
            return(self.online)
        except Exception as e:
            logging.error('Exception teslaEV_Wake for vehicle id {}: {}'.format(EVid, e))
            logging.error('Trying to reconnect')
            
            return(None)


    def teslaEV_HonkHorn(self, EVid):
        logging.debug('teslaEV_HonkHorn for {}'.format(EVid))
        #S = self.teslaApi.teslaConnect()
        #with requests.Session() as s:
        try:
            state = self.teslaEV_GetConnectionStatus(EVid) 
            if state in ['asleep']:             
                state = self.teslaEV_Wake(EVid)
            if state in ['online']:    
                payload = {}        
                code, temp = self._callApi('POST', '/vehicles/'+str(EVid) +'/command/honk_horn', payload ) 
                logging.debug('teslaEV_HonkHorn {}'.format(temp))
                #temp = r.json()
                if temp:
                    if temp['response']:
                        if temp['response']['result']:
                            logging.debug(temp['response']['result'])
                            return(temp['response']['result'])
                        else:
                            return(False)
                else:
                    return(False)
    
        except Exception as e:
            logging.error('Exception teslaEV_HonkHorn for vehicle id {}: {}'.format(EVid, e))
            logging.error('Trying to reconnect')
            
            return(False)


    def teslaEV_PlaySound(self, EVid, sound):
        logging.debug('teslaEV_PlaySound for {}'.format(EVid))
        #S = self.teslaApi.teslaConnect()
        #with requests.Session() as s:
        try:
            #s.auth = OAuth2BearerToken(S['access_token'])    
            state = self.teslaEV_GetConnectionStatus(EVid) 
            if state in ['asleep']:             
                state = self.teslaEV_Wake(EVid)
            if state in ['online']:    
                payload = {'sound' : sound}        
                code, temp = self._callApi('POST', '/vehicles/'+str(EVid) +'/command/remote_boombox', payload ) 
                logging.debug('teslaEV_PlaySound {}'.format(temp))
                #temp = r.json()
                if code == 'ok':
                    if temp['response']:
                        if temp['response']['result']:
                            logging.debug(temp['response']['result'])
                            return(temp['response']['result'])
                        else:
                            return(False)
                else:
                    logging.debug('teslaEV_PlaySound - failed - {} - {} '.format(code, temp))
            else:
                return(False)
    
        except Exception as e:
            logging.error('Exception teslaEV_PlaySound for vehicle id {}: {}'.format(EVid, e))
            logging.error('Trying to reconnect')
            
            return(False)

# Needs to be updated 

    def teslaEV_Doors(self, EVid, ctrl):
        logging.debug('teslaEV_Doors {} for {}'.format(ctrl, EVid))
        
        #S = self.teslaApi.teslaConnect()
        #with requests.Session() as s:
        try:
            #s.auth = OAuth2BearerToken(S['access_token'])    
            payload = {}      
            if ctrl == 'unlock':  
                code, temp = self._callApi('POST', '/vehicles/'+str(EVid) +'/command/door_unlock', payload ) 
            elif ctrl == 'lock':
                code, temp = self._callApi('POST', '/vehicles/'+str(EVid) +'/command/door_lock',  payload ) 
            else:
                logging.debug('Unknown door control passed: {}'.format(ctrl))
                return(False)
            #temp = r.json()
            logging.debug(temp['response']['result'])
            return(temp['response']['result'])
        except Exception as e:
            logging.error('Exception teslaEV_Doors for vehicle id {}: {}'.format(EVid, e))
            logging.error('Trying to reconnect')
            
            return(False)


    def teslaEV_TrunkFrunk(self, EVid, frunkTrunk):
        logging.debug('teslaEV_Doors {} for {}'.format(frunkTrunk, EVid))
        
        #S = self.teslaApi.teslaConnect()
        #with requests.Session() as s:
        try:
            #s.auth = OAuth2BearerToken(S['access_token'])
            payload = {} 
            if frunkTrunk.upper() == 'FRUNK' or frunkTrunk.upper() == 'FRONT':
                cmd = 'front' 
            elif frunkTrunk.upper()  == 'TRUNK' or frunkTrunk.upper() == 'REAR':
                    cmd = 'rear' 
            else:
                logging.debug('Unknown trunk command passed: {}'.format(cmd))
                return(False)
            payload = {'which_trunk':cmd}      
            code, temp = self._callApi('POST', '/vehicles/'+str(EVid) +'/command/actuate_trunk', payload ) 
            #temp = r.json()
            logging.debug(temp['response']['result'])
            return(temp['response']['result'])
        
        except Exception as e:
            logging.error('Exception teslaEV_TrunkFrunk for vehicle id {}: {}'.format(EVid, e))
            logging.error('Trying to reconnect')
            
            return(None)


    def teslaEV_HomeLink(self, EVid):
        logging.debug('teslaEV_HomeLink for {}'.format(EVid))

        #S = self.teslaApi.teslaConnect()
        #with requests.Session() as s:
        try:
            #s.auth = OAuth2BearerToken(S['access_token'])    
            payload = {'lat':self.carInfo[EVid]['drive_state']['latitude'],
                        'lon':self.carInfo[EVid]['drive_state']['longitude']}        
            code, temp = self._callApi('POST', '/vehicles/'+str(EVid) +'/command/trigger_homelink', payload ) 
            #temp = r.json()
            logging.debug(temp['response']['result'])
            return(temp['response']['result'])
        except Exception as e:
            logging.error('Exception teslaEV_HomeLink for vehicle id {}: {}'.format(EVid, e))
            logging.error('Trying to reconnect')
            
            return(False)

