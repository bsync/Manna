#!/bin/bash
sudo apt update
sudo apt install docker.io make
sudo systemctl start docker
sudo systemctl enable docker
sudo curl -L https://github.com/docker/compose/releases/download/1.21.2/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
git clone https://github.com/bsync/Manna.git
sudo groupadd docker
sudo usermod -aG docker $USER
echo "Logout and back on to use docker without sudo"
