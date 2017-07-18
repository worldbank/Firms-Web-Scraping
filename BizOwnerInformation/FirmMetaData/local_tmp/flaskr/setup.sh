echo "[Must be run with sudo!]"
echo "... installing mongo db ..."

# Note: The NextML system (under Docker) needs to communicate with Mongo DB
# so that we can remove and add verified business submissions.
#
# This requires that the containers be able to "see" Mongo DB. The NextML containers
# live on the `docker0` network (in the host). So, on the host, Mongo DB needs to
# also listen on docker0 (172.17.0.0 on my system).
# see: https://stackoverflow.com/questions/29109134/how-to-set-mongod-conf-bind-ip-with-multiple-ip-address
# see: https://docs.mongodb.com/manual/reference/configuration-options/#net-options
#
# for binding mongo db to multiple databases, this needs to be set in /etc/mongd.conf
# currently setting this up (throwing code=exited, status=48)
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
sudo systemctl start mongodb
sudo systemctl status mongodb
sudo systemctl enable mongodb

# note: installing python 3 like this may not be needed if run on same system as
# Firm Web Scraping.
echo " ... install python-pip ..."
sudo apt-get -y install python3-pip
pip3 install pip3 --upgrade

echo " ... installing the firm meta data web app"
sudo -H pip3 install -e /home/ubuntu/Firms-Web-Scraping/BizOwnerInformation/FirmMetaData/local_tmp/flaskr/

echo " ... finished setting up system ..."
echo " ... to start the Firm Meta Data Crowd Scraping system, run ./run.sh ..."
echo " ... to view the front end HIT page, go to http://<instance dns name>/hit..."
