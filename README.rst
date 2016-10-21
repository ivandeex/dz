.. image:: https://travis-ci.org/ivandeex/dz.svg?branch=master
     :target: https://travis-ci.org/ivandeex/dz
     :alt: Build Status

.. image:: https://coveralls.io/repos/github/ivandeex/dz/badge.svg?branch=master
     :target: https://coveralls.io/github/ivandeex/dz?branch=master
     :alt: Coverage Status

.. image:: https://landscape.io/github/ivandeex/dz/master/landscape.svg?style=flat
   :target: https://landscape.io/github/ivandeex/dz/master
   :alt: Code Health

.. image:: https://requires.io/github/ivandeex/dz/requirements.svg?branch=master
     :target: https://requires.io/github/ivandeex/dz/requirements/?branch=master
     :alt: Requirements Status

D.Z.
====

`DZ` is an app for Django coupled with a site scraper
built on top of the scraping framework `Scrapy`.

Installation
============

D.Z. can be installed by cloning this github repository::

    $ git clone https://github.com/ivandeex/dz.git

Then create virtual environment and run prepare.sh
to install python requirements and setup database::

    $ cd dz
    $ virtualenv venv
    $ source ./venv/bin/activate
    $ ./prepare.sh all

Running
=======

To run a live server with fake data, type::

    $ ./prepare.sh liveserver

and point your browser to http://localhost:8000/, then click `Enter` when finished.

To run production web server and schedule crawl jobs, type::

    $ honcho start web botservice botlog

Testing
=======

DZ has somewhat incomplete test suite powered by Django. To run it, type this::

    $ ./prepare.sh test

License
=======
MIT
