from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.contrib.auth import get_user_model
from srcOptics.models import Organization
import os, getpass


class Command(BaseCommand):
    help = 'Initializes DB and creates an admin account'
    def add_arguments(self, parser):
        parser.add_argument('-e', '--easy', action='store_true', help='Run in easy mode. Creates account admin / password')
    def handle(self, *args, **kwargs):
        os.system('dropdb srcopt; createdb srcopt')
        call_command('makemigrations')
        call_command('migrate')
        if kwargs['easy']:
            username = 'admin'
            email =  ''
            password = 'password'
        else:
            print('Create an admin account')
            username = input('Username: ')
            email = input('Email: ')
            while True:
                password = getpass.getpass(prompt='Password: ')
                if password == '':
                    print('Password cannot be empty!')
                    continue
                confirm = getpass.getpass(prompt='Password (again): ')
                if password == confirm:
                    break
                else:
                    print('Passwords do not match!')
        
        User = get_user_model()
        admin = User.objects.create_superuser(username, email, password)
        org = Organization.objects.create(name="root")
        #org.admins.set(admin)
