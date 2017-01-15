#pylint: disable=C0103
"""
Initialize necessary variables and objects.
"""

# Keep track of when Eva was first started.
import datetime
START_TIME = datetime.datetime.now()
# Shortcut for plugins to access the Eva configuration singleton.

from eva.config import get_config
conf = get_config()

# Shortcut for plugins to access Eva logger.
from eva.logger import Logger
log = Logger()

# Shortcut for plugins to access the Eva scheduler.
from eva.scheduler import get_scheduler
scheduler = get_scheduler()

# Shortcut for plugins to access the publish function.
from eva.util import publish
