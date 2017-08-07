#!/usr/bin/python3

import time
import datetime as dt
from WS_UMB import WS_UMB
from urllib.request import urlopen
import json

umb = WS_UMB()

lastMinute = dt.datetime.now().minute
lastHour = dt.datetime.now().hour
lastDay = dt.datetime.now().day

totalRain_OneHourAgo = umb.onlineDataQuery(1, 640)[0]
totalRain_OneDayAgo = totalRain_OneHourAgo

wu_StationID = "STATIONNAME"
wu_Password = "PASSWORD"

filename = 'data.json'

while True:
	url = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?ID=" + wu_StationID + "&PASSWORD=" + wu_Password + "&dateutc=now" 
	
	totalRain_now = umb.onlineDataQuery(1, 640)[0] # inches

	if (dt.datetime.now().day != lastDay):
		lastDay = dt.datetime.now().day
		url += "&dailyrainin=" + str(round(totalRain_now - totalRain_OneDayAgo,1))
		totalRain_OneDayAgo = totalRain_now

	if (dt.datetime.now().hour != lastHour):
		lastHour = dt.datetime.now().hour
		url += "&rainin=" + str(round(totalRain_now - totalRain_OneHourAgo,1))
		totalRain_OneHourAgo = totalRain_now
	
	if (dt.datetime.now().minute != lastMinute):
		lastMinute = dt.datetime.now().minute
		url += "&tempf=" + str(round(umb.onlineDataQuery(1, 105)[0],1))  # °F
		url += "&dewptf=" + str(round(umb.onlineDataQuery(1, 115)[0],1)) # °F
		url += "&humidity=" + str(round(umb.onlineDataQuery(1, 200)[0],1))
		url += "&baromin=" + str(round(umb.onlineDataQuery(1, 300)[0] / 33.863886666667,1)) # inches Hg
		url += "&windspeedmph=" + str(round(umb.onlineDataQuery(1, 410)[0],1)) # miles per hour
		url += "&winddir=" + str(round(umb.onlineDataQuery(1, 500)[0],1))
		
		url += "&softwaretype=Lufft_WS600UMB&action=updateraw"
		conn = urlopen(url)
		if (conn.read() == b'success\n'):
			print(url)
		conn.close()
		
		mydict = {}
		timestamp = dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
		mydict['DateTime'] = timestamp
		temperatur = round(umb.onlineDataQuery(1, 100)[0], 2)			# sampling rate 1min
		mydict['Temperatur'] = temperatur
		windchill = round(umb.onlineDataQuery(1, 111)[0], 2)			# sampling rate 1min
		mydict['Windchill'] = windchill
		relLuftfeuchtigkeit = round(umb.onlineDataQuery(1, 200)[0], 2)	# sampling rate 1min
		mydict['rel. Luftfeuchtigkeit'] = relLuftfeuchtigkeit
		absLuftdruck = round(umb.onlineDataQuery(1, 300)[0], 2)			# sampling rate 1min
		mydict['abs. Luftdruck'] = absLuftdruck
		windgeschwindigkeit = round(umb.onlineDataQuery(1, 400)[0], 2)	# sampling rate 10s
		mydict['Windgeschwindigkeit'] = windgeschwindigkeit
		windrichtung = round(umb.onlineDataQuery(1, 500)[0], 2)			# sampling rate 10s
		mydict['Windrichtung'] = windrichtung
		absNiederschlagsmenge = umb.onlineDataQuery(1, 600)[0]			# sampling rate 1min
		mydict['abs. Niederschlagsmenge'] = absNiederschlagsmenge
		niederschlagsart = umb.onlineDataQuery(1, 700)[0]				# sampling rate 1min or shorter
		mydict['Niederschlagsart'] = niederschlagsart
		niederschlagsintensitaet = umb.onlineDataQuery(1, 800)[0]		# sampling rate 6min
		mydict['Niederschlagsintensitaet'] = niederschlagsintensitaet
		
		with open(filename) as f:
			data = json.load(f)
	
		print (json.dumps(mydict, sort_keys=True, indent=4, separators=(',', ': ')))
		data.append(mydict)
	
		with open(filename, 'w') as f:
			json.dump(data, f, sort_keys=True, indent=4, separators=(',', ': '))
		
	
	time.sleep(10)
