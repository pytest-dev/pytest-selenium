Development
===========

To contribute to `pytest-selenium` you can use `Hatch`_ to manage
a python virtual environment and `pre-commit <https://pre-commit.com/>`_ to help you with
styling and formatting.

To setup the virtual environment and pre-commit, run:

.. code-block:: bash

  $ hatch -e test run pre-commit install

If you're not using `Hatch`_, to install `pre-commit`, run:

.. code-block:: bash

  $ pip install pre-commit
  $ pre-commit install


Automated Testing
-----------------

All pull requests and merges are tested in `GitHub Actions <https://docs.github.com/en/actions>`_
based on the workflows defined in ``.github/workflows``.

Running Tests
-------------

You will need `Tox <http://tox.testrun.org/>`_ installed to run the tests
against the supported Python versions. If you're using `Hatch`_ it will be
installed for you.

With `Hatch`_, run:

.. code-block:: bash

  $ hatch -e test run tox

Otherwise, to install and run, do:

.. code-block:: bash

  $ pip install tox
  $ tox

Drivers
-------

The tests requires that Docker is available and uses the Selenium/Seleniarm containerized browsers and drivers.

Read more here: `Docker-Seleniarm <https://github.com/seleniumhq-community/docker-seleniarm>`_

To start the browsers (and drivers):

.. code-block:: bash

  $ docker/start

You can check status by running:

.. code-block:: bash

  $ docker ps

To stop the containers, run:

.. code-block:: bash

  $ docker/start down

Releasing a new version
-----------------------

Follow these steps to release a new version of the project:

1. Update your local master with the upstream master (``git pull --rebase upstream master``)
2. Create a new branch and update ``news.rst`` with the new version, today's date, and all changes/new features
3. Commit and push the new branch and then create a new pull request
4. Wait for tests and reviews and then merge the branch
5. Once merged, update your local master again (``git pull --rebase upstream master``)
6. Tag the release with the new release version (``git tag <new tag>``)
7. Push the tag (``git push upstream --tags``)
8. Done. You can monitor the progress on `Travis <https://travis-ci.org/pytest-dev/pytest-selenium/>`_

.. _Hatch: https://hatch.pypa.io/latest/
