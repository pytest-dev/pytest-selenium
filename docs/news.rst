Release Notes
=============

**1.10.0 (unreleased)**

* Add alternate credentials environment variables for Jenkins declarative
  pipelines.

  * Thanks to `@BeyondEvil <https://github.com/BeyondEvil>`_ for the PR

* Deprecate :code:`--firefox-extension`, :code:`--firefox-path`,
  :code:`--firefox-preference`, and :code:`--firefox-profile` command line
  options. The preferred way to set these is now through the
  :code:`firefox_options` fixture.

* Only create a Firefox profile if :code:`--firefox-extension`,
  :code:`--firefox-preference`, or :code:`--firefox-profile` is specified.

* Add :code:`chrome_options` fixture for configuring Google Chrome.

* Add :code:`driver_args` fixture for adding command line arguments to the
  driver services. Currently only used by Chrome and PhantomJS.

* Add support for TestingBot local tunnel via :code:`--host` and :code:`--port`
  command line options.

  * Thanks to `@micheletest <https://github.com/micheletest>`_ for the report
    and to `@BeyondEvil <https://github.com/BeyondEvil>`_ for the PR

* Add support for Microsoft Edge.

  * Thanks to `@birdsarah <https://github.com/birdsarah>`_ for the PR

* Add driver logs to HTML report.

  * Thanks to `@jrbenny35 <https://github.com/jrbenny35>`_ for the PR

**1.9.1 (2017-03-01)**

* Add capabilities to metadata during :code:`pytest_configure` hook instead of
  the :code:`session_capabilities` fixture to make them available to other
  plugins earlier.

**1.9.0 (2017-02-27)**

* Add driver and session capabilities to metadata provided by
  `pytest-metadata <https://pypi.python.org/pypi/pytest-metadata/>`_

**1.8.0 (2017-01-25)**

* **BREAKING CHANGE:** Moved cloud testing provider credentials into separate
  files for improved security.

  * If you are using the environment variables for specifying cloud testing
    provider credentials, then you will not be affected.
  * If you are storing credentials from any of the cloud testing providers in
    one of the default configuration files then they will no longer be used.
    These files are often checked into source code repositories, so it was
    previously very easy to accidentally expose your credentials.
  * Each cloud provider now has their own configuration file, such as
    ``.browserstack``, ``.crossbrowsertesting``, ``.saucelabs``,
    ``.testingbot`` and these can be located in the working directory or in the
    user's home directory. This provides a convenient way to set up these files
    globally, and override them for individual projects.
  * To migrate, check ``pytest.ini``, ``tox.ini``, and ``setup.cfg`` for any
    keys starting with ``browserstack_``, ``crossbrowsertesting_``,
    ``saucelabs_``, or ``testingbot_``. If you find any, create a new
    configuration file for the appropriate cloud testing provider with your
    credentials, and remove the entries from the original file.
  * The configuration keys can differ between cloud testing providers, so
    please check the :doc:`user_guide` for details.
  * See `#60 <https://github.com/pytest-dev/pytest-selenium/issues/60>`_ for
    for original issue and related patch.

**1.7.0 (2016-11-29)**

* Introduced a ``firefox_options`` fixture.
* Switched to Firefox options for speciying binary and profile.

**1.6.0 (2016-11-17)**

* Added support for `CrossBrowserTesting <https://crossbrowsertesting.com/>`_.

**1.5.1 (2016-11-03)**

* Fix issues with Internet Explorer driver.

**1.5.0 (2016-10-13)**

* Replaced driver fixtures with generic ``driver_class`` fixture.
* Introduced a ``driver_kwargs`` fixture.

**1.4.0 (2016-09-30)**

* Added support for Safari.

**1.3.1 (2016-07-13)**

* Made ``firefox_path`` a session scoped fixture.

**1.3.0 (2016-07-12)**

* Moved retrieval of Firefox path to ``firefox_path`` fixture.
* Added driver and sensitive URL to report header.
* Moved base URL implementation to the pytest-base-url plugin.

**1.2.1 (2016-02-25)**

* Fixed regression with Chrome, PhantomJS, and Internet Explorer drivers.

**1.2.0 (2016-02-25)**

* Added support for Python 3.
* Introduced a new capabilities fixture to combine session and marker
  capabilities.
* **BREAKING CHANGE:** Renamed session scoped capabilities fixture to
  session_capabilities.

  * If you have any ``capabilities`` fixture overrides, they will need to be
    renamed to ``session_capabilities``.

* Move driver implementations into fixtures and plugins.

**1.1 (2015-12-14)**

* Consistently stash the base URL in the configuration options.
* Drop support for pytest 2.6.
* Avoid deprecation warnings in pytest 2.8.
* Report warnings when gathering debug fails. (#40)

**1.0 (2015-10-26)**

* Official release

**1.0b5 (2015-10-20)**

* Assign an initial value to log_types. (#38)

**1.0b4 (2015-10-19)**

* Use strings for HTML to support serialization when running multiple processes.
* Catch exception if driver has not implemented log types.

**1.0b3 (2015-10-14)**

* Allow the sensitive URL regex to be specified in a configuration file.

**1.0b2 (2015-10-06)**

* Added support for non ASCII characters in log files. (#33)
* Added support for excluding any type of debug.

**1.0b1 (2015-09-08)**

* Initial beta
