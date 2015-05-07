pytest_mozwebqa
===============

pytest_mozwebqa is a plugin for [py.test](http://pytest.org/) that provides additional features needed for Mozilla's WebQA projects.

Requires:

  * py.test
  * selenium
  * pyyaml
  * requests

Continuous Integration
----------------------
[![Build Status](https://travis-ci.org/mozilla/pytest-mozwebqa.svg?branch=master)](http://travis-ci.org/mozilla/pytest-mozwebqa)

Installation
------------

    $ python setup.py install

Running tests with pytest_mozwebqa
----------------------------------

    Usage: py.test [options] [file_or_dir] [file_or_dir] [...]

For full usage details run `py.test --help`.

### Configuration

You can also create a `mozwebqa.cfg` file that will be used to set defaults.
This is so that projects can keep this alongside the tests to simplify running
them via the command line. The options are currently limited to those that could
be project specific.

    [DEFAULT]
    baseurl: 'http://www.example.com'
    tags: 'tag1, tag2'
    privacy: 'public restricted'

The `tags` entry is an optional comma separated list of tags that are set when
using Sauce Labs. This is useful for filtering the list of jobs based on the
application under test or similar.

The `privacy` entry is used to determine who you share your Sauce Labs jobs
with. Check the
[documentation](https://saucelabs.com/docs/additional-config#sharing) for the
accepted values. This defaults to
[public restricted](https://saucelabs.com/docs/additional-config#restricted).

### Examples

Run tests against a local webdriver using Firefox:

    $ py.test --baseurl=http://example.com --driver=firefox --firefoxpath=/Applications/Firefox.app/Contents/MacOS/firefox-bin

Run tests against a local webdriver using Google Chrome:

    $ py.test --baseurl=http://example.com --driver=chrome --chromepath=/Applications/chromedriver

Run tests against a remote webdriver server either directly or via grid:

    $ py.test --baseurl=http://example.com --browsername=firefox --browserver=5 --platform=mac

Writing tests for pytest_mozwebqa
---------------------------------

You will need to include the `mozwebqa` in the method signature for your tests, and pass it when constructing page objects.

### Example

    def test_new_user_can_register(self, mozwebqa):
        home_pg = home_page.HomePage(mozwebqa)
        home_pg.go_to_home_page()
        home_pg.login_region.click_sign_up()

        registration_pg = registration_page.RegistrationPage(mozwebqa)
        registration_pg.register_new_user()
        Assert.equal(registration_pg.page_title, "Sign Up Complete!")

Destructive tests
-----------------

In order to prevent accidentally running destructive tests, only tests marked as nondestructive will run by default. If you want to mark a test as nondestructive then add the appropriate marker as shown below:

### Example (mark test as nondestructive)

    import pytest
    @pytest.mark.nondestructive
    def test_safely(self, mozwebqa):
        ...

If you want to run destructive tests then you can specify the `--destructive` command line option.

Sensitive environments
----------------------

If running against a sensitive (production) environment any destructive tests will be skipped with an appropriate error message. You can specify a regular expression that matches your sensitive environments using the `--sensitiveurl` command line option.

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

Using credentials files
-----------------------

The credentials files use YAML syntax, and the usage will vary depending on the project. A typical file will contain at least one user with a unique identifier and login credentials:

### Example

    # admin:
    #   email: admin@example.com
    #   username: admin
    #   password: password

HTML report
-----------

If the pytest-html plugin is installed then the HTML reports will include
additional information such as the failing URL, screenshot, and page source.
For Sauce Labs, a link to the job and inline video will also be included. Check
the [pytest-html documentation](https://pypi.python.org/pypi/pytest-html) for
how to install the plugin and generate HTML reports.

Privacy
-------

You can specify the job sharing level for Sauce Labs jobs.

Privacy marks have higher priority than the `privacy` entry in `mozwebqa.cfg`.

### Example

    import pytest
    
    @pytest.mark.privacy('public')
    def test_public(self, mozwebqa):
        home_pg = home_page.HomePage(mozwebqa)

You can also explicitly mark the test as private, which sets the test
appopriately in Sauce Labs jobs.

### Example

    import pytest
    
    @pytest.mark.privacy('private')
    def test_private(self, mozwebqa):
        home_pg = home_page.HomePage(mozwebqa)

For the full list of accepted values, check the
[Sauce Labs documentation](https://saucelabs.com/docs/additional-config#sharing).

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

Cloud integration
-----------------

### Sauce Labs

To run your automated tests using [Sauce Labs](https://saucelabs.com/), specify
`SauceLabs` as your driver and set the `SAUCELABS_USERNAME` and
`SAUCELABS_API_KEY` environment variables:

```shell
export SAUCELABS_USERNAME=Username
export SAUCELABS_API_KEY=Secret
py.test --driver=SauceLabs --browsername=Firefox --platform="Windows 8"
```

See the [supported platforms](https://docs.saucelabs.com/reference/platforms-configurator/)
to help you with your configuration. Additional capabilities can be set using
the `--capability` comand line arguments. See the
[test configuration documentation](https://docs.saucelabs.com/reference/test-configuration/)
for full details of what can be configured.

### BrowserStack

To run your automated tests using [BrowserStack](https://www.browserstack.com/),
specify `BrowserStack` as your driver and set the `BROWSERSTACK_USERNAME` and
`BROWSERSTACK_ACCESS_KEY` environment variables:

```shell
export BROWSERSTACK_USERNAME=Username
export BROWSERSTACK_ACCESS_KEY=Secret
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
