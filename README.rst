Querium  Open edX Platform Fork
This is the main edX platform which consists of LMS and Studio.


Installation / Updates (as per Lawrence McDaniel)
------------

*Add any changes to /edx/app/edx_ansible/server-vars.yml*

.. code-block:: bash

  sudo ./edx.platform-stop.sh
  sudo rm -rf /edx/app/edxapp/edx-platform
  sudo /edx/bin/update edx-platform querium.dev
  sudo ./edx.install-theme.sh
  sudo ./edx.install-config.sh
  sudo ./edx.compile-assets.sh
  sudo ./edx.platform-restart-full.sh


Custom Modules (as per Lawrence McDaniel)
------------

`Salesforce Integration Module`_: Rest api, django admin console, and manage.py command line tools to capture and upload salesforce tracking data for Open Stax marketing team.

.. _Salesforce Integration Module: https://github.com/QueriumCorp/edx-platform.roverplatform.com/blob/querium.master/cms/djangoapps/openstax_integrator



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

Documentation
-------------

Documentation details can be found in the `docs index.rst`_.

.. _docs index.rst: docs/index.rst

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

.. _individual contributor agreement: http://open.edx.org/sites/default/files/wysiwyg/individual-contributor-agreement.pdf
.. _CONTRIBUTING: https://github.com/edx/edx-platform/blob/master/CONTRIBUTING.rst
