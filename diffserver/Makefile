.PHONY: run syncdb test shell

export PYTHONPATH:=$(shell pwd)
export DJANGO_SETTINGS_MODULE:=settings
export PORT=8200

run:
	python manage.py runserver $(PORT)

syncdb:
	python manage.py syncdb

test:
	python manage.py test diffapp

shell:
	python manage.py shell
