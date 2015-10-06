from setuptools import setup

setup(name='pytest-selenium',
      version='1.0b2',
      description='pytest plugin for Selenium',
      long_description=open('README.rst').read(),
      author='Dave Hunt',
      author_email='dhunt@mozilla.com',
      url='https://github.com/davehunt/pytest-selenium',
      packages=['pytest_selenium', 'pytest_selenium.cloud'],
      install_requires=[
          'pytest>=2.6.4',
          'pytest-html>=1.6',
          'pytest-variables',
          'selenium>=2.26.0',
          'requests'],
      entry_points={'pytest11': [
          'selenium = pytest_selenium.pytest_selenium',
          'selenium_safety = pytest_selenium.safety']},
      license='Mozilla Public License 2.0 (MPL 2.0)',
      keywords='py.test pytest selenium saucelabs browserstack webqa qa '
               'mozilla',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
          'Operating System :: POSIX',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: MacOS :: MacOS X',
          'Topic :: Software Development :: Quality Assurance',
          'Topic :: Software Development :: Testing',
          'Topic :: Utilities',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7'])
