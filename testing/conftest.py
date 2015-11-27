#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from .webserver import SimpleWebServer

pytest_plugins = 'pytester'


@pytest.fixture(scope='session')
def base_url(webserver):
    return 'http://localhost:{0}'.format(webserver.port)


@pytest.fixture
def webserver_base_url(webserver):
    return '--base-url={0}'.format(base_url(webserver))


@pytest.fixture(autouse=True)
def testdir(request, webserver_base_url):
    item = request.node
    if 'testdir' not in item.funcargnames:
        return

    testdir = request.getfuncargvalue('testdir')

    testdir.makepyfile(conftest="""
        import pytest
        @pytest.fixture
        def webtext(base_url, selenium):
            selenium.get(base_url)
            return selenium.find_element_by_tag_name('h1').text
        """)

    def runpytestqa(*args, **kwargs):
        return testdir.runpytest(webserver_base_url, '--driver', 'Firefox',
                                 *args, **kwargs)

    testdir.runpytestqa = runpytestqa

    def inline_runqa(*args, **kwargs):
        return testdir.inline_run(webserver_base_url, '--driver', 'Firefox',
                                  *args, **kwargs)

    testdir.inline_runqa = inline_runqa

    def quick_qa(*args, **kwargs):
        reprec = inline_runqa(*args)
        outcomes = reprec.listoutcomes()
        names = ('passed', 'skipped', 'failed')
        for name, val in zip(names, outcomes):
            wantlen = kwargs.get(name)
            if wantlen is not None:
                assert len(val) == wantlen, name

    testdir.quick_qa = quick_qa
    return testdir


@pytest.fixture(scope='session', autouse=True)
def webserver(request):
    webserver = SimpleWebServer()
    webserver.start()
    request.addfinalizer(webserver.stop)
    return webserver
