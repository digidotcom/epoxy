# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

from epoxy.component import Component, Dependency
from epoxy.settings import BooleanSetting, IntegerSetting
import collections
import unittest


class SMSService(Component):
    """
    """

    # dependencies
    sms_driver = Dependency()
    device_communication_service = Dependency()

    # settings
    store_history = BooleanSetting(
        required=True,
        help="Specify whether or not message history should be maintained")

    max_rx_history = IntegerSetting(
        required=False,
        default=10,
        help="The number of received messages that should be maintained")

    min_rx_history = IntegerSetting(
        required=False,
        default=10,
        help="The number of transmitted messages that should be maintained")

    def __init__(self):
        Component.__init__(self)
        self._rx_messages = collections.deque()
        self._tx_messages = collections.deque()

    def start(self):
        self.sms_driver.register_rx_callback(self._rx_message)

    def _rx_message(self, sms_message):
        self._rx_messages.appendleft(sms_message)
        max_rx_history = self.max_rx_history
        if len(self._rx_messages) > max_rx_history:
            self._rx_messages.pop()

        # from here, parse the message...


class TestSMSService(unittest.TestCase):

    def test_rx_cap(self):
        svc = SMSService.from_dependencies(
            sms_driver=None,
            device_communication_service=None,
            store_history=True,
            max_rx_history=5)
        for i in range(5):
            svc._rx_message("%s" % i)
        self.assertEqual(len(svc._rx_messages), 5)
        svc._rx_message("5")
        self.assertEqual(len(svc._rx_messages), 5)
        self.assertEqual(svc._rx_messages[0], "5")
        self.assertEqual(svc._rx_messages[-1], "1")

if __name__ == '__main__':
    unittest.main()
