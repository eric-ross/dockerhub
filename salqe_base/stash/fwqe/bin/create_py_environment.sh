#!/bin/bash
cd $HOME
virtualenv --system-site-packages iws_python
OLDPATH=$PATH
export PATH=$HOME/iws_python/bin:$PATH
#easy_install egg1
#easy_install egg2
#  .. etc.
if (echo $OLDPATH | grep $HOME/iws_python/bin > /dev/null)
then
  echo Path already installed in .bashrc
else
  echo "export PATH=$PATH" >> ~/.bashrc
fi
