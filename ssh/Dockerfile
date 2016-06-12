# sshd
#
# VERSION               0.0.2

FROM ubuntu:16.04
MAINTAINER Eric Ross <epr@evross.com>

RUN apt-get update && apt-get install -y openssh-server sudo
RUN mkdir /var/run/sshd
RUN useradd ericadmin
RUN usermod -a -G sudo ericadmin
RUN echo 'ericadmin:screencast' | chpasswd

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
