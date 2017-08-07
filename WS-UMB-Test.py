#!/usr/bin/python3

import time
import datetime
from WS_UMB import WS_UMB
import json # http://www.json.org/ # https://jsonlint.com/ # https://docs.python.org/3/library/json.html

umb = WS_UMB()

min6counter = 0
while True:
	mydict = {}

	timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
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

	niederschlagsart = umb.onlineDataQuery(1, 700)[0] 				# sampling rate 1min or shorter
	mydict['Niederschlagsart'] = niederschlagsart
	
	if (min6counter % 6 == 0):
		niederschlagsintensitaet = umb.onlineDataQuery(1, 800)[0] 		# sampling rate 6min
		mydict['Niederschlagsintensitaet'] = niederschlagsintensitaet
	
	
	with open('data.json') as f:
		data = json.load(f)

	print (json.dumps(mydict, sort_keys=True, indent=4, separators=(',', ': ')))
	data.append(mydict)

	with open('data.json', 'w') as f:
		json.dump(data, f, sort_keys=True, indent=4, separators=(',', ': '))
	
	min6counter += 1
	time.sleep(60)


#timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
#print ("Date and Time: " + timestamp)
#temperatur = round(umb.onlineDataQuery(1, 100)[0], 2)			# sampling rate 1min
#print ("Temperatur: "				+ str(temperatur) + "°C")
#windchill = round(umb.onlineDataQuery(1, 111)[0], 2)			# sampling rate 1min
#print ("Windchill: "				+ str(windchill) + "°C")
#relLuftfeuchtigkeit = round(umb.onlineDataQuery(1, 200)[0], 2)	# sampling rate 1min
#print ("rel. Luftfeuchtigkeit: "	+ str(relLuftfeuchtigkeit) + "%")
#absLuftdruck = round(umb.onlineDataQuery(1, 300)[0], 2)			# sampling rate 1min
#print ("abs. Luftdruck: "			+ str(absLuftdruck) + " hPa")
#windgeschwindigkeit = round(umb.onlineDataQuery(1, 400)[0], 2)	# sampling rate 10s
#print ("Windgeschwindigkeit: "		+ str(windgeschwindigkeit) + " m/s")
#windrichtung = round(umb.onlineDataQuery(1, 500)[0], 2)			# sampling rate 10s
#print ("Windrichtung: "				+ str(windrichtung) + "°")
#absNiederschlagsmenge = umb.onlineDataQuery(1, 600)[0]			# sampling rate 1min
#print ("abs. Niederschlagsmenge: "	+ str(absNiederschlagsmenge) + " liter/m²")
#niederschlagsart = umb.onlineDataQuery(1, 700)[0] 				# sampling rate 1min or shorter
#print ("Niederschlagsart: "			+ str(niederschlagsart))
#print ("Kühlgrenztemperatur: "		+ str(round(umb.onlineDataQuery(1, 114)[0], 2)) + "°C")		# sampling rate 1min
#print ("Spezifische Enthalpie: "	+ str(round(umb.onlineDataQuery(1, 215)[0], 2)) + " kJ/kg")	# sampling rate 1min
#print ("abs. Luftfeuchtigkeit: "	+ str(round(umb.onlineDataQuery(1, 205)[0], 2)) + " g/m³")	# sampling rate 1min
#print ("Luftfeuchtigkeit (Verh.): "+ str(round(umb.onlineDataQuery(1, 210)[0], 2)) + " g/kg")	# sampling rate 1min
#print ("rel. Luftdruck: "			+ str(round(umb.onlineDataQuery(1, 305)[0], 2)) + " hPa")		# sampling rate 1min
#print ("Luftdichte: "				+ str(round(umb.onlineDataQuery(1, 310)[0], 2)) + " kg/m³")	# sampling rate 1min
#print ("mitl. Windgeschwindigkeit: "+ str(round(umb.onlineDataQuery(1, 460)[0], 2)) + " m/s")		# sampling rate 10min
#print ("Kompass: "					+ str(round(umb.onlineDataQuery(1, 510)[0], 2)) + "°") 		# sampling rate 5min
#print ("Niederschlagsmenge (dif): "	+ str(umb.onlineDataQuery(1, 605)[0]) + " liter/m²")# value gets reseted after call


umb.close()
