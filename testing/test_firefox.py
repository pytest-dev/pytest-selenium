# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = [pytest.mark.nondestructive, pytest.mark.firefox]


def test_launch(testdir, httpserver):
    httpserver.serve_content(content="<h1>Success!</h1>")
    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_pass(webtext):
            assert webtext == u'Success!'
    """
    )
    testdir.quick_qa(file_test, passed=1)


def test_launch_case_insensitive(testdir, httpserver):
    httpserver.serve_content(content="<h1>Success!</h1>")
    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_pass(webtext):
            assert webtext == u'Success!'
    """
    )
    testdir.quick_qa("--driver", "firefox", file_test, passed=1)


def test_profile(testdir, httpserver):
    """Test that specified profile is used when starting Firefox.

    The profile changes the colors in the browser, which are then reflected
    when calling value_of_css_property.
    """
    httpserver.serve_content(content='<h1>Success!</h1><a href="#">Link</a>')
    profile = testdir.tmpdir.mkdir("profile")
    profile.join("prefs.js").write(
        'user_pref("browser.anchor_color", "#FF69B4");'
        'user_pref("browser.display.foreground_color", "#FF0000");'
        'user_pref("browser.display.use_document_colors", false);'
    )
    file_test = testdir.makepyfile(
        """
        import pytest
        from selenium.webdriver.common.by import By
        @pytest.mark.nondestructive
        def test_profile(base_url, selenium):
            selenium.get(base_url)
            header = selenium.find_element(By.TAG_NAME, 'h1')
            anchor = selenium.find_element(By.TAG_NAME, 'a')
            header_color = header.value_of_css_property('color')
            anchor_color = anchor.value_of_css_property('color')
            assert header_color == 'rgb(255, 0, 0)'
            assert anchor_color == 'rgb(255, 105, 180)'
    """
    )
    testdir.quick_qa("--firefox-profile", profile, file_test, passed=1)


def test_profile_with_preferences(testdir, httpserver):
    """Test that preferences override profile when starting Firefox.

    The profile changes the colors in the browser, which are then reflected
    when calling value_of_css_property. The test checks that the color of the
    h1 tag is overridden by the profile, while the color of the a tag is
    overridden by the preference.
    """
    httpserver.serve_content(content='<h1>Success!</h1><a href="#">Link</a>')
    profile = testdir.tmpdir.mkdir("profile")
    profile.join("prefs.js").write(
        'user_pref("browser.anchor_color", "#FF69B4");'
        'user_pref("browser.display.foreground_color", "#FF0000");'
        'user_pref("browser.display.use_document_colors", false);'
    )
    file_test = testdir.makepyfile(
        """
        import pytest
        from selenium.webdriver.common.by import By
        @pytest.mark.nondestructive
        def test_preferences(base_url, selenium):
            selenium.get(base_url)
            header = selenium.find_element(By.TAG_NAME, 'h1')
            anchor = selenium.find_element(By.TAG_NAME, 'a')
            header_color = header.value_of_css_property('color')
            anchor_color = anchor.value_of_css_property('color')
            assert header_color == 'rgb(255, 0, 0)'
            assert anchor_color == 'rgb(255, 0, 0)'
    """
    )
    testdir.quick_qa(
        "--firefox-preference",
        "browser.anchor_color",
        "#FF0000",
        "--firefox-profile",
        profile,
        file_test,
        passed=1,
    )


@pytest.mark.xfail(reason="https://github.com/SeleniumHQ/selenium/pull/5069")
def test_extension(testdir):
    """Test that a firefox extension can be added when starting Firefox."""
    import os

    path = os.path.join(os.path.split(os.path.dirname(__file__))[0], "testing")
    extension = os.path.join(path, "empty.xpi")
    file_test = testdir.makepyfile(
        """
        import time
        import pytest
        from selenium.webdriver.common.by import By
        from selenium.common.exceptions import StaleElementReferenceException
        from selenium.webdriver.support.ui import WebDriverWait
        @pytest.mark.nondestructive
        def test_extension(selenium):
            selenium.get('about:support')
            extensions = WebDriverWait(
                selenium, timeout=10,
                ignored_exceptions=StaleElementReferenceException).until(
                    lambda s: s.find_element(By.ID,
                        'extensions-tbody').text)
            assert 'Test Extension (empty)' in extensions
    """
    )
    testdir.quick_qa("--firefox-extension", extension, file_test, passed=1)


def test_preferences_marker(testdir, httpserver):
    """Test that preferences can be specified using the marker."""
    httpserver.serve_content(content='<h1>Success!</h1><a href="#">Link</a>')
    file_test = testdir.makepyfile(
        """
        import pytest
        from selenium.webdriver.common.by import By
        @pytest.mark.nondestructive
        @pytest.mark.firefox_preferences({
            'browser.anchor_color': '#FF69B4',
            'browser.display.foreground_color': '#FF0000',
            'browser.display.use_document_colors': False})
        def test_preferences(base_url, selenium):
            selenium.get(base_url)
            header = selenium.find_element(By.TAG_NAME, 'h1')
            anchor = selenium.find_element(By.TAG_NAME, 'a')
            header_color = header.value_of_css_property('color')
            anchor_color = anchor.value_of_css_property('color')
            assert header_color == 'rgb(255, 0, 0)'
            assert anchor_color == 'rgb(255, 105, 180)'
    """
    )
    testdir.quick_qa(file_test, passed=1)


def test_arguments_marker(testdir):
    file_test = testdir.makepyfile(
        """
        import pytest
        pytestmark = pytest.mark.firefox_arguments('baz')
        @pytest.mark.nondestructive
        @pytest.mark.firefox_arguments('foo', 'bar')
        def test_arguments(firefox_options):
            actual = sorted(firefox_options.arguments)
            expected = sorted(['baz', 'foo', 'bar'])
            assert actual == expected
    """
    )
    testdir.quick_qa(file_test, passed=1)
