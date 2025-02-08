import asyncio
import pytest
from browser_use.browser.browser import Browser, BrowserConfig
import subprocess
import requests
from browser_use.browser.context import BrowserContext, BrowserContextConfig

# All needed imports are already present in the test file:
#   import asyncio
#   import pytest
#   from browser_use.browser.browser import Browser, BrowserConfig
#   import subprocess
#   import requests
@pytest.mark.asyncio
async def test_setup_standard_browser(monkeypatch):
    """
    Test that _setup_standard_browser correctly launches a standard browser.
    This test uses a fake Playwright object with a monkey-patched launch method to
    simulate starting a browser. The test verifies that the returned browser instance
    matches the dummy object and checks for expected launch arguments.
    """
    # Dummy browser instance to be returned by fake_launch.
    dummy_browser = object()
    
    # Define an async fake launch method that simulates launching the browser.
    async def fake_launch(headless, args, proxy):
        # Assert that we received some expected options.
        assert headless is True
        # The '--no-sandbox' arg is expected in the standard launch.
        assert '--no-sandbox' in args
        # Extra chromium args from config should be appended.
        assert '--extra-arg' in args
        # When disable_security is False, disable_security_args should not be added.
        assert '--disable-web-security' not in args
        # Return the dummy browser instance.
        return dummy_browser
    
    # Create a fake Chromium class with the launch method.
    class FakeChromium:
        async def launch(self, headless, args, proxy):
            return await fake_launch(headless, args, proxy)
    
    # Create a fake Playwright class with a chromium attribute.
    class FakePlaywright:
        def __init__(self):
            self.chromium = FakeChromium()
    
    # Prepare a BrowserConfig that will force _setup_standard_browser branch.
    config = BrowserConfig(
        headless=True,
        disable_security=False,  # so that disable_security_args is not added
        extra_chromium_args=['--extra-arg'],
        chrome_instance_path=None,
        wss_url=None,
        cdp_url=None,
    )
    
    # Instantiate a Browser with the above config.
    browser_instance = Browser(config)
    
    # Now call _setup_browser with our fake playwright.
    result = await browser_instance._setup_browser(FakePlaywright())
    
    # Confirm that the dummy browser is returned.
    assert result is dummy_browser
@pytest.mark.asyncio
async def test_setup_cdp_browser(monkeypatch):
    """
    Test that _setup_cdp correctly connects to a remote browser via CDP.
    This test uses a fake Playwright object with a fake connect_over_cdp method to
    simulate connecting to a remote browser over CDP. The test verifies that the dummy
    browser instance is returned and that the provided CDP URL is used.
    """
    # Dummy browser instance to be returned by fake_connect_over_cdp.
    dummy_browser = object()
    
    async def fake_connect_over_cdp(cdp_url, timeout=None):
        # Assert that the expected CDP URL is passed.
        assert cdp_url == 'http://dummy-cdp'
        return dummy_browser
    
    class FakeChromium:
        async def connect_over_cdp(self, cdp_url, timeout=None):
            return await fake_connect_over_cdp(cdp_url, timeout)
    
    class FakePlaywright:
        def __init__(self):
            self.chromium = FakeChromium()
    
    # Prepare a BrowserConfig that forces the _setup_cdp branch.
    config = BrowserConfig(
        headless=False,
        disable_security=True,
        extra_chromium_args=[],
        chrome_instance_path=None,
        wss_url=None,
        cdp_url='http://dummy-cdp',
    )
    
    # Instantiate a Browser with the above config.
    browser_instance = Browser(config)
    
    # Call _setup_browser with our fake playwright object.
    result = await browser_instance._setup_browser(FakePlaywright())
    
    # Confirm that the dummy browser is returned.
    assert result is dummy_browser
@pytest.mark.asyncio
async def test_setup_wss_browser(monkeypatch):
    """
    Test that _setup_wss correctly connects to a remote browser via WSS.
    This test uses a fake Playwright object with a fake 'connect' method to simulate
    connecting to a remote browser over WSS. The dummy browser instance is returned,
    verifying that the provided WSS URL is correctly used.
    """
    # Dummy browser instance to be returned by fake_connect.
    dummy_browser = object()
    
    async def fake_connect(wss_url):
        # Assert that the expected WSS URL is passed.
        assert wss_url == 'ws://dummy-wss'
        return dummy_browser
    
    class FakeChromium:
        async def connect(self, wss_url):
            return await fake_connect(wss_url)
    
    class FakePlaywright:
        def __init__(self):
            self.chromium = FakeChromium()
    
    # Prepare a BrowserConfig that forces the _setup_wss branch.
    config = BrowserConfig(
        headless=True,
        disable_security=True,
        extra_chromium_args=[],
        chrome_instance_path=None,
        wss_url='ws://dummy-wss',
        cdp_url=None,
    )
    
    # Instantiate a Browser with the above config.
    browser_instance = Browser(config)
    
    # Now call _setup_browser with our fake playwright.
    result = await browser_instance._setup_browser(FakePlaywright())
    
    # Confirm that the dummy browser is returned.
    assert result is dummy_browser
@pytest.mark.asyncio
async def test_setup_browser_with_instance(monkeypatch):
    """
    Test that _setup_browser_with_instance correctly handles launching a new Chrome instance
    when no existing instance is detected. The first call to requests.get() raises a ConnectionError,
    and subsequent calls return a FakeResponse with a status code 200. Then the browser connects via CDP.
    """
    # Dummy browser instance to be returned by fake_connect_over_cdp.
    dummy_browser = object()
    # Create a counter list to track number of requests.get calls.
    call_count = [0]
    
    # Create a fake response class.
    class FakeResponse:
        def __init__(self, status_code):
            self.status_code = status_code
    # Define the fake requests.get function.
    def fake_requests_get(url, timeout):
        # On the first call, simulate that the instance wasn't started yet.
        if call_count[0] == 0:
            call_count[0] += 1
            raise requests.ConnectionError
        # On subsequent calls, simulate a reachable Chrome instance.
        return FakeResponse(200)
    
    # Monkey-patch the requests module.
    monkeypatch.setattr(requests, "get", fake_requests_get)
    # Monkey-patch subprocess.Popen to do nothing (simulate starting chrome).
    monkeypatch.setattr(subprocess, "Popen", lambda args, stdout, stderr: None)
    
    # Define a fake Chromium class with async connect_over_cdp method.
    class FakeChromium:
        async def connect_over_cdp(self, endpoint_url, timeout):
            # Assert that the endpoint_url and timeout are as expected.
            assert endpoint_url == 'http://localhost:9222'
            assert timeout == 20000
            return dummy_browser
    
    # Define a fake Playwright class with the chromium attribute.
    class FakePlaywright:
        def __init__(self):
            self.chromium = FakeChromium()
    
    # Prepare a BrowserConfig to trigger the chrome_instance_path branch.
    config = BrowserConfig(
        headless=False,
        disable_security=True,
        extra_chromium_args=[],
        chrome_instance_path='/dummy/chrome',
        wss_url=None,
        cdp_url=None,
    )
    
    # Instantiate the Browser with the chrome_instance_path set.
    browser_instance = Browser(config)
    
    # Now call _setup_browser with our fake Playwright.
    result = await browser_instance._setup_browser(FakePlaywright())
    
    # Confirm that the dummy browser is returned.
    assert result is dummy_browser
@pytest.mark.asyncio
async def test_close_browser():
    """
    Test that the close method properly calls close/stop on playwright_browser and playwright,
    and resets these attributes to None.
    """
    # Create fake objects to simulate browser closing and playwright stopping.
    class FakeBrowser:
        def __init__(self):
            self.closed = False
        async def close(self):
            self.closed = True
    class FakePlaywright:
        def __init__(self):
            self.stopped = False
        async def stop(self):
            self.stopped = True
    # Instantiate a Browser with default configuration.
    browser_instance = Browser(BrowserConfig())
    # Assign fake objects.
    fake_browser = FakeBrowser()
    fake_playwright = FakePlaywright()
    browser_instance.playwright_browser = fake_browser
    browser_instance.playwright = fake_playwright
    # Call the close method.
    await browser_instance.close()
    # Verify that the fake methods were called.
    assert fake_browser.closed is True, "Expected the FakeBrowser's close() to be called"
    assert fake_playwright.stopped is True, "Expected the FakePlaywright's stop() to be called"
    # Ensure that the attributes are reset to None.
    assert browser_instance.playwright_browser is None, "Expected playwright_browser to be None after close()"
    assert browser_instance.playwright is None, "Expected playwright to be None after close()"
@pytest.mark.asyncio
async def test_get_playwright_browser_memoization(monkeypatch):
    """
    Test that get_playwright_browser memoizes the browser instance.
    The first call to get_playwright_browser should invoke _init (which we monkey-patch)
    and subsequent calls should return the already initialized browser.
    """
    dummy_browser = object()  # Dummy browser instance to be returned by fake_init.
    calls = []  # To record calls to fake_init.
    async def fake_init(self):
        calls.append(1)
        self.playwright = "fake playwright"  # Dummy value.
        self.playwright_browser = dummy_browser
        return dummy_browser
    # Monkey-patch the _init method on the Browser class.
    monkeypatch.setattr(Browser, "_init", fake_init)
    # Create a Browser with default config.
    config = BrowserConfig()
    browser_instance = Browser(config)
    # First call should trigger fake_init.
    result1 = await browser_instance.get_playwright_browser()
    # Second call should not trigger fake_init again.
    result2 = await browser_instance.get_playwright_browser()
    # Verify that both calls return the same dummy browser.
    assert result1 is dummy_browser
    assert result2 is dummy_browser
    # Verify that fake_init was only called once.
    assert len(calls) == 1, "Expected _init to be called only once"
@pytest.mark.asyncio
async def test_new_context_returns_browser_context(monkeypatch):
    """
    Test that new_context returns an instance of BrowserContext with the correct configuration and a reference
    to the Browser instance.
    """
    # Create a Browser instance with a simple configuration.
    config = BrowserConfig(headless=True, disable_security=True, extra_chromium_args=["--some-arg"])
    browser_instance = Browser(config)
    
    # Prepare a custom BrowserContextConfig instance.
    custom_context_config = BrowserContextConfig()
    
    # Call new_context and capture the returned BrowserContext instance.
    context_instance = await browser_instance.new_context(custom_context_config)
    
    # Verify that the returned object is a BrowserContext.
    assert isinstance(context_instance, BrowserContext), "Expected a BrowserContext instance."
    
    # Verify that the context's config is the custom one supplied.
    assert context_instance.config == custom_context_config, "Expected the context config to match the provided custom config."
    
    # Verify that the Browser reference stored in the context is the same as the browser_instance.
    assert context_instance.browser is browser_instance, "Expected the BrowserContext to reference the original Browser instance."
@pytest.mark.asyncio
async def test_del_schedules_close_on_running_loop(monkeypatch):
    """
    Test that the __del__ method schedules close using create_task on a running loop.
    The test simulates a running event loop by monkey-patching asyncio.get_running_loop and verifies 
    that __del__ correctly schedules a call to close(), which is then executed.
    """
    closed_called = False
    async def fake_close():
        nonlocal closed_called
        closed_called = True
    # Create a fake loop that simulates a running event loop.
    class FakeLoop:
        def __init__(self):
            self.tasks = []
        def is_running(self):
            return True
        def create_task(self, coro):
            self.tasks.append(coro)
            return coro
    fake_loop = FakeLoop()
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: fake_loop)
    # Instantiate a Browser with dummy playwright_browser and playwright attributes so that __del__ goes into the proper branch.
    browser_instance = Browser(BrowserConfig())
    browser_instance.playwright_browser = object()
    browser_instance.playwright = object()
    # Monkey-patch the close method to use our fake_close.
    monkeypatch.setattr(browser_instance, "close", fake_close)
    # Call __del__ explicitly to simulate object destruction.
    browser_instance.__del__()
    # Validate that the fake loop's create_task was indeed called exactly once.
    assert len(fake_loop.tasks) == 1, "Expected create_task to be called exactly once in __del__."
    # Execute the scheduled close coroutine.
    await fake_loop.tasks[0]
    # Verify that the fake close method was called.
    assert closed_called is True, "Expected close() to be executed via create_task in __del__."
@pytest.mark.asyncio
async def test_init_initializes_browser(monkeypatch):
    """
    Test that _init correctly initializes the playwright browser.
    The test monkey-patches async_playwright to simulate starting up a fake Playwright instance,
    and also replaces _setup_browser with a fake that returns a dummy browser instance.
    It then verifies that the Browser instance correctly stores the returned playwright and browser.
    """
    # Dummy browser instance to return
    dummy_browser = object()
    
    # Create a fake Chromium class where launch returns the dummy_browser.
    class FakeChromium:
        async def launch(self, headless, args, proxy):
            return dummy_browser
    # Create a fake Playwright class with chromium attribute.
    class FakePlaywright:
        def __init__(self):
            self.chromium = FakeChromium()
        async def stop(self):
            pass
    # Fake async_playwright context manager class.
    class FakeAsyncPlaywright:
        async def start(self):
            return FakePlaywright()
        async def stop(self):
            pass
    
    # Define a fake async_playwright function that returns our fake async context.
    def fake_async_playwright():
        return FakeAsyncPlaywright()
    
    # Patch the async_playwright in the original module.
    monkeypatch.setattr("browser_use.browser.browser.async_playwright", fake_async_playwright)
    
    # Monkey-patch _setup_browser to simulate a standard browser launch using our FakePlaywright.
    async def fake_setup_browser(self, playwright):
        # Assert that playwright is an instance of FakePlaywright.
        assert isinstance(playwright, FakePlaywright)
        # Simulate launching a browser instance.
        return await playwright.chromium.launch(headless=True, args=["dummy-arg"], proxy=None)
    
    monkeypatch.setattr(Browser, "_setup_browser", fake_setup_browser)
    
    # Prepare a BrowserConfig that forces the standard branch.
    config = BrowserConfig(
        headless=True,
        disable_security=False,
        extra_chromium_args=["--extra-arg"],
        chrome_instance_path=None,
        wss_url=None,
        cdp_url=None,
    )
    
    # Instantiate Browser and call _init.
    browser_instance = Browser(config)
    result = await browser_instance._init()
    
    # Verify that _init returns the dummy_browser and assigns attributes.
    assert result is dummy_browser, "Expected _init to return the dummy browser instance."
    assert browser_instance.playwright is not None, "Expected playwright attribute to be set."
    assert browser_instance.playwright_browser is dummy_browser, \
        "Expected playwright_browser attribute to be the dummy browser instance."
@pytest.mark.asyncio
async def test_del_calls_asyncio_run_when_no_running_loop(monkeypatch):
    """
    Test that __del__ calls asyncio.run when no running event loop is active.
    This test simulates a non-running event loop by returning a fake loop where is_running() returns False.
    It monkey-patches asyncio.run to set a flag and executes the coroutine, ensuring that close() is called.
    """
    run_called = False
    async def fake_close():
        nonlocal run_called
        run_called = True
    # Create a fake loop which indicates it is not running.
    class FakeLoop:
        def is_running(self):
            return False
    fake_loop = FakeLoop()
    def fake_get_running_loop():
        return fake_loop
    # Monkey-patch asyncio.get_running_loop to return our fake loop.
    monkeypatch.setattr(asyncio, "get_running_loop", fake_get_running_loop)
    # Monkey-patch asyncio.run with a fake_run function that executes the coroutine synchronously.
    def fake_run(coro):
        nonlocal run_called
        run_called = True
        # Create and use a new event loop to run the coroutine.
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()
    monkeypatch.setattr(asyncio, "run", fake_run)
    # Instantiate a Browser with dummy playwright attributes so that __del__ will schedule a close.
    browser_instance = Browser(BrowserConfig())
    browser_instance.playwright_browser = object()
    browser_instance.playwright = object()
    # Replace close() to use our fake_close so we can detect if it gets executed.
    monkeypatch.setattr(browser_instance, "close", fake_close)
    # Call __del__ explicitly to simulate cleanup when the object is destroyed.
    browser_instance.__del__()
    # Verify that asyncio.run (fake_run) was called and that it executed close().
    assert run_called is True, "Expected asyncio.run to be called in __del__ when event loop is not running."