#Got some of this makefile from https://gist.github.com/magopian/4077998


# target: help - Display callable targets.
help:
	@egrep "^# target:" [Mm]akefile

test:
	python3 manage.py test

update:
	pip3 install -U -r requirements.txt

generate_secret:
	python3 manage.py generate_secret

scanner:
	ssh-agent python3 manage.py scan

migrate:
	python3 manage.py makemigrations
	python3 manage.py migrate

server:
	python3 manage.py runserver

compilecss:
	sass --update --sourcemap=none --style compressed srcOptics/static/_scss:srcOptics/static

isort:
	isort -rc .


bug:
	grep BUG -rn source_optics

fixme:
	grep FIXME -rn source_optics

todo:
	grep TODO -rn source_optics

gource:
	gource -s .06 -1280x720 --auto-skip-seconds .1 --hide mouse,progress,filenames --key --multi-sampling --stop-at-end --file-idle-time 0 --max-files 0  --background-colour 000000 --font-size 22 --title "SourceOptics" --output-ppm-stream - --output-framerate 30 | avconv -y -r 30 -f image2pipe -vcodec ppm -i - -b 65536K movie.mp4

uwsgi:
	# FIXME: not tested yet
	uwsgi --http :8003 --wsgi-file source_optics/wsgi.py -H env --plugins python3 --static-map /static=static

clean:
	find . -name '*.pyc' | xargs rm -r
	find . -name '__pycache__' | xargs rm -rf

indent_check:
	pycodestyle --select E111 source_optics/

pyflakes:
	pyflakes source_optics/
	pyflakes source_optics/views/*.py
