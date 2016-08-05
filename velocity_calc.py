#!/usr/bin/python

import socket
import sys

PROGRAM_NAME = 'velocity_calc'

# Check to see if python script is running
global prog_lock_socket   # Without this our lock gets garbage collected
prog_lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
try:
    prog_lock_socket.bind('\0' + PROGRAM_NAME)
    print 'Starting:', PROGRAM_NAME, '.'
except socket.error:
    print PROGRAM_NAME, 'is already started.'
    prog_lock_socket.shutdown(socket.SHUT_RDWR)
    prog_lock_socket.close()
    sys.exit()


from subprocess import call
import datetime
import logging
import serial

import time
import math

import utm

logging.basicConfig(filename='/home/pi/_velocity_calc.log', level=logging.DEBUG)

# Run in a continual loop, every ten seconds read lat and lon from the GPS and
# convert it to meters, record the current position (X, Y, Z)
# If we have a previous position, then calculate the distance between the
# current position and the previous position.
# If the distance is greater than some threshold, then call beacon_now to 
# broadcast our position.

THRESHOLD = 5 # meters (low number for testing)
delta_distance = 0.0
prev_location = None


def logAndPrint(message, level):
    if level == 0:
        logging.info(PROGRAM_NAME + ': ' + message)
    elif level == 1:
        logging.warning(PROGRAM_NAME + ': ' + message)
    else:
        logging.error(PROGRAM_NAME + ': ' + message)
    print message
    return


def getGpsLocation(gpsString):
    """"""
    gps = gpsString.split('\n')
    ggaLine = ''
    location = None
    for s in gps:
        if s.startswith('$GPGGA'):
            ggaLine = s
            logAndPrint('GPS data: ' + ggaLine, 0)
            break
    if ggaLine != '':
        # Now parse the GPS string and format it into an APRS string.
        fields = ggaLine.split(',')
        lat = fields[2] # dddmm.mmmm
        dddmm, mmm = lat.split('.')
        latDegrees = int(dddmm[:-2])
        latMinutes = float(dddmm[-2:] + '.' + mmm)
        nS = fields[3] # 'N' or 'S'
        lon = fields[4] 
        dddmm, mmm = lon.split('.')
        lonDegrees = int(dddmm[:-2])
        lonMinutes = float(dddmm[-2:] + '.' + mmm)
        eW = fields[5] # 'E' or 'W'
        fix = fields[6]
        alt = float(fields[9])
        # Convert to degrees decimal degrees.
        lat = latDegrees + latMinutes / 60.0
        if nS == 'S':
            lat *= -1
        lon = lonDegrees + lonMinutes / 60.0
        if eW == 'W':
            lon *= -1
        location = (lat, lon, alt)
    return location 


while True:
    beacon_lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        beacon_lock_socket.bind('\0' + 'beacon_now')
        logAndPrint('Velocity calc got the lock, proceeding with GPS reading.', 0)
        sp = serial.Serial('/dev/ttyUSB0', 38400, timeout=5)
        location = None
        for i in range(10):
            gpsString = sp.read(1024)
            try:
                location = getGpsLocation(gpsString) # Parse the GPS data.
            except Exception, e:
                print e, 'retry: ', i
            if location != None:
                break
        sp.close() 
        beacon_lock_socket.shutdown(socket.SHUT_RDWR)
        beacon_lock_socket.close()
        # Convert lat lon to UTM:
        if location != None:
            logAndPrint('Got a good location:' + repr(location), 0)
            utmLocation = utm.from_latlon(location[0], location[1])
            logAndPrint('UTM location:' + repr(utmLocation), 0)
            # Everything is in meters now :)
            location = (utmLocation[0], utmLocation[1], location[2])
            # Do the distance formula in 3D.
            if prev_location != None:
                dX = location[0] - prev_location[0]
                dY = location[1] - prev_location[1]
                dZ = location[2] - prev_location[2]
                delta_distance += math.sqrt(math.pow(dX, 2) + math.pow(dY, 2) + math.pow(dZ, 2))
                logAndPrint('Calculated distance delta: ' + str(delta_distance), 0)
            prev_location = location
            if delta_distance > THRESHOLD:
                logAndPrint('Delta distance > threshold, beaconing.', 0)
                ret = call(['/home/pi/beacon_now.py'])
                logAndPrint('Beacon_now return code: ' + str(ret), 0)
                delta_distance = 0.0
    except Exception, e:
        logAndPrint('The lock exists, or other error, try again later.', 1)
        logAndPrint('Exception: ' + str(e), 1)
        beacon_lock_socket.shutdown(socket.SHUT_RDWR)
        beacon_lock_socket.close()
    print 'Sleeping for 10 seconds.' # Don't log this.
    time.sleep(10)


logAndPrint('Program exiting, unhandled exception.', 2)
beacon_lock_socket.shutdown(socket.SHUT_RDWR)
beacon_lock_socket.close()

