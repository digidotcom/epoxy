# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

from epoxy.component import Component, Dependency
from epoxy.settings import StringSetting
import unittest


class TestDependencyComponent(Component):

    next = Dependency(required=False)

    def __init__(self):
        self.is_started = False

    def start(self):
        if self.is_started:
            raise ValueError
        self.is_started = True


class TestRequiredDependencyComponent(Component):
    dependency = Dependency(required=True)


class TestRequiredSettingComponent(Component):
    setting = StringSetting(required=True)


class TestComponent(unittest.TestCase):

    def test_start_with_deps(self):
        # d->c->b->a->

        a = TestDependencyComponent.from_dependencies()
        b = TestDependencyComponent.from_dependencies(next=a)
        c = TestDependencyComponent.from_dependencies(next=b)
        d = TestDependencyComponent.from_dependencies(next=c)

        self.assertListEqual([X.is_started for X in [a, b, c, d]],
                             [False] * 4)

        d.start_with_deps()

        self.assertListEqual([X.is_started for X in [a, b, c, d]],
                             [True] * 4)

    def test_invalid_dependency(self):
        a = TestDependencyComponent.from_dependencies()
        with self.assertRaises(ValueError):
            TestDependencyComponent.from_dependencies(not_real_dependency=1,
                                                      next=a)

    def test_missing_dependency(self):
        with self.assertRaises(ValueError):
            TestRequiredDependencyComponent.from_dependencies()

    def test_missing_setting(self):
        with self.assertRaises(ValueError):
            TestRequiredSettingComponent.from_dependencies()


if __name__ == '__main__':
    unittest.main()
