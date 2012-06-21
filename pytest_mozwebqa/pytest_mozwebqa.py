#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import py
import re
import ConfigParser

import requests

import credentials

__version__ = '1.1'

def pytest_configure(config):
    if not hasattr(config, 'slaveinput'):

        config.addinivalue_line(
            'markers', 'nondestructive: mark the test as nondestructive. ' \
            'Tests are assumed to be destructive unless this marker is ' \
            'present. This reduces the risk of running destructive tests ' \
            'accidentally.')

        if config.option.webqa_report_path:
            from html_report import HTMLReport
            config._html = HTMLReport(config)
            config.pluginmanager.register(config._html)

        if not config.option.run_destructive:
            if config.option.markexpr:
                config.option.markexpr = 'nondestructive and (%s)' % config.option.markexpr
            else:
                config.option.markexpr = 'nondestructive'


def pytest_unconfigure(config):
    html = getattr(config, '_html', None)
    if html:
        del config._html
        config.pluginmanager.unregister(html)


def pytest_sessionstart(session):
    if session.config.option.base_url and not (session.config.option.skip_url_check or session.config.option.collectonly):
        r = requests.get(session.config.option.base_url, verify=False)
        assert r.status_code == 200, 'Base URL did not return status code 200. (URL: %s, Response: %s)' % (session.config.option.base_url, r.status_code)


def pytest_runtest_setup(item):
    item.debug = {
        'urls': [],
        'screenshots': [],
        'html': [],
        'logs': [],
        'network_traffic': []}
    TestSetup.base_url = item.config.option.base_url

    # consider this environment sensitive if the base url or any redirection
    # history matches the regular expression
    sensitive = False
    if TestSetup.base_url and not item.config.option.skip_url_check:
        r = requests.get(TestSetup.base_url, verify=False)
        urls = [h.url for h in r.history] + [r.url]
        matches = [re.search(item.config.option.sensitive_url, u) for u in urls]
        sensitive = any(matches)

    destructive = 'nondestructive' not in item.keywords

    if (sensitive and destructive):
        first_match = matches[next(i for i, match in enumerate(matches) if match)]

        # skip the test with an appropriate message
        py.test.skip('This test is destructive and the target URL is ' \
                     'considered a sensitive environment. If this test is ' \
                     'not destructive, add the \'nondestructive\' marker to ' \
                     'it. Sensitive URL: %s' % first_match.string)

    if item.config.option.sauce_labs_credentials_file:
        item.sauce_labs_credentials = credentials.read(item.config.option.sauce_labs_credentials_file)

    if item.config.option.credentials_file:
        TestSetup.credentials = credentials.read(item.config.option.credentials_file)

    test_id = '.'.join(split_class_and_test_names(item.nodeid))

    if 'skip_selenium' not in item.keywords:
        if hasattr(item, 'sauce_labs_credentials'):
            from sauce_labs import Client
            TestSetup.selenium_client = Client(
                test_id,
                item.config.option,
                item.keywords,
                item.sauce_labs_credentials)
        else:
            from selenium_client import Client
            TestSetup.selenium_client = Client(
                test_id,
                item.config.option)
        TestSetup.selenium_client.start()
        item.session_id = TestSetup.selenium_client.session_id
        TestSetup.selenium = TestSetup.selenium_client.selenium
        TestSetup.timeout = TestSetup.selenium_client.timeout
        TestSetup.default_implicit_wait = TestSetup.selenium_client.default_implicit_wait
    else:
        TestSetup.timeout = item.config.option.webqatimeout
        TestSetup.selenium = None


def pytest_runtest_teardown(item):
    if hasattr(TestSetup, 'selenium') and TestSetup.selenium and 'skip_selenium' not in item.keywords:
        TestSetup.selenium_client.stop()


def pytest_runtest_makereport(__multicall__, item, call):
    report = __multicall__.execute()
    if report.when == 'call':
        report.session_id = getattr(item, 'session_id', None)
        if hasattr(TestSetup, 'selenium') and TestSetup.selenium and not 'skip_selenium' in item.keywords:
            if report.skipped and 'xfail' in report.keywords or report.failed and 'xfail' not in report.keywords:
                url = TestSetup.selenium_client.url
                url and item.debug['urls'].append(url)
                screenshot = TestSetup.selenium_client.screenshot
                screenshot and item.debug['screenshots'].append(screenshot)
                html = TestSetup.selenium_client.html
                html and item.debug['html'].append(html)
                log = TestSetup.selenium_client.log
                log and item.debug['logs'].append(log)
                report.sections.append(('pytest-mozwebqa', _debug_summary(item.debug)))
            network_traffic = TestSetup.selenium_client.network_traffic
            network_traffic and item.debug['network_traffic'].append(network_traffic)
            report.debug = item.debug
            if hasattr(item, 'sauce_labs_credentials') and report.session_id:
                result = {'passed': report.passed or (report.failed and 'xfail' in report.keywords)}
                import sauce_labs
                sauce_labs.Job(report.session_id).send_result(
                    result,
                    item.sauce_labs_credentials)
    return report


def pytest_funcarg__mozwebqa(request):
    return TestSetup(request)


def pytest_addoption(parser):
    config = ConfigParser.ConfigParser(defaults={
        'baseurl': '',
        'api': 'webdriver'
    })
    config.read('mozwebqa.cfg')

    group = parser.getgroup('selenium', 'selenium')
    group._addoption('--baseurl',
                     action='store',
                     dest='base_url',
                     default=config.get('DEFAULT', 'baseurl'),
                     metavar='url',
                     help='base url for the application under test.')
    group._addoption('--skipurlcheck',
                     action='store_true',
                     dest='skip_url_check',
                     default=False,
                     help='skip the base url and sensitivity checks. (default: %default)')
    group._addoption('--api',
                     action='store',
                     default=config.get('DEFAULT', 'api'),
                     metavar='api',
                     help="version of selenium api to use. 'rc' uses selenium rc. 'webdriver' uses selenium webdriver. (default: %default)")
    group._addoption('--host',
                     action='store',
                     default='localhost',
                     metavar='str',
                     help='host that selenium server is listening on. (default: %default)')
    group._addoption('--port',
                     action='store',
                     type='int',
                     default=4444,
                     metavar='num',
                     help='port that selenium server is listening on. (default: %default)')
    group._addoption('--driver',
                     action='store',
                     dest='driver',
                     default='Remote',
                     metavar='str',
                     help='webdriver implementation. (default: %default)')
    group._addoption('--capabilities',
                     action='store',
                     dest='capabilities',
                     metavar='str',
                     help='json string of additional capabilties to set (webdriver).')
    group._addoption('--chromepath',
                     action='store',
                     dest='chrome_path',
                     metavar='path',
                     help='path to the google chrome driver executable.')
    group._addoption('--firefoxpath',
                     action='store',
                     dest='firefox_path',
                     metavar='path',
                     help='path to the target firefox binary.')
    group._addoption('--firefoxpref',
                     action='store',
                     dest='firefox_preferences',
                     metavar='str',
                     help='json string of firefox preferences to set (webdriver).')
    group._addoption('--profilepath',
                     action='store',
                     dest='profile_path',
                     metavar='str',
                     help='path to the firefox profile to use (webdriver).')
    group._addoption('--extension',
                     action='append',
                     dest='extension_paths',
                     metavar='str',
                     help='path to browser extension to install (webdriver).')
    group._addoption('--chromeopts',
                     action='store',
                     dest='chrome_options',
                     metavar='str',
                     help='json string of google chrome options to set (webdriver).')
    group._addoption('--operapath',
                     action='store',
                     dest='opera_path',
                     metavar='path',
                     help='path to the opera driver.')
    group._addoption('--browser',
                     action='store',
                     dest='browser',
                     metavar='str',
                     help='target browser (standalone rc server).')
    group._addoption('--environment',
                     action='store',
                     dest='environment',
                     metavar='str',
                     help='target environment (grid rc).')
    group._addoption('--browsername',
                     action='store',
                     dest='browser_name',
                     metavar='str',
                     help='target browser name (webdriver).')
    group._addoption('--browserver',
                     action='store',
                     dest='browser_version',
                     metavar='str',
                     help='target browser version (webdriver).')
    group._addoption('--platform',
                     action='store',
                     metavar='str',
                     help='target platform (webdriver).')
    group._addoption('--webqatimeout',
                     action='store',
                     type='int',
                     default=60,
                     metavar='num',
                     help='timeout (in seconds) for page loads, etc. (default: %default)')
    group._addoption('--capturenetwork',
                     action='store_true',
                     dest='capture_network',
                     default=False,
                     help='capture network traffic to test_method_name.json (selenium rc). (default: %default)')
    group._addoption('--build',
                     action='store',
                     dest='build',
                     metavar='str',
                     help='build identifier (for continuous integration).')
    group._addoption('--untrusted',
                     action='store_true',
                     dest='assume_untrusted',
                     default=False,
                     help='assume that all certificate issuers are untrusted. (default: %default)')
    group._addoption('--proxy',
                     action='store',
                     dest='proxy',
                     metavar='str',
                     help='http proxy address.')

    group = parser.getgroup('safety', 'safety')
    group._addoption('--sensitiveurl',
                     action='store',
                     dest='sensitive_url',
                     default='mozilla\.(com|org)',
                     metavar='str',
                     help='regular expression for identifying sensitive urls. (default: %default)')
    group._addoption('--destructive',
                     action='store_true',
                     dest='run_destructive',
                     default=False,
                     help='include destructive tests (tests not explicitly marked as \'nondestructive\'). (default: %default)')

    group = parser.getgroup('credentials', 'credentials')
    group._addoption("--credentials",
                     action="store",
                     dest='credentials_file',
                     metavar='path',
                     help="location of yaml file containing user credentials.")
    group._addoption('--saucelabs',
                     action='store',
                     dest='sauce_labs_credentials_file',
                     metavar='path',
                     help='credendials file containing sauce labs username and api key.')

    group = parser.getgroup("terminal reporting")
    group.addoption('--webqareport',
                    action='store',
                    dest='webqa_report_path',
                    metavar='path',
                    default='results/index.html',
                    help='create mozilla webqa custom report file at given path. (default: %default)')


def split_class_and_test_names(nodeid):
    names = nodeid.split("::")
    names[0] = names[0].replace("/", '.')
    names = [x.replace(".py", "") for x in names if x != "()"]
    classnames = names[:-1]
    classname = ".".join(classnames)
    name = names[-1]
    return (classname, name)


def _debug_summary(debug):
    summary = []
    if debug['urls']:
        summary.append('Failing URL: %s' % debug['urls'][-1])
    return '\n'.join(summary)


class TestSetup:
    '''
        This class is just used for monkey patching
    '''
    def __init__(self, request):
        self.request = request
