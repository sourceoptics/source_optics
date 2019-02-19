FROM ubuntu:latest

RUN apt-get update;\
apt-get install -y python3.6;\
apt-get install -y postgresql postgresql-contrib;\
apt-get install -y python-setuptools python-dev build-essential;\
apt-get install -y python3-pip;\
pip3 install django;\
alias python=python3

RUN mkdir /home/srcOptics
WORKDIR /home/srcOptics

RUN apt-get update;\
apt-get install -y git