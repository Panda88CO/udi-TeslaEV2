# udi-teslaEV  -  for Polyglot v3 
## Tesla EV Node server
The main node displays node status and the number of EVs associated with account
Each EV will have a Status node and 2 subnodes - Climate and Charging
Status gives an overview and allow some generic control
Climate controls Climate settings as well as Windows
Charging control Charging settings 

## Code
Code is written in Python 3 and is using API info from https://developer.tesla.com/docs/fleet-api#overview (this is an official API)


## Installation
Ensure Refresh token is obtained and entered - may need to start node server for field to show up first time 
Short Poll sends a heart beat to the ISY
Long Poll does a refresh of the all vehicle's status 
Note, there are limitations emposed by the API:

1 API request / car / 5 min
Commands limits	50 API requests / car / day
Wake limits	5 API requests / car / hour.

## Notes 
If additional fields for control or display is desired contact author @ https://github.com/Panda88CO/udi-TeslaEV
Tesla is changing the log in procedures at times so code may needs to be updated in case they change the login requirement
