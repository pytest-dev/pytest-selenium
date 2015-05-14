# pytest_mozwebqa

pytest_mozwebqa is a plugin for [py.test](http://pytest.org/) that provides additional features needed for Mozilla's WebQA projects.

Requires:

  * py.test
  * selenium
  * requests

Continuous Integration
----------------------
[![Build Status](https://travis-ci.org/mozilla/pytest-mozwebqa.svg?branch=master)](http://travis-ci.org/mozilla/pytest-mozwebqa)

## Installation

To install pytest-mozwebqa:

```bash
pip install pytest-mozwebqa
```

## Usage

The basic usage of this plugin comes from specifying the `mozwebqa` argument
in your test methods. Doing this will launch a web browser based on your
command line options. You will then have access to the
[Selenium WebDriver](http://selenium.googlecode.com/git/docs/api/py/webdriver_remote/selenium.webdriver.remote.webdriver.html)
client that controls the browser instance:

```python
def test_example(mozwebqa):
mozwebqa.selenium.get('http://www.example.com/')
assert mozwebqa.selenium.title == 'Example Domain'
```

For the full list of command line options, run `py.test --help`.

### Specifying a base URL

The base URL is the location for the application under test. It can be
specified in a number of ways. The simplest of these is the `--baseurl`
command line option, however it can be more convenient to create a
`mozwebqa.cfg` file:

```INI
[DEFAULT]
baseurl: 'http://www.example.com'
```

Alternatively, you can reimplement the `base_url` py.test fixture. This allows
the value of the base URL to be controlled by your tests. A common use for
this is when you want to run tests against a local copy of your application
that's started by your test framework:

```python
import pytest
@pytest.fixture(scope='session')
def base_url(live_server):
    return live_server.url
```

### Accessing the base URL

If you want to access the base URL from your test, you can do so by specifying
the `base_url` argument in your test method. This can be useful if you want to
run tests that do not require a browser instance against your application:

```python
def test_status_code(base_url):
    from urllib2 import urlopen
    assert urlopen(base_url).getcode() == 200
```

### Destructive tests

In order to prevent accidentally running destructive tests, only tests marked
as nondestructive will run by default. If you want to mark a test as
nondestructive then add the appropriate marker as shown below:

```python
import pytest
@pytest.mark.nondestructive
def test_safely(mozwebqa):
    assert True
```

If you want to run destructive tests then you can specify the `--destructive`
command line option.

### Sensitive environments

If running against a sensitive (production) environment, any destructive tests
will be skipped with an appropriate error message. You can specify a regular
expression that matches your sensitive environments using the `--sensitiveurl`
command line option. By default all URLs are considered sensitive.

Setting capabilities
--------------------

It's possible to specify additional capabilities on the command line:

### Example (accept SSL certificates)

    --capability=acceptSslCerts:true


Setting Firefox preferences
---------------------------

If you're using Firefox it's possible to set custom preferences:

### Example (disable addon compatibility checking)

    --firefoxpref=extensions.checkCompatibility.nightly:false

Specifying a Firefox profile
----------------------------

If you're using Firefox it's possible to specify an existing Firefox profile to use when starting Firefox.

### Example (use the profile located at /path/to/profile_directory)

    --profilepath='/path/to/profile_directory'

Installing Firefox extensions
-----------------------------

If you're using Firefox it's possible to install extensions when starting the browser.

### Example (install the extensions located at /path/to/ext1/ext1.xpi and /path/to/ext2/ext2.xpi)

    --extension='/path/to/ext1/ext1.xpi' --extension='/path/to/ext2/ext2.xpi'

Setting Google Chrome options
-----------------------------

If you're using Google Chrome then you can set various options on the command line using a JSON string.

Valid keys are:
 * arguments: a list of command-line arguments to use when starting Google Chrome.
 * binary_location: path to the Google Chrome executable to use.

For more details on Google Chrome options see: http://code.google.com/p/chromedriver/wiki/CapabilitiesAndSwitches

### Example (set initial homepage)

    --chromeopts='{"arguments":["homepage=http://www.example.com"]}'

Installing Google Chrome extensions
-----------------------------------

If you're using Google Chrome it's possible to install extensions when starting the browser.

### Example (install the extensions located at /path/to/ext1/ext1.crx and /path/to/ext2/ext2.crx)

    --extension='/path/to/ext1/ext1.crx' --extension='/path/to/ext2/ext2.crx'

## HTML report

If the pytest-html plugin is installed then the HTML reports will include
additional information such as the failing URL, screenshot, and page source.
For Sauce Labs, a link to the job and inline video will also be included. Check
the [pytest-html documentation](https://pypi.python.org/pypi/pytest-html) for
how to install the plugin and generate HTML reports.

## Appium

To use [Appium](http://appium.io/) instead of Selenium, simply specify the
[appropriate capabilities](http://appium.io/slate/en/master/?python#appium-server-capabilities).
For example, to run web application tests against Safari on an iPhone simulator:

```shell
py.test --browsername=Safari \
--capability=platformName:iOS \
--capability=platformVersion:8.2 \
--capability="deviceName:iPhone Simulator" \
--capability=appiumVersion:1.3.7
```

## Sauce Labs integration

To run your automated tests using [Sauce Labs](https://saucelabs.com/), you
must provide a valid username and API key. This can be done either by creating
a `setup.cfg` file with a `[saucelabs]` section or by setting the
`SAUCELABS_USERNAME` and `SAUCELABS_API_KEY` environment variables.

### Configuration

Below is an example `setup.cfg` showing the configuration options:

```INI
[saucelabs]
username = username
api-key = secret
tags = tag1, tag2
privacy = public
```

The `tags` entry is an optional comma separated list of tags that can be used
to filter the jobs in the Sauce Labs dashboard.

The `privacy` entry is used to determine who you share your Sauce Labs jobs
with. Check the
[documentation](https://saucelabs.com/docs/additional-config#sharing) for the
accepted values. If not set, this defaults to
[public restricted](https://saucelabs.com/docs/additional-config#restricted).

### Running tests

To run your automated tests, simply specify `SauceLabs` as your driver:

```shell
py.test --driver=SauceLabs --browsername=Firefox --platform="Windows 8"
```

See the [supported platforms](https://docs.saucelabs.com/reference/platforms-configurator/)
to help you with your configuration. Additional capabilities can be set using
the `--capability` comand line arguments. See the
[test configuration documentation](https://docs.saucelabs.com/reference/test-configuration/)
for full details of what can be configured.

### Privacy

You can specify the job sharing level for individual tests by setting a mark on
the test method. This takes priority over the `privacy` entry in the
configuration file:

```python
import pytest
@pytest.mark.privacy('public')
def test_public(mozwebqa):
    assert True
```

You can also explicitly mark the test as private:


```python
import pytest
@pytest.mark.privacy('private')
def test_private(mozwebqa):
    assert True
```

For the full list of accepted values, check the
[Sauce Labs documentation](https://saucelabs.com/docs/additional-config#sharing).

## BrowserStack integration

To run your automated tests using
[BrowserStack](https://www.browserstack.com/), you must provide a valid
username and access key. This can be done either by creating a `setup.cfg`
file with a `[browserstack]` section or by setting the `BROWSERSTACK_USERNAME`
and `BROWSERSTACK_ACCESS_KEY` environment variables.

### Configuration

Below is an example `setup.cfg` showing the configuration options:

```ini
[browserstack]
username = username
access-key = secret
```

### Running tests

To run your automated tests, simply specify `BrowserStack` as your driver:

```shell
py.test --driver=BrowserStack --browsername=firefox --platform=WIN8
```

See the [capabilities documentation](https://www.browserstack.com/automate/capabilities)
for additional configuration that can be set using `--capability` command line
arguments.

Using a proxy server
--------------------

If you want the browser launched to use a proxy (currently only supported by Firefox and Google Chrome) you must specify the `--proxyhost` and `--proxyport` command line arguments.

### Example (proxy is running on localhost port 8080)

    --proxyhost=localhost --proxyport=8080
