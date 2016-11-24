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

`DZ` is a Django application coupled with a site scraper built on top of
the `Scrapy` framework.

Developer environment
=====================

D.Z. can be installed by cloning this github repository::

    $ git clone https://github.com/ivandeex/dz.git

Then run ``scripts/make.sh``, which will create a virtual environment,
install python and `node.js` requirements and setup database::

    $ cd dz
    $ ./scripts/make.sh setup-devel
    $ ./scripts/make.sh prepare

Running development server
==========================

To run a live server with fake data, type::

    $ ./scripts/make.sh liveserver

and point your browser to http://localhost:8000/, then click `Enter` when finished.

To run production web server and schedule crawl jobs, type::

    $ honcho start web botservice botlog

Testing
=======

DZ has a Django-powered test suite, which can be run as::

    $ ./scripts/make.sh test

Installing on production
========================

First, build and install bot executable on a Windows box::

    $ cd dz
    $ ./scripts/make.sh build-bot
    $ ./scripts/make.sh install-bot

Then install backend and configure nginx on a Linux production server::

    $ ./scripts/make.sh install-web

License
=======

The MIT License (MIT)
---------------------

Copyright (c) 2016, ivandeex

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
