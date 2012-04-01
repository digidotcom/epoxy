# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

from epoxy.component import Component, Dependency, ComponentList
from epoxy.configuration import YamlConfigurationLoader
from epoxy.core import ComponentManager
import os
import unittest


class TestDependencyListComponent(Component):

    others = Dependency()

    def ping(self):
        return True


class TestDependencyList(unittest.TestCase):

    def test_dependency_list(self):
        mgr = ComponentManager()
        loader = YamlConfigurationLoader(
            os.path.join(os.path.dirname(__file__),
                         "test_dependency_list.yml"))
        mgr.launch_configuration(loader.load_configuration())
        a = mgr.components["a"]
        b = mgr.components["b"]
        c = mgr.components["c"]
        d = mgr.components["d"]

        self.assertListEqual(a.others.get_list(), [b, c, d])

        for comp in (b, c, d):
            self.assertListEqual(comp.others.get_list(), [])

        # list.index implementation
        self.assertEqual(a.others.index(b), 0)
        self.assertEqual(a.others.index(c), 1)
        self.assertEqual(a.others.index(d), 2)

        # list subscript implementation
        self.assertEqual(a.others[0], b)
        self.assertEqual(a.others[1], c)
        self.assertEqual(a.others[2], d)

        # list.count implementation
        self.assertEqual(a.others.count(b), 1)
        self.assertEqual(a.others.count(c), 1)
        self.assertEqual(a.others.count(d), 1)

        # list __reversed__ implementation
        self.assertListEqual(list(reversed(a.others)), [d, c, b])

    def test_missing_item_in_dep_list(self):
        mgr = ComponentManager()
        loader = YamlConfigurationLoader(
            os.path.join(os.path.dirname(__file__),
                         "test_dependency_list.yml"))
        configuration = loader.load_configuration()

        # Delete component b
        del configuration['components']['b']

        with self.assertRaises(ValueError):
            mgr.launch_configuration(configuration)

    def test_component_list_missing(self):
        with self.assertRaises(ValueError):
            ComponentList.from_dependencies(dependency_list=['a'])

    def test_component_list_extra(self):
        with self.assertRaises(ValueError):
            ComponentList.from_dependencies(dependency_list=['a'],
                                            a=1, b=2)

if __name__ == '__main__':
    unittest.main()
