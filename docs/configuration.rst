.. _configuration:

Configuration
=============

Eva is very flexible and easy to configure.

If you have
`Web UI Plugins <https://github.com/edouardpoitras/eva-web-ui-plugins>`_
enabled, you can configure each individual plugin from the Web UI instead of
managing config files on disk.

.. _eva-core-configuration:

Eva Core
--------

The core of Eva can be configured through the ``eva.conf`` file.

You can find this configuration file in any of the following locations:

*  ~/eva.conf
* ~/.eva.conf
* ~/eva/eva.conf
* /etc/eva.conf
* /etc/eva/eva.conf

If you can't find the configuration file, Eva is most likely using all default
options for your installation. You can simply create the file in any of the
locations mentioned above and Eva will pick up your settings on next restart.

Here is the contents of the Eva specification file (``eva/eva.conf.spec``) which
outlines the different configuration options available::

    [eva]
    # The git-accessible repo that holds all the available Eva plugins for download.
    plugin_repository = string(default='https://github.com/edouardpoitras/eva-plugin-repository.git')

    # The local path where the plugin_repository will be stored on disk.
    plugin_repo_path = string(default='/tmp/eva-plugin-repository')

    # The local directory holding all existing (and downloaded) plugins.
    plugin_directory = string(default='~/eva/plugins')

    # The local directory holding all plugin configurations.
    config_directory = string(default='~/eva/configs')

    # The list of enabled plugins - dependencies will be handled by Eva on boot.
    enabled_plugins = force_list(default=list('web_ui_plugins', 'web_ui_updater'))

    [logging]
    # The namespace used for logging.
    log_name = string(default='eva')

    # The logging level.
    log_level = option('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', default='INFO')

    [mongodb]
    # The MongoDB username.
    username = string(default='')

    # The MongoDB password.
    password = string(default='')

    # The MongoDB host where Eva's database will be held.
    host = string(default='localhost')

    # The MongoDB port used to access Eva's database.
    port = integer(default=27017)

    # The MongoDB database name for Eva.
    database = string(default='eva')

.. note::

    See the
    `ConfigObj documentation <https://configobj.readthedocs.io/en/latest/>`_ for
    more details on the specification file syntax.

An example configuration file could look like this::

    [eva]
    plugin_directory = /etc/eva/plugins
    config_directory = /etc/eva/configs
    enabled_plugins = web_ui_plugins, web_ui_updater, weather

    [logging]
    log_level = DEBUG

    [mongodb]
    host = my.eva.com
    username = myusername
    password = mypassword
    database = my_eva

.. _eva-plugins-configuration:

Eva Plugins
-----------

All Eva plugins have the option of supplying a specification file to allow users
to configure different behaviour for their installation.

.. note::

    The plugin specification file must be named after the plugin name.
    If a plugin is named ``my_plugin``, the specification file must be in the
    root of the plugin directory and named ``my_plugin.conf.spec``.

When a plugin is enabled, Eva will scan the ``config_directory`` for a matching
config file for that plugin. If one is found, the configuration values are
validated through the plugin's specification file, loaded, and made available to
all the plugins. The values can be accessed through the ``conf`` singleton.

For example, the `Weather <https://github.com/edouardpoitras/eva-weather>`_ plugin
has the following entries in it's specification file (``weather.conf.spec``)::

    darksky_api_key = string(default='')
    location = string(default='')
    latitude = float(-90.0, 90.0)
    longitude = float(-180.0, 180.0)
    metric = boolean(default=True)

.. note::

    See the
    `ConfigObj documentation <https://configobj.readthedocs.io/en/latest/>`_ for
    more details on the specification file syntax.

This means that if the weather plugin is enabled, all plugins (include weather)
can access those configuration options like so::

    from eva import conf
    location = conf['plugins']['weather']['config']['location']

Not all that exciting as the location is set to an empty string by default.
However, if a file named ``weather.conf`` is in the Eva config directory
(default is ``~/eva/configs``), Eva will pull in those values when loading the
plugin::

    # Making sure the weather plugin knows where I am.
    location = 'Ottawa, Ontario, Canada'

Now the location variable from above will contain the value 'Ottawa, Ontario, Canada'.
