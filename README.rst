Rover Open edX Platform
=======================
.. image:: https://img.shields.io/badge/hack.d-Lawrence%20McDaniel-orange.svg
     :target: https://lawrencemcdaniel.com
     :alt: Hack.d Lawrence McDaniel

This is the main edX platform which consists of LMS and Studio. 

Documentation
-------------
Documentation for all Rover source code is now located 
in `Read The Docs <https://querium-adminroverbyopenstaxorg.readthedocs-hosted.com>`__

**Legacy Documentation** can be found in the `docs index.rst`_.

.. _docs index.rst: docs/index.rst



Git Work Flow
------------

.. image:: docs/git-workflow.png


Work with a feature branch off querium.dev
------------
.. code-block:: bash

  # how to create a new feature branch named "querium.dev-oauth" from querium.dev
  git checkout -b querium.dev-oauth querium.dev
  git branch --set-upstream-to=origin/querium.dev-oauth querium.dev-oauth

  # How to merge querium.dev-oauth modifications into querium.dev
  git checkout querium.dev
  git pull                            # to synch your local repo with remote
  git checkout querium.dev-oauth
  git pull                            # to sunch your locla repo with remote
  git rebase -i querium.dev           # rebase querium.dev-oauth to querium.dev
  git checkout querium.dev
  git merge querium.dev-oauth         # merge querium.dev-oauth into querium.dev

  # Push your changes to Github
  git push origin querium.dev
  git push origin querium.dev-oauth



Merge querium.dev into querium.master
------------
.. code-block:: bash

  git checkout querium.master
  git pull                            # to synch your local repo with remote
  git checkout querium.dev
  git pull                            # to sunch your local repo with remote
  git rebase -i querium.master        # rebase querium.dev to querium.master
  git checkout querium.master
  git merge querium.dev               # merge querium.dev into querium.master

  # Push your changes to Github
  git push origin querium.master
  git push origin querium.dev



License
-------

The code in this repository is licensed under version 3 of the AGPL
unless otherwise noted. Please see the `LICENSE`_ file for details.

.. _LICENSE: https://github.com/edx/edx-platform/blob/master/LICENSE



