production: 
	docker-compose -f docker-compose.yml -f docker-compose.pro.yml up ${FLAGS}

dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up ${FLAGS}

down:
	docker-compose down

build_manna:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml build manna

restart:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart manna

debug:
	docker-compose stop manna
	docker-compose -f docker-compose.yml -f docker-compose.pro.yml run \
		-e FLASK_DEBUG=0 \
		-e WORKERS=1 \
		--name mannadbg \
		--service-ports \
		--rm manna
			   
shell:
	docker-compose run --rm --entrypoint ash manna

# Rules to dump production volumes
pro_dump: 
	cd backups; ./transfer_volumes.sh -d PROSERVER

