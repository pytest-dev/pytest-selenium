User Guide
==========

.. contents:: :depth: 3

Quick Start
***********

The pytest-selenium plugin provides a method scoped selenium
`fixture <http://pytest.org/latest/fixture.html>`_ for your tests. This means
that any test with selenium as an argument will cause a browser instance to be
invoked. The browser may run locally or remotely depending on your
configuration, and may even run headless.

Here's a simple example test that opens a website using Selenium:

.. code-block:: python

  def test_example(selenium):
      selenium.get('http://www.example.com')

To run the above test you will need to specify the browser instance to be
invoked. For example, to run it using Firefox installed in a default location:

.. code-block:: bash

  $ py.test --driver Firefox

For full details of the Selenium API you can refer to the
`documentation <http://seleniumhq.github.io/selenium/docs/api/py/api.html>`_.

.. _configuration-files:

Configuration Files
*******************

There are a number of options and values that can be set in an INI-style
configuration file. For details of the expected name, format, and location of
these configuration files, check the
`pytest documentation <http://pytest.org/latest/customize.html#command-line-options-and-configuration-file-settings>`_.


Specifying a Base URL
*********************

To specify a base URL, refer to the documentation for the
`pytest-base-url <https://github.com/pytest-dev/pytest-base-url>`_ plugin.

Sensitive Environments
**********************

To avoid accidental changes being made to sensitive environments such as
your production instances, all tests are assumed to be destructive. Any
destructive tests attempted to run against a sensitive environment will be
skipped.

Nondestructive Tests
--------------------

To explicitly mark a test as nondestructive, you can add the appropriate marker
as shown here:

.. code-block:: python

  import pytest
  @pytest.mark.nondestructive
  def test_nondestructive(selenium):
      selenium.get('http://www.example.com')

Indicating Sensitive Environments
---------------------------------

Sensitive environments are indicated by a regular expression applied to the
base URL or any URLs discovered in the history of redirects when retrieving
the base URL. By default this matches all URLs, but can be configured by
setting the ``SENSITIVE_URL`` environment variable, using a
:ref:`configuration file <configuration-files>`, or by using the command line.

An example using a :ref:`configuration file <configuration-files>`:

.. code-block:: ini

  [pytest]
  sensitive_url = example\.com

An example using the command line:

.. code-block:: bash

  $ py.test --sensitive-url "example\.com"

Specifying a Browser
********************

To indicate the browser you want to run your tests against you will need to
specify a driver and optional capabilties.

Firefox
-------

To run your automated tests with Firefox version 47 or earlier, simply specify
``Firefox`` as your driver:

.. code-block:: bash

  $ py.test --driver Firefox

For Firefox version 48 onwards, you will need to
`download GeckoDriver <https://github.com/mozilla/geckodriver/releases>`_ and
``selenium`` 3.0 or later. If the driver executable is not available on your
path, you can use the ``--driver-path`` option to indicate where it can be
found:

.. code-block:: bash

  $ py.test --driver Firefox --driver-path /path/to/geckodriver

See the `GeckoDriver documentation <https://github.com/mozilla/geckodriver>`_
for more information.

Configuration
~~~~~~~~~~~~~

The current implementation of the Firefox driver does not allow you to specify
the binary path, preferences, profile path, or extensions via capabilities.
There are therefore additional command line options for each of these. Check
``--help`` for further details.

Chrome
------

To use Chrome, you will need to
`download ChromeDriver <https://sites.google.com/a/chromium.org/chromedriver/downloads>`_
and specify ``Chrome`` for the ``--driver`` command line option. If the driver
executable is not available on your path, you can use the ``--driver-path``
option to indicate where it can be found:

.. code-block:: bash

  $ py.test --driver Chrome --driver-path /path/to/chromedriver

See the `ChromeDriver documentation <https://sites.google.com/a/chromium.org/chromedriver/>`_
for more information.

Internet Explorer
-----------------

To use Internet Explorer, you will need to download and configure the
`Internet Explorer Driver <https://github.com/SeleniumHQ/selenium/wiki/InternetExplorerDriver>`_
and specify ``IE`` for the ``--driver`` command line option. If the driver
executable is not available on your path, you can use the ``--driver-path``
option to indicate where it can be found:

.. code-block:: batch

  > py.test --driver IE --driver-path \path\to\IEDriverServer.exe

PhantomJS
---------

To use PhantomJS, you will need `download it <http://phantomjs.org/download.html>`_
and specify ``PhantomJS`` for the ``--driver`` command line option. If
the driver executable is not available on your path, you can use the
``--driver-path`` option to indicate where it can be found:

.. code-block:: bash

  $ py.test --driver PhantomJS --driver-path /path/to/phantomjs

See the `PhantomJS documentation <http://phantomjs.org/quick-start.html>`_ for
more information.

Safari
------

To use Safari, you will need to have at least Safari 10 running on OS X El
Capitan or later, and ``selenium`` 3.0 or later. Once you have these
prerequisites, simply specify ``Safari`` for the ``--driver`` command line
option.

.. code-block:: bash

  $ py.test --driver Safari

Selenium Server/Grid
--------------------

To run your automated tests against a
`Selenium server <https://github.com/SeleniumHQ/selenium/wiki/RemoteWebDriverServer>`_
or a `Selenium Grid <https://github.com/SeleniumHQ/selenium/wiki/Grid2>`_ you
must have a server running and know the host and port of the server.

By default Selenium will listen on host 127.0.0.1 and port 4444. This is also
the default when running tests against a remote driver.

To run your automated tests, simply specify ``Remote`` as your driver. Browser
selection is determined using capabilities. Check the
`desired capabilities documentation <https://github.com/SeleniumHQ/selenium/wiki/DesiredCapabilities#used-by-the-selenium-server-for-browser-selection>`_
for details of accepted values. There are also a number of
`browser specific capabilities <https://github.com/SeleniumHQ/selenium/wiki/DesiredCapabilities#browser-specific-capabilities>`_
that can be set. Be sure to also check the documentation for your chosen
driver, as the accepted capabilities may differ:

.. code-block:: bash

  $ py.test --driver Remote --capability browserName firefox

Note that if your server is not running locally or is running on an alternate
port you will need to specify the ``--host`` and ``--port`` command line
options:

.. code-block:: bash

  $ py.test --driver Remote --host selenium.hostname --port 5555 --capability browserName firefox

Sauce Labs
----------

To run your automated tests using `Sauce Labs <https://saucelabs.com/>`_, you
must provide a valid username and API key. This can be done either by using
a ``.saucelabs`` configuration file in the working directory or your home
directory, or by setting the ``SAUCELABS_USERNAME`` and ``SAUCELABS_API_KEY``
environment variables.

Configuration
~~~~~~~~~~~~~

Below is an example ``.saucelabs`` configuration file:

.. code-block:: ini

  [credentials]
  username = username
  key = secret

Running tests
~~~~~~~~~~~~~

To run your automated tests, simply specify ``SauceLabs`` as your driver:

.. code-block:: bash

  $ py.test --driver SauceLabs --capability browserName Firefox

See the `supported platforms <https://docs.saucelabs.com/reference/platforms-configurator/>`_
to help you with your configuration. Additional capabilities can be set using
the ``--capability`` command line arguments. See the
`test configuration documentation <https://docs.saucelabs.com/reference/test-configuration/>`_
for full details of what can be configured.

BrowserStack
------------

To run your automated tests using
`BrowserStack <https://www.browserstack.com/>`_, you must provide a valid
username and access key. This can be done either by using
a ``.browserstack`` configuration file in the working directory or your home
directory, or by setting the ``BROWSERSTACK_USERNAME`` and
``BROWSERSTACK_ACCESS_KEY`` environment variables.

Configuration
~~~~~~~~~~~~~

Below is an example ``.browserstack`` configuration file:

.. code-block:: ini

  [credentials]
  username = username
  key = secret

Running tests
~~~~~~~~~~~~~

To run your automated tests, simply specify ``BrowserStack`` as your driver:

.. code-block:: bash

  $ py.test --driver BrowserStack --capability browserName Firefox

See the
`capabilities documentation <https://www.browserstack.com/automate/capabilities>`_
for additional configuration that can be set using ``--capability`` command line
arguments.

TestingBot
----------

To run your automated tests using `TestingBot <http://testingbot.com/>`_, you
must provide a valid key and secret. This can be done either by using
a ``.testingbot`` configuration file in the working directory or your home
directory, or by setting the ``TESTINGBOT_KEY`` and ``TESTINGBOT_SECRET``
environment variables.

Configuration
~~~~~~~~~~~~~

Below is an example ``.testingbot`` configuration file:

.. code-block:: ini

  [credentials]
  key = key
  secret = secret

Running tests
~~~~~~~~~~~~~

To run your automated tests, simply specify ``TestingBot`` as your driver:

.. code-block:: bash

  $ py.test --driver TestingBot --capability browserName firefox --capability version 39 --capability platform WIN8

See the `list of available browsers <http://testingbot.com/support/getting-started/browsers.html>`_
to help you with your configuration. Additional capabilities can be set using
the ``--capability`` command line arguments. See the
`test options <http://testingbot.com/support/other/test-options>`_
for full details of what can be configured.

CrossBrowserTesting
-------------------

To run your automated tests using
`CrossBrowserTesting <https://crossbrowsertesting.com/>`_, you must provide a
valid username and auth key. This can be done either by using
a ``.crossbrowsertesting`` configuration file in the working directory or your
home directory, or by setting the ``CROSSBROWSERTESTING_USERNAME`` and
``CROSSBROWSERTESTING_AUTH_KEY`` environment variables.

Configuration
~~~~~~~~~~~~~

Below is an example ``.crossbrowsertesting`` configuration file:

.. code-block:: ini

  [credentials]
  username = username
  key = secret

Running tests
~~~~~~~~~~~~~

To run your automated tests, simply specify ``CrossBrowserTesting`` as your
driver:

.. code-block:: bash

  $ py.test --driver CrossBrowserTesting --capability os_api_name Win10 --capability browser_api_name FF46

Additional capabilities can be set using the ``--capability`` command line
arguments. See the
`automation capabilities <https://help.crossbrowsertesting.com/selenium-testing/general/crossbrowsertesting-automation-capabilities/>`_
for full details of what can be configured.

Specifying Capabilities
***********************

Configuration options are specified using a capabilities dictionary. This is
required when using a Selenium server to specify the target environment, but
can also be used to configure local drivers.

Command Line Capabilities
-------------------------

Simple capabilities can be set or overridden on the command line:

.. code-block:: bash

  $ py.test --driver Remote --capability browserName Firefox

Capabilities Files
------------------

To specify capabilities, you can provide a JSON file on the command line using
the `pytest-variables <https://github.com/pytest-dev/pytest-variables>`_ plugin.
For example if you had a ``capabilties.json`` containing your capabilities, you
would need to include ``--variables capabilities.json`` on your command line.

The following is an example of a variables file including capabilities:

.. code-block:: json

  { "capabilities": {
      "browserName": "Firefox",
      "platform": "MAC" }
  }

Capabilities Fixtures
---------------------

The ``session_capabilities`` fixture includes capabilities that
apply to the entire test session (including any command line or file based
capabilities). Any changes to these capabilities will apply to every test.
These capabilities are also reported at the top of the HTML report.

.. code-block:: python

  import pytest
  @pytest.fixture(scope='session')
  def session_capabilities(session_capabilities):
      session_capabilities['tags'] = ['tag1', 'tag2', 'tag3']
      return session_capabilities

The ``capabilities`` fixture contains all of the session capabilities, plus any
capabilities specified by the capabilities marker. Any changes to these
capabilities will apply only to the tests covered by scope of the fixture
override.

.. code-block:: python

  import pytest
  @pytest.fixture
  def capabilities(capabilities):
      capabilities['public'] = 'private'
      return capabilities

Capabilities Marker
-------------------

You can add or change capabilities using the ``capabilities`` marker:

.. code-block:: python

  import pytest
  @pytest.mark.capabilities(foo='bar')
  def test_capabilities(selenium):
      selenium.get('http://www.example.com')

Common Selenium Setup
*********************

If you have common setup that you want to apply to your tests, such as setting
the implicit timeout or window size, you can override the ``selenium`` fixture:

.. code-block:: python

  import pytest
  @pytest.fixture
  def selenium(selenium):
      selenium.implicitly_wait(10)
      selenium.maximize_window()
      return selenium

HTML Report
***********

A custom HTML report is generated when the ``--html`` command line option is
given. By default this will include additional debug information for failures.

Debug Types
-----------

The following debug information is gathered by default when a test fails:

* **URL** - The current URL open in the browser.
* **HTML** - The HTML source of the page open in the browser.
* **LOG** - All logs available. Note that this will vary depending on the browser and
  server in use. See
  `logging <https://github.com/SeleniumHQ/selenium/wiki/Logging>`_ for more
  details.
* **SCREENSHOT** - A screenshot of the page open in the browser.

Capturing Debug
---------------

To change when debug is captured you can either set ``selenium_capture_debug``
in a :ref:`configuration file <configuration-files>`, or set the
``SELENIUM_CAPTURE_DEBUG`` environment variable. Valid options are: ``never``,
``failure`` (the default), and ``always``. Note that always capturing debug will
dramatically increase the size of the HTML report.

Excluding Debug
---------------

You may need to exclude certain types of debug from the report. For example, log
files can contain sensitive information that you may not want to publish. To
exclude a type of debug from the report, you can either set
``selenium_exclude_debug`` in a :ref:`configuration file <configuration-files>`,
or set the ``SELENIUM_EXCLUDE_DEBUG`` environment variable to a list of the
`Debug Types`_ to exclude.

For example, to exclude HTML, logs, and screenshots from the report, you could
set ``SELENIUM_EXCLUDE_DEBUG`` to ``html:logs:screenshot``.
