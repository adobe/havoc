FROM python:latest
MAINTAINER Julien Fabre <julien.fabre@tubemogul.com>

RUN echo deb http://httpredir.debian.org/debian jessie-backports main | \
      sed 's/\(.*\)-sloppy \(.*\)/&@\1 \2/' | tr @ '\n' | \
      tee /etc/apt/sources.list.d/backports.list

RUN apt-get -y update && apt-get install -y haproxy -t jessie-backports

ADD . /havoc

WORKDIR /havoc

RUN pip install -r requirements.txt

RUN python setup.py install 
