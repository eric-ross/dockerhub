#!/bin/bash
cd $HOME
echo "NOTE:  this will only work if you have created a virtual python"
echo "environment.  Use the create_py_environment.sh command, logout, then"
echo "logon to achieve this task.\n\n"
easy_install -f http://salx.vcd.hp.com/packages salqe
