DETACH=-d
TARGETS=
DEVMODE=debug

production: 
	docker-compose -f docker/docker-compose.yml up ${DETACH} ${TARGETS}

dev:
	docker-compose -f docker/docker-compose.yml -f docker/docker-compose.${DEVMODE}.yml up ${DETACH} ${TARGETS}

mdev:
	docker-compose -f docker/docker-compose.yml -f docker/docker-compose.debug.yml stop manna
	docker-compose -f docker/docker-compose.yml -f docker/docker-compose.debug.yml run --rm manna bash

restart:
	docker-compose -f docker/docker-compose.yml -f docker/docker-compose.${DEVMODE}.yml restart ${TARGETS}

build:
	docker-compose -f docker/docker-compose.yml -f docker/docker-compose.${DEVMODE}.yml build ${TARGETS}

down:
	docker-compose -f docker/docker-compose.yml down

# Rules to dump production volumes
pro_dump: 
	cd backups; ./transfer_volumes.sh -d PROSERVER

