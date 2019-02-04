#!/bin/bash
#databse needs to exist first
dropdb srcopt
createdb srcopt
python manage.py migrate
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@myproject.com', 'password')" | python manage.py shell
