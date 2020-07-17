#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytest_plugins = "pytester"


def base_url(httpserver):
    return httpserver.url


@pytest.fixture
def httpserver_base_url(httpserver):
    return "--base-url={0}".format(base_url(httpserver))


@pytest.fixture(autouse=True)
def testdir(request, httpserver_base_url):
    item = request.node
    if "testdir" not in item.fixturenames:
        return

    testdir = request.getfixturevalue("testdir")

    conftest = """
        import pytest
        @pytest.fixture
        def webtext(base_url, selenium):
            selenium.get(base_url)
            return selenium.find_element_by_tag_name('h1').text
        """

    if item.get_closest_marker("chrome"):
        conftest += """
        @pytest.fixture
        def chrome_options(chrome_options):
            chrome_options.add_argument("headless")
            return chrome_options
        """

    testdir.makepyfile(conftest=conftest)

    testdir.makefile(
        ".cfg",
        setup=r"""
        [tool:pytest]
        filterwarnings =
            error::DeprecationWarning
            ignore:--firefox-\w+ has been deprecated:DeprecationWarning
            ignore:desired_capabilities has been deprecated
            ignore:service_log_path has been deprecated
    """,
    )

    def runpytestqa(*args, **kwargs):
        return testdir.runpytest(
            httpserver_base_url, "--driver", "Firefox", *args, **kwargs
        )

    testdir.runpytestqa = runpytestqa

    def inline_runqa(*args, **kwargs):
        return testdir.inline_run(
            httpserver_base_url, "--driver", "Firefox", *args, **kwargs
        )

    testdir.inline_runqa = inline_runqa

    def quick_qa(*args, **kwargs):
        reprec = inline_runqa(*args)
        outcomes = reprec.listoutcomes()
        names = ("passed", "skipped", "failed")
        for name, val in zip(names, outcomes):
            wantlen = kwargs.get(name)
            if wantlen is not None:
                assert len(val) == wantlen, name

    testdir.quick_qa = quick_qa
    return testdir
