Development
===========

Automated Testing
-----------------

All pull requests and merges are tested in `Travis CI <https://travis-ci.org/>`_
based on the ``.travis.yml`` file.

Usually, a link to your specific travis build appears in pull requests, but if
not, you can find it on the
`pull requests page <https://travis-ci.org/pytest-dev/pytest-selenium/pull_requests>`_

The only way to trigger Travis CI to run again for a pull request, is to submit
another change to the pull branch.

Running Tests
-------------

You will need `Tox <http://tox.testrun.org/>`_ installed to run the tests
against the supported Python versions.

.. code-block:: bash

  $ pip install tox
  $ tox

Drivers
-------
To run the tests you're going to need some browser drivers.

Chromedriver
~~~~~~~~~~~~
To install the latest `chromedriver <https://sites.google.com/a/chromium.org/chromedriver/>`_
on your Mac or Linux (64-bit), run:

.. code-block:: bash

  $ ./installation/chromedriver.sh

For Windows users, please see `here <https://sites.google.com/a/chromium.org/chromedriver/getting-started>`_.

Geckodriver
~~~~~~~~~~~
To install the latest `geckodriver <https://firefox-source-docs.mozilla.org/testing/geckodriver/>`_
on your Mac or Linux (64-bit), run:

.. code-block:: bash

  $ ./installation/geckodriver.sh

Safaridriver
~~~~~~~~~~~~
Instructions for `safaridriver <https://developer.apple.com/documentation/webkit/testing_with_webdriver_in_safari?language=objc>`_.

Edgedriver
~~~~~~~~~~
Instructions for `edgedriver <https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/#downloads>`_.

IEDriver
~~~~~~~~
Instructions for `iedriver <https://github.com/SeleniumHQ/selenium/wiki/InternetExplorerDriver>`_.
