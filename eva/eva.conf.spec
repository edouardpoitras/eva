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
