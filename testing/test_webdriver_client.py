#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytestmark = [pytest.mark.skip_selenium,
                           pytest.mark.nondestructive]


def testStartWebDriverClient(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            mozwebqa.selenium.get('http://localhost:8000/')
            header = mozwebqa.selenium.find_element_by_tag_name('h1')
            assert header.text == 'Success!'
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:8000',
                                '--api=webdriver',
                                '--driver=firefox',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1

def testSpecifyingFirefoxProfile(testdir):
    """Test that a specified profile is used when starting firefox.
        The profile changes the colors in the browser, which are then reflected when calling
        value_of_css_property.
    """
    profile = testdir.tmpdir.mkdir('profile')
    profile.join('prefs.js').write(
        'user_pref("browser.anchor_color", "#FF69B4");'
        'user_pref("browser.display.foreground_color", "#FF0000");'
        'user_pref("browser.display.use_document_colors", false);')
    file_test = testdir.makepyfile("""
        import pytest, time
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            mozwebqa.selenium.get('http://localhost:8000/')
            header = mozwebqa.selenium.find_element_by_tag_name('h1')
            anchor = mozwebqa.selenium.find_element_by_tag_name('a')
            header_color = header.value_of_css_property('color')
            anchor_color = anchor.value_of_css_property('color')
            assert header_color == 'rgba(255, 0, 0, 1)'
            assert anchor_color == 'rgba(255, 105, 180, 1)'
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:8000',
        '--api=webdriver',
        '--driver=firefox',
        '--profilepath=%s' % profile,
        file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1

def testSpecifyingFirefoxProfileAndOverridingPreferences(testdir):
    """Test that a specified profile is used when starting firefox.
        The profile changes the colors in the browser, which are then reflected when calling
        value_of_css_property. The test checks that the color of the h1 tag is overridden by
        the profile, while the color of the a tag is overridden by the preference.
    """
    profile = testdir.tmpdir.mkdir('profile')
    profile.join('prefs.js').write(
        'user_pref("browser.anchor_color", "#FF69B4");'
        'user_pref("browser.display.foreground_color", "#FF0000");'
        'user_pref("browser.display.use_document_colors", false);')
    file_test = testdir.makepyfile("""
        import pytest, time
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            mozwebqa.selenium.get('http://localhost:8000/')
            header = mozwebqa.selenium.find_element_by_tag_name('h1')
            anchor = mozwebqa.selenium.find_element_by_tag_name('a')
            header_color = header.value_of_css_property('color')
            anchor_color = anchor.value_of_css_property('color')
            assert header_color == 'rgba(255, 0, 0, 1)'
            assert anchor_color == 'rgba(255, 0, 0, 1)'
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:8000',
        '--api=webdriver',
        '--driver=firefox',
        '--firefoxpref=''{"browser.anchor_color":"#FF0000"}''',
        '--profilepath=%s' % profile,
        file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1

def testAddingFirefoxExtension(testdir):
    """Test that a firefox extension can be added when starting firefox."""
    import os
    path_to_extensions_folder = os.path.join(os.path.split(os.path.dirname(__file__))[0], 'testing')
    extension = os.path.join(path_to_extensions_folder, 'empty.xpi')
    file_test = testdir.makepyfile("""
        import pytest, time
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            mozwebqa.selenium.get('about:support')
            extensions = mozwebqa.selenium.find_element_by_id('extensions-tbody').text
            assert 'Test Extension (empty)' in extensions
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:8000',
        '--api=webdriver',
        '--driver=firefox',
        '--extension=''%s''' % extension,
        file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1
