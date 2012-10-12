#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import pytest

pytestmark = pytestmark = [pytest.mark.skip_selenium,
                           pytest.mark.nondestructive]

failure_files = ('screenshot.png', 'html.txt')
log_file = 'log.txt'
network_traffic_file = 'networktraffic.json'


def testDebugOnFail(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_debug(mozwebqa):
            mozwebqa.selenium.open('/')
            assert mozwebqa.selenium.get_text('css=h1') != 'Success!'
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--api=rc',
                                '--browser=*firefox',
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
            mozwebqa.selenium.open('/')
            assert mozwebqa.selenium.get_text('css=h1') != 'Success!'
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--api=rc',
                                '--browser=*firefox',
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
            mozwebqa.selenium.open('/')
            assert mozwebqa.selenium.get_text('css=h1') == 'Success!'
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--api=rc',
                                '--browser=*firefox',
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
            mozwebqa.selenium.open('/')
            assert mozwebqa.selenium.get_text('css=h1') == 'Success!'
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--api=rc',
                                '--browser=*firefox',
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
            mozwebqa.selenium.open('/')
            assert mozwebqa.selenium.get_text('css=h1') == 'Success!'
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--api=rc',
                                '--browser=*firefox',
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
            mozwebqa.selenium.open('/')
            assert mozwebqa.selenium.get_text('css=h1') != 'Success!'
    """)
    report_subdirectory = 'report'
    reprec = testdir.inline_run(
        '--baseurl=http://localhost:%s' % webserver.port,
        '--api=rc',
        '--browser=*firefox',
        '--webqareport=%s/result.html' % report_subdirectory,
        file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    path = _test_debug_path(os.path.join(str(testdir.tmpdir),
                                         report_subdirectory))
    for file in failure_files:
        assert os.path.exists(os.path.join(path, file))
        assert os.path.isfile(os.path.join(path, file))


def testLogWhenPublic(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.public
        @pytest.mark.nondestructive
        def test_debug(mozwebqa):
            mozwebqa.selenium.open('/')
            assert mozwebqa.selenium.get_text('css=h1') != 'Success!'
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--api=rc',
                                '--browser=*firefox',
                                '--webqareport=result.html',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    path = _test_debug_path(str(testdir.tmpdir))
    assert os.path.exists(os.path.join(path, log_file))
    assert os.path.isfile(os.path.join(path, log_file))


def testNoLogWhenNotPublic(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_debug(mozwebqa):
            mozwebqa.selenium.open('/')
            assert mozwebqa.selenium.get_text('css=h1') != 'Success!'
    """)
    reprec = testdir.inline_run(
        '--baseurl=http://localhost:%s' % webserver.port,
        '--api=rc',
        '--browser=*firefox',
        '--webqareport=result.html',
        file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    path = _test_debug_path(str(testdir.tmpdir))
    assert not os.path.exists(os.path.join(path, log_file))


def testNoLogWhenPrivate(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.private
        @pytest.mark.nondestructive
        def test_debug(mozwebqa):
            mozwebqa.selenium.open('/')
            assert mozwebqa.selenium.get_text('css=h1') != 'Success!'
    """)
    reprec = testdir.inline_run(
        '--baseurl=http://localhost:%s' % webserver.port,
        '--api=rc',
        '--browser=*firefox',
        '--webqareport=result.html',
        file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    path = _test_debug_path(str(testdir.tmpdir))
    assert not os.path.exists(os.path.join(path, log_file))


def testCaptureNetworkTraffic(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_capture_network_traffic(mozwebqa):
            mozwebqa.selenium.open('/')
            assert mozwebqa.selenium.get_text('css=h1') == 'Success!'
    """)
    reprec = testdir.inline_run(
        '--baseurl=http://localhost:%s' % webserver.port,
        '--api=rc',
        '--browser=*firefox',
        '--capturenetwork',
        '--webqareport=index.html',
        file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1
    path = _test_debug_path(str(testdir.tmpdir))
    json_data = open(os.path.join(path, network_traffic_file))
    import json
    data = json.load(json_data)
    json_data.close()
    assert len(data) > 0


def _test_debug_path(root_path):
    debug_path = os.path.join(root_path, 'debug')
    for i in range(2):
        debug_path = os.path.join(debug_path, os.listdir(debug_path)[0])
    return debug_path
