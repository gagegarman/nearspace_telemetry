#!/bin/sh
### BEGIN INIT INFO
# Provides:          setup-beacon
# Required-Start:    $syslog
# Required-Stop:     $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Setup APRS beaconing.
### END INIT INFO

PATH=/bin:/usr/bin:/sbin:/usr/sbin
NAME=setup-beacon

case "$1" in
  start)
    echo -n "Starting setup-beacon"
    sudo kissattach /dev/ttyAMA0 1 10.1.1.3
    echo "$NAME."
    ;;

  stop)
    echo -n "Stopping APRS gateway: "
    sudo killall kissattach
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

