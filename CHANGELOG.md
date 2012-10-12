Change Log
==========

1.1
---

* Added support for setting a proxy for Firefox, Google Chrome, and Opera
* Added support for specifying a Firefox profile
* Added support for specifying Firefox extensions

1.0
---

* First stable release
* Added support for Opera
* Compatible with pytest-timeout

0.10 (beta)
-----------

* Allow additional capabilities to be specified on the command line

0.9 (beta)
----------

* Only run nondestructive tests by default
* Skip destructive tests if running against a sensitive environment

0.8 (beta)
----------

 * Added support for privacy markers
 * Capture final URL on test failures
 * Capture log on test failures if test is marked as public
 * Capture HTML and screenshot only on test failures
 * Improved the debug gathering
 * Timeout value is now expected in seconds
 * Added support for specifying Google Chrome options

0.7 (beta)
----------

 * Added support for specifying Firefox preferences - fixes issue #27

0.6 (beta)
----------

 * By default Sauce Labs jobs are public (restricted) - fixes issue #14
 * Avoid running configuration hook for all slave processes - fixes issues #22 and #23
 * Add test durations to HTML report when running with multiple processes - fixes issue #9

0.5 (beta)
----------

 * Added a build identifier for when running with continuous integration

0.4 (beta)
----------

 * Changed default HTML report to results/index.html
 * Send pass/fail status to Sauce Labs - fixes issue #21
 * Added support for custom tags for Sauce Labs jobs
 * Added support for configuration files
 * Remove test names from Sauce Labs tags - fixes issue #20

0.3 (beta)
----------

 * Added error count to custom report - fixes issue #15
 * Catch exceptions thrown when attempting to capture screenshots - fixes issue #16

0.2 (beta)
----------

 * Added custom HTML reports

0.1 (alpha)
-----------

 * Initial release