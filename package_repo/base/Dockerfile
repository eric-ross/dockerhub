from ubuntu:16.04
MAINTAINER eric.ross@hp.com
ENV http_proxy=http://web-proxy.austin.hpicorp.net:8080 https_proxy=http://web-proxy.austin.hpicorp.net:8080 no_proxy=hp.com,hpicorp.net
ARG DEBIAN_FRONTEND=noninteractive
ADD certs/* /root/certs/
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get install -y build-essential
RUN apt-get install -y python-dev
RUN apt-get install -y python-pip
RUN apt-get install -y libssl-dev
RUN apt-get install -y python-setuptools
RUN apt-get install -y vim
RUN apt-get install -y libffi-dev
RUN pip install --upgrade pip
RUN pip install --upgrade virtualenv
RUN pip install cryptography
RUN bash -c "cat /root/certs/* >> /etc/ssl/certs/ca-certificates.crt"
EXPOSE 80
ENTRYPOINT /bin/bash


