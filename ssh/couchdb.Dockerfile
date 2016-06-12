# couchdb
#
# VERSION               0.0.2

FROM eross77/sshd
MAINTAINER Eric Ross <epr@evross.com>

RUN apt-get update && apt-get install -y couchdb
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

EXPOSE 22
EXPOSE 3958
CMD ["/usr/sbin/sshd", "-D"]
