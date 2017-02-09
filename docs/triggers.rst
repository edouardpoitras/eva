.. _triggers:

Triggers
========

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

eva.pre_boot
++++++++++++

    A trigger that gets fired before Eva starts loading plugins.
    This is not accessible by Eva plugins.

eva.plugins_loaded
++++++++++++++++++

    A trigger that gets fired immediately after all Eva plugins have been loaded.

eva.post_boot
+++++++++++++

    This trigger is fired once Eva has booted, but before Eva has begun to
    listen for commands.

eva.voice_recognition
+++++++++++++++++++++

    A trigger that gets fired when a new interaction has begun, but only
    ``input_audio`` was provided (no ``input_text``). This is primarily used
    by plugins that transcribe audio.

    :param data: The data received from the clients on query/command.
          See :func:`eva.context.EvaContext.__init__` for more details.
    :type data: dict

eva.pre_interaction_context
+++++++++++++++++++++++++++

    A trigger that gets fired when a new interaction is about to begin.
    No :class:`eva.context.EvaContext` object is available at this point.

    :param data: The data received from the clients on query/command.
          See :func:`eva.context.EvaContext.__init__` for more details.
    :type data: dict

eva.pre_interaction
+++++++++++++++++++

    Same as the ``eva.pre_interaction_context`` trigger except that the context
    object has been created and is passed to the registered function.

    :param context: The context object created for this interaction.
    :type context: :class:`eva.context.EvaContext`

eva.interaction
+++++++++++++++

    This trigger is where most plugin check if they should be handling the input
    from the user.

    Usually plugins will check if another plugin has not already acted on the
    user's query/command before acting::

        @gossip.register('eva.interaction')
        def interaction(context)
            if not context.response_ready():
                context.set_output_text('Too late other plugins, I'm responding!')

    You would typically want to use the context object's
    :func:`eva.context.EvaContext.contains` method to see if certain text was
    part of the query/command from the user::

        @gossip.register('eva.interaction')
        def interaction(context)
            if not context.response_ready() and context.contains('weather'):
                weather = get_current_weather()
                context.set_output_text('Here is the current weather: %s' %weather)

    :param context: The context object created for this interaction.
    :type context: :class:`eva.context.EvaContext`

    .. todo::

        Need to mention other plugins that offer more powerful tools like
        follow-up questions and intent parsing.

eva.post_interaction
++++++++++++++++++++

    Triggered immediately after ``eva.interaction``.

    :param context: The context object created for this interaction.
    :type context: :class:`eva.context.EvaContext`

eva.text_to_speech
++++++++++++++++++

    This trigger is called when the interaction is complete and no output_audio
    is present in the context object. This is primarily used by plugins to convert
    text to audio data for the clients to play as a response from Eva.

    You would usually use the :func:`eva.context.EvaContext.set_output_audio`
    if you wanted to add output_audio to the interaction.

    :param context: The context object created for this interaction.
    :type context: :class:`eva.context.EvaContext`

eva.pre_return_data
+++++++++++++++++++

    This is triggered right before returning the response data to the clients.
    It gives plugins the opportunity to alter the raw response from Eva.

    :param return_data: Same as what is returned from the
        :func:`eva.director.interact` function.
    :type return_data: dict

eva.scheduler.job_failed
++++++++++++++++++++++++

    This is triggered when an APScheduler job sends the ``EVENT_JOB_ERROR``
    event. See `APScheduler events documentation <https://apscheduler.readthedocs.io/en/latest/modules/events.html>`_
    for more details.

    :param event: The APScheduler event returned from the failed job.
    :type event: `apscheduler.events.JobEvent <https://apscheduler.readthedocs.io/en/latest/modules/events.html#apscheduler.events.JobEvent>`_

eva.scheduler.job_succeeded
+++++++++++++++++++++++++++

    This is triggered when an APScheduler job sends the ``EVENT_JOB_EXECUTED``
    event. See `APScheduler events documentation <https://apscheduler.readthedocs.io/en/latest/modules/events.html>`_
    for more details.

    :param event: The APScheduler event returned from the successful job.
    :type event: `apscheduler.events.JobEvent <https://apscheduler.readthedocs.io/en/latest/modules/events.html#apscheduler.events.JobEvent>`_

eva.logger.debug
++++++++++++++++

    A trigger that gets fired every time a debug message is logged.

    :param message: The message that is being logged.
    :type message: string

eva.logger.info
+++++++++++++++

    A trigger that gets fired every time a info message is logged.

    :param message: The message that is being logged.
    :type message: string

eva.logger.warning
++++++++++++++++++

    A trigger that gets fired every time a warning message is logged.

    :param message: The message that is being logged.
    :type message: string

eva.logger.error
++++++++++++++++

    A trigger that gets fired every time a error message is logged.

    :param message: The message that is being logged.
    :type message: string

eva.logger.critical
+++++++++++++++++++

    A trigger that gets fired every time a critical message is logged.

    :param message: The message that is being logged.
    :type message: string

eva.pre_publish
+++++++++++++++

    A trigger that is fired when a message is getting ready for publishing.

    :param message: The message that will be published.
    :type message: string

eva.publish
+++++++++++

    A trigger that is fired right before a message will be published to clients.

    :param message: The message that will be published.
    :type message: string

eva.post_publish
++++++++++++++++

    A trigger that is fired immediately after a message is published to clients.

    :param message: The message that will be published.
    :type message: string

eva.pre_set_input_text
++++++++++++++++++++++

    A trigger that gets fired right before setting a new ``input_text`` value
    for the current interaction.

    :param text: The new text that is being set as ``input_text``.
    :type text: string
    :param plugin_id: The plugin ID that is setting this new ``input_text``.
    :type plugin_id: string
    :param context: The context object for this interaction.
    :type context: :class:`eva.context.EvaContext`

eva.post_set_input_text
+++++++++++++++++++++++

    A trigger that gets fired right after setting a new ``input_text`` value
    for the current interaction.

    :param text: The new text that was set as ``input_text``.
    :type text: string
    :param plugin_id: The plugin ID that has set this new ``input_text``.
    :type plugin_id: string
    :param context: The context object for this interaction.
    :type context: :class:`eva.context.EvaContext`

eva.pre_set_input_audio
+++++++++++++++++++++++

    A trigger that gets fired right before setting a new ``input_audio`` value
    for the current interaction.

    :param audio: The new audio data that is being set.
    :type audio: binary string
    :param content_type: The content type of this audio data.
    :type content_type: string
    :param plugin_id: The plugin ID that is setting this new audio data.
    :type plugin_id: string
    :param context: The context object for this interaction.
    :type context: :class:`eva.context.EvaContext`

eva.post_set_input_audio
++++++++++++++++++++++++

    A trigger that gets fired right after setting a new ``input_audio`` value
    for the current interaction.

    :param audio: The new audio data that was set.
    :type audio: binary string
    :param content_type: The content type of this audio data.
    :type content_type: string
    :param plugin_id: The plugin ID that has set this new audio data.
    :type plugin_id: string
    :param context: The context object for this interaction.
    :type context: :class:`eva.context.EvaContext`

eva.pre_set_output_text
+++++++++++++++++++++++

    A trigger that gets fired right before setting a new ``output_text`` value
    for the current interaction.

    :param text: The new text that is being set as ``output_text``.
    :type text: string
    :param responding: True if this new ``output_text`` is responding to this
        interaction's query/command. False if simply altering the response.
        This flag is used in :func:`eva.context.EvaContext.response_ready` to
        determine if a response has already been formulated for a query/command.
    :type responding: boolean
    :param plugin_id: The plugin ID that is setting this new ``output_text``.
    :type plugin_id: string
    :param context: The context object for this interaction.
    :type context: :class:`eva.context.EvaContext`

eva.post_set_output_text
++++++++++++++++++++++++

    A trigger that gets fired right after setting a new ``output_text`` value
    for the current interaction.

    :param text: The new text that was set as ``output_text``.
    :type text: string
    :param responding: True if this new ``output_text`` was responding to this
        interaction's query/command. False if simply altering the response.
        This flag is used in :func:`eva.context.EvaContext.response_ready` to
        determine if a response has already been formulated for a query/command.
    :type responding: boolean
    :param plugin_id: The plugin ID that was setting this new ``output_text``.
    :type plugin_id: string
    :param context: The context object for this interaction.
    :type context: :class:`eva.context.EvaContext`

eva.pre_set_output_audio
++++++++++++++++++++++++

    A trigger that gets fired right before setting a new ``output_audio`` value
    for the current interaction.

    :param audio: The new audio data that is being set.
    :type audio: binary string
    :param content_type: The content type of this audio data.
    :type content_type: string
    :param plugin_id: The plugin ID that is setting this new audio data.
    :type plugin_id: string
    :param context: The context object for this interaction.
    :type context: :class:`eva.context.EvaContext`

eva.post_set_output_audio
+++++++++++++++++++++++++

    A trigger that gets fired right after setting a new ``output_audio`` value
    for the current interaction.

    :param audio: The new audio data that is being set.
    :type audio: binary string
    :param content_type: The content type of this audio data.
    :type content_type: string
    :param plugin_id: The plugin ID that is setting this new audio data.
    :type plugin_id: string
    :param context: The context object for this interaction.
    :type context: :class:`eva.context.EvaContext`
