# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import pytest
import requests

DRIVER = 'BrowserStack'
API_JOB_URL = 'https://www.browserstack.com/automate/sessions/{session}.json'
EXECUTOR_URL = 'http://{username}:{key}@hub.browserstack.com:80/wd/hub'


def pytest_addoption(parser):
    parser.addini('browserstack_username',
                  help='browserstack username',
                  default=os.getenv('BROWSERSTACK_USERNAME'))
    parser.addini('browserstack_access_key',
                  help='browserstack access key',
                  default=os.getenv('BROWSERSTACK_ACCESS_KEY'))


@pytest.mark.optionalhook
def pytest_selenium_runtest_makereport(item, report, summary, extra):
    if item.config.getoption('driver') != DRIVER:
        return

    passed = report.passed or (report.failed and hasattr(report, 'wasxfail'))
    session_id = item._driver.session_id
    auth = (_username(item.config), _access_key(item.config))
    api_url = API_JOB_URL.format(session=session_id)

    try:
        job_info = requests.get(api_url, auth=auth, timeout=10).json()
        job_url = job_info['automation_session']['browser_url']
        # Add the job URL to the summary
        summary.append('{0} Job: {1}'.format(DRIVER, job_url))
        pytest_html = item.config.pluginmanager.getplugin('html')
        # Add the job URL to the HTML report
        extra.append(pytest_html.extras.url(job_url, '{0} Job'.format(DRIVER)))
    except Exception as e:
        summary.append('WARNING: Failed to determine {0} job URL: {1}'.format(
            DRIVER, e))

    try:
        # Update the job result
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
    except Exception as e:
        summary.append('WARNING: Failed to update job status: {0}'.format(e))


def driver_kwargs(request, test, capabilities, **kwargs):
    capabilities.setdefault('name', test)
    executor = EXECUTOR_URL.format(
        username=_username(request.config),
        key=_access_key(request.config))
    kwargs = {
        'command_executor': executor,
        'desired_capabilities': capabilities}
    return kwargs


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
