#!/usr/bin/python3

import time
import struct

class UMBError(BaseException):
    pass

class WS_UMB:
    """
    This is a simple driver for communicating to Weatherstations
    made by the German company Lufft. It implements their UMB-Protocol.
    You just need a USB-to-RS485 dongle and connect it to your PWS 
    according to the wiring diagram you find in the manual.
    Downsides: This class does not replace the UMB-config-tool, because
    its not able to set the config values in your PWS at the moment.
    
    Attributes
    ----------
    device : string
        Serial port. Default is /dev/ttyUSB0
    
    baudrate : integer
        The default baud rate is 19200
        
    Methods
    -------
    onlineDataQuery (channel, receiver_id=1):
        Use this method to request a value from one channel.
        It will return a (value, status) tuple.
        Status number 0 means everything is ok.
        It have more the one PWS on the BUS, use receiver_id to
        distinguish between them.
        
    checkStatus(status):
        You can lookup, what a status number means.
    
    Usage
    -----
    1. In your python-script: 
        from WS_UMB import WS_UMB
        
        with WS_UMB() as umb:
            value, status = umb.onlineDataQuery(SomeChannelNumber)
            if status != 0:
                print(umb.checkStatus(status))
            else:
                print(value)
    
    2. As a standalone program:
        ./WS_UMB.py 100 111 200 300 460 580
    """

    def __init__(self, device='/dev/ttyUSB0', baudrate=19200):
        self.device = device
        self.baudrate = baudrate
    
    def __enter__(self): # throws a SerialException if it cannot connect to device
        import serial
        self.serial = serial.Serial(self.device, baudrate = self.baudrate, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS, interCharTimeout=1)
        return self
    
    def __exit__(self, exception_type, exception_value, traceback):
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
        
        if type_of_value == 16:     # UNSIGNED_CHAR
            value = struct.unpack('<B', rx_frame[14:15])[0]
        elif type_of_value == 17:   # SIGNED_CHAR
            value = struct.unpack('<b', rx_frame[14:15])[0]
        elif type_of_value == 18:   # UNSIGNED_SHORT
            value = struct.unpack('<H', rx_frame[14:16])[0]
        elif type_of_value == 19:   # SIGNED_SHORT
            value = struct.unpack('<h', rx_frame[14:16])[0]
        elif type_of_value == 20:   # UNSIGNED_LONG
            value = struct.unpack('<L', rx_frame[14:18])[0]
        elif type_of_value == 21:   # SIGNED_LONG
            value = struct.unpack('<l', rx_frame[14:18])[0]
        elif type_of_value == 22:   # FLOAT
            value = struct.unpack('<f', rx_frame[14:18])[0]
        elif type_of_value == 23:   # DOUBLE
            value = struct.unpack('<d', rx_frame[14:22])[0]
        
        return (value, status)
    
    def checkStatus(self, status):
        if status == 0:
            return ("Status: Kommando erfolgreich; kein Fehler; alles i.O.")
        elif status == 16:
            return ("Status: unbekanntes Kommando; wird von diesen Gerät nicht unterstützt")
        elif status == 17:
            return ("Status: ungültige Parameter")
        elif status == 18:
            return ("Status: ungültige Header-Version")
        elif status == 19:
            return ("Status: ungültige Version des Befehls")
        elif status == 20:
            return ("Status: Passwort für Kommando falsch")
        elif status == 32:
            return ("Status: Lesefehler")
        elif status == 33:
            return ("Status: Schreibfehler")
        elif status == 34:
            return ("Status: Länge zu groß; max. zulässige Länge wird in <maxlength> angegeben")
        elif status == 35:
            return ("Status: ungültige Adresse / Speicherstelle")
        elif status == 36:
            return ("Status: ungültiger Kanal")
        elif status == 37:
            return ("Status: Kommando in diesem Modus nicht möglich")
        elif status == 38:
            return ("Status: unbekanntes Test-/Abgleich-Kommando")
        elif status == 39:
            return ("Status: Fehler bei der Kalibrierung")
        elif status == 40:
            return ("Status: Gerät nicht bereit; z.B. Initialisierung / Kalibrierung läuft")
        elif status == 41:
            return ("Status: Unterspannung")
        elif status == 42:
            return ("Status: Hardwarefehler")
        elif status == 43:
            return ("Status: Fehler in der Messung")
        elif status == 44:
            return ("Status: Fehler bei der Geräteinitialisierung")
        elif status == 45:
            return ("Status: Fehler im Betriebssystem")
        elif status == 48:
            return ("Status: Fehler in der Konfiguration, Default-Konfiguration wurde geladen")
        elif status == 49:
            return ("Status: Fehler im Abgleich / der Abgleich ist ungültig, Messung nicht möglich")
        elif status == 50:
            return ("Status: CRC-Fehler beim Laden der Konfiguration; Default-Konfiguration wurde geladen")
        elif status == 51:
            return ("Status: CRC-Fehler beim Laden der Abgleich-Daten; Messung nicht möglich")
        elif status == 52:
            return ("Status: Abgleich Step 1")
        elif status == 53:
            return ("Status: Abgleich OK")
        elif status == 54:
            return ("Status: Kanal deaktiviert")
    
    def onlineDataQuery (self, channel, receiver_id=1):
        return self.send_request(receiver_id, 35, 16, int(channel).to_bytes(2,'little'))

#dummy class for testing
class WS_UMB_dummy:
    def __init__(self):
        pass
    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        pass
    def onlineDataQuery (self, channel, receiver_id=1):
        return float(channel), 0
    def checkStatus(self, status):
        return ("Status: unbekanntes Kommando; wird von diesen Gerät nicht unterstützt")
    def close(self):
        pass

import sys
import json

if __name__ == "__main__":
    with WS_UMB() as umb:
    #with WS_UMB_dummy() as umb:
        mydict = {}  
        for channel in sys.argv[1:]:
            if 100 <= int(channel) <= 29999:
                value, status = umb.onlineDataQuery(channel)
                if status == 0:
                    mydict[channel] = value
                else:
                    sys.stderr.write("On channel " + str(channel) + " got bad " + umb.checkStatus(status) + "\n")
    print (json.dumps(mydict, separators=(',', ': ')))
