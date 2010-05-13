#!/bin/sh -e

DIR=/home/envek/Work/orderman-dev/
PIDFILE=$DIR/orderman.pid
LOGFILE=$DIR/paster.log
INIFILE=$DIR/development.ini

cd $DIR
case "$1" in
  start)
    su - envek -c "paster serve --daemon --pid-file=$PIDFILE --log-file=$LOGFILE $INIFILE start"
    ;;
  stop)
    su - envek -c "paster serve --daemon --pid-file=$PIDFILE --log-file=$LOGFILE $INIFILE stop"
    ;;
  restart)
    su - envek -c "paster serve --daemon --pid-file=$PIDFILE --log-file=$LOGFILE $INIFILE restart"
    ;;
  force-reload)
    su - envek -c "paster serve --daemon --pid-file=$PIDFILE --log-file=$LOGFILE $INIFILE restart"
    service apache2 restart
    ;;
  *)
    echo $"Usage: $0 {start|stop|restart|force-reload}"
    exit 1
esac

exit 0
