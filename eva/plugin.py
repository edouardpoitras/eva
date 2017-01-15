"""
All necessary helper functions to facilitate plugin management.
"""

import os
import sys
import pip
import shutil
import importlib
import gossip
from git import Repo
from eva.config import get_eva_directory, get_config, get_plugin_config
from eva import conf
from eva import log

def load_plugins():
    """
    The function that is called during Eva's boot sequence.
    Will fetch the plugin directory , load all of the plugins' info files, load
    all of the plugin's configurations, and enable all the required plugins and
    their dependencies specified in Eva's configuration file.

    Fires the `eva.plugins_loaded` trigger.
    """
    # Get all plugins.
    plugin_dir = get_plugin_directory()
    load_plugin_directory(plugin_dir)
    # Get all user-defined configurations.
    config_dir = conf['eva']['config_directory']
    if '~' in config_dir: config_dir = os.path.expanduser(config_dir)
    load_plugin_configs(config_dir)
    # Enable all necessary plugins.
    enable_plugins()
    gossip.trigger('eva.plugins_loaded')
    log.info('Plugins loaded successfully')

def get_plugin_directory():
    """
    Helper function to get Eva's plugin directory specified in the config file.

    Will automatically replace ``~`` with the user's home directory.
    """
    plugin_dir = conf['eva']['plugin_directory']
    if '~' in plugin_dir: plugin_dir = os.path.expanduser(plugin_dir)
    return plugin_dir

def load_plugin_directory(plugin_dir):
    """
    Will crawl Eva's plugin directory and load the plugin info files for all the
    valid plugins found. The info file information will eventually be used when
    enabling plugins and their dependencies.

    This function does not return anything. It stores all plugin information in
    the ``conf['plugins']`` dict. Every plugin should have the following accessible
    information once this function is run::

        conf['plugins'][<plugin_id>] = {
            'info': 'Data from the info file for this plugin'
            'path': 'The path of the plugin on disk'
            'git': 'True if the plugin is a git repo (and can be updated)'
        }

    Use the following statement to access the conf dict: ``from eva import conf``

    :param plugin_dir: The directory containing available Eva plugins. Typically
        the return value of :func:`get_plugin_directory`.
    :type plugin_dir: string
    """
    log.info('Loading plugins from: %s' %plugin_dir)
    plugins = {}
    if os.path.isdir(plugin_dir):
        for plugin_name in os.listdir(plugin_dir):
            plugin_path = plugin_dir + '/' + plugin_name
            if not os.path.isdir(plugin_path):
                # A stranded file in the plugins directory.
                log.debug('Ignoring file: %s' %plugin_path)
                continue
            if plugin_name.startswith('_') or plugin_name.endswith('_'):
                # Skip folders that start or end with '_'.
                log.debug('Skipping file: %s' %plugin_path)
                continue
            # Valid plugins must have an info file and matching py file.
            if not os.path.exists(plugin_path + '/' + plugin_name + '.info'):
                log.debug('Plugin found with no info file - skipping: %s' %plugin_name)
                continue
            if not os.path.exists(plugin_path + '/' + plugin_name + '.py'):
                log.debug('Plugin found with no python file - skipping: %s' %plugin_name)
                continue
            # At this point we assume we have a valid plugin.
            # Fetch plugin info.
            plugins[plugin_name] = {'info': load_plugin_info(plugin_path, plugin_name),
                                    'path': plugin_path,
                                    'git': plugin_is_git_repo(plugin_path)}
            log.debug('Plugin info: %s' %plugins[plugin_name])
        if 'plugins' in conf:
            conf['plugins'].update(plugins)
        else:
            conf['plugins'] = plugins
    else:
        log.warning('Plugin directory does not exist - ' + plugin_dir)

def load_plugin_configs(config_dir):
    """
    Function that loops through all available plugins and loads their
    corresponding plugin configuration if found in the configuration directory
    provided.

    The :func:`load_plugin_directory` function must be called before calling this
    function as it relies on the plugin info files having been loaded into the
    ``conf['plugins']`` dict.

    :param config_dir: The configuration directory that holds all Eva plugin
        configuration files.
    :type config_dir: string
    """
    # Loop through plugins and fetch configs.
    log.info('Loading plugin configuration files from %s' %config_dir)
    if 'plugins' not in conf:
        log.warning('No plugin configurations loaded')
        return
    for plugin in conf['plugins']:
        plugin_config = get_plugin_config(plugin, config_dir)
        conf['plugins'][plugin]['config'] = plugin_config
        log.debug('Loaded plugin configuration for %s: %s' %(plugin, plugin_config))

def enable_plugins():
    """
    Function that enables all plugins specified in Eva configuration file.
    Will enable all available plugins if none is specified in the configs.
    """
    log.info('Enabling plugins specified in configuration')
    to_enable = conf['eva']['enabled_plugins']
    if len(to_enable) < 1:
        log.info('No plugins specified in configuration, enabling all available plugins')
        to_enable = conf['plugins'].keys()
    downloadable_plugins = get_downloadable_plugins()
    for plugin_name in to_enable:
        enable_plugin(plugin_name, downloadable_plugins)

def enable_plugin(plugin_id, downloadable_plugins=None):
    """
    Enables a single plugin, which entails:

        * If already enabled, return
        * If plugin not found, search online repository
        * Download if found in repository, else log and return
        * Recusively enable dependencies if found, else log error and return
        * Run a ``pip install -r requirements.txt --user`` if requirements file found
        * Insert plugin directory in Python path and dynamically import module
        * Execute the ``<plugin>.on_enable()`` function if found

    :todo: Need to clean up, comment, and shorten this function.
    :param plugin_id: The plugin id to enable.
    :type plugin_id: string
    :param downloadable_plugins: A dict of plugins that are available for
        download from Eva's repository. This is typically the return value of the
        :func:`get_downloadable_plugins` function.
    :type downloadable_plugins: dict
    """
    if plugin_enabled(plugin_id): return
    log.debug('Attempting to enable %s' %plugin_id)
    if downloadable_plugins is None:
        downloadable_plugins = get_downloadable_plugins()
    if 'plugins' not in conf: conf['plugins'] = {}
    if plugin_id not in conf['plugins']:
        if plugin_id not in downloadable_plugins:
            log.error('Could not enable plugin %s: plugin not found locally or in repository' %plugin_id)
            return
        destination = get_plugin_directory() + '/' + plugin_id
        download_plugin(plugin_id, destination)
        conf['plugins'][plugin_id] = {'info': load_plugin_info(destination, plugin_id),
                                      'path': destination,
                                      'git': True}
        plugin_config_dir = os.path.expanduser(conf['eva']['config_directory'])
        conf['plugins'][plugin_id]['config'] = get_plugin_config(plugin_id, plugin_config_dir)
    plugin_conf = conf['plugins'][plugin_id]
    dependencies = plugin_conf['info']['dependencies']
    local_plugins = conf['plugins'].keys()
    available_plugs = local_plugins + list(downloadable_plugins.keys())
    # Don't bother enabling if we can't find all dependencies.
    missing_deps = set(dependencies) - set(available_plugs)
    if len(missing_deps) > 0:
        log.error('Could not import plugin ' + plugin_id + ' due to unmet dependencies - ' + ', '.join(missing_deps))
        return
    # Enable dependencies.
    for dependency in dependencies:
        log.debug('Enabling %s dependency: %s' %(plugin_id, dependency))
        enable_plugin(dependency)
    # Install any python module dependencies specified by the plugin.
    plugin_path = conf['plugins'][plugin_id]['path']
    requirements_file = plugin_path + '/requirements.txt'
    if os.path.isfile(requirements_file):
        log.info('Found requirements.txt for %s. Installing python dependencies' %plugin_id)
        pip.main(['install','-r', requirements_file, '--user', '-qq'])
    # Do the import of our python module.
    try:
        # Let's add this directory to our path to import the module.
        if plugin_path not in sys.path: sys.path.insert(0, plugin_path)
        mod = importlib.import_module(plugin_id)
        conf['plugins'][plugin_id]['module'] = mod
        log.info('Plugin enabled: %s' %plugin_id)
        try:
            log.debug('Running %s.on_enable()' %plugin_id)
            mod.on_enable()
        except AttributeError: # Not necessary to have a on_enable() function.
            pass
    except ImportError as err:
        log.error('Could not import plugin ' + plugin_id+ ' - ' + str(err))

def plugin_enabled(plugin_id):
    """
    Function used to determine whether a plugin is enabled or not.
    Simply looks in the ``conf['plugins']`` dict to see if the imported module is
    present.

    :param plugin_id: The plugin name.
    :type plugin_id: string
    :return: True if the plugin seems to be enabled, False otherwise.
    :rtype: boolean
    """
    if 'plugins' not in conf: return False
    plugins = conf['plugins']
    if plugin_id in plugins:
        return 'module' in plugins[plugin_id]
    return False

def load_plugin_info(plugin_path, plugin_id):
    """
    Given a plugin path and plugin name, this function will attempt to return
    a loaded plugin info file as a ConfigObj specification instance.

    :param plugin_path: The path of the plugin in question.
    :type plugin_path: string
    :param plugin_id: The plugin ID.
    :type plugin_id: string
    :return: A ConfigObj specification instance.
    :rtype: `ConfigObj  <https://configobj.readthedocs.io/en/latest/>`_
    """
    plugin_file = plugin_path + '/' + plugin_id + '.info'
    spec_file = get_eva_directory() + '/plugin.info.spec'
    return get_config(plugin_file, spec_file)

def plugin_is_git_repo(plugin_path):
    """
    Will attempt to determine if the plugin_path specified is a git repo.
    Simply checks if the ``.git`` folder exists.

    :todo: There's probably a better way of doing this.
    :param plugin_path: The path of the plugin to check.
    :type plugin_path: string
    """
    return os.path.isdir(plugin_path + '/.git')

def num_available_plugins():
    """
    Function used to get the number of available plugins.
    Will simply check the length of the ``conf['plugins']`` dict.

    :return: The number of available plugins.
    :rtype: integer
    """
    return len(conf['plugins'])

def num_enabled_plugins():
    """
    Function used to determine the number of enabled plugins.
    Simply checks if the ``module`` key exists in the ``conf['plugins'][<plugin>]``
    dict.

    :return: The number of enabled plugins.
    :rtype: integer
    """
    enabled = 0
    for plugin in conf['plugins']:
        if 'module' in conf['plugins'][plugin]:
            enabled += 1
    return enabled

def get_downloadable_plugins(pull_latest=False):
    """
    Gets a dict of downloadable plugins from the plugin repository.
    The plugin repository is simply a git repo with a list of available plugins
    stored in a CSV file. The repository will be cloned locally if not found.

    :param pull_latest: Whether or not to perform a ``git pull`` on the
        repository before parsing the plugins.
    :type pull_latest: boolean
    :return: A dict of all available plugins for download. The format is:

    ::

        {
            <plugin_id> {
                'id': <id>,
                'name': <name>,
                'description': <description>,
                'url': <url>
            }
            ...
        }

    :rtype: dict
    """
    repo_url = conf['eva']['plugin_repository']
    plugin_repo_path = conf['eva']['plugin_repo_path']
    try:
        if not os.path.isdir(plugin_repo_path):
            Repo.clone_from(repo_url, plugin_repo_path)
        elif pull_latest:
            pull_repo(path)
    except Exception as err: #pylint: disable=W0703
        log.error('Could not get list of downloadable plugins: %s' %err)
        return {}
    fhandle = open(plugin_repo_path + '/plugins.csv')
    plugins = {}
    for line in fhandle.readlines():
        line = line.strip()
        _id, name, description, url = line.split(',')
        plugins[_id] = {'id': _id,
                        'name':  name,
                        'description': description,
                        'url': url}
    return plugins

def refresh_downloadable_plugins():
    """
    Will remove the entire local directory holding the plugin repository and
    re-clone the repo locally. This can be useful when changing plugin repositories.
    """
    plugin_repo_path = conf['eva']['plugin_repo_path']
    if os.path.exists(plugin_repo_path): shutil.rmtree(plugin_repo_path)
    get_downloadable_plugins()

def download_plugin(plugin_id, destination):
    """
    Will download the specified plugin to the specified destination if it is
    found in the plugin repository.

    :param plugin_id: The plugin ID to download.
    :type plugin_id: string
    :param destination: The destination to download the plugin on disk.
    :type destination: string
    """
    downloadable_plugins = get_downloadable_plugins()
    if plugin_id not in downloadable_plugins:
        log.error('Could not find plugin in repository: %s' %plugin_id)
        return
    if os.path.exists(destination): shutil.rmtree(destination)
    Repo.clone_from(downloadable_plugins[plugin_id]['url'], destination)
    log.info('%s plugin downloaded' %plugin_id)

def pull_repo(repo_path):
    """
    Helper function to perform the equivalent of a ``git pull origin master``
    on a specified git repository on disk.

    :param repo_path: The path of the git repository to pull.
    :type repo_path: string
    """
    repo = Repo(repo_path)
    origin = repo.remotes.origin
    repo.head.ref.set_tracking_branch(origin.refs.master)
    origin.pull()
