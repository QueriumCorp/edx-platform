<<<<<<< HEAD
Rover Open edX Platform
=======================
.. image:: https://img.shields.io/badge/hack.d-Lawrence%20McDaniel-orange.svg
     :target: https://lawrencemcdaniel.com
     :alt: Hack.d Lawrence McDaniel

This is the main edX platform which consists of LMS and Studio. 
||||||| df94c82a04
This is the main edX platform which consists of LMS and Studio.


Installation
------------

Please refer to the following wiki pages in our `configuration repo`_ to
install edX:

-  `edX Developer Stack`_: These instructions are for developers who want
   to contribute or make changes to the edX source code.
-  `edX Full Stack`_: Using Vagrant/Virtualbox this will setup all edX
   services on a single server in a production like configuration.
-  `edX Ubuntu 16.04 64-bit Installation`_: This will install edX on an
   existing Ubuntu 16.04 server.

.. _configuration repo: https://github.com/edx/configuration
.. _edX Developer Stack: https://github.com/edx/devstack
.. _edX Full Stack: https://openedx.atlassian.net/wiki/display/OpenOPS/Running+Fullstack
.. _edX Ubuntu 16.04 64-bit Installation: https://openedx.atlassian.net/wiki/display/OpenOPS/Native+Open+edX+Ubuntu+16.04+64+bit+Installation


License
-------

The code in this repository is licensed under version 3 of the AGPL
unless otherwise noted. Please see the `LICENSE`_ file for details.

.. _LICENSE: https://github.com/edx/edx-platform/blob/master/LICENSE


The Open edX Portal
---------------------

See the `Open edX Portal`_ to learn more about Open edX. You can find
information about the edX roadmap, as well as about hosting, extending, and
contributing to Open edX. In addition, the Open edX Portal provides product
announcements, the Open edX blog, and other rich community resources.

To comment on blog posts or the edX roadmap, you must create an account and log
in. If you do not have an account, follow these steps.

#. Visit `open.edx.org/user/register`_.
#. Fill in your personal details.
#. Select **Create New Account**. You are then logged in to the `Open edX
   Portal`_.

.. _Open edX Portal: https://open.edx.org
.. _open.edx.org/user/register: https://open.edx.org/user/register
=======
This is the core repository of the Open edX software. It includes the LMS
(student-facing, delivering courseware), and Studio (course authoring)
components.

Installation
------------

Installing and running an Open edX instance is not simple.  We strongly
recommend that you use a service provider to run the software for you.  They
have free trials that make it easy to get started:
https://openedx.org/get-started/

If you will be modifying edx-platform code, the `Open edX Developer Stack`_ is
a Docker-based development environment.

If you want to run your own Open edX server and have the technical skills to do
so, `Open edX Ubuntu 16.04 64-bit Installation`_ has instructions to install
it on an existing Ubuntu 16.04 server.

.. _Open edX Developer Stack: https://github.com/edx/devstack
.. _Open edX Ubuntu 16.04 64-bit Installation: https://openedx.atlassian.net/wiki/display/OpenOPS/Native+Open+edX+Ubuntu+16.04+64+bit+Installation


License
-------

The code in this repository is licensed under version 3 of the AGPL
unless otherwise noted. Please see the `LICENSE`_ file for details.

.. _LICENSE: https://github.com/edx/edx-platform/blob/master/LICENSE


More about Open edX
-------------------

See the `Open edX site`_ to learn more about the Open edX world. You can find
information about hosting, extending, and contributing to Open edX software. In
addition, the Open edX site provides product announcements, the Open edX blog,
and other rich community resources.

.. _Open edX site: https://openedx.org
>>>>>>> 27b0e8d845d7795eefda17ea2bc2ba58460bb092

Documentation
-------------
Documentation for all Rover source code is now located 
in `Read The Docs <http://readthedocs.roverbyopenstax.org/>`__

<<<<<<< HEAD
**Legacy Documentation** can be found in the `docs index.rst`_.
||||||| df94c82a04
Documentation details can be found in the `docs index.rst`_.
=======
Documentation can be found at https://docs.edx.org.
>>>>>>> 27b0e8d845d7795eefda17ea2bc2ba58460bb092


<<<<<<< HEAD
||||||| df94c82a04
Getting Help
------------

If you’re having trouble, we have several different mailing lists where
you can ask for help:

-  `openedx-ops`_: everything related to *running* Open edX. This
   includes installation issues, server management, cost analysis, and
   so on.
-  `openedx-translation`_: everything related to *translating* Open edX
   into other languages. This includes volunteer translators, our
   internationalization infrastructure, issues related to Transifex, and
   so on.
-  `openedx-analytics`_: everything related to *analytics* in Open edX.
-  `edx-code`_: anything else related to Open edX. This includes feature
   requests, idea proposals, refactorings, and so on.

Our real-time conversations are on Slack. You can request a `Slack
invitation`_, then join our `community Slack team`_.

.. _openedx-ops: https://groups.google.com/forum/#!forum/openedx-ops
.. _openedx-translation: https://groups.google.com/forum/#!forum/openedx-translation
.. _openedx-analytics: https://groups.google.com/forum/#!forum/openedx-analytics
.. _edx-code: https://groups.google.com/forum/#!forum/edx-code
.. _Slack invitation: https://openedx-slack-invite.herokuapp.com/
.. _community Slack team: http://openedx.slack.com/


Issue Tracker
-------------

`We use JIRA for our issue tracker`_, not GitHub Issues. To file a bug
or request a new feature, please make a free account on our JIRA and
create a new issue! If you’re filing a bug, we’d appreciate it if you
would follow `our guidelines for filing high-quality, actionable bug
reports`_. Thanks!

.. _We use JIRA for our issue tracker: https://openedx.atlassian.net/
.. _our guidelines for filing high-quality, actionable bug reports: https://openedx.atlassian.net/wiki/display/SUST/How+to+File+a+Quality+Bug+Report


How to Contribute
-----------------

Contributions are very welcome, but for legal reasons, you must submit a
signed `individual contributor agreement`_ before we can accept your
contribution. See our `CONTRIBUTING`_ file for more information – it
also contains guidelines for how to maintain high code quality, which
will make your contribution more likely to be accepted.


Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email
security@edx.org.
=======
Getting Help
------------

If you're having trouble, we have discussion forums at
https://discuss.openedx.org where you can connect with others in the community.

Our real-time conversations are on Slack. You can request a `Slack
invitation`_, then join our `community Slack team`_.

For more information about these options, see the `Getting Help`_ page.

.. _Slack invitation: https://openedx-slack-invite.herokuapp.com/
.. _community Slack team: http://openedx.slack.com/
.. _Getting Help: https://openedx.org/getting-help


Issue Tracker
-------------

We use JIRA for our issue tracker, not GitHub issues. You can search
`previously reported issues`_.  If you need to report a problem,
please make a free account on our JIRA and `create a new issue`_.

.. _previously reported issues: https://openedx.atlassian.net/projects/CRI/issues
.. _create a new issue: https://openedx.atlassian.net/secure/CreateIssue.jspa?issuetype=1&pid=11900


How to Contribute
-----------------

Contributions are welcome! The first step is to submit a signed
`individual contributor agreement`_.  See our `CONTRIBUTING`_ file for more
information – it also contains guidelines for how to maintain high code
quality, which will make your contribution more likely to be accepted.


Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email
security@edx.org.
>>>>>>> 27b0e8d845d7795eefda17ea2bc2ba58460bb092

<<<<<<< HEAD
||||||| df94c82a04
.. _individual contributor agreement: http://open.edx.org/sites/default/files/wysiwyg/individual-contributor-agreement.pdf
.. _CONTRIBUTING: https://github.com/edx/edx-platform/blob/master/CONTRIBUTING.rst
=======
.. _individual contributor agreement: https://openedx.org/wp-content/uploads/2019/01/individual-contributor-agreement.pdf
.. _CONTRIBUTING: https://github.com/edx/edx-platform/blob/master/CONTRIBUTING.rst
>>>>>>> 27b0e8d845d7795eefda17ea2bc2ba58460bb092
