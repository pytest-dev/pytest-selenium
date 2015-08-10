Development
===========

Automated Testing
-----------------

All pull requests and merges are tested in `Travis CI <https://travis-ci.org/>`_
based on the ``.travis.yml`` file.

Usually, a link to your specific travis build appears in pull requests, but if
not, you can find it on the
`pull requests page <https://travis-ci.org/davehunt/pytest-selenium/pull_requests>`_

The only way to trigger Travis CI to run again for a pull request, is to submit
another change to the pull branch.

Running Tests
-------------

You will need `pytest <http://pytest.org/>`_ installed to run the tests:

.. code-block:: bash

  $ py.test testing
