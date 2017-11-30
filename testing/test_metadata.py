# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytest.mark.nondestructive


def test_metadata_default_host_port(testdir):
    host = 'localhost'
    port = 4444
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_pass(metadata):
            assert metadata['Server'] == '{}:{}'
    """.format(host, port))
    testdir.quick_qa('--driver', 'Remote', file_test, passed=1)


def test_metadata_host_port(testdir):
    host = 'notlocalhost'
    port = 4441
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_pass(metadata):
            assert metadata['Server'] == '{}:{}'
    """.format(host, port))
    testdir.quick_qa('--driver', 'Remote',
                     '--host', host,
                     '--port', port,
                     file_test, passed=1)
