FROM ubuntu:16.04
MAINTAINER Eric Ross eric.ross@hp.com

RUN apt-get -y update && apt-get install -y 
RUN apt-get install -y openssh-server
RUN apt-get install -y net-tools
RUN apt-get install -y couchdb vim
RUN adduser --disabled-password --gecos "" trex
RUN usermod --password $(echo growth | openssl passwd -1 -stdin) trex
RUN usermod -aG sudo trex
RUN mkdir /var/run/couchdb
RUN chown couchdb /var/run/couchdb
RUN echo 'admin = "growth"' >> /etc/couchdb/local.ini
RUN echo '[httpd]' >> /etc/couchdb.local.ini
RUN echo 'bind_address=0.0.0.0' >> /etc/couchdb.local.ini
RUN mkdir /var/run/sshd

CMD /bin/echo "Install completed"
EXPOSE 5984
CMD ["/usr/bin/couchdb"]
