# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytest.mark.nondestructive


@pytest.fixture
def testfile(testdir):
    return testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_capabilities(capabilities):
            assert capabilities['foo'] == 'bar'
    """)


def test_command_line(testfile, testdir):
    testdir.quick_qa('--capability', 'foo', 'bar', testfile, passed=1)


def test_file(testfile, testdir):
    variables = testdir.makefile('.json', '{"capabilities": {"foo": "bar"}}')
    testdir.quick_qa('--variables', variables, testfile, passed=1)


def test_fixture(testfile, testdir):
    testdir.makeconftest("""
        import pytest
        @pytest.fixture(scope='session')
        def capabilities():
            return {'foo': 'bar'}
    """)
    testdir.quick_qa(testfile, passed=1)


def test_mark(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        @pytest.mark.capabilities(foo='bar')
        def test_capabilities(session_capabilities, capabilities):
            assert 'foo' not in session_capabilities
            assert capabilities['foo'] == 'bar'
    """)
    testdir.quick_qa(file_test, passed=1)
