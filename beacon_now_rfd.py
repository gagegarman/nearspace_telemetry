#!/usr/bin/python

"""Call from a cron job to broadcast the current position via APRS.
"""

import sys
import time

import socket
import logging

PROGRAM_NAME = 'beacon_now'


def logAndPrint(message, level):
    if level == 0:
        logging.info(PROGRAM_NAME + ': ' + message)
    elif level == 1:
        logging.warning(PROGRAM_NAME + ': ' + message)
    else:
        logging.error(PROGRAM_NAME + ': ' + message)
    print message
    return


# From: https://stackoverflow.com/questions/788411/check-to-see-if-python-script-is-running
# Check to see if python script is running
global lock_socket   # Without this our lock gets garbage collected
lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
logging.basicConfig(filename='/home/pi/_beacon_now.log',level=logging.DEBUG)
try:
    lock_socket.bind('\0' + PROGRAM_NAME)
    logAndPrint('I got the lock, proceeding with beacon.', 0)
except socket.error:
    logAndPrint('The lock exists, exiting.', 1)
    lock_socket.shutdown(socket.SHUT_RDWR)
    lock_socket.close()
    sys.exit()


from subprocess import call
import datetime

# Stop the serial port service for /dev/ttyAMA0. Perform a kissattach operation
# and assign an IP address for waht it's worth. This is done on startup in:
# /etc/init.d/setup_beacon.
# Open a serial port to read GPS data. When we get a good location parsed out
# of the GPS stream, transmit it using the beacon program (from AX-25 tools).

dateTime = str(datetime.datetime.now())
logAndPrint('beacon_now: writing message: ' + dateTime, 0)

import serial

SEND_RFD = False
SEND_HAM = True

def parseGps(nmeaLocation):
    # Now parse the GPS string and format it into an APRS string.
    fields = nmeaLocation.split(',')
    id = fields[0]
    utc = fields[1]
    utcHHMMSS = utc[:6]
    lat = '{:0.2f}'.format(float(fields[2]))
    nS = fields[3] # 'N' or 'S'
    lon = '{:0.2f}'.format(float(fields[4])) # dddmm.mmmm
    eW = fields[5] # 'E' or 'W'
    # This goes in the comment field: fix: 1 or 0, sat: #, dop: #, sep: #
    fix = fields[6]
    sat = str(int(fields[7])) # Number of satellites used 0 to 12
    hdop = fields[8]
    # Put altitude in the actual message.
    alt = str(int(float(fields[9])))
    sep = fields[11]
    # Format the location string:
    location = '@' + utcHHMMSS + 'h' + lat + nS + '/' + lon + eW + '_' + alt
    # Include position fix, satellite count, horizontal dilution of precision
    # and geoidal separation in the comment section of the APRS string.
    comment = '/fx:' + fix + ',st:' + sat + ',dp:' + hdop + ',sp:' + sep
    location += comment
    return location


# GPS serial port, this needs to be configured per the GPS module's spec.
sp = serial.Serial('/dev/ttyUSB0', 38400, timeout=5)
newLocation = None

for i in range(10):
    location = None
    gpsString = sp.read(1024) # Read 1024 bytes from the GPS serial stream.
    gps = gpsString.split('\n')
    ggaStr = ''
    for s in gps:
        try:
            if s.startswith('$GPGGA'):
                ggaStr = s
                print ggaStr
                # Parse fields:
                newLocation = parseGps(ggaStr)
                # Keep storing the new location as long as it is valid, so we
                # get the most recent location from the gps string.
                location = newLocation
        except Exception, e:
            logAndPrint('Exception: ' + str(e), 1)
    if location is not None:
        break
    else:
        logAndPrint('Location not initialized, retry: ' + str(i) \
            + ', GPS data: ' + str(ggaStr), 1)

sp.close()

if location != None:
    #location += 'Some custom message.'
    # Log the location and send the APRS string via beacon.
    logAndPrint('APRS string: ' + str(location), 0)
    if SEND_HAM:
        print 'Sending location via HT.'
        ret = call(['/usr/sbin/beacon', '-s', '-d BEACON', '1', location])
        logAndPrint('beacon return code: ' + str(ret), 0)
    # Now send the GPS data to the 900MHz RFD modem's serial port:
    if SEND_RFD:
        print gpsString
        rfd = serial.Serial('/dev/ttyUSB1', 57600)
        rfd.write(gpsString)
        rfd.close()
else:
    logAndPrint('Failed to parse GPS GPGGA string for location information.', 0)

lock_socket.shutdown(socket.SHUT_RDWR)
lock_socket.close()

# Output should look something like:
"""
$GPGGA,045435.000,4401.9799,N,12307.2442,W,2,10,0.83,164.5,M,-21.4,M,0000,0000*50
$GPGGA,045436.000,4401.9799,N,12307.2442,W,2,10,0.83,164.5,M,-21.4,M,0000,0000*53
$GPGGA,045437.000,4401.9799,N,12307.2442,W,2,10,0.83,164.5,M,-21.4,M,0000,0000*52
@045437h4401.97N/12307.24W_164/fx:2,st:10,dp:0.83,sp:-21.4
"""

