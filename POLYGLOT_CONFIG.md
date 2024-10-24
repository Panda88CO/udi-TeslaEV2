# teslaEV

## Installation

# udi-teslaEV  -  for Polyglot v3x 
## Tesla EV Node server
The main node displays node status and the number of EVs associated with account
Each EV will have a Status node and 2 subnodes - Climate and Charging
Status gives an overview and allow some generic control
Climate controls Climate settings as well as Windows
Charging control Charging settings 

## Code
Code is written in Python 3 


## Installation
Requires PG3x
To issue commands one must instll an electronic key on the EV
On you mobile device open  https://tesla.com/_ak/my.isy.io. It should open the tesla app and approve the key-install - Older EVs may not support the virtual key
 
Run the node server 
Update configuration parameters - most important is region NA (North America), EU (Europe and most of rest of world), CN (China)
Note - currently only NA is supported for commands
Set TEMP_UNIT (C/F) and DIST_UNIT (Miles/Km) 
Set LOCATION_EN (True/False)

Location is needed to get access to longitue and latitude needed to control windows (close) as well as homelink 
Note, if Location is enabled - an Icon will show on App.

Restart node server and press autheticate (should only be needed first time)

Note, there are limitations emposed by the API:

Data (update/Poll) limit:   200 API requests / car / day
Commands limit:	            50 API requests / car / day
Wake-up limit:        	    15 API requests / car / day
Charging commands limit:    5 API requests / car / day

ShortPoll = default 10 min (120 call/day)
    Polls data from car if it is awake - does nothing if car is asleep
    sends heartbeat to ISY

LongPoll = default 60min (24 call/day)
    Polls data from car. If it is asleep it will wake the car and retrieve data if wake is successful

## Notes 
If additional fields for control or display is desired contact author @ https://github.com/Panda88CO/udi-TeslaEV



