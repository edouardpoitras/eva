.. Eva documentation master file, created by
   sphinx-quickstart on Fri Jan  6 15:43:20 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Documentation
=============

Eva is an open source alternative to Amazon Echo or Google Home.
The core of Eva is a simple service that provides hooks for plugins during
interactions with users. On it's own, Eva does very little. It's potential comes
from the `plugins <https://github.com/edouardpoitras/eva-plugin-repository>`_
the user chooses to enable (or create).

Installation
++++++++++++

If you wish to use docker-compose to run Eva, ensure you have installed
`Docker <https://docs.docker.com/engine/installation/>`_ and the
`docker-compose <https://docs.docker.com/compose/install/>`_ utility.

If you wish to run Eva outside of Docker, install the required Python
dependencies::

    pip3 install -r requirements.txt

.. todo::

    Allow for a proper pip install eva command.

First Steps
+++++++++++++

To run Eva with docker-compose, you simply have to run the following command::

    docker-compose up

This may take a while on the first run as the Eva container is built and all
the dependencies are installed.

To run Eva outside of Docker, you simply have to execute the
``eva.directory.serve()`` function. This is exactly what the ``serve.py`` script
does for you::

    python3 serve.py

The default setting for Eva is to install the `Web UI Plugins <https://github.com/edouardpoitras/eva-web-ui-plugins>`_
and `Web UI Updater <https://github.com/edouardpoitras/eva-web-ui-updater>`_
plugins (and their dependencies) on first startup. This behaviour can be changed
by modifying the core Eva :ref:`configuration <core-configuration>` file
(typically found at ``~/eva/eva.conf``).

Alternatively, once Eva is started, you may navigate to the Web UI
(https://localhost:8080) and enable/disable plugins as needed.

.. note::

    A self-signed certificate warning from your browser is normal at this point.

While you're in the Web UI, you may as well download and enable the
`Web UI Interact <https://github.com/edouardpoitras/eva-web-ui-interact>`_
plugin which will allow you to test out Eva from the Web UI.

We discuss Eva clients more in depth on the :ref:`clients` page.

Eva's capabilities are entirely controlled by the plugins enabled by the user.
Try enabling the `echo <https://github.com/edouardpoitras/eva-echo>`_ plugin and
see if Eva echos back the commands you send it. Also try the
`weather <https://github.com/edouardpoitras/eva-weather>`_ plugin and ask Eva
for the current forecast (you'll need to setup DarkSky API keys).

.. note::

    You will need to have enabled a voice recognition plugin if you wish to speak to Eva instead of using text commands.

.. note::

    You will need to enable a Text-to-Speech plugin if you wish to receive spoken words from Eva as a response.

.. toctree::
   :maxdepth: 2

   clients
   configuration
   plugin_development
   triggers
   api

Index and Search
================

* :ref:`genindex`
* :ref:`search`
