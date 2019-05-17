#Got some of this makefile from https://gist.github.com/magopian/4077998


# target: help - Display callable targets.
help:
	@egrep "^# target:" [Mm]akefile

test:
	python manage.py test

update:
	pip install -U -r requirements.txt

migrate:
	python manage.py makemigrations
	python manage.py migrate

server:
	python manage.py runserver

install:
	python manage.py init -es

compilecss:
	sass --update --sourcemap=none --style compressed srcOptics/static/_scss:srcOptics/static
