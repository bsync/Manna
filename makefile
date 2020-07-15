production: 
	docker-compose up -d

dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

down:
	docker-compose down

build_pro:
	docker-compose build nginx manna

build_dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml build 

restart:
	docker-compose restart manna

debug:
	docker-compose stop manna
	docker-compose run \
		-e FLASK_ENV=development \
		-e FLASK_DEBUG=0 \
		-e WORKERS=1 \
		--name mannadbg \
		--service-ports \
		--rm manna
			   
shell:
	docker-compose run --rm --entrypoint ash manna

# Rules to dump production volumes
pro_dump: 
	cd backups; ./transfer_volumes.sh

