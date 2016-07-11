#!/usr/bin/python

from subprocess import call
import datetime
import logging
logging.basicConfig(filename='/home/pi/aprs-beacon.log',level=logging.DEBUG)
# Stop the serial port service for /dev/ttyAMA0.
# Perform a kissattach operation and assign an IP address for waht its worth.
# Open a serial port to read GPS data. Start a reader thread.
# Open a reader thread to read on AX listen. When we get specific
# commands, take various actions.
# When we get a goo location parsed out of the GPS stream,
# Transmit it using the beacon program.

message = str(datetime.datetime.now())
logging.info('beacon-now: writing message: ' + message)

import serial

def parseGps(nmeaLocation):
    # Now parse the GPS string and format it into an APRS string.
    fields = nmeaLocation.split(',')
    id = fields[0]
    utc = fields[1]
    utcHHMMSS = utc[:6]
    lat = fields[2][:-2]
    nS = fields[3] # 'N' or 'S'
    lon  = fields[4][:-2] # dddmm.mmmm
    eW = fields[5] # 'E' or 'W'
    # This goes in the comment field: fix: 1 or 0, sat: #, dop: #, sep: #
    fix = fields[6]
    sat = str(int(fields[7])) # Number of satellites used 0 to 12
    hdop = fields[8]
    # Put Altitude in the actual message.
    alt = str(int(float(fields[9])))
    sep = fields[11]
    # Format the location string:
    location = '@' + utcHHMMSS + 'h' + lat + nS + '/' + lon + eW + '_' + alt
    comment = '/fx:' + fix + ',st:' + sat + ',dp:' + hdop + ',sp:' + sep
    location += comment
    return location


sp = serial.Serial('/dev/ttyUSB0', 9600, timeout=5)
location = None
newLocation = None

for i in range(10):
    gps = sp.read(1024)
    gps = gps.split('\n')
    for s in gps:
        try:
            if s.startswith('$GPGGA'):
                print s
                # Parse fields:
                newLocation = parseGps(s)
                # Keep storing the new location as long as it is valid.
                location = newLocation
        except Exception, e:
            print e
    if location is not None:
        break
    else:
        message = 'Location not initialized, retry: ' + str(i)
        print message
        logging.warning('beacon-now: ' + message)

print location
if location != None:
    logging.info('beacon-now, GPS data: ' + location)
    ret = call(["/usr/sbin/beacon", "-s", "-d BEACON", "1", location])
# Check the return code of beacon?
else:
    message = 'Failed to parse GPS GPGGA string for location information.'
    print message
    logging.warning('beacon-now: ' + message)

