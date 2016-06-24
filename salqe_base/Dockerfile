FROM centos:6.8
COPY stash/etc/fstab /etc/fstab
COPY stash/fwqe /fwqe
COPY stash/etc/yum.repos.d/* /etc/yum.repos.d/.
RUN yum install -y sudo 
RUN yum install -y util-linux-ng
RUN echo "trex    ALL=(ALL)       ALL" > /etc/sudoers.d/trex
RUN groupadd -g 58700 testexec
RUN adduser -g testexec -m -u 58750 trex
RUN echo trex:growth | chpasswd
ENV PATH=/fwqe/tools/bin:$PATH
RUN /bin/bash

