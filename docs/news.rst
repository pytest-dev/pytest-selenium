Release Notes
=============

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
