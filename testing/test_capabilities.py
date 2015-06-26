# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytest.mark.nondestructive


def test_file(testdir):
    variables = testdir.makefile('.json', '{"capabilities": {"foo": "bar"}}')
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_capabilities(capabilities):
            assert capabilities['foo'] == 'bar'
    """)
    testdir.quick_qa('--variables', variables, file_test, passed=1)


def test_fixture(testdir):
    testdir.makeconftest("""
        import pytest
        @pytest.fixture
        def capabilities():
            return {'foo': 'bar'}
    """)
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_capabilities(capabilities):
            assert True
    """)
    testdir.quick_qa(file_test, passed=1)
