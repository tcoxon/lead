FROM phusion/baseimage
MAINTAINER Bytten Studio "bytten.games@gmail.com"
RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential unzip lighttpd python-flup
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

RUN mkdir -p /app/log
EXPOSE 5001

CMD ["/sbin/my_init"]

RUN mkdir /etc/service/lighttpd
ADD docker/lighttpd.sh /etc/service/lighttpd/run
RUN adduser --disabled-password --disabled-login --no-create-home www
RUN chown -R www /app/log
