# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

from epoxy.component import Component
from epoxy.settings import IntegerSetting, StringSetting, BooleanSetting, \
    FloatSetting, ListSetting, DictionarySetting, BaseSetting, SettingInstance
import unittest


class ExampleComponent(Component):
    """
    """

    string_setting = StringSetting()
    integer_setting = IntegerSetting()
    boolean_setting = BooleanSetting()
    float_setting = FloatSetting(required=False)
    list_setting = ListSetting(required=False)
    dictionary_setting = DictionarySetting(required=False)

    def start(self):
        pass


class TestSettings(unittest.TestCase):

    def test_numeric_setting(self):
        svc = ExampleComponent.from_dependencies(
            string_setting=12345,
            integer_setting=12345,
            boolean_setting=12345,
            float_setting=12345,
            list_setting=[1, 2, 3, 4, 5],
            )
        self.assertEqual(svc.string_setting, '12345')
        self.assertEqual(svc.integer_setting, 12345)
        self.assertEqual(svc.boolean_setting, True)
        self.assertAlmostEqual(svc.float_setting, 12345)
        self.assertListEqual(svc.list_setting, [1, 2, 3, 4, 5])

    def test_string_setting(self):
        svc = ExampleComponent.from_dependencies(
            string_setting='12345',
            integer_setting='12345',
            boolean_setting='12345',
            float_setting='12345',
            list_setting='12345',
            dictionary_setting={'1': '2', '3': '4'}
            )
        self.assertEqual(svc.string_setting, '12345')
        self.assertEqual(svc.integer_setting, 12345)
        self.assertEqual(svc.boolean_setting, False)  # Unexpected?
        self.assertAlmostEqual(svc.float_setting, 12345)
        self.assertListEqual(svc.list_setting, ['1', '2', '3', '4', '5'])
        self.assertDictEqual(svc.dictionary_setting, {'1': '2', '3': '4'})

    def test_boolean_setting_true(self):
        svc = ExampleComponent.from_dependencies(
            string_setting='true',
            integer_setting='12345',
            boolean_setting='true',
            )
        self.assertEqual(svc.string_setting, 'true')
        self.assertEqual(svc.integer_setting, 12345)
        self.assertEqual(svc.boolean_setting, True)

    def test_boolean_setting_false(self):
        svc = ExampleComponent.from_dependencies(
            string_setting='false',
            integer_setting='12345',
            boolean_setting='false',
            )
        self.assertEqual(svc.string_setting, 'false')
        self.assertEqual(svc.integer_setting, 12345)
        self.assertEqual(svc.boolean_setting, False)

    def test_boolean_setting_zero(self):
        svc = ExampleComponent.from_dependencies(
            string_setting=0,
            integer_setting=0,
            boolean_setting=0,
            )
        self.assertEqual(svc.string_setting, '0')
        self.assertEqual(svc.integer_setting, 0)
        self.assertEqual(svc.boolean_setting, False)

    def test_encoding(self):
        # Encoding doesn't seem to be used by this library,
        # and is difficult to access as is.  Get rid of it or change it?
        self.assertEqual(
            StringSetting().encode('12345'),
            '12345'
        )
        self.assertEqual(
            IntegerSetting().encode(12345),
            '12345'
        )
        self.assertEqual(
            FloatSetting().encode(12345.6),
            '12345.6'
        )
        self.assertEqual(
            BooleanSetting().encode(True),
            'true'
        )
        self.assertEqual(
            BooleanSetting().encode(False),
            'false'
        )
        self.assertEqual(
            ListSetting().encode([1, 2, 3, 4, 5]),
            '[1, 2, 3, 4, 5]'
        )
        self.assertEqual(
            DictionarySetting().encode({'1': '2'}),
            "{'1': '2'}"
        )

    def test_base_setting(self):
        with self.assertRaises(NotImplementedError):
            BaseSetting().encode('12345')
        with self.assertRaises(NotImplementedError):
            BaseSetting().decode('12345')

    def test_setting_instance_set(self):
        si = SettingInstance(StringSetting, 'abcde')
        self.assertEqual(si.get_value(), 'abcde')
        si.set_value(object(), '12345')
        self.assertEqual(si.get_value(), '12345')

if __name__ == '__main__':
    unittest.main()
