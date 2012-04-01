# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

"""Epoxy core.

Note on logging: since Epoxy is typically used to launch an application,
and often define the logging *for* that application, we can't necessarily
enable standard Python logging to log from Epoxy itself.  The default
logging action (defined in `_default_log`) will be simply `print`; if
you wish to override this behavior, you could by setting
`epoxy.core.log = my_logging_function`.

"""
from collections import OrderedDict
from epoxy.component import Component
from epoxy.utils import load_module
import six


def _default_log(text, *args):
    if args:
        text %= args
    print(text)


log = _default_log


class ComponentReference(object):
    """Represent data and operations about a reference to a component.

    This is an intermediate step, used internally, from the conversion
    of data *about* a `Component` into a fully instantiated `Component`
    instance.

    """

    @classmethod
    def from_config_data(cls, name, config_data):
        class_path = config_data['class']
        dependencies = config_data.get('dependencies', {})
        settings = config_data.get('settings', {})
        priority = config_data.get('priority', 10)
        return cls(name, class_path, dependencies, settings, priority)

    def __init__(self, name, class_path, dependencies, settings, priority):
        self.name = name
        self.class_path = class_path
        self.dependencies = dependencies
        self.settings = settings
        self.priority = priority
        self._instance = None

    def get_instance(self, graph):
        """Instantiate into a `Component` instance."""
        if self._instance is None:

            construction_kwargs = {}
            for dep_key, dep_val in six.iteritems(self.dependencies):
                construction_kwargs[dep_key] = \
                    graph.nodes[dep_val].get_instance(graph)
            construction_kwargs.update(self.settings)
            module_path, class_name = self.class_path.split(':', 1)
            module = load_module(module_path)
            class_ref = getattr(module, class_name)
            self._instance = class_ref.from_dependencies(**construction_kwargs)

        return self._instance


class ComponentGraph(object):
    """Encapsulate information/operations on a graph of Components"""

    @classmethod
    def from_component_data(cls, components_data):
        component_nodes = {}
        for component_key, component_value in six.iteritems(components_data):
            component_nodes[component_key] = \
                ComponentReference.from_config_data(component_key,
                                                    component_value)

        component_edges = set({})
        for component_key, component_node in list(dict(component_nodes).items()):
            for dep_name, dep_value in list(component_node.dependencies.items()):
                if isinstance(dep_value, list):
                    # Value is a list here.  We want to create a simple
                    # list-like Component to provide access to these
                    # dependencies.
                    dep_list = dep_value
                    dep_value = '__component_list__%s__%s' \
                        % (component_key, dep_name)
                    # dependencies may not be instantiated yet;
                    # we have to pass a list with the order of prereqs,
                    # and a dict with the prereqs themselves.
                    comp_ref = ComponentReference(
                                name=dep_value,
                                class_path='epoxy.component:ComponentList',
                                dependencies=OrderedDict([(X, X)
                                                          for X in dep_list]),
                                settings={'dependency_list':dep_list},
                                priority=10)
                    component_node.dependencies[dep_name] = dep_value
                    component_nodes[dep_value] = comp_ref

                    # Finally make sure everything in the dependency list
                    # exists, and add an edge for it.
                    for dep_item in dep_list:
                        if dep_item not in component_nodes:
                            raise ValueError(
                              ("Configuration error detected"
                               " with component list %s. "
                               "Dependency '%s' references '%s'"
                               " which does not "
                               "seem to exist")
                               % (component_key, dep_name, dep_item))
                        targeted_dep = component_nodes[dep_item]
                        component_edges.add((comp_ref, targeted_dep))

                elif dep_value not in component_nodes:
                    raise ValueError(
                      ("Configuration error detected with component %s. "
                       "Dependency '%s' references '%s' which does not "
                       "seem to exist") % (component_key, dep_name, dep_value))
                targeted_dep = component_nodes[dep_value]
                component_edges.add((component_node, targeted_dep))

        return cls(component_nodes, component_edges)

    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges

    def _get_full_ordering(self):
        component_nodes = self.nodes.copy()
        component_edges = self.edges.copy()

        instantiation_ordering = []
        remaining_nodes = sorted(component_nodes.values(),
                                 key=lambda x: x.priority)
        previous_remaining_nodes = -1
        while True:
            if len(remaining_nodes) == 0:
                break  # we are done
            elif previous_remaining_nodes == len(remaining_nodes):
                raise ValueError(
                    ("Graph processing not making any additional "
                     "progress (likely due to a cycle in the graph).  The edges "
                     "remaining in the graph are as follows: %s" %
                     " ".join(["%s -> %s" % (a.name, b.name)
                               for a, b in component_edges])))
            else:
                previous_remaining_nodes = len(remaining_nodes)

            # find a node that has no unresolved dependencies
            dependers = set(x[0] for x in component_edges)
            for node in list(remaining_nodes):
                if node not in dependers:
                    instantiation_ordering.append(node)
                    remaining_nodes.remove(node)
                    for edge_st, edge_end in component_edges.copy():
                        if edge_end == node:
                            component_edges.remove((edge_st, edge_end))
                    break

        return instantiation_ordering

    def _get_targetted_ordering(self, target_component, ancestors=()):
        # Get an order of dependencies ending at the specified target
        #
        # This is basically a tree traversal problem where we do a preorder
        # traversal of the dependencies from our target adding nodes on
        # the peripheral to the instantiation ordering.  As such,
        # this method does use recursion
        instantiation_ordering = []
        target_component_ref = self.nodes[target_component]
        for dependency in target_component_ref.dependencies.values():
            # check for cycles (makes runtime quadratic)
            if dependency in ancestors:
                raise ValueError(
                    "A cycle was detected in the subgraph selected "
                    "for building a component ordering.")

            # recurse on all dependencies but do a filter to ensure that
            # we do not add the same node twice
            subgraph = self._get_targetted_ordering(dependency,
                                list(ancestors) + [target_component])
            for el in subgraph:
                if el not in instantiation_ordering:
                    instantiation_ordering.append(el)

        instantiation_ordering.append(target_component_ref)
        return instantiation_ordering

    def get_ordering(self, target_component=None):
        """Get an ordering of nodes in dependency-order (all should be met)

        The default behavior (with no target specified) is to build a
        global ordering of dependencies.  If a ``target_component`` is
        specified, then a graph will be built that ends the dependency
        chain with the targeted component.

        """
        if target_component:
            return self._get_targetted_ordering(target_component)
        else:
            return self._get_full_ordering()


class ComponentManager(Component):
    """Object responsible for object instantiation"""

    def __init__(self):
        Component.__init__(self)
        self.components = {}
        self.ordered_components = []
        self.graph = None
        self._launched = False
        self._dependencies_settings_lookup = {}

    def _load_graph(self, data, debug=0):
        if not self.graph:
            self.graph_built = True
            if debug > 1:
                log("Building graph of components...")
            self.graph = self.build_component_graph(data)

    def launch_subgraph(self, data, entry_point, debug=0, **kwargs):
        """Launch and run a part of the entire component graph

        This is useful when you have a large application but you want to
        run a part of the application before starting everything else as
        loading in all that other stuff may take a long time.  The method
        takes an ``entry_point`` which is a string which should look like::

            <component>:<method_name>

        The component for the ``entry_point`` and all dependencies will be
        instantiated and started before the provided method is called.  This
        method call may block and the return value from that call will be
        returned from this method.

        If, subsequently, other subgraphs are launched or the overall
        configuration is launched, components that have already been
        initiated and started will not be reinitiated.

        """
        entry_component, entry_method = entry_point.split(':', 1)
        self._load_graph(data, debug=debug)
        component_ordering = self.graph.get_ordering(entry_component)

        # instantation all component and build ordered instance list
        components = {}
        ordered_components = []
        for component_reference in component_ordering:
            try:
                component = component_reference.get_instance(self.graph)
            except:
                log("Error: Instantiating component %r",
                    component_reference.name)
                raise
            components[component_reference.name] = component
            ordered_components.append(component)

        for component in ordered_components:
            component.launch()

        entry_component = components[entry_component]
        self.components.update(components)
        return getattr(entry_component, entry_method)(**kwargs)

    def launch_configuration(self, data, debug=0):
        """Given a configuration, validate and launch based on data

        There are a few different steps here that happen in a particular
        order.  They are as follows:

        1) Build a ComponentGraph from the provided data
        2) Validate the graph (no dependency cycles) and build an ordering
           which ensure that before any object, X, is instatiated that all
           the object on which it depends have alreadby been instantiated.
        3) Instantiate all components in the graph in computed order
        4) In the same, order, call start() on each component
        5) If an entry-point is specified, call the entry-point method that
           has been specified.  Otherwise, the call will return.

        """
        self._load_graph(data, debug=debug)

        # 2) Build the ordering and check for cycles
        component_ordering = self.graph.get_ordering()

        # 3) Instantiate all components and build ordered instance list
        if debug:
            log("Instantiating Components...")
        for component_reference in component_ordering:
            component = component_reference.get_instance(self.graph)
            self.components[component_reference.name] = component
            self.ordered_components.append(component)
            if debug > 1:
                log("  Instantiated %s", component_reference.name)

        # 4) Call start() on each component in order
        if debug:
            log("Starting Components...")
        for component in self.ordered_components:
            component.launch()
            if debug > 2:
                log("  Started %r", component)

        # 5) Execute entry-point if it has been specified
        entry_point = data.get('entry-point', None)
        if entry_point is not None:
            entry_component_name, entry_method = entry_point.split(':', 1)
            entry_component = self.components[entry_component_name]
            entry_point_method = getattr(entry_component, entry_method)

            # call the entry point method with no arguments
            entry_point_method()

    def build_component_graph(self, data):
        """Build a component graph from a collection of configuration data

        In the component graph, each component is represented as a node and
        dependencies are represented as edges starting from the node containing
        the dependency and ending at the dependency.  This graph can then
        be used later on for determining the order in which components should
        be instantiated.  The graph is directed and should be acyclic.  All
        nodes depend on the "system" node so they are all actually a part of
        the graph (connected).

        """
        components = data.get('components', {})
        # create a component_reference to this component
        components["component_manager"] = {
            "class": "epoxy.core:ComponentManager"
        }
        graph = ComponentGraph.from_component_data(components)
        graph.nodes["component_manager"]._instance = self
        return graph
