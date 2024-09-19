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
Run the node server 
Update configuration parameters - most important is region NA (North America), EU (Europe and most of rest of world), CN (China)
Set TEMP_UNIT and DIST_UNIT
Set LOCATION_EN
Note, if Location is enabled - an Icon will show on App.
Location is needed to get access to longitue and latitude as well as homelink 

Restart node server and press autheticate (should only be needed first time)

Note, there are limitations emposed by the API:
1 API request / car / 5 min
Data (update/Poll) limit:   200 API requests / car / day
Commands limit:	            50 API requests / car / day
Wake-up limit:        	    15 API requests / car / day
Charging commands limit:    5 API requests / car / day

ShortPoll = default 10 min (120 call/day)
    Polls data from car if it is awake - does nothing if car is asleep
    sends heartbeat to ISY

LongPoll = default 60min (24)
    Polls data from car. If it is asleep it will wake the csara and retrieve data

## Notes 
If additional fields for control or display is desired contact author @ https://github.com/Panda88CO/udi-TeslaEV

