#Got some of this makefile from https://gist.github.com/magopian/4077998


# target: help - Display callable targets.
help:
	@egrep "^# target:" [Mm]akefile

test:
	python3 manage.py test

update:
	pip3 install -U -r requirements.txt

migrate:
	python3 manage.py makemigrations
	python3 manage.py migrate

server:
	python3 manage.py runserver

install:
	python3 manage.py init -es

compilecss:
	sass --update --sourcemap=none --style compressed srcOptics/static/_scss:srcOptics/static
