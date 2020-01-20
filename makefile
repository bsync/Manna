up: 
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build manna

restart:
	docker-compose restart manna

debug:
	docker-compose stop manna
	docker-compose run \
               -e FLASK_ENV=development \
               -e FLASK_DEBUG=0 \
			   -e WORKERS=1 \
			   --service-ports \
			   --rm manna 
			   
shell:
	docker-compose run --rm --entrypoint ash manna

