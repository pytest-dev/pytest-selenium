from setuptools import setup

setup(
    name="pytest-selenium",
    use_scm_version=True,
    description="pytest plugin for Selenium",
    long_description=open("README.rst").read(),
    author="Dave Hunt",
    author_email="dhunt@mozilla.com",
    url="https://github.com/pytest-dev/pytest-selenium",
    packages=["pytest_selenium", "pytest_selenium.drivers"],
    install_requires=[
        "pytest>=3.6",
        "pytest-base-url",
        "pytest-html>=1.14.0",
        "pytest-variables>=1.5.0",
        "selenium>=3.0.0",
        "requests",
    ],
    entry_points={
        "pytest11": [
            "selenium = pytest_selenium.pytest_selenium",
            "selenium_safety = pytest_selenium.safety",
            "browserstack_driver = pytest_selenium.drivers.browserstack",
            "crossbrowsertesting_driver = "
            "pytest_selenium.drivers.crossbrowsertesting",
            "chrome_driver = pytest_selenium.drivers.chrome",
            "edge_driver = pytest_selenium.drivers.edge",
            "firefox_driver = pytest_selenium.drivers.firefox",
            "ie_driver = pytest_selenium.drivers.internet_explorer",
            "remote_driver = pytest_selenium.drivers.remote",
            "phantomjs_driver = pytest_selenium.drivers.phantomjs",
            "safari_driver = pytest_selenium.drivers.safari",
            "saucelabs_driver = pytest_selenium.drivers.saucelabs",
            "testingbot_driver = pytest_selenium.drivers.testingbot",
        ]
    },
    setup_requires=["setuptools_scm"],
    license="Mozilla Public License 2.0 (MPL 2.0)",
    keywords="py.test pytest selenium saucelabs browserstack webqa qa " "mozilla",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Utilities",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
