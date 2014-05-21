Epoxy
=====

Introduction
------------

Epoxy is an inversion of control framework for Python applications
packaged with a set of adapters that can be used with a number of
existing technologies.  Epoxy allows you to clearly separate out the
concern of mapping dependencies to components from defining those
components.

Epoxy is probably overkill for small apps (like the example below) but
shows its true value on larger projects where a higher degree of
flexibility and lower degree of coupling is desirable.

License
-------

This library is available under the terms of the MPL.  Please see the
LICENSE file for details.

An Example
----------

Here's an example of an epoxy component:

    from epoxy.component import Component, Dependency

    class PrinterComponent(Component):
    
        prefix = StringSetting(required=False, default="PRINTING")

        def print(self, stuff):
            print ("[%s] %%s" % self.prefix) % stuff

        def start(self):
            print self.print("Warming up printer")


    class ScreenRenderer(Component):

        printer = Dependency()

        def render_screen(self):
            self.printer.print("My Stuff")

        def start(self):
            self.printer.print("Screen Renderer Initialized")

In this example, ScreenRenderer does not need to know the precise
printer which will be used as a dependency at runtime, it just needs
to declare the dependency and use it (there is an assumed interface,
as with much in python we just use duck typing).

To wire these components up at runtime, we would write a yaml file
that would have something like this:

    components:
      printer:
        class: my.module:PrinterComponent
        settings:
          prefix: PREFIX

      screen_renderer:
        class: my.module:ScreenRenderer
        dependencies:
          printer: printer

    entry-point:
      screen_renderer:render_screen

Finally, to load in our configuration and run the application, we
would write something like the following:

    from epoxy.configuration import YamlConfigurationLoader
    from epoxy.core import ComponentManager

    loader = YamlConfigurationLoader("myapp.yml")
    config = loader.load_configuration()
    component_mgr = ComponentManager()
    component_mgr.launch_configuration(config)

This would run our entry point and print the following to the screen:

    [PREFIX] Warming up printer
    [PREFIX] Screen Renderer Initialized
    [PREFIX] my stuff

Writing a Component
-------------------

Any Component that is written should follow these basic rules in order
to play nicely:

1.  No-args constructor: Components should have a no-args constructor
    in order to be instantiated by the framework.  To initialize a
    Component in your own code (maybe from a unit test) you can use
    the "from_dependencies" classmethod available on any component and
    pass in any relevant dependencies/settings as keyword arguments.
    
    For instance, instantiating our previous object graph would look
    like the following:
    
        printer = PrinterComponent.from_dependencies(prefix="FROM_DEPS")
        renderer = ScreenRenderer.from_dependencies(printer=printer)

    When ``__init__`` is executed it is guaranteed that all dependencies
    will be present and initialized (but not started).

2.  Implement ``start()`` method: After all objects in the graph are
    instantiated, they will be started.  Like with ``__init__``,
    dependencies will be present and will have had ``start()`` called.
    Calls to ``start()`` should not block.  For long-running tasks, using
    an entry-point is more appropriate.

3.  Avoid Dependency Cycles: If the object graph has dependencies, you
    will get errors when trying to build the dependency graph and you
    will not be able to run your application.  There are many
    different strategies for breaking these cycles.  If you run into
    this issue and are ticked off, just know that fixing this issue is
    making your application better.

