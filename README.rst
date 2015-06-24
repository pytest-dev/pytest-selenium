pytest-selenium
===============

pytest-selenium is a plugin for `py.test <http://pytest.org>`_ that provides
support for running `Selenium <http://seleniumhq.org/>`_ based tests. This
plugin is still in development. Please check back for updates.

.. image:: https://img.shields.io/pypi/l/pytest-selenium.svg
   :target: https://github.com/davehunt/pytest-selenium/blob/master/LICENSE
   :alt: License
.. image:: https://img.shields.io/pypi/v/pytest-selenium.svg
   :target: https://pypi.python.org/pypi/pytest-selenium/
   :alt: PyPI
.. image:: https://img.shields.io/travis/davehunt/pytest-selenium.svg
   :target: https://travis-ci.org/davehunt/pytest-selenium/
   :alt: Travis
.. image:: https://img.shields.io/github/issues-raw/davehunt/pytest-selenium.svg
   :target: https://github.com/davehunt/pytest-selenium/issues
   :alt: Issues
.. image:: https://img.shields.io/requires/github/davehunt/pytest-selenium.svg
   :target: https://requires.io/github/davehunt/pytest-selenium/requirements/?branch=master
   :alt: Requirements

Server and Grid integration
---------------------------

To run your automated tests against a
`Selenium server <https://github.com/SeleniumHQ/selenium/wiki/RemoteWebDriverServer>`_
or or `Selenium Grid <https://github.com/SeleniumHQ/selenium/wiki/Grid2>`_ you
must have a server running and know the host and port of the server.

By default Selenium will listen on host 127.0.0.1 and port 4444. This is also
the default when running tests against a remote driver.

Running tests
^^^^^^^^^^^^^

To run your automated tests, simply specify ``Remote`` as your driver and
provide the ``browserName`` capability for the browser you want to launch::

  py.test --driver=Remote --capability=browserName:firefox

Browser selection is determined using capabilities. Check the
`documentation <https://github.com/SeleniumHQ/selenium/wiki/DesiredCapabilities#used-by-the-selenium-server-for-browser-selection>`_
for details of accepted values. There are also a number of
`browser specific capabilities <https://github.com/SeleniumHQ/selenium/wiki/DesiredCapabilities#browser-specific-capabilities>`_
that can be set. Be sure to also check the documentation for your chosen
driver, as the accepted capabilities may differ.

Note that if your server is not running locally or is running on an alternate
port you will need to specify the ``--host`` and ``--port`` command line
options.

Sauce Labs integration
----------------------

To run your automated tests using `Sauce Labs <https://saucelabs.com/>`_, you
must provide a valid username and API key. This can be done either by using
a ``setup.cfg`` file or by setting the ``SAUCELABS_USERNAME`` and
``SAUCELABS_API_KEY`` environment variables.

Configuration
^^^^^^^^^^^^^

Below is an example ``setup.cfg`` showing the configuration options:

.. code-block:: ini

  [pytest]
  sauce_labs_username = username
  sauce_labs_api_key = secret
  sauce_labs_job_visibility = public
  sauce_labs_tags = tag1 tag2

The `sauce_labs_job_visibility` entry is used to determine who you share your
Sauce Labs jobs with. Check the
`documentation <https://saucelabs.com/docs/additional-config#sharing>`_ for the
accepted values. If not set, this defaults to
`public restricted <https://saucelabs.com/docs/additional-config#restricted>`_.

The ``sauce_labs_tags`` entry is an optional space separated list of tags that
can be used to filter the jobs in the Sauce Labs dashboard.

Running tests
^^^^^^^^^^^^^

To run your automated tests, simply specify ``SauceLabs`` as your driver::

  py.test --driver=SauceLabs --capability=browserName:Firefox

See the `supported platforms <https://docs.saucelabs.com/reference/platforms-configurator/>`_
to help you with your configuration. Additional capabilities can be set using
the ``--capability`` command line arguments. See the
`test configuration documentation <https://docs.saucelabs.com/reference/test-configuration/>`_
for full details of what can be configured.

Job visibility
^^^^^^^^^^^^^^

You can specify the job sharing level for individual tests by setting a mark on
the test method. This takes priority over the ``sauce_labs_job_visibility`` entry in the
configuration file:

.. code-block:: python

  import pytest
  @pytest.mark.sauce_labs_job_visibility('public')
  def test_public(selenium):
      assert True

You can also explicitly mark the test as private:

.. code-block:: python

  import pytest
  @pytest.mark.sauce_labs_job_visibility('private')
  def test_private(selenium):
      assert True

For the full list of accepted values, check the
`Sauce Labs documentation <https://saucelabs.com/docs/additional-config#sharing>`_.

BrowserStack integration
------------------------

To run your automated tests using
`BrowserStack <https://www.browserstack.com/>`_, you must provide a valid
username and access key. This can be done either by using a ``setup.cfg`` file or
by setting the ``BROWSERSTACK_USERNAME`` and ``BROWSERSTACK_ACCESS_KEY``
environment variables.

Configuration
^^^^^^^^^^^^^

Below is an example ``setup.cfg`` showing the configuration options:

.. code-block:: ini

  [pytest]
  browserstack_username = username
  browserstack_access_key = secret

Running tests
^^^^^^^^^^^^^

To run your automated tests, simply specify ``BrowserStack`` as your driver::

  py.test --driver=BrowserStack --capability=browserName:firefox

See the `capabilities documentation <https://www.browserstack.com/automate/capabilities>`_
for additional configuration that can be set using ``--capability`` command line
arguments.
