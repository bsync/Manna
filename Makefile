SHELL=bash

.PHONY: run
.ONESHELL:

run:
	flask run

vimeosession:
	[ ! -v VIMEO_TOKEN ] || . .env
	ipython -m web.vimeoresource -i
