import asyncio
import pytest
from browser_use.browser.context import BrowserContext, BrowserContextConfig, BrowserError, BrowserSession
from browser_use.dom.views import DOMElementNode
import os
import json
import base64
from browser_use.dom.service import DomService
from browser_use.browser.context import BrowserContext, BrowserContextConfig, BrowserSession

@pytest.mark.asyncio
async def test_navigate_to_disallowed_url():
    """
    Test that navigating to a non-allowed URL raises a BrowserError.
    """
    config = BrowserContextConfig(allowed_domains=["allowed.com"])
    
    class DummyBrowser:
        def __init__(self):
            self.config = type("DummyConfig", (), {"cdp_url": None, "chrome_instance_path": None})
            self.contexts = []
        
        async def get_playwright_browser(self):
            raise Exception("get_playwright_browser should not be called during this test")
        
        async def new_context(self, **kwargs):
            raise Exception("new_context should not be called during this test")
    
    dummy_browser = DummyBrowser()
    context = BrowserContext(dummy_browser, config=config)
    
    with pytest.raises(BrowserError) as exc_info:
        await context.navigate_to("https://disallowed.com")
    
    assert "Navigation to non-allowed URL" in str(exc_info.value)
@pytest.mark.asyncio
async def test_enhanced_css_selector_for_element():
    """
    Test that the enhanced CSS selector generator produces a selector that includes the xpath base,
    valid class names, and safe attributes from a DOMElementNode.
    """
    dummy_element = DOMElementNode(
        tag_name='div',
        xpath='/html/body/div',
        attributes={
            'class': 'foo bar',
            'id': '123',
            'data-qa': 'test',
            'non_safe': 'should_not_be_included'
        },
        children=[],
        parent=None,
        is_visible=True,
        highlight_index=0
    )
    
    selector = BrowserContext._enhanced_css_selector_for_element(dummy_element, include_dynamic_attributes=True)
    
    assert selector.startswith("html > body > div")
    assert ".foo" in selector
    assert ".bar" in selector
    assert '[id="123"]' in selector
    assert '[data-qa="test"]' in selector
    assert "non_safe" not in selector
@pytest.mark.asyncio
async def test_convert_simple_xpath_to_css_selector():
    """
    Test conversion of simple XPath expressions to CSS selectors using BrowserContext._convert_simple_xpath_to_css_selector.
    This test checks a typical indexed XPath, a non-indexed XPath, and the empty string case.
    """
    result = BrowserContext._convert_simple_xpath_to_css_selector("html/body/div")
    assert result == "html > body > div"
    
    result = BrowserContext._convert_simple_xpath_to_css_selector("/html/body/div[1]/span[2]")
    assert result == "html > body > div:nth-of-type(1) > span:nth-of-type(2)"
    
    result = BrowserContext._convert_simple_xpath_to_css_selector("")
    assert result == ""
@pytest.mark.asyncio
async def test_save_cookies_writes_file(tmp_path):
    """
    Test that the save_cookies method writes the expected cookies to a file.
    """
    cookies_file = tmp_path / "cookies.json"
    config = BrowserContextConfig(cookies_file=str(cookies_file))
    
    class DummyContext:
        async def cookies(self):
            return [{"name": "test", "value": "123"}]
        async def close(self):
            pass
    dummy_page = type("DummyPage", (), {})()
    
    class DummyBrowser:
        config = type("DummyConfig", (), {"cdp_url": None, "chrome_instance_path": None})
    
    dummy_browser = DummyBrowser()
    context = BrowserContext(dummy_browser, config=config)
    context.session = BrowserSession(context=DummyContext(), current_page=dummy_page, cached_state=context._get_initial_state())
    
    await context.save_cookies()
    
    with open(cookies_file, 'r') as f:
        cookies = json.load(f)
    assert cookies == [{"name": "test", "value": "123"}]
@pytest.mark.asyncio
async def test_get_page_html_returns_correct_html():
    """
    Test that get_page_html returns the dummy HTML returned by the current page.
    """
    class DummyPage:
        url = "http://dummy.url"
        
        async def content(self):
            return "dummy html"
    
    class DummyContextObj:
        async def cookies(self):
            return []
        async def close(self):
            pass
    
    class DummyBrowser:
        config = type("DummyConfig", (), {"cdp_url": None, "chrome_instance_path": None})
    
    dummy_browser = DummyBrowser()
    config = BrowserContextConfig()
    context = BrowserContext(dummy_browser, config=config)
    
    dummy_page = DummyPage()
    dummy_context_obj = DummyContextObj()
    context.session = BrowserSession(
        context=dummy_context_obj,
        current_page=dummy_page,
        cached_state=context._get_initial_state(dummy_page)
    )
    
    result = await context.get_page_html()
    assert result == "dummy html"
@pytest.mark.asyncio
async def test_take_screenshot_returns_base64():
    """
    Test that take_screenshot returns a base64 encoded string of the screenshot provided by the dummy page.
    This verifies that the screenshot bytes are correctly base64 encoded.
    """
    class DummyPage:
        url = "http://dummy.url"
        async def screenshot(self, full_page=False, animations='disabled'):
            return b"dummy screenshot"
        async def wait_for_load_state(self):
            return None
    dummy_page = DummyPage()
    class DummyContextObj:
        pages = [dummy_page]
        async def cookies(self):
            return []
        async def close(self):
            return None
    class DummyBrowser:
        config = type("DummyConfig", (), {"cdp_url": None, "chrome_instance_path": None})
    
    dummy_browser = DummyBrowser()
    config = BrowserContextConfig()
    browser_context = BrowserContext(dummy_browser, config=config)
    
    browser_context.session = BrowserSession(
        context=DummyContextObj(),
        current_page=dummy_page,
        cached_state=browser_context._get_initial_state(dummy_page)
    )
    
    result = await browser_context.take_screenshot(full_page=True)
    expected = base64.b64encode(b"dummy screenshot").decode('utf-8')
    assert result == expected
@pytest.mark.asyncio
async def test_click_element_node_normal():
    """
    Test that _click_element_node, when provided a valid element,
    performs the click action and returns None (indicating no download path).
    This test bypasses actual DOM service interactions using dummy implementations.
    """
    # Monkey-patch DomService.get_clickable_elements to avoid actual JS evaluation.
    async def dummy_get_clickable_elements(self, focus_element, viewport_expansion, highlight_elements):
        class DummyContent:
            element_tree = DOMElementNode(
                tag_name='root',
                xpath='',
                attributes={},
                children=[],
                parent=None,
                is_visible=True,
                highlight_index=None
            )
            selector_map = {}
        return DummyContent()
    DomService.get_clickable_elements = dummy_get_clickable_elements
    # Create a dummy DOMElementNode for a button.
    dummy_element = DOMElementNode(
        tag_name='button',
        xpath='/html/body/button',
        attributes={},
        children=[],
        parent=None,
        is_visible=True,
        highlight_index=0
    )
    
    # Dummy element handle simulating click and scroll behavior.
    class DummyElementHandle:
        async def click(self, timeout):
            return None
        async def scroll_into_view_if_needed(self, timeout=2500):
            return None
    # Dummy page with necessary methods; note that evaluate now accepts extra arguments.
    class DummyPage:
        url = "http://allowed.com"
        
        async def wait_for_load_state(self):
            return None
        
        async def evaluate(self, script, *args, **kwargs):
            return 1
        
        async def title(self):
            return "dummy title"
    
    # Dummy context object for session.
    class DummyContextObj:
        pages = [DummyPage()]
        
        async def cookies(self):
            return []
        
        async def close(self):
            return None
    # Use allowed_domains so navigation is allowed.
    config = BrowserContextConfig(allowed_domains=["allowed.com"])
    class DummyBrowser:
        config = type("DummyConfig", (), {"cdp_url": None, "chrome_instance_path": None})
    dummy_browser = DummyBrowser()
    context = BrowserContext(dummy_browser, config=config)
    # Set up a dummy session with our dummy page and context object.
    dummy_page = DummyPage()
    dummy_context_obj = DummyContextObj()
    context.session = BrowserSession(
        context=dummy_context_obj,
        current_page=dummy_page,
        cached_state=context._get_initial_state(dummy_page)
    )
    # Monkey-patch get_locate_element to always return our DummyElementHandle instance.
    async def dummy_get_locate_element(element: DOMElementNode):
        return DummyElementHandle()
    context.get_locate_element = dummy_get_locate_element
    # Override _check_and_handle_navigation to do nothing.
    async def dummy_check_and_handle_navigation(page):
        return
    context._check_and_handle_navigation = dummy_check_and_handle_navigation
    # Override _update_state to bypass heavy DOM processing.
    async def dummy_update_state(focus_element=-1):
        return context._get_initial_state(dummy_page)
    context._update_state = dummy_update_state
    # Call _click_element_node and verify it returns None (normal click without a download).
    result = await context._click_element_node(dummy_element)
    assert result is None
@pytest.mark.asyncio
async def test_reset_context_clears_tabs_and_resets_state():
    """
    Test that reset_context closes all existing pages and creates a new current page with a reset state.
    The DummyPage now includes a 'url' attribute to fix the AttributeError.
    """
    # Define dummy implementations for a Page and Context
    class DummyPage:
        def __init__(self):
            self.closed = False
            self.url = "dummy_url"  # Added to allow _get_initial_state to access page.url
        async def close(self):
            self.closed = True
        async def wait_for_load_state(self):
            return None
        async def title(self):
            return "dummy title"
    class DummyContextObj:
        def __init__(self, pages):
            self.pages = pages
        async def new_page(self):
            new_page = DummyPage()
            self.pages.append(new_page)
            return new_page
        async def cookies(self):
            return []
        async def close(self):
            return None
    # Create multiple dummy pages
    page1 = DummyPage()
    page2 = DummyPage()
    dummy_context_obj = DummyContextObj([page1, page2])
    # Create a dummy browser
    DummyBrowser = type("DummyBrowser", (), {"config": type("DummyConfig", (), {"cdp_url": None, "chrome_instance_path": None})})
    dummy_browser = DummyBrowser()
    config = BrowserContextConfig()
    # Create BrowserContext and set its session manually using our dummy context and pages.
    context = BrowserContext(dummy_browser, config=config)
    context.session = BrowserSession(
        context=dummy_context_obj,
        current_page=page1,
        cached_state=context._get_initial_state(page1)
    )
    # Call reset_context which should close all existing pages and create a new current page.
    await context.reset_context()
    # Check that the old dummy pages have been closed.
    assert page1.closed, "First dummy page should be closed after reset_context"
    assert page2.closed, "Second dummy page should be closed after reset_context"
    # Check that a new current page has been created and is not closed.
    new_page = context.session.current_page
    assert not new_page.closed, "New current page should not be closed"
    # Verify that the cached state has been reset (its URL should match an initial empty state).
    initial_state = context._get_initial_state()
    assert context.session.cached_state.url == initial_state.url, "Cached state should be reset after calling reset_context"
@pytest.mark.asyncio
async def test_switch_to_tab_with_negative_index():
    """
    Test that switch_to_tab correctly handles negative indices to switch to the last tab.
    """
    # Dummy Page with required methods
    class DummyPage:
        def __init__(self, url):
            self.url = url
            self.brought_to_front = False
        async def wait_for_load_state(self):
            return None
        async def bring_to_front(self):
            self.brought_to_front = True
            return None
        async def title(self):
            return "Title " + self.url
    # Dummy Context object holding pages
    class DummyContextObj:
        def __init__(self, pages):
            self.pages = pages
        async def cookies(self):
            return []
        async def close(self):
            return None
    # Dummy Browser object with minimal configuration
    class DummyBrowser:
        config = type("DummyConfig", (), {"cdp_url": None, "chrome_instance_path": None})
    # Create multiple dummy pages
    dummy_page1 = DummyPage("http://dummy.com/page1")
    dummy_page2 = DummyPage("http://dummy.com/page2")
    dummy_page3 = DummyPage("http://dummy.com/page3")
    dummy_context_obj = DummyContextObj([dummy_page1, dummy_page2, dummy_page3])
    # Configure allowed_domains to ensure pages with dummy.com are allowed
    config = BrowserContextConfig(allowed_domains=["dummy.com"])
    context = BrowserContext(DummyBrowser(), config=config)
    context.session = BrowserSession(
        context=dummy_context_obj,
        current_page=dummy_page1,
        cached_state=context._get_initial_state(dummy_page1)
    )
    # Use negative index to switch to the last page
    await context.switch_to_tab(-1)
    # Assert that the current page is now the last dummy page
    assert context.session.current_page is dummy_context_obj.pages[-1]
    # Also verify that bring_to_front was triggered on that page
    assert dummy_context_obj.pages[-1].brought_to_front is True
@pytest.mark.asyncio
async def test_is_file_uploader_identifies_file_input():
    """
    Test that is_file_uploader correctly identifies DOM elements that function as file uploaders.
    This test covers a direct file input element, a non-file element, and a nested file input element.
    """
    # Create a dummy Browser object with minimal configuration.
    class DummyBrowser:
        config = type("DummyConfig", (), {"cdp_url": None, "chrome_instance_path": None})
    
    dummy_browser = DummyBrowser()
    config = BrowserContextConfig()
    context = BrowserContext(dummy_browser, config=config)
    
    # Create a DOMElementNode representing a file input element.
    file_input = DOMElementNode(
        tag_name='input',
        xpath='/html/body/input',
        attributes={'type': 'file'},
        children=[],
        parent=None,
        is_visible=True,
        highlight_index=0
    )
    
    # Verify that the file input is identified as a file uploader.
    is_uploader = await context.is_file_uploader(file_input)
    assert is_uploader is True
    
    # Create a DOMElementNode representing a non-file input element (e.g., text input).
    text_input = DOMElementNode(
        tag_name='input',
        xpath='/html/body/input',
        attributes={'type': 'text'},
        children=[],
        parent=None,
        is_visible=True,
        highlight_index=1
    )
    
    is_uploader_text = await context.is_file_uploader(text_input)
    assert is_uploader_text is False
    
    # Create a parent element that contains a child file input element.
    child_file_input = DOMElementNode(
        tag_name='input',
        xpath='/html/body/div/input',
        attributes={'type': 'file'},
        children=[],
        parent=None,
        is_visible=True,
        highlight_index=2
    )
    parent_div = DOMElementNode(
        tag_name='div',
        xpath='/html/body/div',
        attributes={},
        children=[child_file_input],
        parent=None,
        is_visible=True,
        highlight_index=3
    )
    # Set the child's parent reference.
    child_file_input.parent = parent_div
    
    is_uploader_nested = await context.is_file_uploader(parent_div)
    assert is_uploader_nested is True