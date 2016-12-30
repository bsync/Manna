.SILENT:

.PHONY: instructions
instructions: venv
	@echo "First source the virtual environment ('source venv/bin/activate')!"

venv:
	[ $$(which virtualenv) ] || sudo pip install virtualenv
	virtualenv venv
	. venv/bin/activate; pip install -r requirements.txt

.PHONY: avenv
active_venv: venv
	@if [ ! $$VIRTUAL_ENV ]; then \
		echo "Virtual Environment not set:"; $(MAKE) instructions; exit 1; \
	fi
	@if [ $$(dirname $$VIRTUAL_ENV) = $$(dirname venv) ]; then \
		echo "Virtual Environment not correct:"; $(MAKE) instructions; exit 2; \
	fi

mannadev: active_venv
	FLASK_APP=manna.py FLASK_DEBUG=1 flask run 
	
mannadock:
	docker run -it --net=host -v $(PWD):/code -v /media/jthorine/logostore/Pleroma/lessons:/code/lessons alpython:v5_flaskrun

print-%:
	@echo '$*=$($*)'
