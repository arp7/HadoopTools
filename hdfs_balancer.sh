#!/bin/bash

# ==============================================================================
# HDFS Balancer Script
# Based on the INPUT value this script automatically pulls
# the top / under utilized hosts for HDFS balancing
# ==============================================================================

# Usage Function
usage ()
{
        echo -e "Usage: $BASENAME {start|stop|status}"
}

# Global Declaration
GLOBAL ()
{
BASENAME=$(basename $0)
PID_FILE="/tmp/$BASENAME.pid"
PID=`cat $PID_FILE`
HDFS="/usr/bin/hdfs"
LOGDIR="/var/log/hdfs-balancer"
LOG="$LOGDIR/balancer.log"
}

# Start the Balancer service
start ()
{
        USER_CK
	GLOBAL
        echo -n "Starting $0"
        PIDFILE
        echo $$ > ${PID_FILE}
#       PICK_NODES
        export INPUT=4 # Top X && Bottom X nodes = 2 x X Nodes would be balanced.
        HDFS_KEYTAB
        mkdir -p /var/log/hdfs-balancer

while :
        do
                GET_HOSTS
#               SLOW_BALANCER_RUN
                FAST_BALANCER_RUN
                sleep 5
done
}

# Stop the Balancer service
stop ()
{
  USER_CK
  GLOBAL
  printf "Stopping $0: \n"
  PRE_CK
  BALANCER=`ps -ef | grep $0 | grep -v grep | awk '{print $2}' | head -n1`
  true > $PID_FILE
  kill -9 $BALANCER
}

# Status on the Balancer Run
status ()
{
        USER_CK
	GLOBAL
        if [[ $(ps -ef | grep $0 | egrep -v 'status|grep') > /dev/null ]]; then
                echo -e "`ps -p $PID | tail -1 | awk '{print $NF}'` Running..."
                egrep 'Executing|^Time' $LOG | tail -2
                grep 'M' $LOG | tail -1 | grep -v ^Time
		echo -e "\nFetching Current Utilization Status... Please Wait...\n"
                CURRENT=`grep Executing $LOG | tail -1 | awk '{print $NF}' | perl -i -pe 's/\,/|/g'`
		echo -e "`$HDFS dfsadmin -report | egrep '^DFS Remaining%|^Hostname' | sed 'N;s/\n/ /' | egrep "$CURRENT"`\n"
        else
                echo -e "`hostname`: Balancer Stopped"
        fi
}

# Ensure the existence of PID file
PIDFILE ()
{
        if [[ ! -e $PID_FILE ]]; then
                touch $PID_FILE
        fi
}

# Pick the Number of nodes to balance
PICK_NODES ()
{
        printf "INFO: The below value would Twice the Number of Input Nodes\n"
        printf "Enter the Number of Hosts to Balance and press [ENTER]: "
        read INPUT
}

## Previlege User Check
USER_CK ()
{
        if ! [[ $(whoami) =~ ^(hdfs)$ ]]; then
                echo "Must be a hdfs user to run $0"
                exit 1;
        fi
}

## Pre-Check
PRE_CK ()
{
BPID=`ps -ef | grep balancer.Balancer | grep -v grep | awk '{print $2}' | tail -n1`
        if [[ "" != "$BPID" ]]; then
                echo -e "\n`date`: Found !!! Balancer Running on `hostname`. Terminating..."
                kill -9 $BPID
        else
                echo -e "\n`hostname`: Balancer Not Running"

        fi
}

# Generating the Keytabs
HDFS_KEYTAB ()
{
/usr/bin/kinit -kt /etc/security/keytabs/hdfs.headless.keytab $(/usr/bin/klist -kt /etc/security/keytabs/hdfs.headless.keytab | tail -1 | awk '{print $NF}')
}

# Picking the Top and Under utilized host and excludes the Dead node
GET_HOSTS ()
{
TOPX=`hdfs dfsadmin -report | egrep '^DFS Remaining%|^Hostname' | sed 'N;s/\n/ /' | sort -n -k 5,5 | grep -vwE "(0)" |head -n $INPUT | awk '{print $2}' | paste -s -d, -`
BOTTOMX=`hdfs dfsadmin -report | egrep '^DFS Remaining%|^Hostname' | sed 'N;s/\n/ /' | sort -n -k 5,5 | grep -vwE "(0)" |tail -n $INPUT | awk '{print $2}' | paste -s -d, -`
HOSTS="${TOPX},${BOTTOMX}"
}

# Run the Balancer
SLOW_BALANCER_RUN ()
{
PRE_CK
echo "INFO: Executing SLOW_BALANCER_RUN"
echo -e "`date`: Executing the balancer between $HOSTS" >> $LOG
HDFS_KEYTAB
$HDFS balancer -Ddfs.datanode.balance.bandwidthPerSec=104857600 -Ddfs.balancer.max-size-to-move=10737418240 -DFS.datanode.balance.max.concurrent.moves=10 -threshold 5 -include $HOSTS 1>>$LOG
}

### The Below Balancer runs in full throttle
FAST_BALANCER_RUN ()
{
PRE_CK
echo "INFO: Executing FAST_BALANCER_RUN"
echo -e "`date`: Executing the balancer against $HOSTS" >> $LOG
HDFS_KEYTAB
$HDFS balancer -Ddfs.datanode.balance.bandwidthPerSec=1048576000 -Ddfs.balancer.max-size-to-move=53687091200 -DFS.datanode.balance.max.concurrent.moves=10 -Ddfs.balancer.getBlocks.size=2147483648 -Ddfs.balancer.getBlocks.min-block-size=10485760 -threshold 4 -include $HOSTS 1>>$LOG
}

#----------------------------------------------------------------------
# Main Logic
#----------------------------------------------------------------------
case "$1" in
  start)
        start
        ;;
  stop)
        stop
        ;;
  status)
        status
        ;;
  *)
        usage
        exit 4
        ;;
esac
exit 0

