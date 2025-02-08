import pytest
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from browser_use.dom.views import DOMElementNode, SelectorMap
import asyncio
import base64
from browser_use.browser.views import URLNotAllowedError, BrowserError, BrowserState, TabInfo
import json
import logging
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, TypedDict
from playwright.async_api import Browser as PlaywrightBrowser
from playwright.async_api import BrowserContext as PlaywrightBrowserContext
from playwright.async_api import ElementHandle, FrameLocator, Page
from browser_use.dom.service import DomService
from browser_use.utils import time_execution_sync

def test_is_url_allowed():
    """
    Test the _is_url_allowed method of BrowserContext.
    
    This test creates a BrowserContext with a restricted allowed_domains list and verifies that:
    - URLs within the allowed domains (including subdomains) return True.
    - URLs outside of the allowed domains return False.
    """
    class DummyBrowser:
        async def get_playwright_browser(self):
            pass
    # Create a BrowserContextConfig that only allows the "example.com" domain.
    config = BrowserContextConfig(allowed_domains=["example.com"])
    # Instantiate BrowserContext with a dummy browser instance.
    context = BrowserContext(browser=DummyBrowser(), config=config)
    
    # URLs that should be allowed
    assert context._is_url_allowed("https://example.com") is True
    assert context._is_url_allowed("https://sub.example.com/path") is True
    
    # URL that should not be allowed
    assert context._is_url_allowed("https://notexample.com") is False
def test_enhanced_css_selector_for_element():
    """
    Test the _enhanced_css_selector_for_element method of BrowserContext.
    
    This test creates a dummy DOMElementNode with a simple XPath and attributes,
    including a valid class, a safe 'id' attribute, and an additional dynamic attribute.
    It then verifies that the generated CSS selector string is as expected.
    """
    # Create a dummy DOMElementNode with a simple xpath and attributes.
    dummy_element = DOMElementNode(
        tag_name="div",
        is_visible=True,
        parent=None,
        xpath="/html/body/div",
        attributes={
            "class": "test-class",   # valid CSS class to be appended as .test-class
            "id": "unique",          # safe attribute that should be appended as [id="unique"]
            "data-qa": "test"        # dynamic attribute allowed by default (include_dynamic_attributes=True)
        },
        children=[]
    )
    
    expected_selector = 'html > body > div.test-class[id="unique"][data-qa="test"]'
    
    result_selector = BrowserContext._enhanced_css_selector_for_element(dummy_element, include_dynamic_attributes=True)
    
    assert result_selector == expected_selector
def test_convert_simple_xpath_to_css_selector():
    """
    Tests the conversion of XPath expressions to CSS selectors in BrowserContext.
    
    This test covers multiple cases:
    - A simple XPath that includes numeric indices.
    - An XPath using the last() function.
    - An empty XPath input.
    """
    # Test conversion with multiple indices
    xpath1 = "/html/body/div[2]/span[1]"
    expected1 = "html > body > div:nth-of-type(2) > span:nth-of-type(1)"
    result1 = BrowserContext._convert_simple_xpath_to_css_selector(xpath1)
    assert result1 == expected1
    # Test conversion with the last() function in XPath
    xpath2 = "/div[last()]"
    expected2 = "div:last-of-type"
    result2 = BrowserContext._convert_simple_xpath_to_css_selector(xpath2)
    assert result2 == expected2
    # Test conversion with an empty XPath string
    xpath3 = ""
    expected3 = ""
    result3 = BrowserContext._convert_simple_xpath_to_css_selector(xpath3)
    assert result3 == expected3
@pytest.mark.asyncio
async def test_get_scroll_info(monkeypatch):
    """
    Test the get_scroll_info method of BrowserContext.
    This test overrides get_current_page to return a dummy page with predetermined scroll values.
    It verifies that the function correctly calculates the pixels above and below the viewport.
    """
    # Define a dummy page that simulates the evaluate method for scrolling values.
    class DummyPage:
        async def evaluate(self, script):
            if script == 'window.scrollY':
                return 100  # pixels above
            elif script == 'window.innerHeight':
                return 800  # viewport height
            elif script == 'document.documentElement.scrollHeight':
                return 2000  # total height of the page
            else:
                raise ValueError("Unexpected script provided: " + script)
    
    dummy_page = DummyPage()
    # Define a dummy browser for our BrowserContext instance.
    class DummyBrowser:
        async def get_playwright_browser(self):
            pass  # Not used in this test
    # Instantiate our BrowserContext with a dummy browser and default configuration.
    context = BrowserContext(browser=DummyBrowser(), config=BrowserContextConfig())
    
    # Override get_current_page to always return our dummy_page.
    async def fake_get_current_page():
        return dummy_page
    monkeypatch.setattr(context, "get_current_page", fake_get_current_page)
    
    # Call get_scroll_info which uses the overridden get_current_page method.
    pixels_above, pixels_below = await context.get_scroll_info(dummy_page)
    
    # Expected values:
    # pixels_above should be 100.
    # pixels_below should be total_height - (scrollY + viewport_height) = 2000 - (100 + 800) = 1100.
    assert pixels_above == 100
    assert pixels_below == 1100
@pytest.mark.asyncio
async def test_take_screenshot(monkeypatch):
    """
    Test the take_screenshot method of BrowserContext.
    
    This test overrides get_current_page to return a dummy page that returns a predetermined
    binary screenshot (b"dummy"). It verifies that the base64 encoded screenshot matches the expected output.
    """
    class DummyPage:
        async def screenshot(self, full_page=False, animations='disabled'):
            return b"dummy"
    # Create a dummy browser as required by BrowserContext's __init__
    class DummyBrowser:
        async def get_playwright_browser(self):
            pass
    # Instantiate BrowserContext with the dummy browser and default config.
    context = BrowserContext(browser=DummyBrowser(), config=BrowserContextConfig())
    # Override get_current_page to return our DummyPage.
    async def fake_get_current_page():
        return DummyPage()
    monkeypatch.setattr(context, "get_current_page", fake_get_current_page)
    # Call take_screenshot and verify that the encoded result is as expected.
    screenshot_b64 = await context.take_screenshot()
    expected_b64 = base64.b64encode(b"dummy").decode("utf-8")
    assert screenshot_b64 == expected_b64
@pytest.mark.asyncio
async def test_input_text_element_node_success(monkeypatch):
    """
    Test that _input_text_element_node successfully performs text input on a DOM element.
    
    This test overrides get_current_page and get_locate_element to return dummy objects
    that record calls to scroll_into_view_if_needed, fill, and type. It then verifies that these
    methods were invoked with the expected parameters.
    """
    # Create a dummy DOMElementNode representing the target element.
    dummy_dom_element = DOMElementNode(
        tag_name="input",
        is_visible=True,
        parent=None,
        xpath="/html/body/input",
        attributes={"type": "text"},
        children=[]
    )
    # Create a dummy element handle that records method calls.
    class DummyElementHandle:
        def __init__(self):
            self.calls = []
        async def scroll_into_view_if_needed(self, timeout=2500):
            self.calls.append(("scroll_into_view_if_needed", timeout))
        async def fill(self, text):
            self.calls.append(("fill", text))
        async def type(self, text):
            self.calls.append(("type", text))
    dummy_element_handle = DummyElementHandle()
    # Create a dummy page; its wait_for_load_state is a no-op.
    class DummyPage:
        async def wait_for_load_state(self):
            self.called = True  # Record that wait_for_load_state was called
    dummy_page = DummyPage()
    # Create a dummy browser for instantiating BrowserContext.
    class DummyBrowser:
        async def get_playwright_browser(self):
            pass
    # Instantiate BrowserContext using the dummy browser and default configuration.
    context = BrowserContext(browser=DummyBrowser(), config=BrowserContextConfig())
    
    # Override get_current_page to always return our dummy_page.
    async def fake_get_current_page():
        return dummy_page
    monkeypatch.setattr(context, "get_current_page", fake_get_current_page)
    
    # Override get_locate_element to always return our dummy_element_handle.
    async def fake_get_locate_element(element: DOMElementNode):
        return dummy_element_handle
    monkeypatch.setattr(context, "get_locate_element", fake_get_locate_element)
    
    # Call _input_text_element_node with the dummy DOMElementNode and a sample text.
    test_text = "hello world"
    await context._input_text_element_node(dummy_dom_element, test_text)
    
    # Verify that scroll_into_view_if_needed, fill, and type were called with expected arguments.
    expected_calls = [
        ("scroll_into_view_if_needed", 2500),
        ("fill", ""),
        ("type", test_text)
    ]
    assert dummy_element_handle.calls == expected_calls
@pytest.mark.asyncio
async def test_check_and_handle_navigation_not_allowed(monkeypatch):
    """
    Test that _check_and_handle_navigation raises URLNotAllowedError for a disallowed URL and calls go_back.
    
    This test instantiates a BrowserContext configured to only allow 'example.com'.
    It then creates a dummy page with a URL that is not allowed, replaces the go_back method with
    a fake function that records its invocation, and ensures that calling _check_and_handle_navigation
    results in a URLNotAllowedError with a proper message and that the fake go_back function was called.
    """
    # Define a flag to record if go_back was called.
    flag = {"go_back_called": False}
    async def fake_go_back():
        flag["go_back_called"] = True
    # Create a dummy browser that does nothing.
    class DummyBrowser:
        async def get_playwright_browser(self):
            pass
    # Instantiate BrowserContext with allowed domains set to only "example.com"
    config = BrowserContextConfig(allowed_domains=["example.com"])
    context = BrowserContext(browser=DummyBrowser(), config=config)
    # Monkey-patch go_back to record its call.
    monkeypatch.setattr(context, "go_back", fake_go_back)
    # Create a dummy page with a disallowed URL.
    class DummyPage:
        url = "https://notexample.com"
    dummy_page = DummyPage()
    # Expect that _check_and_handle_navigation raises URLNotAllowedError.
    with pytest.raises(URLNotAllowedError) as exc_info:
        await context._check_and_handle_navigation(dummy_page)
    # Verify that the error message indicates the disallowed URL.
    assert "Navigation to non-allowed URL" in str(exc_info.value)
    # Verify that our fake go_back was called.
    assert flag["go_back_called"] is True
@pytest.mark.asyncio
async def test_reset_context(monkeypatch):
    """
    Test that reset_context closes all existing pages and resets the session state
    by creating a new current page. The dummy context simulates pages with a simple
    close implementation and a new_page method.
    """
    # Define a dummy Page class that records whether it was closed.
    class DummyPage:
        def __init__(self, name):
            self.name = name
            self.closed = False
        async def close(self):
            self.closed = True
        async def wait_for_load_state(self):
            pass
    # Define a dummy context with a list of pages and a new_page method.
    class DummyContext:
        def __init__(self, pages):
            self.pages = pages
        async def new_page(self):
            new_page = DummyPage("new_page")
            self.pages.append(new_page)
            return new_page
    # Define a dummy session that holds the context, cached state, and current page.
    class DummySession:
        def __init__(self, context):
            self.context = context
            self.cached_state = None
            self.current_page = context.pages[0] if context.pages else None
    # Create initial dummy pages.
    page1 = DummyPage("page1")
    page2 = DummyPage("page2")
    dummy_context = DummyContext([page1, page2])
    dummy_session = DummySession(dummy_context)
    # Define a dummy browser required by BrowserContext.
    class DummyBrowser:
        async def get_playwright_browser(self):
            pass
    # Instantiate BrowserContext using the dummy browser and default config.
    context = BrowserContext(browser=DummyBrowser(), config=BrowserContextConfig())
    # Monkey-patch get_session to return our dummy session.
    async def fake_get_session():
        return dummy_session
    monkeypatch.setattr(context, "get_session", fake_get_session)
    # Call reset_context which should close all pages and create a new page.
    await context.reset_context()
    # Verify that both original pages were closed.
    assert page1.closed is True
    assert page2.closed is True
    # Verify that a new page was created and assigned as the current page.
    assert dummy_session.current_page.name == "new_page"
    # Verify that the cached state was reset (default initial state has empty URL).
    assert dummy_session.cached_state.url == ""