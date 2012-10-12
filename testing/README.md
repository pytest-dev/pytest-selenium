# Running tests of pytest-mozwebqa

Tests can be run on pytest_mozwebqa by running:

    $ py.test

For a full list of options to run py.test use: `$ py.test --help`

## Requirements
Many of the tests use the Selenium RC API (--api=rc) and require a Selenium server running at http://localhost:4444

To get this:
* Download selenium server from http://seleniumhq.org/download/
* Start the server: `$ java -jar selenium-server-x.x.x.jar`
