# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import pytest
import requests
from selenium.webdriver import Remote

from pytest_selenium import split_class_and_test_names

API_JOB_URL = 'https://www.browserstack.com/automate/sessions/{session}.json'
EXECUTOR_URL = 'http://{username}:{key}@hub.browserstack.com:80/wd/hub'


def pytest_addoption(parser):
    parser.addini('browserstack_username',
                  help='browserstack username',
                  default=os.getenv('BROWSERSTACK_USERNAME'))
    parser.addini('browserstack_access_key',
                  help='browserstack access key',
                  default=os.getenv('BROWSERSTACK_ACCESS_KEY'))


def pytest_selenium_runtest_makereport(item, report, summary, extra):
    if item.config.getoption('driver') != 'BrowserStack':
        return

    # Add the job URL to the summary
    driver = getattr(item, '_driver', None)
    auth = (_username(item.config), _access_key(item.config))
    api_url = API_JOB_URL.format(session=driver.session_id)
    job_info = requests.get(api_url, auth=auth, timeout=10).json()
    job_url = job_info['automation_session']['browser_url']
    summary.append('BrowserStack Job: {0}'.format(job_url))
    pytest_html = item.config.pluginmanager.getplugin('html')
    if pytest_html is not None:
        # Add the job URL to the HTML report
        extra.append(pytest_html.extras.url(job_url, 'BrowserStack Job'))

    # Update the job result
    passed = report.passed or (report.failed and hasattr(report, 'wasxfail'))
    job_status = job_info['automation_session']['status']
    status = 'running' if passed else 'error'
    if report.when == 'teardown' and passed:
        status = 'completed'
    if job_status not in ('error', status):
        # Only update the result if it's not already marked as failed
        requests.put(
            api_url,
            headers={'Content-Type': 'application/json'},
            params={'status': status},
            auth=auth,
            timeout=10)


@pytest.fixture
def browserstack_driver(request, capabilities):
    """Return a WebDriver using a BrowserStack instance"""
    test_id = '.'.join(split_class_and_test_names(request.node.nodeid))
    capabilities['name'] = test_id
    executor = EXECUTOR_URL.format(
        username=_username(request.config),
        key=_access_key(request.config))
    return Remote(command_executor=executor,
                  desired_capabilities=capabilities)


def _access_key(config):
    access_key = config.getini('browserstack_access_key')
    if not access_key:
        raise pytest.UsageError('BrowserStack access key must be set')
    return access_key


def _username(config):
    username = config.getini('browserstack_username')
    if not username:
        raise pytest.UsageError('BrowserStack username must be set')
    return username
