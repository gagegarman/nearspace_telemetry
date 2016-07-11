#!/usr/bin/python

from subprocess import call
import datetime
import logging

logging.basicConfig(filename='/home/pi/aprs-beacon.log',level=logging.DEBUG)
# Open a serial port to read GPS data, parse the GGA string and beacon it.
# TODO:
# Read the last line appended to the received packet log for AX listen.
# When we get specific commands, take various actions. 

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
    # Put altitude in the actual message.
    alt = str(int(float(fields[9])))
    sep = fields[11]
    # Format the location string:
    location = '@' + utcHHMMSS + 'h' + lat + nS + '/' + lon + eW + '_' + alt
    comment = '/fx:' + fix + ',st:' + sat + ',dp:' + hdop + ',sp:' + sep
    location += comment
    return location


sp = serial.Serial('/dev/ttyUSB0', 9600)
gps = sp.read(1024)
gps = gps.split('\n')

location = None
prevLocation = None

for s in gps:
    try:
        if s.startswith('$GPGGA'):
            print s
            # Parse fields:
            prevLocation = parseGps(s)
            # Keep storing the new location as long as it is valid.
            location = prevLocation
    except Exception, e:
        print e

print location
if location != None:
    logging.info('beacon-now, GPS data: ' + location)
    ret = call(["/usr/sbin/beacon", "-s", "-d BEACON", "1", location])
    # Check the return code of beacon?
else:
    message = 'Failed to parse GPS GPGGA string for location information.'
    print message
    logging.warning('beacon-now: ' + message)


# Output should look something like:
"""
$GPGGA,045435.000,4401.9799,N,12307.2442,W,2,10,0.83,164.5,M,-21.4,M,0000,0000*50
$GPGGA,045436.000,4401.9799,N,12307.2442,W,2,10,0.83,164.5,M,-21.4,M,0000,0000*53
$GPGGA,045437.000,4401.9799,N,12307.2442,W,2,10,0.83,164.5,M,-21.4,M,0000,0000*52
@045437h4401.97N/12307.24W_164/fx:2,st:10,dp:0.83,sp:-21.4
"""


