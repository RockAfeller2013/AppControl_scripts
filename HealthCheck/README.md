# Carbon Black Health Check 

The script is designed to be executed in the customer’s environment in order to query the App Control server and generate a zip file containing the results. The best method for completing this is to create a new Case on the Broadcom Support Portal and upload it to the case.

## Setup API Key as per following 
- Create an API User and Get its API Token https://techdocs.broadcom.com/us/en/carbon-black/app-control/carbon-black-app-control/8-11-2/app-control-user-guide_tile/GUID-757E4F0C-1A20-4B38-B7D6-B8063C71C02C-en/GUID-47338240-780C-4B97-9921-285EEEF06F4C-en/GUID-6529F642-7C7D-4AFE-90DD-EB3448F98106-en.html
D928E7CA-FF50-4AFB-8B17-275876EA03AE

## Download and Run it the script

```
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/RockAfeller2013/AppControl_scripts/refs/heads/main/HealthCheck/ac_ta.ps1" -OutFile "ac_ta.ps1"
iwr "https://raw.githubusercontent.com/RockAfeller2013/AppControl_scripts/refs/heads/main/HealthCheck/ac_ta.ps1" -OutFile "ac_ta.ps1"
```

## Upload the Diagnotics to the Support Case
