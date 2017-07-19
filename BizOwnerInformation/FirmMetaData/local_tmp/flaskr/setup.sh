echo "[Must be run with sudo! Assumes Docker is installed as well]"
echo "... installing mongo db ..."

# Note: The NextML system (under Docker) needs to communicate with Mongo DB
# so that we can remove and add verified business submissions.
#
# This requires that the containers be able to "see" Mongo DB. The NextML containers
# live on the `docker0` network (in the host). So, on the host, Mongo DB needs to
# also listen on docker0 (172.17.0.0 on my system).
# see: https://docs.mongodb.com/manual/reference/configuration-options/#net-options
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927
echo "deb http://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.2 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.2.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo echo "[Unit]
Description=High-performance, schema-free document-oriented database
After=network.target

[Service]
User=mongodb
ExecStart=/usr/bin/mongod --quiet --config /etc/mongod.conf

[Install]
WantedBy=multi-user.target" > /etc/systemd/system/mongodb.service

# Modify /etc/mongod.conf to include the docker0 network so
# that NextML can also modify the database (primarily for
# Metadata verification)
export FLASK_IP=$(ip -4 addr show docker0 | grep -Po 'inet \K[\d.]+') # gets docker0 ip
sudo sed -i -e 's|127.0.0.1|'"127.0.0.1,$FLASK_IP"'|g' /etc/mongod.conf

sudo systemctl start mongodb
sudo systemctl status mongodb
sudo systemctl enable mongodb

# note: installing python 3 like this may not be needed if run on same system as
# Firm Web Scraping.
echo " ... install python-pip ..."
sudo apt-get -y install python3-pip
pip3 install pip3 --upgrade

echo " ... installing the firm meta data web app"
# note, not entirely sure what path to use so pip can pick up this webapp but it's either
# this directory or the one below
sudo -H pip3 install -e .

echo " ... finished setting up system ..."
echo " ... to start the Firm Meta Data Crowd Scraping system, run ./run.sh ..."
echo " ... to view the front end HIT page, go to http://<instance dns name>/hit..."
