"""
Holds functions related to Eva and plugins configuration.
"""
import os
import inspect
from configobj import ConfigObj
from validate import Validator

def get_config(config_file=None, spec_file=None, **kwargs):
    """
    Function used to fetch Eva core and plugin configurations on startup.
    If config_file and spec_file are ``None``, assumes the we're looking for
    Eva's config and spec file.

    .. warning::

        This function should not be used directly unless you know what you are
        doing. Use the singleton conf variable to access Eva and plugin
        configurations::

            from eva import conf
            plugin_directory = conf['eva']['plugin_directory']
            fake_plugin_variable = conf['plugins']['fake_plugin']['config']['variable_name']

    :param config_file: The location of the configuration file to parse.
    :type config_file: string
    :param spec_file: The location of the configuration specification file.
    :type spec_file: string
    :return: The loaded configuration object.
    :rtype: `ConfigObj  <https://configobj.readthedocs.io/en/latest/>`_
    """
    if config_file is None:
        config_file = get_eva_config_file()
    config = ConfigObj(config_file, configspec=get_config_spec(spec_file), **kwargs)
    # First round of validation to see if everything is OK.
    results = config.validate(Validator())
    if results:
        # Everything OK, return the config.
        return config
    # Something went wrong, re-validate and preserve errors.
    results = config.validate(Validator(), preserve_errors=True)
    invalid = []
    for section_name, section in results.items():
        print(section_name)
        print(section)
        for key, value in section.items():
            if value is False:
                invalid.append('[' + section_name + '] - ' + key)
    raise Exception('Invalid config values in %s for: %s' %(config_file, ', '.join(invalid)))

def get_plugin_config(plugin_id, config_dir):
    """
    Wrapper around :func:`get_config` to fetch a plugin's configurations.

    .. warning::

        The same :func:`get_config` warning applies for this function. Stick with
        the conf singleton in order to retrieve plugin configurations.

    :param plugin_id: The plugin ID.
    :type plugin_id: string
    :param config_dir: The directory where the plugin configuration file is found.
    :type config_dir: string
    :return: The loaded configuration object.
    :rtype: `ConfigObj  <https://configobj.readthedocs.io/en/latest/>`_
    """
    from eva import conf
    plugin_dir = conf['plugins'][plugin_id]['path']
    spec_file = plugin_dir + '/' + plugin_id + '.conf.spec'
    config_file = config_dir + '/' + plugin_id + '.conf'
    return get_config(config_file, spec_file)

def get_config_spec(spec_file=None):
    """
    Returns a configuration specification based on the spec file provided.
    Assumes the ``<eva_directory>/eva.conf.spec`` file if no spec file path
    specified.

    :param spec_file: The path of the specification file to load.
    :type spec_file: string
    :return: The specification file object.
    :rtype: `ConfigObj  <https://configobj.readthedocs.io/en/latest/>`_
    """
    if spec_file is None:
        spec_file = get_eva_directory() + '/eva.conf.spec'
    return ConfigObj(spec_file, encoding='UTF8', list_values=False, _inspec=True)

def get_eva_directory():
    """
    Function used to get the directory of the current file. Effectively
    determining Eva's source code directory.

    :return: Eva's source code directory.
    :rtype: string
    """
    return \
      os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))

def get_eva_config_file():
    """
    Function that attempts to determine where Eva's main configuration file resides.

    Looks for the following files:

        * ~/eva.conf
        * ~/.eva.conf
        * ~/eva/eva.conf
        * /etc/eva.conf
        * /etc/eva/eva.conf

    :return: Eva's configuration file, if found.
    :rtype: string
    """
    # Search in user home directory first.
    home = os.path.expanduser('~')
    for fname in ['/eva.conf', '/.eva.conf', '/eva/eva.conf']:
        if os.path.isfile(home + fname):
            return home + fname
    # Then search system-wide.
    if os.path.isfile('/etc/eva.conf'):
        return '/etc/eva.conf'
    if os.path.isfile('/etc/eva/eva.conf'):
        return '/etc/eva/eva.conf'

def save_config(plugin_id=None, section=None):
    """
    Save current active plugin configuration to disk.

    If ``plugin_id`` is not provided, then ``section_id`` MUST be provided. That
    is because without ``plugin_id``, Eva assumes you're trying to save it's core
    configuration - which requires a section to save.

    If Eva can't find it's core configuration object when saving, it will write
    out it's current configurations to ``~/eva/eva.conf``.

    :param plugin_id: The plugin ID to have it's configurations preserved.
        If ``None``, assumes Eva's core configurations - in which case ``section`` is required.
    :type plugin_id: string
    :param section: If ``plugin_id`` is ``None``, section must be provided to
        determine which section of the Eva configuration file should be saved.
    :type section: string
    """
    # Load up the active singleton.
    from eva import conf
    # Only save the relevant sections.
    if plugin_id is None:
        assert section is not None, 'Must provide a section to update eva core configuration.'
        # Save eva core configuration.
        old_configuration = get_config()
        old_configuration[section] = conf[section]
        if old_configuration.filename is None:
            save_location = os.path.expanduser('~') + '/eva'
            try:
                os.makedirs(save_location)
            except FileExistsError:
                pass
            old_configuration.write(open(save_location + '/eva.conf', 'wb'))
        else:
            old_configuration.write()
    else:
        plugin_config_directory = os.path.expanduser(conf['eva']['config_directory'])
        # Ensure the configs directory exists.
        try:
            os.makedirs(plugin_config_directory)
        except FileExistsError:
            pass
        old_configuration = get_plugin_config(plugin_id, plugin_config_directory)
        if old_configuration.filename is None:
            # We're still using default values - create config file for plugin.
            # Update all default values.
            for configuration in conf['plugins'][plugin_id]['config']:
                old_configuration[configuration] = \
                    conf['plugins'][plugin_id]['config'][configuration]
            old_configuration.write(open(plugin_config_directory + '/' + plugin_id + '.conf', 'wb'))
        else:
            # We already have a config file for this plugin, save to disk.
            conf['plugins'][plugin_id]['config'].write()
