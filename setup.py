from setuptools import setup

setup(
    name = 'pytest-mozwebqa',
    version = '0.8',
    description='Mozilla WebQA plugin for py.test.',
    author = 'Dave Hunt',
    author_email = 'dhunt@mozilla.com',
    install_requires = ['pytest>=2.2.3', 'selenium', 'pyyaml', 'requests'],
    url = 'https://github.com/davehunt/pytest-mozwebqa',
    packages = ['mozwebqa'],
    # the following makes a plugin available to py.test
    entry_points = {
        'pytest11': [
            'mozwebqa = mozwebqa.mozwebqa',
        ]
    },
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL)',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
        'Topic :: Utilities',
        'Programming Language :: Python',
    ]
)
