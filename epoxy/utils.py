# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

"""Simple utilities used by other modules in this package."""


def load_module(path):
    """Return a reference to the module with the specified path

    Path should be given in dotted notation and be fully qualified.  That
    is it should look like path.to.module.

    """
    return __import__(path, globals(), locals(), [''])
