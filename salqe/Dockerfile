FROM ubuntu:16.04
MAINTAINER Eric Ross eric.ross@hp.com

ENV http_proxy=http://web-proxy.austin.hpicorp.net:8080
ENV https_proxy=http://web-proxy.austin.hpicorp.net:8080
ENV no_proxy=hp.com,hpicorp.net,localhost
RUN apt-get -y update && apt-get upgrade -y 
RUN apt-get install -y apt-utils net-tools
RUN apt-get install -y  openssh-server net-tools vim nano sudo git python
RUN adduser --disabled-password --gecos "" trex
RUN usermod --password $(echo growth | openssl passwd -1 -stdin) trex
RUN usermod -aG sudo trex
RUN mkdir /var/run/sshd
RUN apt-get clean
RUN echo "root   ALL=(ALL) ALL" >> /etc/sudoers
COPY files/proxy.sh /etc/profile.d/proxy.sh
CMD ["su","-","trex"]
