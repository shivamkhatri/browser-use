import pytest
import asyncio
from unittest.mock import AsyncMock
from browser_use.browser.browser import Browser, BrowserConfig
import requests
import subprocess
from browser_use.browser.context import BrowserContext, BrowserContextConfig

# No additional imports needed since the test uses only imports already present in the test file.
@pytest.mark.asyncio
async def test_close_cleans_up():
    """
    Test that the 'close' method cleans up the playwright browser and playwright attributes
    by calling their asynchronous shutdown methods and setting them to None.
    """
    browser_instance = Browser()
    dummy_browser = AsyncMock()
    dummy_playwright = AsyncMock()
    browser_instance.playwright_browser = dummy_browser
    browser_instance.playwright = dummy_playwright
    await browser_instance.close()
    dummy_browser.close.assert_called_once()
    dummy_playwright.stop.assert_called_once()
    assert browser_instance.playwright is None
    assert browser_instance.playwright_browser is None
@pytest.mark.asyncio
async def test_setup_standard_browser():
    """
    Test that the _setup_browser method chooses the standard browser setup branch when
    no CDP, WSS, or Chrome instance path is provided. This is done by injecting a dummy 
    playwright object with a dummy chromium.launch method and verifying that it is called 
    with the expected arguments, and that the returned browser is the dummy browser.
    """
    dummy_browser = AsyncMock()
    dummy_chromium = type("DummyChromium", (), {})()
    dummy_chromium.launch = AsyncMock(return_value=dummy_browser)
    dummy_playwright = type("DummyPlaywright", (), {})()
    dummy_playwright.chromium = dummy_chromium
    config = BrowserConfig(headless=True, disable_security=False, extra_chromium_args=["--test-arg"])
    browser_instance = Browser(config=config)
    result = await browser_instance._setup_browser(dummy_playwright)
    dummy_chromium.launch.assert_called_once()
    called_args, called_kwargs = dummy_chromium.launch.call_args
    assert called_kwargs["headless"] == True
    assert called_kwargs["proxy"] is None
    args_list = called_kwargs["args"]
    assert "--test-arg" in args_list
    assert "--no-sandbox" in args_list
    assert result == dummy_browser
@pytest.mark.asyncio
async def test_setup_cdp_branch():
    """
    Test that when a CDP URL is provided, the _setup_browser method calls
    _setup_cdp, which in turn calls playwright.chromium.connect_over_cdp with the provided URL.
    """
    dummy_browser = AsyncMock()
    dummy_chromium = type("DummyChromium", (), {})()
    dummy_chromium.connect_over_cdp = AsyncMock(return_value=dummy_browser)
    dummy_playwright = type("DummyPlaywright", (), {})()
    dummy_playwright.chromium = dummy_chromium
    config = BrowserConfig(cdp_url="http://example.com/json/version")
    browser_instance = Browser(config=config)
    result = await browser_instance._setup_browser(dummy_playwright)
    dummy_chromium.connect_over_cdp.assert_called_once_with("http://example.com/json/version")
    assert result == dummy_browser
@pytest.mark.asyncio
async def test_setup_browser_with_instance_failure(monkeypatch):
    """
    Test that _setup_browser_with_instance raises a RuntimeError when failing to connect to a new Chrome instance.
    This simulates the absence of an existing Chrome instance by forcing requests.get to always fail and ensuring
    that playwright.chromium.connect_over_cdp fails after launching a new instance.
    """
    class DummyChromium:
        async def connect_over_cdp(self, endpoint_url, timeout):
            raise Exception("Connection failed")
    
    class DummyPlaywright:
        pass
    dummy_playwright = DummyPlaywright()
    dummy_playwright.chromium = DummyChromium()
    
    config = BrowserConfig(chrome_instance_path="dummy/chrome")
    browser_instance = Browser(config=config)
    
    def always_fail_get(url, timeout):
        raise requests.ConnectionError
    monkeypatch.setattr(requests, "get", always_fail_get)
    
    def dummy_popen(args, stdout, stderr):
        return None
    monkeypatch.setattr(subprocess, "Popen", dummy_popen)
    
    async def dummy_sleep(_):
        pass
    monkeypatch.setattr(asyncio, "sleep", dummy_sleep)
    
    with pytest.raises(RuntimeError, match="To start chrome in Debug mode"):
        await browser_instance._setup_browser_with_instance(dummy_playwright)
@pytest.mark.asyncio
async def test_setup_wss_branch():
    """
    Test that when a WSS URL is provided in the configuration,
    the _setup_browser method uses the _setup_wss branch,
    calling playwright.chromium.connect with the provided wss_url,
    and returning the dummy browser.
    """
    dummy_browser = AsyncMock()
    dummy_chromium = type("DummyChromium", (), {})()
    dummy_chromium.connect = AsyncMock(return_value=dummy_browser)
    dummy_playwright = type("DummyPlaywright", (), {})()
    dummy_playwright.chromium = dummy_chromium
    config = BrowserConfig(wss_url="ws://example.com/socket")
    browser_instance = Browser(config=config)
    result = await browser_instance._setup_browser(dummy_playwright)
    dummy_chromium.connect.assert_called_once_with("ws://example.com/socket")
    assert result == dummy_browser
@pytest.mark.asyncio
async def test_new_context_creation():
    """
    Test that new_context creates a BrowserContext with the correct configuration and links back to the original Browser instance.
    """
    custom_context_config = BrowserContextConfig()
    browser_instance = Browser()
    context = await browser_instance.new_context(config=custom_context_config)
    assert isinstance(context, BrowserContext)
    assert context.browser == browser_instance
    assert context.config == custom_context_config
@pytest.mark.asyncio
async def test_get_playwright_browser_returns_cached():
    """
    Test that get_playwright_browser returns the cached browser instance when it has already been initialized,
    bypassing the _init call.
    """
    browser_instance = Browser()
    dummy_browser = AsyncMock()
    browser_instance.playwright_browser = dummy_browser
    returned_browser = await browser_instance.get_playwright_browser()
    assert returned_browser == dummy_browser
@pytest.mark.asyncio
async def test_setup_standard_browser_with_disable_security():
    """
    Test that when disable_security is enabled in the configuration,
    the _setup_standard_browser method includes the disable security arguments
    along with extra chromium arguments when launching the browser.
    """
    dummy_browser = AsyncMock()
    # Create a dummy chromium with a mocked launch method.
    dummy_chromium = type("DummyChromium", (), {})()
    dummy_chromium.launch = AsyncMock(return_value=dummy_browser)
    
    dummy_playwright = type("DummyPlaywright", (), {})()
    dummy_playwright.chromium = dummy_chromium
    # Use config with disable_security True (default) and extra_chromium_args.
    config = BrowserConfig(headless=False, disable_security=True, extra_chromium_args=["--my-extra"])
    browser_instance = Browser(config=config)
    result = await browser_instance._setup_browser(dummy_playwright)
    
    dummy_chromium.launch.assert_called_once()
    called_args, called_kwargs = dummy_chromium.launch.call_args
    # Verify that the headless configuration is passed correctly.
    assert called_kwargs["headless"] is False
    # Verify no proxy is passed.
    assert called_kwargs["proxy"] is None
    args_list = called_kwargs["args"]
    # Check that base launch parameters expected in standard mode are present.
    assert "--no-sandbox" in args_list
    # Check that disable security flags have been added.
    assert "--disable-web-security" in args_list
    assert "--disable-site-isolation-trials" in args_list
    assert "--disable-features=IsolateOrigins,site-per-process" in args_list
    # Check that extra chromium arguments are included.
    assert "--my-extra" in args_list
    # Verify the dummy browser was returned.
    assert result == dummy_browser
@pytest.mark.asyncio
async def test_get_playwright_browser_initialization(monkeypatch):
    """
    Test that get_playwright_browser properly initializes the browser when no cached instance exists.
    This verifies that async_playwright is started, _setup_browser is called from _init,
    and that the returned browser instance is cached.
    """
    # Create a dummy browser to be returned by launch.
    dummy_browser = AsyncMock()
    # Create a dummy Chromium with a mocked launch method.
    class DummyChromium:
        async def launch(self, headless, args, proxy):
            return dummy_browser
    dummy_chromium = DummyChromium()
    # Create a dummy Playwright with a dummy chromium attribute and a stop method.
    class DummyPlaywright:
        def __init__(self):
            self.chromium = dummy_chromium
            self.stop = AsyncMock()
    dummy_playwright = DummyPlaywright()
    # Create a dummy async_playwright function that returns a dummy async context.
    class DummyAsyncPlaywright:
        async def start(self):
            return dummy_playwright
        async def stop(self):
            pass
    # Monkey-patch async_playwright in the browser module with our dummy.
    monkeypatch.setattr("browser_use.browser.browser.async_playwright", lambda: DummyAsyncPlaywright())
    # Create a Browser instance with config that triggers the standard browser branch.
    config = BrowserConfig(headless=True, disable_security=False, extra_chromium_args=["--test-arg"])
    browser_instance = Browser(config=config)
    # Call get_playwright_browser which should initialize the browser and cache it.
    result_browser = await browser_instance.get_playwright_browser()
    # Verify that _init has been called and the playwright and browser instances cached.
    assert browser_instance.playwright == dummy_playwright
    assert browser_instance.playwright_browser == dummy_browser
    assert result_browser == dummy_browser
@pytest.mark.asyncio
async def test_setup_browser_with_instance_no_path():
    """
    Test that _setup_browser_with_instance immediately raises a ValueError 
    when the chrome_instance_path is not provided in the configuration.
    """
    # Create a BrowserConfig with chrome_instance_path explicitly set to None.
    config = BrowserConfig(chrome_instance_path=None)
    browser_instance = Browser(config=config)
    # Provide a dummy playwright (it won't be used since the method should fail immediately)
    dummy_playwright = object()
    
    # Verify that calling _setup_browser_with_instance raises ValueError
    with pytest.raises(ValueError, match="Chrome instance path is required"):
        await browser_instance._setup_browser_with_instance(dummy_playwright)