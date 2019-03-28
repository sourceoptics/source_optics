#Got some of this makefile from https://gist.github.com/magopian/4077998


# target: help - Display callable targets.
help:
	@egrep "^# target:" [Mm]akefile

# target: test - calls the "test" django command
test:
	django-admin.py test --settings=$(TEST_SETTINGS)

# target: update - install (and update) pip requirements
update:
	pip install -U -r requirements.txt

# target: migrate - updates database schema
migrate:
	python manage.py makemigrations
	python manage.py migrate

# target: server - runs application servero
server:
	python manage.py runserver

# target: install - initializes starting database
install:
	python manage.py init -es

# target: compilecss - compiles minified CSS files from SASS files in static directory
compilecss:
	sass --update --sourcemap=none --style compressed srcOptics/static/_scss:srcOptics/static
