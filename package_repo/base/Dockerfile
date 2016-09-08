from python:2
MAINTAINER eric.ross@hp.com
ENV http_proxy=http://web-proxy.austin.hpicorp.net:8080 https_proxy=http://web-proxy.austin.hpicorp.net:8080 no_proxy=hp.com,hpicorp.net
ARG DEBIAN_FRONTEND=noninteractive

RUN pip install --upgrade pip

ADD certs/* /etc/certs/
RUN bash -c "cat /etc/certs/* >> /etc/ssl/certs/ca-certificates.crt"

# include the Dockerfile so that image can be reconstructed.
ADD Dockerfile /etc/Dockerfile
EXPOSE 80
ENTRYPOINT /bin/bash


