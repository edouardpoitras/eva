# Every Eva plugin should have a name matching it's python module name.
name = string(default='Plugin Unknown')
# Description of this Eva plugin.
description = string(default='No description')
# The current version of the Eva plugin.
version = string(default='0.0.0')
# List of Eva plugin dependencies for this plugin.
dependencies = force_list(default=list())
# Use the requirements.txt for Python module dependencies.
