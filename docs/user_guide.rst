User Guide
==========

.. contents::

Firefox
*******

To run your automated tests with Firefox, specify ``Firefox`` as your driver::

  py.test --driver Firefox

Chrome
******

To use Chrome as the driver, you need to have ChromeDriver installed. You can
download it
`here <https://sites.google.com/a/chromium.org/chromedriver/downloads>`_.
You may either download ChromeDriver to a location in your PATH, or utilize
the option to specify the driver path during test execution.

To run your automated tests, specify ``Chrome`` as your driver::

  py.test --driver Chrome

If ChromeDriver is not on your path, use ``--driver-path`` to specify the
location::

  py.test --driver Chrome --driver-path /path/to/chromedriver

For more information relating to ChromeDriver, you may read its documentation
`here <https://sites.google.com/a/chromium.org/chromedriver/>`_.

PhantomJS
*********

To use PhantomJS as the driver, you need to have it installed. You can download
it `here <http://phantomjs.org/download.html>`_.
You may either download PhantomJS to a location in your PATH, or utilize
the option to specify the driver path during test execution.

To run your automated tests, specify ``PhantomJS`` as your driver::

  py.test --driver PhantomJS

If PhantomJS is not on your path, use ``--driver-path`` to specify the
location::

  py.test --driver PhantomJS --driver-path /path/to/phantomjs

For more information relating to PhantomJS, you may read its documentation
`here <http://phantomjs.org/quick-start.html>`_.

Selenium Server/Grid
********************

To run your automated tests against a
`Selenium server <https://github.com/SeleniumHQ/selenium/wiki/RemoteWebDriverServer>`_
or a `Selenium Grid <https://github.com/SeleniumHQ/selenium/wiki/Grid2>`_ you
must have a server running and know the host and port of the server.

By default Selenium will listen on host 127.0.0.1 and port 4444. This is also
the default when running tests against a remote driver.

To run your automated tests, simply specify ``Remote`` as your driver. Browser
selection is determined using capabilities. Check the
`documentation <https://github.com/SeleniumHQ/selenium/wiki/DesiredCapabilities#used-by-the-selenium-server-for-browser-selection>`_
for details of accepted values. There are also a number of
`browser specific capabilities <https://github.com/SeleniumHQ/selenium/wiki/DesiredCapabilities#browser-specific-capabilities>`_
that can be set. Be sure to also check the documentation for your chosen
driver, as the accepted capabilities may differ::

  py.test --driver Remote --capability browserName firefox

Note that if your server is not running locally or is running on an alternate
port you will need to specify the ``--host`` and ``--port`` command line
options::

  py.test --driver Remote --host selenium.hostname --port 5555 --capability browserName firefox


Sauce Labs
**********

To run your automated tests using `Sauce Labs <https://saucelabs.com/>`_, you
must provide a valid username and API key. This can be done either by using
a ``setup.cfg`` file or by setting the ``SAUCELABS_USERNAME`` and
``SAUCELABS_API_KEY`` environment variables.

Configuration
-------------

Below is an example ``setup.cfg`` showing the configuration options:

.. code-block:: ini

  [pytest]
  sauce_labs_username = username
  sauce_labs_api_key = secret
  sauce_labs_job_visibility = public

The `sauce_labs_job_visibility` entry is used to determine who you share your
Sauce Labs jobs with. Check the
`documentation <https://saucelabs.com/docs/additional-config#sharing>`_ for the
accepted values. If not set, this defaults to
`public restricted <https://saucelabs.com/docs/additional-config#restricted>`_.

Running tests
-------------

To run your automated tests, simply specify ``SauceLabs`` as your driver::

  py.test --driver SauceLabs --capability browserName Firefox

See the `supported platforms <https://docs.saucelabs.com/reference/platforms-configurator/>`_
to help you with your configuration. Additional capabilities can be set using
the ``--capability`` command line arguments. See the
`test configuration documentation <https://docs.saucelabs.com/reference/test-configuration/>`_
for full details of what can be configured.

Job visibility
--------------

You can specify the job sharing level for individual tests by setting a mark on
the test method. This takes priority over the ``sauce_labs_job_visibility``
entry in the configuration file:

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

BrowserStack
************

To run your automated tests using
`BrowserStack <https://www.browserstack.com/>`_, you must provide a valid
username and access key. This can be done either by using a ``setup.cfg`` file
or by setting the ``BROWSERSTACK_USERNAME`` and ``BROWSERSTACK_ACCESS_KEY``
environment variables.

Configuration
-------------

Below is an example ``setup.cfg`` showing the configuration options:

.. code-block:: ini

  [pytest]
  browserstack_username = username
  browserstack_access_key = secret

Running tests
-------------

To run your automated tests, simply specify ``BrowserStack`` as your driver::

  py.test --driver BrowserStack --capability browserName Firefox

See the
`capabilities documentation <https://www.browserstack.com/automate/capabilities>`_
for additional configuration that can be set using ``--capability`` command line
arguments.

Capabilities
************

Configuration options are specified using a capabilities dictionary. This is
required when using a Selenium server to specify the target environment, but
can also be used to configure local drivers.

To specify capabilities, you can provide a JSON file on the command line using
the `pytest-variables <https://github.com/davehunt/pytest-variables>`_ plugin.
For example if you had a ``capabilties.json`` containing your capabilities, you
would need to include ``--variables capabilities.json`` on your command line.

The following is an example of a variables file including capabilities:

.. code-block:: json

  { "capabilities": {
      "browserName": "Firefox",
      "platform": "MAC" }
  }

Simple capabilities can be set or overridden on the command line::

  py.test --driver Remote --capability browserName Firefox

You can also add or change capabilities by overwriting the ``capabilities``
fixture:

.. code-block:: python

  import pytest
  @pytest.fixture
  def capabilities(capabilities):
      capabilities['tags'] = ['tag1', 'tag2', 'tag3']
      return capabilities
