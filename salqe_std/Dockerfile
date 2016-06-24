FROM eross77/salqe_base
MAINTAINER "Eric Ross <eric.ross@hp.com>
RUN cat /etc/resolv.conf
#RUN yum install -y fwqe-python-libs fwqecups fwqe-pyqt4 fwqe-sip fwqe-git
RUN yum install -y sudo
RUN yum install -y  fwqe-sip fwqe-git
RUN mkdir -p /fwqe/tools/bin
RUN ln -s /fwqe/tools/git/bin/* /fwqe/tools/bin/.
RUN yum install -y fwqe-python-libs fwqecups 
RUN ln -s /fwqe/tools/python-2.7/bin/* /fwqe/tools/bin/.
RUN ln -s /fwqe/tools/cups/bin/* /fwqe/tools/bin/.
RUN yum install -y fwqe-pyqt4
ENV PATH=/fwqe/tools/bin:$PATH
CMD /bin/bash

