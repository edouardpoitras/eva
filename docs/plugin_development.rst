Plugin Development
==================

A typical Eva plugin will consist of a folder with the following structure:

* `plugin_name`/
* `plugin_name`/`plugin_name`.py
* `plugin_name`/`plugin_name`.info (optional)
* `plugin_name`/`plugin_name`.conf.spec (optional)
* `plugin_name`/requirements.txt (optional)

Folder Structure
----------------

The plugin folder must be located in the :ref:`eva-core-configuration`
``plugin_directory`` for Eva to pick it up as an available plugin (unless it's
already in the public
`plugin repository <https://github.com/edouardpoitras/eva-plugin-repository>`_).

.. warning::

    The name of the info file, python file, and spec file must match the folder
    name in order to be picked up by Eva.

The specification file and the requirements.txt file are optional.

Python File
-----------

This is where your plugin code resides. You can do anything you want with your
plugin, but it's most likely a good idea to make use of some of the helper
functions and triggers that Eva exposes to the plugins.

See the :ref:`api` documentation for more details.

Triggers
++++++++

Triggers are the way that Eva and plugins can interact with each other and share
control of the program flow. Eva uses the
`gossip <https://gossip.readthedocs.io/en/latest/>`_ python module for this
purpose.

To register a function in your plugin to a specific trigger, you simply need to
decorate the function like so::

    import gossip

    @gossip.register('trigger_name_here')
    def custom_function():
        # Perform actions here when the 'trigger_name_here' trigger is fired.
        pass

If the trigger provides variables, your function needs to have those parameters
as well::

    import gossip
    from eva import log

    @gossip.register('test_trigger')
    def custom_function(value):
        log.info('You fired the trigger with the value: %s' %value)

    value = 'Hello World!'
    gossip.trigger('test_trigger', value=value)

It is a good idea to create triggers throughout your plugin to allow other
plugins to modify data, or simply be notified of certain events. Ensure you
document your triggers so other plugin developers can take advantage of them.

There are many ways of managing trigger priorities and dependencies. See the
`gossip`_ documentation for more details.

It is not possible to ``return`` data back to the caller from a registered
trigger. The triggering plugin must provide a referenced object (list, dict,
object) as a parameter to the trigger in order to receive feedback from the
other plugins::

    import gossip

    @gossip.register('test_trigger')
    def test(data):
        data.append('One')
        data.append('Two')

    data = ['Testing']
    gossip.trigger('test_trigger', data=data)
    print(', '.join(data))
    # Testing, One, Two

.. note::

    There are many triggers that are exposed by plugins. If your plugin overlaps
    in functionality with another, or if you want to integrate your plugin with
    another, it is certainly worth looking at the other plugin documentation to
    see if a trigger already exists to fullfill the requirement. If not, I'm
    sure a pull request would be welcome :)

You can register functions in your plugin with any of the following triggers:

``eva.pre_boot``

    A trigger that gets fired before Eva starts loading plugins.
    This is not accessible by Eva plugins.

``eva.plugins_loaded``

    A trigger that gets fired immediately after all Eva plugins have been loaded.

``eva.post_boot``

    This trigger is fired once Eva has booted, but before Eva has begun to
    listen for commands.

``eva.voice_recognition``

    A trigger that gets fired when a new interaction has begun, but only
    ``input_audio`` was provided (no ``input_text``). This is primarily used
    by plugins that transcribe audio.

    :param data: The data received from the clients on query/command.
          See :func:`eva.context.EvaContext.__init__` for more details.
    :type data: dict

``eva.pre_interaction_context``
data=data

``eva.pre_interaction``
context=context

``eva.interaction``
context=context

``eva.post_interaction``
context=context

``eva.text_to_speech``
context=context

``eva.pre_return_data``
return_data=return_data

``eva.scheduler.job_failed``
event=event

``eva.scheduler.job_succeeded``
event=event

``eva.logger.debug``
message=message

``eva.logger.info``
message=message

``eva.logger.warning``
message=message

``eva.logger.error``
message=message

``eva.logger.fatal``
message=message

``eva.pre_publish``
message=message

``eva.publish``
message=message

``eva.post_publish``
message=message

``eva.pre_set_input_text``
text=text
plugin_id=plugin_id
context=self

``eva.post_set_input_text``
text=text
plugin_id=plugin_id
context=self

``eva.pre_set_input_audio``

``eva.post_set_input_audio``

``eva.pre_set_output_text``

``eva.post_set_output_text``

``eva.pre_set_output_audio``

``eva.post_set_output_audio``

Configuration
+++++++++++++

All plugins have the option to load a ``conf`` singleton dictionary that holds
all the configuration and plugin information that Eva sees.  It is also the
primary way of accessing the custom configuration that a user may have
specified for your plugin::

    from eva import conf
    # You can access all sorts of information on plugins.
    location_value = conf['plugins']['weather']['config']['location']
    info_file_object = conf['plugins']['weather']['info']
    path_on_disk = conf['plugins']['weather']['path']
    is_git_repo = conf['plugins']['weather']['git']
    # You can access values from the Eva core configuration file.
    plugin_path = conf['eva']['plugin_directory']
    config_path = conf['eva']['config_directory']

See :ref:`configuration` page for more info on creating your own specification
file and allowing users to provide custom configuration for your plugin.

Scheduler
+++++++++

The ``scheduler`` singleton is an instance of an APScheduler `BackgroundScheduler
<https://apscheduler.readthedocs.io/en/latest/modules/schedulers/background.html>`_.

It should be used for any long-running or periodic jobs that your plugin need to
initiate. The documentation for creating jobs can be found
`here <https://apscheduler.readthedocs.io/en/latest/userguide.html#adding-jobs>`_.

Here is an examples that fires a new job in the background immediately::

    from eva import scheduler
    scheduler.add_job(func_name, id="eva_my_plugin_job")

    def func_name():
        # Job stuff here.
        pass

The function provided needs to exist and the job ID needs to be unique.

Here is an example using the decorator syntax that fires a job every hour::

    from eva import scheduler
    from eva import log

    @scheduler.scheduled_job('interval', hours=1, id='eva_my_plugin_hourly_job')
    def hourly_job():
        log.info('Running this job on the hour again!');

Here is an example of running a job with parameters on a specific date::

    from eva import scheduler
    from eva import log
    scheduler.add_job(birth_day, 'date', run_date=date(2017, 02, 10), args=['Happy Birthday!'])

    def birth_day(message):
        log.info(message)

Publish
+++++++

All plugins can import the ``publish`` function which will allow plugins to
easily broadcast messages to all Eva clients::

    from eva import publish
    publish('This is a message to all!')

``publish`` can take a second parameter, which is the channel to publish the
message on. This value is 'eva_messages' by default as that's the channel that
Eva plugins should be listening on.

.. todo::

    Does not yet support publishing audio to clients.

Logger
++++++

The ``log`` singleton makes for easy logging::

    from eva import log
    log.debug('This is a debug message')
    log.info('This is an info message')
    log.warning('This is a warning message')
    log.error('This is an error message')
    log.critical('This is a critical message')

Info File
---------

The plugin info files are pretty simple.

Here is the specification file used to load Eva plugins::

    # Every Eva plugin should have a name matching it's python module name.
    name = string(default='Plugin Unknown')
    # Description of this Eva plugin.
    description = string(default='No description')
    # The current version of the Eva plugin.
    version = string(default='0.0.0')
    # List of Eva plugin dependencies for this plugin.
    dependencies = force_list(default=list())
    # Use the requirements.txt for Python module dependencies.

As you can see, all fields have a default value, and so it is not necessary
to have an info file.

Here is an example plugin info file taken from the
`Weather <https://github.com/edouardpoitras/eva-weather>`_ plugin::

    name = Weather
    description = Enables the response of weather-related queries from Eva.
    version = 0.1.0
    dependencies = conversations

.. warning::

    The `dependencies` field refers to Eva plugin dependencies, not python
    module dependencies. Use a `requirements.txt` in your plugin folder to
    specify python module dependencies.

Specification File
------------------

A plugin specification file can be provided if you wish to give the user a way
of configuring different aspects of your plugin.

If a specification file is available, Eva will use it to validate a
configuration file that the user may have provided in the ``config_directory``
(see :ref:`eva-core-configuration` configuration for more details).

The `Weather <https://github.com/edouardpoitras/eva-weather>`_ plugin is a good
example. It requires that the user provide an API key in order to access
weather information.

See :ref:`eva-plugins-configuration` configuration for more details and an
example.

requirements.txt File
---------------------

Every plugin can provide a `requirements.txt` in order to specify python module
requirements.

Eva will automatically installs the python modules from this file when the
plugin is enabled.

Full Example
------------
