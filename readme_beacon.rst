Beacon Setup
===========

Configure init Script:
----------------------

Put beacon-now in /etc/init.d, and configure it to be run on startup with rcconf:

From: 
http://xmodulo.com/how-to-check-what-services-are-enabled-on-boot-in-linux.html

Check startup services in Ubuntu or Debian with rcconf
''''''''''''''''''''''''''''''''''''''''''''''''''''''

A command-line utility called rcconf is a runlevel configuration tool for 
Debian-based systems. Using rcconf, you can check a list of available startup 
scripts/services, and enable/disable a particular service as you wish.

To install and start rcconf on Ubuntu or Debian:

::

    sudo apt-get install rcconf
    sudo rcconf


"Install" beacon_now.py
-----------------------

Put beacon_now.py in the home folder, ensure it is executable.

Configure the script per the GPS module's interface (assuming some kind of 
serial port), port name, baud rate, timeout, etc..

Setup a cron job to execute it periodically, e.g. every minute:

::

    sudo crontab -e


::

    # For more information see the manual pages of crontab(5) and cron(8)
    #
    # m h  dom mon dow   command
    * * * * *  /home/pi/beacon_now.py

