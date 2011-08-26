pytest_mozwebqa
===============

pytest_mozwebqa is a plugin for [py.test](http://pytest.org/) that provides additional features needed for Mozilla's WebQA projects.

Requires:

  * py.test
  * selenium
  * pyyaml

Installation
------------

    $ python setup.py install

Running tests with pytest_mozwebqa
----------------------------------

For full usage details run the following command:

    $ py.test --help

    selenium:
      --api=api           version of selenium api to use. 'rc' uses selenium rc.
                          'webdriver' uses selenium webdriver (the default).
      --host=str          host that selenium server is listening on.
      --port=num          port that selenium server is listening on.
      --driver=str        webdriver implementation.
      --chromepath=path   path to the google chrome driver executable.
      --firefoxpath=path  path to the target firefox binary.
      --browser=str       target browser (standalone rc server).
      --environment=str   target environment (grid rc).
      --browsername=str   target browser name (webdriver).
      --browserver=str    target browser version (webdriver).
      --platform=str      target platform (webdriver).
      --baseurl=url       base url for the application under test.
      --timeout=num       timeout for page loads, etc (selenium rc).
      --capturenetwork    capture network traffic to test_method_name.json
                          (selenium rc). (disabled by default).

    credentials:
      --credentials=path  location of yaml file containing user credentials.
      --saucelabs=path    credendials file containing sauce labs username and api key.

### Examples

Run tests against a standalone RC server using Firefox in the default location:

    $ py.test --api=rc --baseurl=http://example.com --browser="*firefox"

Run tests against a grid server with an RC node environment named 'Firefox Beta on Mac OS X':

    $ py.test --api=rc --baseurl=http://example.com --environment="Firefox 5 on Mac OS X"

Run tests against a local webdriver using Firefox:

    $ py.test --baseurl=http://example.com --driver=firefox --firefoxpath=/Applications/Firefox.app/Contents/MacOS/firefox-bin

Run tests against a local webdriver using Google Chrome:

    $ py.test --baseurl=http://example.com --driver=chrome --chromepath=/Applications/chromedriver

Run tests against a remote webdriver server either directly or via grid:

    $ py.test --baseurl=http://example.com --browsername=firefox --browserver=5 --platform=mac

Run tests against Sauce Labs using RC API using Firefox 5 on Windows 2003:

    $ py.test --api=rc --baseurl=http://example.com --browsername=firefox --browserver=5.0 --platform="Windows 2003" --saucelabs=sauce_labs.yaml

Run tests against Sauce Labs using webdriver API using Firefox 5 on Windows:

    $ py.test --baseurl=http://example.com --browsername=firefox --browserver=5.0 --platform=WINDOWS --saucelabs=sauce_labs.yaml

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

Using credentials files
-----------------------

The credentials files use YAML syntax, and the usage will vary depending on the project. A typical file will contain at least one user with a unique identifier and login credentials:

### Example

    # admin:
    #   email: admin@example.com
    #   username: admin
    #   password: password
