#!/bin/bash
TEMPLOG=/tmp/usermount$$
function cleanup() {
  rm -f ${TEMPLOG}
}

VERSIONINFO=`cat /fwqe/tools/etc/fwqe_version`
COPYRIGHT=`cat /fwqe/tools/etc/copyright`

trap cleanup 0
(
cat <<EOF
$COPYRIGHT

Welcome to the FWQE Solution Testing Environment.
$VERSIONINFO

Before running tests you will want to do the following:

1) Mount Test Repository
2) Build Libs

Problems with this environment should be submitted as a ticket to:
https://sal.vcd.hp.com/fwqe/newticket

EOF
) > ${TEMPLOG}
msg ${TEMPLOG}
