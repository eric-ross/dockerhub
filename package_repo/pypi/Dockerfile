from package_repo:latest
MAINTAINER eric.ross@hp.com

ADD conf/* /etc/pypi/conf/
ADD bin/* /usr/local/bin/
ADD docs/* /etc/pypi/docs/
ADD Dockerfile /etc/Dockerfile
RUN bash -c "mkdir /logs /pypi"
RUN pip install cryptography
RUN pip install passlib
RUN pip install pypiserver
EXPOSE 80
ENTRYPOINT /usr/local/bin/startpypi.sh


