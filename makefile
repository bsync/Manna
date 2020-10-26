test:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml run manna pytest tests.py

production: 
	docker-compose up -d

dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

down:
	docker-compose down

build_pro_nginx:
	docker-compose -f docker-compose.yml \
						-f docker-compose.build.yml build nginx

build_dev_nginx:
	docker-compose -f docker-compose.yml \
						-f docker-compose.dev.yml build nginx

build_manna:
	docker-compose -f docker-compose.yml \
						-f docker-compose.build.yml build manna

restart:
	docker-compose restart manna nginx

debug:
	docker-compose stop manna
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml run \
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

