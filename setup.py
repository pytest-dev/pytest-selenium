from setuptools import setup

setup(name='pytest-mozwebqa',
      version='2.0',
      description='Mozilla WebQA plugin for py.test.',
      author='Dave Hunt',
      author_email='dhunt@mozilla.com',
      url='https://github.com/mozilla/pytest-mozwebqa',
      packages=['pytest_mozwebqa', 'pytest_mozwebqa.cloud'],
      install_requires=[
          'pytest>=2.2.4',
          'selenium>=2.26.0',
          'requests==2.6.0'],
      entry_points={'pytest11': [
          'mozwebqa = pytest_mozwebqa.pytest_mozwebqa',
          'mozwebqa_safety = pytest_mozwebqa.safety']},
      license='Mozilla Public License 2.0 (MPL 2.0)',
      keywords='py.test pytest selenium saucelabs browserstack mozwebqa webqa '
               'qa mozilla',
      classifiers=[
          'Development Status :: 5 - Production/Stable',
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
