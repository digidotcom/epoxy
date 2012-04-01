# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

"""Encapsulate details related to configuration loading

All configuration eventually gets mapped down to a data structure consisting
of a few very basic types.  Classes in this module provide some different
methods for loading such a configuration from different resources.

"""
import os
import six
from epoxy.utils import load_module


class YamlConfigurationLoader(object):
    """Load configuration from a yaml file"""

    def __init__(self, base_file):
        import yaml
        self.yaml = yaml
        self.base_file = base_file

    def _load_from_filename(self, filename):
        f = open(filename, "rb")
        try:
            res = self.yaml.load(f)
        finally:
            f.close()
        return res

    def _merge_yaml(self, config1, config2):
        config1_components = config1.get('components', {})
        config2_components = config2.get('components', {})
        for key, value in six.iteritems(config2_components):
            config1_components[key] = value
        for key, value in list(config2.items()):
            if key != "components":
                config1[key] = value
        config1['components'] = config1_components
        return config1

    def _load_from_yaml_helper(self, root_yaml):
        yaml_this_layer = self._load_from_filename(root_yaml)
        root_yaml_directory = os.path.dirname(root_yaml)
        unified_config = {}
        for extension_file in yaml_this_layer.get('extends', []):
            extension_path = os.path.join(root_yaml_directory, extension_file)
            parent_layer = self._load_from_yaml_helper(extension_path)
            self._merge_yaml(unified_config, parent_layer)
        self._merge_yaml(unified_config, yaml_this_layer)
        return unified_config

    def load_configuration(self):
        data = self._load_from_yaml_helper(self.base_file)
        return data


class PythonLoader(object):
    """Given a path in the form <path.to.module:variable_name> load config"""

    def __init__(self, path):
        module_path, variable_name = path.split(':', 1)
        self.module_path = module_path
        self.variable_name = variable_name

    def load_configuration(self):
        module = load_module(self.module_path)
        return getattr(module, self.variable_name)
