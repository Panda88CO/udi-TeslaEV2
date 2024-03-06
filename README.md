# udi-teslaEV  -  for Polyglot v3 
## Tesla EV Node server
The main node displays node status and the number of EVs associated with account
Each EV will have a Status node and 2 subnodes - Climate and Charging
Status gives an overview and allow some generic control
Climate controls Climate settings as well as Windows
Charging control Charging settings 

## Code
Code is written in Python 3 and is using API info from https://tesla-api.timdorr.com/ (this is an unofficial API)

## Refresh Token 
An initial refresh token is required for first install (and perhaps if token somehow expires)
It can be obtained e.g. using Auth for Tesla iPhone app 
https://apps.apple.com/us/app/auth-app-for-tesla/id1552058613 
or Google app (not tested) Tesla Tokens https://play.google.com/store/apps/details?id=net.leveugle.teslatokens

Input refresh token into configuration - be careful there is no trailing space (space at the end of the token) after copying 
The node server keep a copy of the token (file) and will try use this if node server is restarted.  It will also refresh before token expires

## Installation
Ensure Refresh token is obtained and entered - may need to start node server for field to show up first time 
Short Poll sends a heart beat to the ISY
Long Poll does a refresh of the all vehicle's status 

## Notes 
If additional fields for control or display is desired contact author @ https://github.com/Panda88CO/udi-TeslaEV
Tesla is changing the log in procedures at times so code may needs to be updated in case they change the login requirement
