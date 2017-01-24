# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import requests

from pytest_selenium.drivers.cloud import Provider


class BrowserStack(Provider):

    API = 'https://www.browserstack.com/automate/sessions/{session}.json'

    @property
    def auth(self):
        return (self.username, self.key)

    @property
    def executor(self):
        return 'http://{0}:{1}@hub.browserstack.com:80/wd/hub'.format(
            self.username, self.key)

    @property
    def username(self):
        return self.get_credential('username', 'BROWSERSTACK_USERNAME')

    @property
    def key(self):
        return self.get_credential('key', 'BROWSERSTACK_ACCESS_KEY')


@pytest.mark.optionalhook
def pytest_selenium_runtest_makereport(item, report, summary, extra):
    provider = BrowserStack()
    if item.config.getoption('driver') != provider.driver:
        return

    passed = report.passed or (report.failed and hasattr(report, 'wasxfail'))
    session_id = item._driver.session_id
    api_url = provider.API.format(session=session_id)

    try:
        job_info = requests.get(api_url, auth=provider.auth, timeout=10).json()
        job_url = job_info['automation_session']['browser_url']
        # Add the job URL to the summary
        summary.append('{0} Job: {1}'.format(provider.name, job_url))
        pytest_html = item.config.pluginmanager.getplugin('html')
        # Add the job URL to the HTML report
        extra.append(pytest_html.extras.url(job_url, '{0} Job'.format(
            provider.name)))
    except Exception as e:
        summary.append('WARNING: Failed to determine {0} job URL: {1}'.format(
            provider.name, e))

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
                auth=provider.auth,
                timeout=10)
    except Exception as e:
        summary.append('WARNING: Failed to update job status: {0}'.format(e))


def driver_kwargs(request, test, capabilities, **kwargs):
    provider = BrowserStack()
    capabilities.setdefault('name', test)
    kwargs = {
        'command_executor': provider.executor,
        'desired_capabilities': capabilities}
    return kwargs
