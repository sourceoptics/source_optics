from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.contrib.auth import get_user_model
from srcOptics.models import Organization
import os


class Command(BaseCommand):
    help = 'Initializes DB and creates an admin account'
        
    def handle(self, *args, **kwargs):
        os.system('dropdb srcopt; createdb srcopt')
        call_command('makemigrations')
        call_command('migrate')
        print('Create an admin account')
        username = input('Username: ')
        email = input('Email: ')
        while True:
            password = input('Password: ')
            if password == '':
                print('Password cannot be empty!')
                continue
            confirm = input('Password (again): ')
            if password == confirm:
                break
            else:
                print('Passwords do not match!')
        User = get_user_model()
        admin = User.objects.create_superuser(username, email, password)
        org = Organization.objects.create(name="root")
        #org.admins.set(admin)
