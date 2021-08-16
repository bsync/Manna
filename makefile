test:
	python -m pytest tests.py

production: 
	docker-compose -f docker-compose.yml -f docker-compose.pro.yml up ${FLAGS}

down:
	docker-compose down

restart:
	docker-compose -f docker-compose.yml -f docker-compose.pro.yml restart manna

dev:
	docker-compose stop manna
	docker-compose -f docker-compose.yml -f docker-compose.local.yml \
		run \
		-e FLASK_DEBUG=0 \
		-e WORKERS=1 \
		-e FLASK_ENV="development" \
		--name mannadbg \
		--service-ports \
		--rm \
		manna ash

debug_pro:
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

