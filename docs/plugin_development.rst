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

The plugin folder must be located in the :ref:`configured <core-configuration>`
``plugin_directory`` for Eva to pick it up as an available plugin (unless it's
already in the
`public plugin repository <https://github.com/edouardpoitras/eva-plugin-repository>`_).

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

Plugins must register with some triggers in order to be notified of
interactions with the user. Here is a simple example of a weather plugin that
registers to the ``eva.interaction`` trigger in order to handle weather queries
from clients::

    import gossip

    @gossip.register('eva.interaction')
    def interaction(context)
        # Ensure no other plugin has responded to this query yet.
        # Ensure the query contains the word 'weather'.
        if not context.response_ready() and context.contains('weather'):
            weather = get_current_weather()
            # Respond with the weather information.
            context.set_output_text('Here is the current weather: %s' %weather)

For more details and a list of available triggers, see the :ref:`triggers`
section of this documentation.

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
(see :ref:`core-configuration` configuration for more details).

The `Weather <https://github.com/edouardpoitras/eva-weather>`_ plugin is a good
example. It requires that the user provide an API key in order to access
weather information.

See :ref:`plugins-configuration` configuration for more details and an
example.

requirements.txt File
---------------------

Every plugin can provide a `requirements.txt` in order to specify python module
requirements.

Eva will automatically installs the python modules from this file when the
plugin is enabled.

Full Example
------------

We're going to build a simple plugin named ``motivate`` that has the goal of
motivating the user.

Our plugin should be able to send encouraging responses to the user when asked,
and send follow-up motivational comments if the user claims it didn't work the
first time.

It will also send random encouraging statements to the user every day.

Let's start with our info file (``motivate/motivate.info``)::

    name = Motivate
    description = Motivate the user with this amazing plugin!
    version = 0.1.0
    dependencies = conversations

We're adding the `conversations <https://github.com/edouardpoitras/eva-conversations>`_
plugin as a dependency because we want to be able to handle follow-up
query/commands, which is something the conversations plugin offers through it's
``eva.conversations.follow_up`` trigger.

Let's allow the plugin to capture the user's name so as to make the motivations
more personal.

Here our configuration specification file (``motivate/motivate.conf.spec``)::

    user_name = string(default='User')

We won't be using any python modules other than the ones required by Eva, so no
requirements.txt file is needed.

Now for our actual plugin code (``motivate/motivate.py``)::

    import random
    import gossip
    from eva import conf
    from eva import publish
    from eva import scheduler

    # User name pulled from the configuration.
    USER = conf['plugins']['motivate']['config']['user_name']

    # We could also pull motivational phrases from the internet.
    # We could also make the motivational phrases configurable in the spec file.
    PHRASES = ['Never give up %s!' %USER,
               'You can do it %s!' %USER,
               '%s, you don\'t have to have it all figured out to move forward.' %USER,
               '%s, keep your eyes on the stars, and your feet on the ground.' %USER]

    def get_phrase(ask_follow_up=True):
        # Choose a random motivational phrase.
        phrase = random.choice(PHRASES)
        if ask_follow_up:
            # Don't forget to ask if they are sufficiently motivated.
            return '%s Are you sufficiently motivated?' %phrase
        return phrase

    @gossip.register('eva.interaction')
    def interaction(context):
        # Ensure no other plugin has already responded and the user's query or
        # command contains the word 'motivate' (as in 'motivate me please').
        if not context.response_ready() and context.contains('motivate'):
            # Get are motivational phrase.
            response = get_phrase()
            # Apply the response so that Eva knows to send it to the client.
            context.set_output_text(response)

    @gossip.register('eva.conversations.follow_up')
    def follow_up(plugin_id, context):
        # Check if we should be handling the follow-up query/command.
        if plugin_id == 'motivate':
            # If the user's query/command contains the word 'no', we try again.
            if context.contains('no'):
                # Get another motivational phrase.
                response = get_phrase()
                context.set_output_text(response)
            else:
                # Tell other plugins that this interaction has been taken care of.
                context.responded = True
                # Explicitly close the conversation (don't wait for timeout).
                context.conversation.close()

    @scheduler.scheduled_job('interval', hours=24, id='eva_motivate_job')
    def motivate_job():
        # We don't want to ask the user for a follow-up here.
        phrase = get_phrase(False)
        # Publish the motivational message to clients.
        publish(phrase)
