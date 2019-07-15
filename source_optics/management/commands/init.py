# Copyright 2018 SourceOptics Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.conf import settings
from ... models import Organization
import os, getpass, subprocess
from cryptography import fernet


class Command(BaseCommand):
    help = 'Initializes DB and creates an admin account'

    def add_arguments(self, parser):
        parser.add_argument('-e', '--easy', action='store_true', help='Run in easy mode. Creates account admin / password')
        parser.add_argument('-s', '--secret', action='store_true', help='Generate SYMMETRIC_SECRET_KEY for password encryption')

    def handle(self, *args, **kwargs):

        subprocess.call('rm -rf', shell=True)
        try:
            subprocess.call('dropdb srcopt', shell=True)
        except OSError:
            pass

        subprocess.call('createdb srcopt', shell=True)

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

        # if we are regenerating the key
        if kwargs['secret']:
            # create the directory if it doesn't exist
            dirname = os.path.dirname(settings.SYMMETRIC_SECRET_KEY)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            if os.path.exists(settings.SYMMETRIC_SECRET_KEY):
                print("WARNING: running this command again would render some secrets in the database unreadable")
                print("if you wish to proceed, delete %s manually first" % settings.SYMMETRIC_SECRET_KEY)
            else:
                # our symmetric key for password encryption
                fern = fernet.Fernet.generate_key()
                fd = open(settings.SYMMETRIC_SECRET_KEY, "w+")
                fd.write("%s" % fern.decode('utf-8'))
                fd.close()
        
        User = get_user_model()
        admin = User.objects.create_superuser(username, email, password)
        org = Organization.objects.create(name="root")
        #org.admins.set(admin)
