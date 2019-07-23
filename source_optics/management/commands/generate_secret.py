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

import os

from cryptography import fernet
from django.conf import settings
from django.core.management.base import BaseCommand

# FIXME: always create secret if it does not exist
# FIXME: only create the org if there are no organizations


class Command(BaseCommand):
    help = 'Initializes DB and creates an admin account'

    def handle(self, *args, **kwargs):

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
