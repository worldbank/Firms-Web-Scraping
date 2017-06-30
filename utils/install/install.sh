#!/bin/bash

# installs basic libraries needed, may take quite a while
echo 'We have to install several libraries: docker, docker-compose, git, NextML and a Python 3 virtual environment ...'
read -p "Do you want to run this script? Y/N " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then

echo '(1) Installing docker...'
sudo apt-get -y install docker
echo

echo '(2) Installing docker-compose'
#sudo apt-get -y install docker-compose
echo

echo '(3) Installing git'
sudo apt-get -y install git
echo

echo '(4) Fetching NextML from the World Bank private github repository ...'
#git clone https://github.com/worldbank/NEXT
echo

echo '(5) Fetching Firms Web Scraping from the World Bank private repository ...'
#git clone https://github.com/worldbank/Firms-Web-Scraping
echo

echo '(6) Installing Python 3 requirements for Firms Web Scraping into "firms" virtual environment'
virtualenv -q -p python3 firms
firms/bin/pip install -r Firms-Web-Scraping/requirements.txt
echo

fi
