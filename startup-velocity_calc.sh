#!/bin/sh
### BEGIN INIT INFO
# Provides:          startup-velocity_calc
# Required-Start:    $syslog
# Required-Stop:     $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Startup the velocity calculation script.
### END INIT INFO

PATH=/bin:/usr/bin:/sbin:/usr/sbin
NAME=startup-velocity_calc

case "$1" in
  start)
    echo -n 'Starting velocity calculation script. '
    /home/pi/velocity_calc.py&
    echo "$NAME."
    ;;

  stop)
    echo -n 'Stopping velocity calculation script. '
    killall velocity_calc.py
    echo "$NAME."
    ;;

  force-reload|restart)
    $0 stop
    $0 start
    ;;

  *)
    echo "Usage: /etc/init.d/$NAME {start|stop|restart}"
    exit 1
    ;;

esac

