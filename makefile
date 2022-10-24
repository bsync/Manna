DETACH=-d
TARGETS=
OVERRIDE=debug

production: 
	docker-compose -f docker/docker-compose.yml up ${DETACH} ${TARGETS}

test: 
	docker-compose -f docker/docker-compose.yml -f docker/docker-compose.test.yml up ${TARGETS}

dev:
	docker-compose -f docker/docker-compose.yml -f docker/docker-compose.${OVERRIDE}.yml up ${DETACH} ${TARGETS}

mdev:
	docker-compose -f docker/docker-compose.yml -f docker/docker-compose.${OVERRIDE}.yml stop manna
	docker-compose -f docker/docker-compose.yml -f docker/docker-compose.${OVERRIDE}.yml run --rm manna bash

restart:
	docker-compose -f docker/docker-compose.yml -f docker/docker-compose.${OVERRIDE}.yml restart ${TARGETS}

build:
	docker-compose -f docker/docker-compose.yml  build ${TARGETS}

down:
	docker-compose -f docker/docker-compose.yml down

# Rules to dump production volumes
pro_dump: 
	cd backups; ./transfer_volumes.sh -d PROSERVER

