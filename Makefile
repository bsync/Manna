.SILENT:

.PHONY: instructions
instructions: venv
	@echo "First source the virtual environment ('source venv/bin/activate')!"
	@echo "Then make one of the following targets:"
	@echo " mannadev - Runs manna flask app locally in debug mode."

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

massah:
	PYTHONPATH=$(shell pwd) py.test --ignore=venv

massah-local:
	PYTHONPATH=$(shell pwd) py.test --ignore=venv -k test_local_catalog

massah-s3:
	PYTHONPATH=$(shell pwd) py.test --ignore=venv -k test_s3_catalog

mannadev: active_venv
	#FLASK_APP=manna.py FLASK_DEBUG=1 flask run 
	PYTHONPATH=$(shell pwd) python manna.py
	
print-%:
	@echo '$*=$($*)'
