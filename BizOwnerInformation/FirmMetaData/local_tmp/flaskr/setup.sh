echo "[Must be run with sudo!]"
echo "... installing mongo db ..."
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

echo " ... install python-pip ..."
sudo apt-get -y install python-pip
pip install pip --upgrade

echo " ... installing the firm meta data web app"
sudo -H pip install -e /home/ubuntu/Firms-Web-Scraping/BizOwnerInformation/FirmMetaData/local_tmp/flaskr/

echo " ... finished setting up system ..."
echo " ... to start the Firm Meta Data Crowd Scraping system, run ./run.sh ..."
echo " ... to view the front end HIT page, go to http://<instance dns name>/hit..."
