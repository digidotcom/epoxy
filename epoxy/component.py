# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

from epoxy.settings import BaseSetting, SettingInstance, ListSetting
import six


class BaseDependency(object):
    """Container encapsulating some dependency"""

    def __init__(self, class_or_interface=None, required=True, default=None):
        self.class_or_interface = class_or_interface
        self.required = required
        self.default = default

    @classmethod
    def bound_instance(self, value):
        return value


class Dependency(BaseDependency):
    """A Simple Dependency"""


class ComponentMeta(type):
    """Build a dependency graph for the Component with this MetaClass

    When a class which has :class:`Component` as its base is declared, this
    code will search through the class definition and build data structure
    containing information about the dependencies (both references to
    external code and settings) required by this component.  These data
    structure can then be used by the :class:`ComponentManager` or other
    in order to build a working system.

    """

    def __new__(mcs, name, bases, dct):  # @NoSelf
        dependencies = {}
        settings = {}

        # inherit settings/dependencies from parent first
        for kls in bases:
            if hasattr(kls, '_dependencies'):
                dependencies.update(kls._dependencies)
            if hasattr(kls, '_settings'):
                settings.update(kls._settings)

        # now find all the dependencies at this level
        for key, value in list(dct.items()):
            if isinstance(value, BaseDependency):
                dependencies[key] = value
                del dct[key]  # we have it elsewhere now, use __getattr__
            elif isinstance(value, BaseSetting):
                settings[key] = value
                value.name = key
                del dct[key]  # we have it elsewhere now, use __getattr__

        # finally, set the class attributes
        dct['_settings'] = settings
        dct['_dependencies'] = dependencies
        return type.__new__(mcs, name, bases, dct)


class Component(object):
    """A Component is some part of of a System that has a particular interface

    Within the framework, a :class:`Component` is like any other object
    with the exception that it can declare dependencies and settings, each
    of which may or may not be required.  These dependencies can be injected
    when the object is constructed via the :meth:`from_dependencies`
    method.  Components should typically have no-args constructors.

    In many cases, a :class:`Component` might be declared which in turn
    uses a regular Python Object internally (encapsulated) in order to
    do one-time injection of dependencies and settings into some existing
    object.

    """

    def start_with_deps(self, started=None):
        """Start a component and any of its dependnecies"""
        if started is None:
            started = set()
        # start stuff depth first.  Note: does not do cycle detection here
        for depkey in self._dependencies:
            dep = getattr(self, depkey)
            if dep not in started:
                if hasattr(dep, 'start_with_deps'):
                    dep.start_with_deps(started)
                started.add(dep)
        if hasattr(self, 'start'):
            self.start()

    @classmethod
    def from_dependencies(cls, **kwargs):
        """Construct a component from a given setting of dependencies

        Given a set of key, value pairs that are either dependencies or
        settings for some component, construct an instance of the component

        All required dependencies and setting must be supplied in order for
        the object to be constructed and all keys specified must map to some
        setting or dependency on this class.  If any problem is detected
        a ValueError will be raised with an appropriate error description.

        """
        dependency_matches = {}
        settings_matches = {}

        for key, value in six.iteritems(kwargs):
            if key in cls._dependencies:
                dependency_matches[key] = value
            elif key in cls._settings:
                settings_matches[key] = value
            else:
                raise ValueError(
                    "'%s' is neither a dependency nor a setting"
                    " on '%s'" % (key, cls.__name__))

        # create the instance but don't call __init__ as of yet... We will
        # do that after settings and dependencies have been injected into
        # the new instance (as __init__ may depend on these being present)
        instance = object.__new__(cls)

        dependencies_settings_lookup = {}

        # validate and set dependencies
        for key, dependency in six.iteritems(cls._dependencies):
            if key not in dependency_matches:
                if dependency.required:
                    raise ValueError(
                        "'%s' is a required dependency of '%s' but was not "
                        "specified when from_dependncies"
                        " was called" % (key, cls.__name__))
                dep_inst = dependency.bound_instance(dependency.default)
            else:
                match = dependency_matches[key]
                dep_inst = dependency.bound_instance(match)
            dependencies_settings_lookup[key] = dep_inst

        # validate and set settings
        for key, setting in six.iteritems(cls._settings):
            if key not in settings_matches:
                if setting.required:
                    raise ValueError("'%s' is a required setting but was "
                                     "not specified" % key)
                dep_inst = setting.bound_instance(setting.default)
            else:
                match = settings_matches[key]
                dep_inst = setting.bound_instance(setting.decode(match))
            dependencies_settings_lookup[key] = dep_inst

        # now call __init__ to finish construction
        instance._dependencies_settings_lookup = dependencies_settings_lookup
        for attr, obj in six.iteritems(dependencies_settings_lookup):
            if isinstance(obj, SettingInstance):
                obj = obj.get_value()
            setattr(instance, attr, obj)
        instance._launched = False
        instance.__init__()
        return instance

    def launch(self):
        """Start this component (but only do this once)"""
        if not self._launched:
            self._launched = True
            self.start()

    def start(self):
        """Start this component (top-level start does nothing)"""

    def stop(self):
        """Stop the component (top-level stop does nothing)"""
Component = six.add_metaclass(ComponentMeta)(Component)



class ComponentList(Component):
    """A list of components, used to implement dependency lists.

    This generally will not be instantiated by a user; instead,
    when a dependency is set to a list in the configuration,
    this is an adaptor to set that dependency to a list-like object
    with the ordered dependencies.

    """
    dependency_list = ListSetting()

    def __init__(self, components):
        self._components = components

    # List interface

    def __getitem__(self, index):
        return self._components[index]

    def __len__(self):
        return len(self._components)

    def __iter__(self):
        return iter(self._components)

    def __reversed__(self):
        return reversed(self._components)

    def index(self, value):
        return self._components.index(value)

    def count(self, value):
        return self._components.count(value)

    def get_list(self):
        return list(self)

    @classmethod
    def from_dependencies(cls, **kwargs):
        kwargs = dict(kwargs)
        dependency_list = kwargs.pop('dependency_list')
        component_list = list()
        for component_key in dependency_list:
            if component_key not in kwargs:
                raise ValueError('Dependency %s somehow missing'
                                 ' from ComponentList' % component_key)
            component_list.append(kwargs.pop(component_key))
        if kwargs:
            raise ValueError('Extra dependencies %s somehow given to'
                             ' ComponentList' % ', '.join(kwargs.keys()))
        instance = cls(component_list)
        instance._launched = False
        return instance

