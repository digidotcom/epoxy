# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

from epoxy.component import Component, Dependency
from epoxy.configuration import YamlConfigurationLoader
from epoxy.core import ComponentManager
import os
import unittest


class TestDependencyComponent(Component):
    next = Dependency(required=False)


class TestConfiguration(unittest.TestCase):

    def test_configuration_extension(self):
        mgr = ComponentManager()
        loader = YamlConfigurationLoader(
            os.path.join(os.path.dirname(__file__),
                         "test_configuration_child.yml"))
        mgr.launch_configuration(loader.load_configuration(), debug=3)
        a = mgr.components["a"]
        b = mgr.components["b"]

        self.assertEqual(b.next, a)

if __name__ == '__main__':
    unittest.main()
