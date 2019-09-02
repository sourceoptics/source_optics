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
#  plugin_loader.py - generic mechanism to load plugins used by all
#  types of plugins. Some plugins return lists, others
#  return dictionaries, it depends on whether they are typically accessed
#  by name or just wrap lots of behaviors which stack additively.
#  --------------------------------------------------------------------------

from importlib import import_module

from django.conf import settings

# in the future not all plugin definitions may required and a partially empty plugins
# list may be ok to enable smooth upgrades. this is the list of required plugins at
# first release ONLY, and some of these plugins, without a definition, mean there is
# no core behavior

REQUIRED_PLUGIN_KEYS = [ 'secrets' ]

class PluginLoader(object):

    def __init__(self):
        self.conf = settings.PLUGIN_CONFIGURATION
        self.check_plugin_configuration()

    def check_plugin_configuration(self):
        for x in REQUIRED_PLUGIN_KEYS:
            if x not in self.conf:
                raise Exception("missing %s configuration in plugin configuration" % x)

    def get_module_instance(self, name, arguments=None):
        imported_module = import_module(name)
        cls = getattr(imported_module, 'Plugin')
        if arguments:
            return cls(arguments)
        else:
            return cls()

    def generic_load(self, section, as_list=False, just_names=False):
        results = dict()
        for (k, v) in self.conf[section].items():
            if not just_names:
                if type(v) == list:
                    results[k] = self.get_module_instance(v[0], v[1])
                else:
                    results[k] = self.get_module_instance(v)
            else:
                results[k] = k
        if as_list or just_names:
            return [ x for x in results.values() ]
        else:
            return results

    def get_secrets_plugins(self):
        return self.generic_load('secrets', as_list=True)

    def get_report_api_plugins(self):
        return self.generic_load('report_api')
