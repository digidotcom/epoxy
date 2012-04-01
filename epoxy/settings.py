# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

"""Abstract and Concrete settings classes that may be used in applications"""


class SettingInstance(object):
    """Encapsulate a reference to some setting"""

    def __init__(self, setting_type, initial_value):
        self.type = setting_type
        self._value = initial_value

    def get_value(self):
        return self._value

    def set_value(self, obj, value):
        self._value = value


class BaseSetting(object):
    """Base class for all settings"""

    instance_type = SettingInstance

    def __init__(self, required=False, default=None, help=""):  # @ReservedAssignment
        self.name = None
        self.required = required
        self.default = default
        self.help = help

    @classmethod
    def bound_instance(cls, value):
        return cls.instance_type(cls, value)

    def encode(self, value):
        """
        Override with how to encode this value to a string.
        """
        raise NotImplementedError("encode is abstract and should be overriden")

    def decode(self, value):
        """
        Override to indicate how to decode `value` into the proper type.
        Note that previous layers (such as YAML interpretation) may have
        already attempted automatic conversion, so `value` need not be
        a string already.
        """
        raise NotImplementedError("decode is abstract and should be overriden")


class StringSetting(BaseSetting):
    """Encapsulate a setting which stores a string value"""

    def encode(self, value):
        return value

    def decode(self, value):
        return str(value)


class BooleanSetting(BaseSetting):
    """Encapsulate a setting which stores a boolean value"""

    def encode(self, value):
        if value:
            return "true"
        else:
            return "false"

    def decode(self, value):
        try:
            return (value.lower() == "true")
        except AttributeError:
            return bool(value)


class IntegerSetting(BaseSetting):
    """Encapsulate a setting which stores an integer value"""

    def encode(self, value):
        return str(value)

    def decode(self, value):
        return int(value)


class FloatSetting(BaseSetting):
    """Encapsulate a setting which stores a floating point value"""

    def encode(self, value):
        return str(value)

    def decode(self, value):
        return float(value)


class ListSetting(BaseSetting):
    """Encapsulate a setting which stores a list of items"""

    def encode(self, value):
        return str(list(value))

    def decode(self, value):
        return list(value)


class DictionarySetting(BaseSetting):
    """Encapsulate a setting which stores a dictionary of items"""

    def encode(self, value):
        return str(dict(value))

    def decode(self, value):
        return value
