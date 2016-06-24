#!/bin/env python
################################################################################
#
#
# (C) Copyright 2013 Hewlett-Packard Development Company, L.P.
#
#
# File Name :  NetworkProxy.py
#
# Purpose:
# - output the bash commands necessary for setting the required proxy vars.
#   This script depends on a missing or correctly configured .salqeconfig
#
#
################################################################################
# Release Notes:
#
# ----- May/23/2013 - Eric Ross  ------------------------------------------
#
################################################################################
#
#  Add the 'network.zone' configuration to the .salqeconfig file
#
#  This config will be used to drive any network dependent scripts (such as proxy configuration)

import json
import os

proxies = {'vancouver':
                ['export http_proxy=http://squid.vcd.hp.com:3128',
                 'export https_proxy=http://squid.vcd.hp.com:3128',
                 'export HTTP_PROXY=http://squid.vcd.hp.com:3128',
                 'export no_proxy=127.0.0.1,localhost,hp.com'],
           'hp':
               ['export http_proxy=http://proxy.houston.hp.com:8080',
                'export https_proxy=http://proxy.houston.hp.com:8080',
                'export HTTP_PROXY=http://proxy.houston.hp.com:8080',
                'export no_proxy=127.0.0.1,localhost,hp.com'],
           'external':['unset http_proxy',
                'unset https_proxy',
                'unset HTTP_PROXY',
                'unset no_proxy']
}
try:
    with open(os.environ['HOME']+'/.salqeconfig','r') as f:
        config = json.load(f)
        if 'network.zone' not in config:
            zone = 'vancouver'
        else:
            zone = config['network.zone']
except IOError:
        zone = 'hp'
for i in proxies[zone]:
    print i


