# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from selenium.webdriver.support.abstract_event_listener import \
    AbstractEventListener

pytestmark = pytest.mark.nondestructive


def test_event_listening_webdriver(testdir, httpserver):
    file_test = testdir.makepyfile("""
        import pytest
        from selenium.webdriver.support.event_firing_webdriver import \
            EventFiringWebDriver

        @pytest.mark.nondestructive
        def test_selenium(base_url, selenium):
            assert isinstance(selenium, EventFiringWebDriver)
            with pytest.raises(Exception) as e:
                selenium.get(base_url)
            assert 'before_navigate_to' in e.exconly()
    """)
    testdir.quick_qa('--event-listener', 'testing.'
                     'test_webdriver.ConcreteEventListener',
                     file_test, passed=1)


class ConcreteEventListener(AbstractEventListener):
    def before_navigate_to(self, url, driver):
        raise Exception('before_navigate_to')
