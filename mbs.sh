#!/bin/bash
sudo apt update
sudo apt install docker.io make
sudo systemctl start docker
sudo systemctl enable docker
sudo curl -L https://github.com/docker/compose/releases/download/1.21.2/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
sudo groupadd docker
sudo usermod -aG docker $USER
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo "To make swap file permanent you need to update /etc/fstab with"
echo "echo '/swapfile   none    swap    sw    0   0' >> /etc/fstab"
echo "Also, logout and back on to use docker without sudo"
