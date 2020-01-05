SHELL=bash

.PHONY: run db
.ONESHELL:

run: db
	@pipenv run flask run

db: mongo
	@ps -ef | grep -v grep | grep -q mongod || \
		./mongo/bin/mongod --dbpath mongo/db --fork --logpath mongo/logs.txt 

mongo: mongodb.tgz
	tar -xzvf mongodb.tgz
	mv mongodb-linux* mongo
	mkdir -p mongo/db

mongodb.tgz: 
	wget -O mongodb.tgz https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-ubuntu1804-4.2.2.tgz

devsession:
	pipenv shell

vimeosession:
	[ ! -v VIMEO_TOKEN ] || . .env
	ipython -m web.vimeoresource -i
