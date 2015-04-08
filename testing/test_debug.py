#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import pytest

pytestmark = pytestmark = [pytest.mark.skip_selenium,
                           pytest.mark.nondestructive]

failure_files = ('screenshot.png', 'html.txt')


def testDebugOnFail(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_debug(mozwebqa):
            mozwebqa.selenium.get(mozwebqa.base_url)
            header = mozwebqa.selenium.find_element_by_tag_name('h1')
            assert header.text != 'Success!'
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--driver=firefox',
                                '--webqareport=result.html',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    path = _test_debug_path(str(testdir.tmpdir))
    for file in failure_files:
        assert os.path.exists(os.path.join(path, file))
        assert os.path.isfile(os.path.join(path, file))


def testDebugOnXFail(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.xfail
        @pytest.mark.nondestructive
        def test_debug(mozwebqa):
            mozwebqa.selenium.get(mozwebqa.base_url)
            header = mozwebqa.selenium.find_element_by_tag_name('h1')
            assert header.text != 'Success!'
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--driver=firefox',
                                '--webqareport=result.html',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(skipped) == 1
    path = _test_debug_path(str(testdir.tmpdir))
    for file in failure_files:
        assert os.path.exists(os.path.join(path, file))
        assert os.path.isfile(os.path.join(path, file))


def testNoDebugOnPass(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_debug(mozwebqa):
            mozwebqa.selenium.get(mozwebqa.base_url)
            header = mozwebqa.selenium.find_element_by_tag_name('h1')
            assert header.text == 'Success!'
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--driver=firefox',
                                '--webqareport=result.html',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1
    debug_path = os.path.sep.join([str(testdir.tmpdir), 'debug'])
    assert not os.path.exists(debug_path)


def testNoDebugOnXPass(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.xfail
        @pytest.mark.nondestructive
        def test_debug(mozwebqa):
            mozwebqa.selenium.get(mozwebqa.base_url)
            header = mozwebqa.selenium.find_element_by_tag_name('h1')
            assert header.text == 'Success!'
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--driver=firefox',
                                '--webqareport=result.html',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    debug_path = os.path.sep.join([str(testdir.tmpdir), 'debug'])
    assert not os.path.exists(debug_path)


def testNoDebugOnSkip(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.skipif('True')
        @pytest.mark.nondestructive
        def test_debug(mozwebqa):
            mozwebqa.selenium.get(mozwebqa.base_url)
            header = mozwebqa.selenium.find_element_by_tag_name('h1')
            assert header.text == 'Success!'
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--driver=firefox',
                                '--webqareport=result.html',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(skipped) == 1
    debug_path = os.path.sep.join([str(testdir.tmpdir), 'debug'])
    assert not os.path.exists(debug_path)


def testDebugWithReportSubdirectory(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_debug(mozwebqa):
            mozwebqa.selenium.get(mozwebqa.base_url)
            header = mozwebqa.selenium.find_element_by_tag_name('h1')
            assert header.text != 'Success!'
    """)
    report_subdirectory = 'report'
    reprec = testdir.inline_run(
        '--baseurl=http://localhost:%s' % webserver.port,
        '--driver=firefox',
        '--webqareport=%s/result.html' % report_subdirectory,
        file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    path = _test_debug_path(os.path.join(str(testdir.tmpdir),
                                         report_subdirectory))
    for file in failure_files:
        assert os.path.exists(os.path.join(path, file))
        assert os.path.isfile(os.path.join(path, file))


def _test_debug_path(root_path):
    debug_path = os.path.join(root_path, 'debug')
    for i in range(2):
        debug_path = os.path.join(debug_path, os.listdir(debug_path)[0])
    return debug_path
