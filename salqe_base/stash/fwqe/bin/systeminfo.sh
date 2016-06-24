#!/bin/bash
TEMPLOG=/tmp/usermount$$
function cleanup() {
  rm -f ${TEMPLOG}
}


trap cleanup 0

(
HOSTNAME=`hostname`
INETINFO=`(ifconfig | grep "inet addr")`
DISKINFO=`df -h`
VERSION=`cat /fwqe/tools/etc/fwqe_version`
NOTES=`cat /fwqe/tools/etc/release_notes`
PROXIES=`env| grep proxy`
cat <<EOF
System Information
Version: $VERSION
Hostname: $HOSTNAME

Problems with this environment should be submitted as a ticket to:
https://sal.vcd.hp.com/fwqe/newticket

==================================
Network:
$INETINFO
$PROXIES

==================================
Disk:
$DISKINFO

EOF
) > ${TEMPLOG}
msg ${TEMPLOG}

