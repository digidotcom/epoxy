# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

from epoxy.component import Component, Dependency
from epoxy.configuration import YamlConfigurationLoader
from epoxy.core import ComponentManager
from epoxy import core as epoxy_core
from epoxy.settings import StringSetting
import os
import unittest
import mock

VALID_TEST_YAML = os.path.join(os.path.dirname(__file__), "test_valid.yaml")
INVALID_TEST_YAML = os.path.join(os.path.dirname(__file__), "test_invalid.yaml")


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

    def setUp(self):
        self.mgr = ComponentManager()
        self.loader = YamlConfigurationLoader(VALID_TEST_YAML)
        self.invalid_loader = YamlConfigurationLoader(INVALID_TEST_YAML)
        self.log = mock.Mock()
        epoxy_core.log = self.log

    def test_graph_ordering(self):
        graph = self.mgr.build_component_graph(self.loader.load_configuration())
        ordering = graph.get_ordering()
        o = [x.name for x in ordering]
        self.assertEqual(len(ordering), 5)  # our 4 plus component_manager
        self.assert_(o.index("b") > o.index("a"))
        self.assert_(o.index("c") > o.index("a"))
        self.assert_(o.index("d") > o.index("c"))

    def test_graph_construction(self):
        self.mgr.launch_configuration(self.loader.load_configuration())
        a = self.mgr.components["a"]
        b = self.mgr.components["b"]
        c = self.mgr.components["c"]
        d = self.mgr.components["d"]
        self.assertEqual(a.previous, None)
        self.assertEqual(b.previous, a)
        self.assertEqual(c.previous, a)
        self.assertEqual(d.previous, c)

    def test_subgraph_construction(self):
        self.mgr.launch_subgraph(self.loader.load_configuration(), 'd:main')

        a = self.mgr.components["a"]
        with self.assertRaises(KeyError):
            self.mgr.components["b"]
        c = self.mgr.components["c"]
        d = self.mgr.components["d"]

        self.assertEqual(a.previous, None)
        self.assertEqual(c.previous, a)
        self.assertEqual(d.previous, c)

        self.assertFalse(a.is_main)
        self.assertFalse(c.is_main)
        self.assertTrue(d.is_main)

    def test_subgraph_bad_entry_point(self):
        with self.assertRaises(AttributeError):
            self.mgr.launch_subgraph(self.loader.load_configuration(), 'd:fake')
        last_log_message = self.log.call_args_list[0][0][0]
        self.assertEqual(last_log_message, "Bad entry point 'd:fake'")

    def test_bad_entry_point(self):
        cfg = self.invalid_loader.load_configuration()
        with self.assertRaises(AttributeError):
            self.mgr.launch_configuration(cfg)
        last_log_message = self.log.call_args_list[0][0][0]
        self.assertEqual(last_log_message, "Bad entry point 'a:fake_method'")

    def test_entry_point(self):
        configuration = self.loader.load_configuration()

        # Add entry-point to configuration
        configuration['entry-point'] = 'd:main'

        self.mgr.launch_configuration(configuration)

        a = self.mgr.components["a"]
        b = self.mgr.components["b"]
        c = self.mgr.components["c"]
        d = self.mgr.components["d"]

        self.assertFalse(a.is_main)
        self.assertFalse(b.is_main)
        self.assertFalse(c.is_main)
        self.assertTrue(d.is_main)

    def test_invalid_class(self):
        configuration = self.loader.load_configuration()

        # Change class to invalid component
        invalid_comp = 'epoxy.test.test_core:InvalidComponent'
        configuration['components']['a']['class'] = invalid_comp

        with self.assertRaises(AttributeError):
            self.mgr.launch_subgraph(configuration, 'd:main')
        last_logged_msg = self.log.call_args_list[0][0][0]
        self.assertEqual(last_logged_msg,
                         "Class path '%s' is invalid, check your epoxy config" % invalid_comp)

    def test_missing_component(self):
        configuration = self.loader.load_configuration()

        # Delete required component
        del configuration['components']['a']

        with self.assertRaises(ValueError):
            self.mgr.launch_subgraph(configuration, 'd:main')

    def test_cycle_detection(self):
        configuration = self.loader.load_configuration()

        # Change class to invalid component
        configuration['components']['a']['dependencies'] = {'previous': 'd'}

        with self.assertRaises(ValueError):
            self.mgr.launch_configuration(configuration)

    def test_subgraph_cycle_detection(self):
        configuration = self.loader.load_configuration()

        # Change class to invalid component
        configuration['components']['a']['dependencies'] = {'previous': 'd'}

        with self.assertRaises(ValueError):
            self.mgr.launch_subgraph(configuration, 'd:main')

    def test_settings(self):
        config = self.loader.load_configuration()
        self.mgr.launch_configuration(config)
        a = self.mgr.components["a"]
        b = self.mgr.components["b"]
        c = self.mgr.components["c"]
        d = self.mgr.components["d"]
        self.assertEqual(a.name, 'alfred')
        self.assertEqual(b.name, 'barry')
        self.assertEqual(c.name, 'charles')
        self.assertEqual(d.name, 'daniel')


if __name__ == '__main__':
    unittest.main()
