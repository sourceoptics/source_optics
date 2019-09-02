# Copyright 2018-2019 SourceOptics Project Contributors
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
#
#  -------------------------------------------------------------------------
#  secrets.py - cloaks and decloaks secrets
#  --------------------------------------------------------------------------

from ..plugin_loader import PluginLoader


class SecretsManager(object):

    HEADER = "[SRCOPT-CLOAK]"

    def __init__(self):
        self.plugin_loader = PluginLoader()
        self.plugins = self.plugin_loader.get_secrets_plugins()

    def is_cloaked(self, msg):
        """
        is the given message encrypted?
        """
        if not msg:
            return False
        return msg.startswith(self.HEADER)

    def uncloak(self, msg):
        """
        return the unencrypted message, don't unencrypt twice
        """
        if not self.is_cloaked(msg):
            return msg
        else:
            for plugin in self.plugins:
                if plugin.recognizes(msg):
                    return plugin.decloak(msg)
            raise Exception("no plugin found to decloak value")

    def cloak(self, msg):
        """
        encrypt the value if it is not already encrypted
        """
        if not msg or self.is_cloaked(msg) or len(self.plugins) == 0:
            return msg
        return self.plugins[0].cloak(msg)
