#!/usr/bin/python3

import sys
import time
import struct

class UMBError(BaseException):
	pass

class WS_UMB:
	def __init__(self, device='/dev/ttyUSB0', baudrate=19200, wait=10):
		import serial
		delayed = False
		for attempt in range(wait + 1):
			try:
				self.serial = serial.Serial(device, baudrate=baudrate, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS, interCharTimeout=1)
				break
			except (OSError, IOError):
				if wait == 0:
					continue
				if attempt == 0:
					sys.stdout.write('Waiting {} seconds for WS-UMB '.format(wait))
					delayed = True
			time.sleep(1)
			sys.stdout.write('.')
			sys.stdout.flush()
		else:
			if delayed:
				print('')
			raise UMBError('failed to access ' + device)
		if delayed:
			print('')

	def close(self):
		self.serial.close()

	def readFromSerial(self, timeout=1):
		timeout_count = 0
		data = b''
		while True:
			if self.serial.inWaiting() > 0:
				new_data = self.serial.read(1)
				data = data + new_data
				timeout_count = 0
			else:
				timeout_count += 1
				if timeout is not None and timeout_count >= 10 * timeout:
					break
				time.sleep(0.01)
		return data

	def calc_next_crc_byte(self, crc_buff, nextbyte):
		for i in range (8):
			if( (crc_buff & 0x0001) ^ (nextbyte & 0x01) ):
				x16 = 0x8408;
			else:
				x16 = 0x0000;
			crc_buff = crc_buff >> 1;
			crc_buff ^= x16;
			nextbyte = nextbyte >> 1;
		return(crc_buff);

	def calc_crc16(self, data):
		crc = 0xFFFF;
		for byte in data:
			crc = self.calc_next_crc_byte(crc, byte);
		return crc
	
	def send_request(self, receiver_id, command, command_version, payload):
		
		SOH, STX, ETX, EOT= b'\x01', b'\x02', b'\x03', b'\x04'
		VERSION = b'\x10'
		TO = int(receiver_id).to_bytes(1,'little')
		TO_CLASS = b'\x70'
		FROM = int(1).to_bytes(1,'little')
		FROM_CLASS = b'\xF0'
		
		LEN = 2
		for payload_byte in payload:
			LEN += 1
		LEN = int(LEN).to_bytes(1,'little')

		COMMAND = int(command).to_bytes(1,'little')
		COMMAND_VERSION = int(command_version).to_bytes(1,'little')

		# Assemble transmit-frame
		tx_frame = SOH + VERSION + TO + TO_CLASS + FROM + FROM_CLASS + LEN + STX + COMMAND + COMMAND_VERSION + payload + ETX 
		# calculate checksum for trasmit-frame and concatenate
		tx_frame += self.calc_crc16(tx_frame).to_bytes(2, 'little') + EOT
		
		# Write transmit-frame to serial
		self.serial.write(tx_frame) 
		#print([hex(c) for c in tx_frame])

		### < --- --- > ###

		# Read frame from serial
		rx_frame = self.readFromSerial()
		#print([hex(c) for c in rx_frame])
		
		# compare checksum field to calculated checksum
		cs_calculated = self.calc_crc16(rx_frame[:-3]).to_bytes(2, 'little')
		cs_received = rx_frame[-3:-1]
		if (cs_calculated != cs_received):
			raise UMBError("RX-Error! Checksum test failed. Calculated Checksum: " + str(cs_calculated) + "| Received Checksum: " + str(cs_received))

		# Check the length of the frame
		length = int.from_bytes(rx_frame[6:7], byteorder='little')
		if (rx_frame[8+length:9+length] != ETX):
			raise UMBError("RX-Error! Length of Payload is not valid. length-field says: " + str(length))
		
		# Check if all frame field are valid
		if (rx_frame[0:1] != SOH):
			raise UMBError("RX-Error! No Start-of-frame Character")
		if (rx_frame[1:2] != VERSION):
			raise UMBError("RX-Error! Wrong Version Number")
		if (rx_frame[2:4] != (FROM + FROM_CLASS)):
			raise UMBError("RX-Error! Wrong Destination ID")
		if (rx_frame[4:6] != (TO + TO_CLASS)):
			raise UMBError("RX-Error! Wrong Source ID")
		if (rx_frame[7:8] != STX):
			raise UMBError("RX-Error! Missing STX field")
		if (rx_frame[8:9] != COMMAND):
			raise UMBError("RX-Error! Wrong Command Number")
		if (rx_frame[9:10] != COMMAND_VERSION):
			raise UMBError("RX-Error! Wrong Command Version Number")
			
		status = int.from_bytes(rx_frame[10:11], byteorder='little')
		type_of_value = int.from_bytes(rx_frame[13:14], byteorder='little')		
		value = 0
		
		if type_of_value == 16: 	# UNSIGNED_CHAR
			value = struct.unpack('<B', rx_frame[14:15])[0]
		elif type_of_value == 17:	# SIGNED_CHAR
			value = struct.unpack('<b', rx_frame[14:15])[0]
		elif type_of_value == 18:	# UNSIGNED_SHORT
			value = struct.unpack('<H', rx_frame[14:16])[0]
		elif type_of_value == 19:	# SIGNED_SHORT
			value = struct.unpack('<h', rx_frame[14:16])[0]
		elif type_of_value == 20:	# UNSIGNED_LONG
			value = struct.unpack('<L', rx_frame[14:18])[0]
		elif type_of_value == 21:	# SIGNED_LONG
			value = struct.unpack('<l', rx_frame[14:18])[0]
		elif type_of_value == 22:	# FLOAT
			value = struct.unpack('<f', rx_frame[14:18])[0]
		elif type_of_value == 23:	# DOUBLE
			value = struct.unpack('<d', rx_frame[14:22])[0]

		return (value, status)

	def checkStatus(self, status):
		if status == 0:
			print ("Status: Kommando erfolgreich; kein Fehler; alles i.O.")
		elif status == 16:
			print ("Status: unbekanntes Kommando; wird von diesen Gerät nicht unterstützt")
		elif status == 17:
			print ("Status: ungültige Parameter")
		elif status == 18:
			print ("Status: ungültige Header-Version")
		elif status == 19:
			print ("Status: ungültige Version des Befehls")
		elif status == 20:
			print ("Status: Passwort für Kommando falsch")
		elif status == 32:
			print ("Status: Lesefehler")
		elif status == 33:
			print ("Status: Schreibfehler")
		elif status == 34:
			print ("Status: Länge zu groß; max. zulässige Länge wird in <maxlength> angegeben")
		elif status == 35:
			print ("Status: ungültige Adresse / Speicherstelle")
		elif status == 36:
			print ("Status: ungültiger Kanal")
		elif status == 37:
			print ("Status: Kommando in diesem Modus nicht möglich")
		elif status == 38:
			print ("Status: unbekanntes Test-/Abgleich-Kommando")
		elif status == 39:
			print ("Status: Fehler bei der Kalibrierung")
		elif status == 40:
			print ("Status: Gerät nicht bereit; z.B. Initialisierung / Kalibrierung läuft")
		elif status == 41:
			print ("Status: Unterspannung")
		elif status == 42:
			print ("Status: Hardwarefehler")
		elif status == 43:
			print ("Status: Fehler in der Messung")
		elif status == 44:
			print ("Status: Fehler bei der Geräteinitialisierung")
		elif status == 45:
			print ("Status: Fehler im Betriebssystem")
		elif status == 48:
			print ("Status: Fehler in der Konfiguration, Default-Konfiguration wurde geladen")
		elif status == 49:
			print ("Status: Fehler im Abgleich / der Abgleich ist ungültig, Messung nicht möglich")
		elif status == 50:
			print ("Status: CRC-Fehler beim Laden der Konfiguration; Default-Konfiguration wurde geladen")
		elif status == 51:
			print ("Status: CRC-Fehler beim Laden der Abgleich-Daten; Messung nicht möglich")
		elif status == 52:
			print ("Status: Abgleich Step 1")
		elif status == 53:
			print ("Status: Abgleich OK")
		elif status == 54:
			print ("Status: Kanal deaktiviert")

	def onlineDataQuery (self, receiver_id, channel):
		return self.send_request(receiver_id, 35, 16, int(channel).to_bytes(2,'little'))
