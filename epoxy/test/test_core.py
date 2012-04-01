# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

from epoxy.component import Component, Dependency
from epoxy.configuration import YamlConfigurationLoader
from epoxy.core import ComponentManager
from epoxy.settings import StringSetting
import os
import unittest


class TestComponent(Component):

    _comp_instantiation_counter = 0

    previous = Dependency(required=False)

    name = StringSetting(required=True,
                         help="Name of this component")

    def __init__(self):
        self.is_main = False
        if self.previous is None:
            self.count = 0
        else:
            self.count = self.previous.count + 1

    def main(self):
        self.is_main = True


class TestDependencyGraphResolution(unittest.TestCase):

    def test_graph_ordering(self):
        mgr = ComponentManager()
        loader = YamlConfigurationLoader(
            os.path.join(os.path.dirname(__file__), "test.yml"))
        graph = mgr.build_component_graph(loader.load_configuration())
        ordering = graph.get_ordering()
        o = [x.name for x in ordering]
        self.assertEqual(len(ordering), 5)  # our 4 plus component_manager
        self.assert_(o.index("b") > o.index("a"))
        self.assert_(o.index("c") > o.index("a"))
        self.assert_(o.index("d") > o.index("c"))

    def test_graph_construction(self):
        mgr = ComponentManager()
        loader = YamlConfigurationLoader(
            os.path.join(os.path.dirname(__file__), "test.yml"))
        mgr.launch_configuration(loader.load_configuration())
        a = mgr.components["a"]
        b = mgr.components["b"]
        c = mgr.components["c"]
        d = mgr.components["d"]
        self.assertEqual(a.previous, None)
        self.assertEqual(b.previous, a)
        self.assertEqual(c.previous, a)
        self.assertEqual(d.previous, c)

    def test_subgraph_construction(self):
        mgr = ComponentManager()
        loader = YamlConfigurationLoader(
            os.path.join(os.path.dirname(__file__), "test.yml"))
        mgr.launch_subgraph(loader.load_configuration(), 'd:main')

        a = mgr.components["a"]
        with self.assertRaises(KeyError):
            mgr.components["b"]
        c = mgr.components["c"]
        d = mgr.components["d"]

        self.assertEqual(a.previous, None)
        self.assertEqual(c.previous, a)
        self.assertEqual(d.previous, c)

        self.assertFalse(a.is_main)
        self.assertFalse(c.is_main)
        self.assertTrue(d.is_main)

    def test_entry_point(self):
        mgr = ComponentManager()
        loader = YamlConfigurationLoader(
            os.path.join(os.path.dirname(__file__), "test.yml"))
        configuration = loader.load_configuration()

        # Add entry-point to configuration
        configuration['entry-point'] = 'd:main'

        mgr.launch_configuration(configuration)

        a = mgr.components["a"]
        b = mgr.components["b"]
        c = mgr.components["c"]
        d = mgr.components["d"]

        self.assertFalse(a.is_main)
        self.assertFalse(b.is_main)
        self.assertFalse(c.is_main)
        self.assertTrue(d.is_main)

    def test_invalid_class(self):
        mgr = ComponentManager()
        loader = YamlConfigurationLoader(
            os.path.join(os.path.dirname(__file__), "test.yml"))
        configuration = loader.load_configuration()

        # Change class to invalid component
        configuration['components']['a']['class'] = \
            'epoxy.test.test_core:InvalidComponent'

        with self.assertRaises(AttributeError):
            mgr.launch_subgraph(configuration, 'd:main')

    def test_missing_component(self):
        mgr = ComponentManager()
        loader = YamlConfigurationLoader(
            os.path.join(os.path.dirname(__file__), "test.yml"))
        configuration = loader.load_configuration()

        # Delete required component
        del configuration['components']['a']

        with self.assertRaises(ValueError):
            mgr.launch_subgraph(configuration, 'd:main')

    def test_cycle_detection(self):
        mgr = ComponentManager()
        loader = YamlConfigurationLoader(
            os.path.join(os.path.dirname(__file__), "test.yml"))
        configuration = loader.load_configuration()

        # Change class to invalid component
        configuration['components']['a']['dependencies'] = {'previous': 'd'}

        with self.assertRaises(ValueError):
            mgr.launch_configuration(configuration)

    def test_subgraph_cycle_detection(self):
        mgr = ComponentManager()
        loader = YamlConfigurationLoader(
            os.path.join(os.path.dirname(__file__), "test.yml"))
        configuration = loader.load_configuration()

        # Change class to invalid component
        configuration['components']['a']['dependencies'] = {'previous': 'd'}

        with self.assertRaises(ValueError):
            mgr.launch_subgraph(configuration, 'd:main')


if __name__ == '__main__':
    unittest.main()
