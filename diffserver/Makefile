.PHONY: run syncdb test shell

export PYTHONPATH:=$(shell pwd)
export DJANGO_SETTINGS_MODULE:=settings

PORT=8200
ERR_LOG=ds.errors.log
PIDFILE=ds.pid



runserver:
	python manage.py runserver $(PORT)

stop:
	@if [ -f $(PIDFILE) ]; \
	then \
		echo "Stabbing process `cat $(PIDFILE)` in the back.."; \
		kill `cat $(PIDFILE)`; \
		echo "Waiting for death screams to stop..."; \
		sleep 3; \
	fi;

run: stop
	python manage.py collectstatic --noinput
	gunicorn --pid=$(PIDFILE) --error-log=$(ERR_LOG) --log-level=debug -b 127.0.0.1:$(PORT) wsgi:application --daemon

syncdb:
	python manage.py syncdb

test:
	python manage.py test diffapp

shell:
	python manage.py shell
