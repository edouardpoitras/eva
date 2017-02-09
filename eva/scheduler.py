"""
Holds functions required to start and manage the Eva scheduler.
"""

import gossip
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from eva.util import get_mongo_client
from eva import conf

def job_failed(event):
    """
    A callback function that gets called when an
    `APScheduler <https://apscheduler.readthedocs.io/en/latest/>`_ job fails.

    Currently will simply fire the `eva.scheduler.job_failed` trigger with the
    failed event object.
    """
    gossip.trigger('eva.scheduler.job_failed', event=event)

def job_succeeded(event):
    """
    A callback function that gets called when an
    `APScheduler <https://apscheduler.readthedocs.io/en/latest/>`_ job succeeds.

    Currently will simply fire the `eva.scheduler.job_succeeded` trigger with the
    success event object.
    """
    gossip.trigger('eva.scheduler.job_succeeded', event=event)

def get_scheduler():
    """
    Function used to return the `APScheduler <https://apscheduler.readthedocs.io/en/latest/>`_
    instance that is used by Eva and plugins.

    .. warning::

        This function should only be used by Eva. Plugins should access the
        scheduler through Eva's singleton object::

            from eva import scheduler
            # This will fire off the job immediately.
            scheduler.add_job(func_name, id="eva_<plugin_id>_job")

    .. todo::

        Need to add listeners for all event types:
        https://apscheduler.readthedocs.io/en/latest/modules/events.html#event-codes

    :note: This function most likely needs to be revisited as it may not be
        thread-safe. Eva and plugins can modify the config singleon
        simultaneously inside and outside of jobs.

    :return: The scheduler object used by plugins to schedule long-running jobs.
    :rtype: `apscheduler.schedulers.background.BackgroundScheduler
        <https://apscheduler.readthedocs.io/en/latest/modules/schedulers/background.html>`_
    """
    client = get_mongo_client()
    db_name = conf['mongodb']['database']
    scheduler = BackgroundScheduler(jobstore=MongoDBJobStore(database=db_name,
                                                             collection='scheduler',
                                                             client=client))
    scheduler.add_listener(job_succeeded, EVENT_JOB_EXECUTED)
    scheduler.add_listener(job_failed, EVENT_JOB_ERROR)
    scheduler.start()
    return scheduler
