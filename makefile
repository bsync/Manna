up: 
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build nginx manna

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

transfer_to_dev:
	docker run --rm -v nginx_secrets:/from alpine ash -c "cd /from ; tar -cf - . " | ssh dev.tullahomabiblechurch.org 'docker run --rm -i -v nginx_secrets:/to alpine ash -c "cd /to ; tar -xpvf - " '

