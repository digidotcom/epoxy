# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

from epoxy.component import Component, Dependency
from epoxy.configuration import PythonLoader
from epoxy.core import ComponentManager
import unittest


class TestDependencyComponent(Component):
    next = Dependency()


class TestLeafComponent(Component):
    pass


data = {
    'components': {
        'a': {
            'class': 'epoxy.test.test_python_loader:TestLeafComponent',
        },
        'b': {
            'class': 'epoxy.test.test_python_loader:TestDependencyComponent',
            'dependencies': {
                'next': 'a',
            }
        },
        'c': {
            'class': 'epoxy.test.test_python_loader:TestDependencyComponent',
            'dependencies': {
                'next': 'b',
            }
        },
    }
}


class TestPythonLoader(unittest.TestCase):

    def test_dependency_list(self):
        mgr = ComponentManager()
        loader = PythonLoader('epoxy.test.test_python_loader:data')
        mgr.launch_configuration(loader.load_configuration())
        a = mgr.components["a"]
        b = mgr.components["b"]
        c = mgr.components["c"]

        self.assertEqual(b.next, a)
        self.assertEqual(c.next, b)


if __name__ == '__main__':
    unittest.main()
